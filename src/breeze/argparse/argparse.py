import dataclasses
from typing import Optional, Any, cast

from rich import print as rprint

from .fc import FuzzinessCalculator


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
        if not isinstance(bool, type(default)) and recv_type is None:
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

    def push(self, k, v):
        setattr(self, k, v)

    def unknown(self, arg) -> None:
        self._unknown.append(arg)


class CWArgParser:
    def __init__(
        self,
        prog: str = "",
        desc: str = ""
    ) -> None:
        self._rule: dict[Any, Any] = {Symbols.me: dict()}
        self._rule.update({
            Symbols.program_name: prog,
            Symbols.description: desc
        })
        self._rule[
            Symbols.me
        ][Symbols.ls_cmd] = set()

    def parse(self, argv: list[str]) -> CWArgBox:
        argv.pop(0)
        rprint(self._rule)
        rprint(argv)

        result = CWArgBox()
        stack: list[Any] = list()

        for idx in range(len(argv)):
            arg = argv[idx]
            # todo
        return result


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
    import sys

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
    parser.parse(sys.argv)



