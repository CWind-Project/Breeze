import importlib.metadata
import sys
from typing import cast, Any, Iterable
from enum import Enum

from .mutex_argparse import BreezeMutexArgParser, BreezeSubCMDHandle, \
    BreezeArgBox, BreezeSymbols, BreezeArgParseError
from .proj import BreezeProjectCreator
from brich import Rich

__package__ = "breeze"


def version(_: Any) -> str:
    result = """\
Breeze Package Manager for CWind Programming Language
Version: v$ver
Copyright (c) 2026 StarWindv, CWind-Project
SPDX-License-Identifier: BSD-3-Clause
"""
    try:
        return result.replace("$ver", importlib.metadata.version(__package__))
    except importlib.metadata.PackageNotFoundError:
        return "Unknown"


def argparse(argv: list) -> tuple[BreezeArgBox, BreezeMutexArgParser]:
    parser = BreezeMutexArgParser(
        prog="breeze",
        desc="CWind-Lang Official Pkg Manager"
    )
    parser.add_mutually_exclusive(
        "version",
        recv_type=type(None),
        helper="Print the Version of this Breeze",
    )
    parser.add_mutually_exclusive(
        "help",
        recv_type=str,
        helper="Print the Verbose Help Msg for <command>"
    )

    new_sub: BreezeSubCMDHandle = cast(
        BreezeSubCMDHandle,
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
        helper="(Under Dev) Create New CWind Project with Library Mode"
    )
    return parser.parse(argv), parser


def main_help(helper_obj: Enum) -> int:
    msg: str = """\
<Bold><Underline>Welcome to Breeze!<Reset>

<Bold>Breeze<UnBold> is a simple package manager for <Bold><Flashing><HyperStart>\
https://github.com/CWind-Project<HyperText>CWind-Lang<HyperEnd><Reset>

<Bold><Underline>Usage:<Reset>
   [#FFC125]breeze<Reset> [Command] [Args] [Options]

<Bold><Underline>Commands:<Reset>
$cmd
"""
    data = {ele.name: ele.value for ele in cast(
        Iterable, cast(object, helper_obj)
    )}
    max_length = max(len(k) for k in data)
    result = str()
    for k, v in data.items():
        result += f"\n   [#7FFFD4]{k:<{max_length}}<Reset>    {v}\n"
    Rich.print(msg.replace("$cmd", result))
    return 0


def is_empty(obj: list | dict):
    stack = [obj]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            if not current: continue
            stack.extend(current.values())
            continue

        if isinstance(current, (list, tuple, set)):
            if not current: continue
            stack.extend(current)
            continue
        return False

    return True

def main() -> Any | None:
    try:
        box, parser = argparse(sys.argv[:])
        if is_empty(list(vars(box).values())):
            return main_help(parser.get_helper())

        result_map = {
            1: getattr(box, "new", None),
            2: getattr(box, "version", None)
        }
        func = {
            1: lambda path: BreezeProjectCreator.create_proj(cast(str, path)),
            2: lambda _: print(version(_))
        }
        for k, v in result_map.items():
            if v: return func[k](v)
        for k, v in vars(box)[BreezeSymbols.suggestions].items():
            Rich.print(
                f"""\
<Bold><Underline>Breeze<Reset>: 
 [E] {k}: This is <Bold>[#FFC125]not<Reset> a breeze command.
 [N] {"Hint":<{len(k)}}: See "<Bold><Underline>[#7FFFD4]breeze<Reset>" (no argument)

<Bold><Underline>Did you mean<Reset>: "{v[0][0]}" ?
        """
            )
    except BreezeArgParseError as err:
        Rich.print(
f"""\
<Bold><Underline>Breeze<Reset>: 
 [E] {err.token}: This Command Failed
 [N] {"Hint":<{len(err.token)}}: {err.msg}
"""
        )



if __name__ == "__main__":
    main()
