from typing import cast
import sys
from rich import print as rprint
from .arg_parse import MutexArgParser, BreezeSubCommandHandle, BreezeArgBox


def argparse() -> BreezeArgBox:
    parser = MutexArgParser(
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
        helper="Print the Help Msg for <command>"
    )

    new_sub: BreezeSubCommandHandle = cast(
        BreezeSubCommandHandle,
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
    return parser.parse(sys.argv)

rprint(argparse())
