import dataclasses
from typing import Optional, Any, cast

from ..correct import Matcher
from .fc import BreezeFuzzinessCalculator, BreezeWordVector


@dataclasses.dataclass()
class BreezeSymbols:
    program_name: str = "prog"
    description: str = "description"
    suggestions: str = "suggestions"
    subcmd: str = "subcommand"
    sep: str = "add_separator"  # 如果为 true, 则代表命令必须以 "--" 开头才被视作命令
    me: str = "mutually_exclusive"
    helper: str = "helper"
    vector: str = "arg_vector"
    recv: str = "receive_type"  # 无论何时何处, 如果 receive 的 type 被设置为 None, 则代表当前这个命令不需要参数, 如果出现在子命令中, 则代表 True
    default: str = "default"
    ls_cmd: str = "command_list"
    debug_env: str = "BREEZE_DEBUG"


class BreezeArgParseError(ValueError):
    def __init__(self, msg, token: str, *args, **kwargs):
        super().__init__(msg)
        self.token = token
        self.msg = msg


class BreezeSubCMDHandle:
    def __init__(self, target: dict) -> None:
        self.__ref = target

    def add_option[T](
            self,
            name: str,
            recv_type: T,
            helper: str = "",
            default: Optional[T | bool] = None,
    ) -> None:
        if default is None and (
                recv_type is None or recv_type is type(None)
        ):
            default = False

        self.__ref[BreezeSymbols.subcmd][name] = {
            BreezeSymbols.recv: recv_type,
            BreezeSymbols.vector: BreezeFuzzinessCalculator.word_to_vector(
                name),
            BreezeSymbols.helper: helper,
            BreezeSymbols.default: default,
            BreezeSymbols.sep: True
        }
        self.__ref[BreezeSymbols.subcmd][BreezeSymbols.ls_cmd].append(name)


class BreezeArgBox:
    def __init__(self):
        self.unknown_args = list()
        self.did_you_mean = None
        self.suggestions: dict[str, list[tuple[str, float]]] = {}

    def push(self, k, v):
        setattr(self, k, v)

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

    def __str__(self) -> str:
        return str(vars(self))


@dataclasses.dataclass()
class _BreezeParserFrame:
    rules: dict[Any, Any]  # 当前层的规则表(含 command_list)
    target: BreezeArgBox  # 结果挂载到哪个对象上
    seen: dict[str, str] = dataclasses.field(
        default_factory=dict)  # 本层已解析的命令名 -> 对应 argv token
    exclusive: bool = False  # 本层命令是否互斥(顶层 mutually_exclusive 为 True)


class BreezeParserEngine:
    def __init__(
            self,
            prog: str = "",
            desc: str = "",
            suggest_top: int = 3,
            suggest_threshold: float = 0.0,
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

    def _parse(self, argv: list[str]) -> BreezeArgBox:
        if argv:
            argv.pop(0)

        result = BreezeArgBox()
        stack: list[_BreezeParserFrame] = [
            _BreezeParserFrame(self._rule[BreezeSymbols.me], result, exclusive=True)
        ]

        idx = 0
        while idx < len(argv):
            token = argv[idx]

            hit, candidates = self.__match_or_collect(stack, token)
            if hit is None:
                result.unknown(token, self.__suggest(candidates, token))
                idx += 1
                continue

            frame, name, rule = hit
            if frame.exclusive and frame.seen:
                prev = next(iter(frame.seen.values()))
                raise BreezeArgParseError(
                    f"argument \"{token}\" conflicts with command "
                    f"\"{prev}\" already parsed at the same level",
                    token
                )
            if name in frame.seen:
                raise BreezeArgParseError(
                    f"argument \"{token}\" repeats command "
                    f"\"{frame.seen[name]}\" at the same level",
                    token
                )
            frame.seen[name] = token

            recv = rule[BreezeSymbols.recv]
            if self.__is_flag(recv):
                frame.target.push(name, True)
                idx += 1
            else:
                raw = self.__take_value(argv, idx, token)
                frame.target.push(name, self.__convert(recv, raw, token))
                idx += 2

            if BreezeSymbols.subcmd in rule:
                self.__apply_defaults(rule, frame.target)
                stack.append(_BreezeParserFrame(rule[BreezeSymbols.subcmd], frame.target))

        return result

    @staticmethod
    def __is_flag(recv: Any) -> bool:
        return recv is None or recv is type(None)

    @staticmethod
    def __match_command(
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
    def __match_or_collect(
            cls,
            stack: list[_BreezeParserFrame],
            token: str,
    ) -> tuple[
        tuple[_BreezeParserFrame, str, dict[Any, Any]] | None,
        list[tuple[str, str, BreezeWordVector]],
    ]:
        candidates: list[tuple[str, str, BreezeWordVector]] = []
        while len(stack) > 1:
            matched = cls.__match_command(stack[-1].rules, token)
            if matched is not None:
                name, rule = matched
                return (stack[-1], name, rule), candidates
            candidates.extend(cls.__candidates(stack[-1].rules))
            stack.pop()

        matched = cls.__match_command(stack[0].rules, token)
        if matched is not None:
            name, rule = matched
            return (stack[0], name, rule), candidates
        candidates.extend(cls.__candidates(stack[0].rules))
        return None, candidates

    @staticmethod
    def __candidates(
            rules: dict[Any, Any],
    ) -> list[tuple[str, str, BreezeWordVector]]:
        """收集一层的候选命令: (名字, 命令行写法, 预计算向量)"""
        out: list[tuple[str, str, BreezeWordVector]] = []
        for name in rules[BreezeSymbols.ls_cmd]:
            rule = rules[name]
            display = f"--{name}" if rule[BreezeSymbols.sep] else name
            out.append((name, display, rule[BreezeSymbols.vector]))
        return out

    def __suggest(
            self,
            candidates: list[tuple[str, str, BreezeWordVector]],
            token: str,
    ) -> list[tuple[str, float]]:
        word = token.lstrip("-").split("=", 1)[0]
        if not word or self._suggest_top <= 0:
            return []

        vocabulary = [name for name, _display, _vector in candidates]
        if not vocabulary:
            return []

        matcher = Matcher(vocabulary)
        display_by_name = {
            name: display for name, display, _vector in candidates
        }
        scored: list[tuple[str, float]] = []
        for candidate in matcher.rank(word, topk=len(vocabulary)):
            if not matcher.is_match(candidate.word, word):
                continue
            score = candidate.similarity * 100.0
            if score < self._suggest_threshold:
                continue
            scored.append((display_by_name[candidate.word], score))
            if len(scored) >= self._suggest_top:
                break
        return scored

    @staticmethod
    def __take_value(args: list[str], idx: int, token: str) -> str:
        if idx + 1 >= len(args):
            raise BreezeArgParseError(
                f"argument \"{token}\" requires a value",
                token
            )
        return args[idx + 1]

    @staticmethod
    def __convert(recv: Any, raw: str, token: str) -> Any:
        try:
            if recv is bool:
                return raw.strip().lower() in {"1", "true", "yes", "on"}
            return recv(raw)
        except (TypeError, ValueError) as err:
            name = getattr(recv, "__name__", str(recv))
            raise BreezeArgParseError(
                f"argument \"{token}\": cannot convert \"{raw}\" to {name}",
                token
            ) from err

    @staticmethod
    def __apply_defaults(
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


__all__ = [
    "BreezeParserEngine",
    "BreezeArgBox",
    "BreezeArgParseError",
    "BreezeSubCMDHandle",
    "BreezeSymbols"
]
