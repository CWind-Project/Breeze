import dataclasses
import sys
from typing import Optional, Any, cast

from .fc import FuzzinessCalculator, NonEnglishError, WordVector


@dataclasses.dataclass()
class Symbols:
    """
    用于收集特殊字符串 / 魔法数字, 防止打错
    """
    program_name: str = "prog"
    description : str = "description"
    # command     : str = "command"
    subcmd : str = "subcommand"
    sep    : str = "add_separator" # 如果为 true, 则代表命令必须以 "--" 开头才被视作命令
    me     : str = "mutually_exclusive"
    helper : str = "helper"
    vector : str = "arg_vector"
    recv   : str = "receive_type"  # 无论何时何处, 如果 receive 的 type 被设置为 None, 则代表当前这个命令不需要参数, 如果出现在子命令中, 则代表 True
    default: str = "default"
    ls_cmd : str = "command_list"


class CWArgParseError(ValueError):
    """argv 无法按已注册的规则解析时抛出"""


class CWSubCommandHandle:
    def __init__(self, target: dict) -> None:
        self.__ref = target

    def add_option[T](
        self,
        name: str,
        recv_type: T,
        helper: Optional[str] = "",
        default: Optional[T] = None,
    ) -> None:
        if default is None and (
            recv_type is None or recv_type is type(None)
        ):
            default = False

        self.__ref[Symbols.subcmd][name] = {
            Symbols.recv   : recv_type,
            Symbols.vector : FuzzinessCalculator.word_to_vector(name),
            Symbols.helper : helper,
            Symbols.default: default,
            Symbols.sep : True
        }
        self.__ref[Symbols.subcmd][Symbols.ls_cmd].append(name)


class CWArgBox:
    def __init__(self):
        self._unknown = list()
        self._suggestions: dict[str, list[tuple[str, float]]] = dict()

    def push(self, k, v):
        setattr(self, k, v)

    def unknown(
        self,
        arg: str,
        suggestions: Optional[list[tuple[str, float]]] = None,
    ) -> None:
        self._unknown.append(arg)
        if suggestions:
            self._suggestions[arg] = suggestions

    def suggest(
        self,
        arg: str,
        top: Optional[int] = None,
    ) -> list[str]:
        """返回某个未识别参数的 "did you mean" 候选(按相似度降序)"""
        items = self._suggestions.get(arg, [])
        if top is not None:
            items = items[:top]
        return [name for name, _score in items]


@dataclasses.dataclass()
class _Frame:
    """显式栈上的一层解析上下文"""

    rules: dict[Any, Any]   # 当前层的规则表(含 command_list)
    target: CWArgBox        # 结果挂载到哪个对象上
    seen: dict[str, str] = dataclasses.field(default_factory=dict)  # 本层已解析的命令名 -> 对应 argv token
    exclusive: bool = False # 本层命令是否互斥(顶层 mutually_exclusive 为 True)


class CWArgParser:
    def __init__(
        self,
        prog: str = "",
        desc: str = "",
        suggest_top: int = 3,
        suggest_threshold: float = 85.0,
    ) -> None:
        self._suggest_top = suggest_top
        self._suggest_threshold = suggest_threshold
        self._rule: dict[Any, Any] = {Symbols.me: dict()}
        self._rule.update({
            Symbols.program_name: prog,
            Symbols.description: desc
        })
        self._rule[
            Symbols.me
        ][Symbols.ls_cmd] = set()

    def parse(self, argv: list[str]) -> CWArgBox:
        args = list(argv)
        if args:
            args.pop(0)

        result = CWArgBox()
        stack: list[_Frame] = [
            _Frame(self._rule[Symbols.me], result, exclusive=True)
        ]

        idx = 0
        while idx < len(args):
            token = args[idx]

            # 从栈顶(最内层子命令)开始尝试匹配, 匹配不上就回退到父层;
            # 同时收集失败层级的候选命令, 留给 "did you mean" 使用
            hit, candidates = self._match_or_collect(stack, token)
            if hit is None:
                result.unknown(token, self._suggest(candidates, token))
                idx += 1
                continue

            frame, name, rule = hit
            if frame.exclusive and frame.seen:
                prev = next(iter(frame.seen.values()))
                raise CWArgParseError(
                    f"argument '{token}' conflicts with command "
                    f"'{prev}' already parsed at the same level"
                )
            if name in frame.seen:
                raise CWArgParseError(
                    f"argument '{token}' repeats command "
                    f"'{frame.seen[name]}' at the same level"
                )
            frame.seen[name] = token

            # 挂载本命令自己的值: flag 挂 True, 否则消费下一个 token
            recv = rule[Symbols.recv]
            if self._is_flag(recv):
                frame.target.push(name, True)
                idx += 1
            else:
                raw = self._take_value(args, idx, token)
                frame.target.push(name, self._convert(recv, raw, token))
                idx += 2

            # 带子命令的命令: 挂载子命令默认值, 然后把子规则表压栈
            if Symbols.subcmd in rule:
                self._apply_defaults(rule, frame.target)
                stack.append(_Frame(rule[Symbols.subcmd], frame.target))

        return result

    @staticmethod
    def _is_flag(recv: Any) -> bool:
        return recv is None or recv is type(None)

    @staticmethod
    def _match_command(
        rules: dict[Any, Any],
        token: str,
    ) -> tuple[str, dict[Any, Any]] | None:
        for name in rules[Symbols.ls_cmd]:
            rule = rules[name]
            if rule[Symbols.sep]:
                if token == f"--{name}":
                    return name, rule
            elif token == name:
                return name, rule
        return None

    @classmethod
    def _match_or_collect(
        cls,
        stack: list[_Frame],
        token: str,
    ) -> tuple[
        tuple[_Frame, str, dict[Any, Any]] | None,
        list[tuple[str, str, WordVector[int]]],
    ]:
        candidates: list[tuple[str, str, WordVector[int]]] = []
        while len(stack) > 1:
            matched = cls._match_command(stack[-1].rules, token)
            if matched is not None:
                name, rule = matched
                return (stack[-1], name, rule), candidates
            candidates.extend(cls._candidates(stack[-1].rules))
            stack.pop()

        matched = cls._match_command(stack[0].rules, token)
        if matched is not None:
            name, rule = matched
            return (stack[0], name, rule), candidates
        candidates.extend(cls._candidates(stack[0].rules))
        return None, candidates

    @staticmethod
    def _candidates(
        rules: dict[Any, Any],
    ) -> list[tuple[str, str, WordVector[int]]]:
        """收集一层的候选命令: (名字, 命令行写法, 预计算向量)"""
        out: list[tuple[str, str, WordVector[int]]] = []
        for name in rules[Symbols.ls_cmd]:
            rule = rules[name]
            display = f"--{name}" if rule[Symbols.sep] else name
            out.append((name, display, rule[Symbols.vector]))
        return out

    def _suggest(
        self,
        candidates: list[tuple[str, str, WordVector[int]]],
        token: str,
    ) -> list[tuple[str, float]]:
        """按键盘距离相似度给未识别 token 找同层候选"""
        word = token.lstrip("-").split("=", 1)[0]
        if not word:
            return []
        try:
            token_vec = FuzzinessCalculator.word_to_vector(word)
        except NonEnglishError:
            return []

        scored: list[tuple[str, float]] = []
        for _name, display, vec in candidates:
            try:
                score = float(
                    FuzzinessCalculator.calc_similarity(token_vec, vec)
                )
            except NonEnglishError:
                continue
            if score >= self._suggest_threshold:
                scored.append((display, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[: self._suggest_top]

    @staticmethod
    def _take_value(args: list[str], idx: int, token: str) -> str:
        if idx + 1 >= len(args):
            raise CWArgParseError(
                f"argument '{token}' requires a value"
            )
        return args[idx + 1]

    @staticmethod
    def _convert(recv: Any, raw: str, token: str) -> Any:
        try:
            if recv is bool:
                return raw.strip().lower() in {"1", "true", "yes", "on"}
            return recv(raw)
        except (TypeError, ValueError) as exc:
            name = getattr(recv, "__name__", str(recv))
            raise CWArgParseError(
                f"argument '{token}': cannot convert '{raw}' to {name}"
            ) from exc

    @staticmethod
    def _apply_defaults(
        rule: dict[Any, Any],
        target: CWArgBox,
    ) -> None:
        subs = rule.get(Symbols.subcmd)
        if subs is None:
            return
        for name in subs[Symbols.ls_cmd]:
            default = subs[name].get(Symbols.default)
            if default is not None:
                target.push(name, default)


    def add_mutually_exclusive(
        self,
        name: str,
        recv_type: type,
        helper: Optional[str] = "",
        add_separator: Optional[bool] = False,
        need_subcmd  : bool = False
    ) -> CWSubCommandHandle | None:
        self._rule[
            Symbols.me
        ][name] = {
            Symbols.recv  : recv_type,
            Symbols.vector: FuzzinessCalculator.word_to_vector(name),
            Symbols.helper: helper,
            Symbols.sep   : add_separator
        }
        self._rule[
            Symbols.me
        ][Symbols.ls_cmd].add(name)
        if need_subcmd:
            self._rule[
                Symbols.me
            ][name][Symbols.subcmd] = dict()
            self._rule[
                Symbols.me
            ][name][Symbols.subcmd][Symbols.ls_cmd] = []
            return CWSubCommandHandle(
                self._rule[
                    Symbols.me
                ][name]
            )
        return None


if __name__ == "__main__":
    parser = CWArgParser(
        prog="breeze",
        desc="CWind-Lang Official Pkg Manager"
    )
    parser.add_mutually_exclusive(
        "version",
        recv_type=type(None),
        helper="Print the Version of this Breeze",
    )

    new_sub: CWSubCommandHandle = cast(
        CWSubCommandHandle,
        parser.add_mutually_exclusive(
            "new",
            recv_type=str,
            helper="Create New CWind Project from Template",
            need_subcmd=True
        )
    )
    new_sub.add_option(
        "lib",
        type(None),
        helper="Create New CWind Project with Library Mode"
    )
    new_sub.add_option(
        "name",
        str,
        helper="Project name override",
        default="default-name",
    )

    try:
        box = parser.parse(sys.argv)
        public = {
            k: v for k, v in vars(box).items()
            if not k.startswith("_")
        }
        unknown = list(box._unknown)
        did_you_mean = {
            arg: box.suggest(arg, top=3)
            for arg in unknown
        }
        print(
            f"{sys.argv[1:]} -> {public}, \n"
            f"unknown={unknown}, did_you_mean={did_you_mean}"
        )
    except CWArgParseError as exc:
        print(f"{sys.argv[1:]} -> CWArgParseError: {exc}")



