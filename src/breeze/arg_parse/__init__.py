from .fc import BreezeFuzzinessCalculator
from .parser import MutexArgParser, BreezeArgParseError, CWindSubCommandHandle
from typing import cast
import sys
from rich import print as rprint


__all__ = [
    "BreezeArgParseError",
    "BreezeFuzzinessCalculator",
    "CWindSubCommandHandle",
    "MutexArgParser"
]

if __name__ == "__main__":
    my_parser = MutexArgParser(
        prog="breeze",
        desc="CWind-Lang Official Pkg Manager"
    )
    my_parser.add_mutually_exclusive(
        "version",
        recv_type=type(None),
        helper="Print the Version of this Breeze",
    )

    new_sub: CWindSubCommandHandle = cast(
        CWindSubCommandHandle,
        my_parser.add_mutually_exclusive(
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
    result = my_parser.parse(sys.argv)
    rprint(vars(result))
    rprint(result.result)

