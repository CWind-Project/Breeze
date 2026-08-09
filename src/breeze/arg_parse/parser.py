import dataclasses
from typing import Optional, Any, cast
from rich import print as rprint

from .fc import BreezeFuzzinessCalculator, BreezeNonEnglishError, BreezeWordVector


@dataclasses.dataclass()
class BreezeSymbols:
    program_name: str = "prog"
    description : str = "description"
    suggestions : str = "suggestions"
    subcmd : str = "subcommand"
    sep    : str = "add_separator" # 如果为 true, 则代表命令必须以 "--" 开头才被视作命令
    me     : str = "mutually_exclusive"
    helper : str = "helper"
    vector : str = "arg_vector"
    recv   : str = "receive_type"  # 无论何时何处, 如果 receive 的 type 被设置为 None, 则代表当前这个命令不需要参数, 如果出现在子命令中, 则代表 True
    default: str = "default"
    ls_cmd : str = "command_list"


class BreezeArgParseError(ValueError):
    """argv 无法按已注册的规则解析时抛出"""


class CWindSubCommandHandle:
    def __init__(self, target: dict) -> None:
        self.__ref = target

    def add_option[T](
        self,
        name: str,
        recv_type: T,
        helper: Optional[str] = "",
        default: Optional[T|bool] = None,
    ) -> None:
        if default is None and (
            recv_type is None or recv_type is type(None)
        ):
            default = False

        self.__ref[BreezeSymbols.subcmd][name] = {
            BreezeSymbols.recv   : recv_type,
            BreezeSymbols.vector : BreezeFuzzinessCalculator.word_to_vector(name),
            BreezeSymbols.helper : helper,
            BreezeSymbols.default: default,
            BreezeSymbols.sep : True
        }
        self.__ref[BreezeSymbols.subcmd][BreezeSymbols.ls_cmd].append(name)


class BreezeArgBox:
    def __init__(self):
        self.unknown_args = list()
        self.result: dict[str, Any] = {
            BreezeSymbols.suggestions: {}
        }
        self.did_you_mean = None
        self.suggestions: dict[str, list[tuple[str, float]]] = self.result[BreezeSymbols.suggestions]

    def push(self, k, v):
        setattr(self, k, v)
        self.result.update( { k:v } )

    def unknown(
        self,
        arg: str,
        suggestions: Optional[list[tuple[str, float]]] = None,
    ) -> None:
        self.unknown_args.append(arg)
        if suggestions:
            self.suggestions[arg] = suggestions

    def suggest(
        self,
        arg: str,
        top: Optional[int] = None,
    ) -> list[str]:
        items = self.suggestions.get(arg, [])
        if top is not None:
            items = items[:top]
        return [name for name, _score in items]


@dataclasses.dataclass()
class _Frame:
    """显式栈上的一层解析上下文"""

    rules: dict[Any, Any]   # 当前层的规则表(含 command_list)
    target: BreezeArgBox        # 结果挂载到哪个对象上
    seen: dict[str, str] = dataclasses.field(default_factory=dict)  # 本层已解析的命令名 -> 对应 argv token
    exclusive: bool = False # 本层命令是否互斥(顶层 mutually_exclusive 为 True)


class MutexArgParser:
    def __init__(
        self,
        prog: str = "",
        desc: str = "",
        suggest_top: int = 3,
        suggest_threshold: float = 85.0,
    ) -> None:
        self._suggest_top = suggest_top
        self._suggest_threshold = suggest_threshold
        self._rule: dict[Any, Any] = {BreezeSymbols.me: dict()}
        self._rule.update({
            BreezeSymbols.program_name: prog,
            BreezeSymbols.description: desc
        })
        self._rule[
            BreezeSymbols.me
        ][BreezeSymbols.ls_cmd] = set()

    def __parse(self, argv: list[str]) -> BreezeArgBox:
        args = list(argv)
        if args:
            args.pop(0)

        result = BreezeArgBox()
        stack: list[_Frame] = [
            _Frame(self._rule[BreezeSymbols.me], result, exclusive=True)
        ]

        idx = 0
        while idx < len(args):
            token = args[idx]

            hit, candidates = self._match_or_collect(stack, token)
            if hit is None:
                result.unknown(token, self._suggest(candidates, token))
                idx += 1
                continue

            frame, name, rule = hit
            if frame.exclusive and frame.seen:
                prev = next(iter(frame.seen.values()))
                raise BreezeArgParseError(
                    f"argument '{token}' conflicts with command "
                    f"'{prev}' already parsed at the same level"
                )
            if name in frame.seen:
                raise BreezeArgParseError(
                    f"argument '{token}' repeats command "
                    f"'{frame.seen[name]}' at the same level"
                )
            frame.seen[name] = token

            recv = rule[BreezeSymbols.recv]
            if self._is_flag(recv):
                frame.target.push(name, True)
                idx += 1
            else:
                raw = self._take_value(args, idx, token)
                frame.target.push(name, self._convert(recv, raw, token))
                idx += 2

            if BreezeSymbols.subcmd in rule:
                self._apply_defaults(rule, frame.target)
                stack.append(_Frame(rule[BreezeSymbols.subcmd], frame.target))

        return result

    @staticmethod
    def _is_flag(recv: Any) -> bool:
        return recv is None or recv is type(None)

    @staticmethod
    def _match_command(
        rules: dict[Any, Any],
        token: str,
    ) -> tuple[str, dict[Any, Any]] | None:
        for name in rules[BreezeSymbols.ls_cmd]:
            rule = rules[name]
            if rule[BreezeSymbols.sep]:
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
        list[tuple[str, str, BreezeWordVector[int]]],
    ]:
        candidates: list[tuple[str, str, BreezeWordVector[int]]] = []
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
    ) -> list[tuple[str, str, BreezeWordVector[int]]]:
        """收集一层的候选命令: (名字, 命令行写法, 预计算向量)"""
        out: list[tuple[str, str, BreezeWordVector[int]]] = []
        for name in rules[BreezeSymbols.ls_cmd]:
            rule = rules[name]
            display = f"--{name}" if rule[BreezeSymbols.sep] else name
            out.append((name, display, rule[BreezeSymbols.vector]))
        return out

    def _suggest(
        self,
        candidates: list[tuple[str, str, BreezeWordVector[int]]],
        token: str,
    ) -> list[tuple[str, float]]:
        word = token.lstrip("-").split("=", 1)[0]
        if not word:
            return []
        try:
            token_vec = BreezeFuzzinessCalculator.word_to_vector(word)
        except BreezeNonEnglishError:
            return []

        scored: list[tuple[str, float]] = []
        for _name, display, vec in candidates:
            try:
                score = float(
                    BreezeFuzzinessCalculator.calc_similarity(token_vec, vec)
                )
            except BreezeNonEnglishError:
                continue
            if score >= self._suggest_threshold:
                scored.append((display, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[: self._suggest_top]

    @staticmethod
    def _take_value(args: list[str], idx: int, token: str) -> str:
        if idx + 1 >= len(args):
            raise BreezeArgParseError(
                f"argument '{token}' requires a value"
            )
        return args[idx + 1]

    @staticmethod
    def _convert(recv: Any, raw: str, token: str) -> Any:
        try:
            if recv is bool:
                return raw.strip().lower() in {"1", "true", "yes", "on"}
            return recv(raw)
        except (TypeError, ValueError) as err:
            name = getattr(recv, "__name__", str(recv))
            raise BreezeArgParseError(
                f"argument '{token}': cannot convert '{raw}' to {name}"
            ) from err

    @staticmethod
    def _apply_defaults(
        rule: dict[Any, Any],
        target: BreezeArgBox,
    ) -> None:
        subs = rule.get(BreezeSymbols.subcmd)
        if subs is None:
            return
        subs = cast(dict, subs)
        for name in subs[BreezeSymbols.ls_cmd]:
            default = subs[name].get(BreezeSymbols.default)
            if default is not None:
                target.push(name, default)


    def add_mutually_exclusive(
        self,
        name: str,
        recv_type: type,
        helper: Optional[str] = "",
        add_separator: Optional[bool] = False,
        need_subcmd  : bool = False
    ) -> CWindSubCommandHandle | None:
        self._rule[
            BreezeSymbols.me
        ][name] = {
            BreezeSymbols.recv  : recv_type,
            BreezeSymbols.vector: BreezeFuzzinessCalculator.word_to_vector(name),
            BreezeSymbols.helper: helper,
            BreezeSymbols.sep   : add_separator
        }
        self._rule[
            BreezeSymbols.me
        ][BreezeSymbols.ls_cmd].add(name)
        if need_subcmd:
            self._rule[
                BreezeSymbols.me
            ][name][BreezeSymbols.subcmd] = dict()
            self._rule[
                BreezeSymbols.me
            ][name][BreezeSymbols.subcmd][BreezeSymbols.ls_cmd] = []
            return CWindSubCommandHandle(
                self._rule[
                    BreezeSymbols.me
                ][name]
            )
        return None

    def parse(self, argv: list[str]) -> BreezeArgBox:
        rprint(self._rule)
        result = self.__parse(argv)
        suggestion = {
            arg: result.suggest(arg, top=3)
            for arg in result.unknown_args
        }
        result.did_you_mean = suggestion
        return result
