import importlib.metadata
import sys
from typing import Any, cast

from .help_renderer import (
    render_command,
    render_parse_error,
    render_unknown_error,
    render_version,
    render_welcome,
    version_text,
)
from .mutex_argparse import BreezeMutexArgParser, BreezeSubCMDHandle, \
    BreezeArgBox, BreezeSymbols, BreezeArgParseError
from .proj import BreezeProjectCreator

__package__ = "breeze"


def version(*_) -> str:
    try:
        value = importlib.metadata.version(__package__ or "breeze")
    except importlib.metadata.PackageNotFoundError:
        value = "Unknown"
    return version_text(value)


def argparse(argv: list) -> tuple[BreezeArgBox, BreezeMutexArgParser]:
    parser = BreezeMutexArgParser(prog="breeze")
    parser.add_mutually_exclusive("version", recv_type=type(None))
    parser.add_mutually_exclusive("help", recv_type=str)

    new_sub: BreezeSubCMDHandle = cast(
        BreezeSubCMDHandle,
        parser.add_mutually_exclusive(
            "new",
            recv_type=str,
            need_subcmd=True
        )
    )
    new_sub.add_option("lib", type(None))
    return parser.parse(argv), parser


def main_help(parser: BreezeMutexArgParser) -> int:
    return render_welcome(parser.command_entries())


def help_sth(sth: str, parser: BreezeMutexArgParser) -> int:
    return render_command(sth, parser.option_entries(sth))


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
            return main_help(parser)
        elif getattr(box, "help", None):
            return help_sth(getattr(box, "help"), parser)

        result_map = {
            1: getattr(box, "new", None),
            2: getattr(box, "version", None),
            3: getattr(box, "help", None)
        }
        func = {
            1: lambda path: BreezeProjectCreator.create_proj(cast(str, path)),
            2: lambda _: render_version(version(_)),
            3: lambda sth: help_sth(sth, parser)
        }
        for k, v in result_map.items():
            if v:
                return func[k](v)
        for token, suggestions in vars(box)[BreezeSymbols.suggestions].items():
            suggestion = suggestions[0][0] if suggestions else None
            return render_unknown_error(token, suggestion)
    except BreezeArgParseError as err:
        return render_parse_error(err.token, err.msg)


if __name__ == "__main__":
    main()
