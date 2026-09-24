import importlib.metadata
import sys
from typing import Any, cast

from .help_renderer import (
    render_command,
    render_command_error,
    render_parse_error,
    render_unknown_error,
    render_version,
    render_welcome,
    version_text,
)
from .mutex_argparse import BreezeMutexArgParser, BreezeSubCMDHandle, \
    BreezeArgBox, BreezeArgParseError
from .proj import (
    BreezeBuildError,
    BreezeProjectCreator,
    build_project,
    check_project,
)

__package__ = "breeze"


def version(*_) -> str:
    try:
        value = importlib.metadata.version(__package__ or "breeze")
    except importlib.metadata.PackageNotFoundError:
        value = "Unknown"
    return version_text(value)


def argparse(argv: list) -> tuple[BreezeArgBox, BreezeMutexArgParser]:
    argv = list(argv)
    if len(argv) >= 4 and argv[1:3] == ["new", "--lib"]:
        argv = [argv[0], "new", argv[3], "--lib", *argv[4:]]
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

    build_sub: BreezeSubCMDHandle = cast(
        BreezeSubCMDHandle,
        parser.add_mutually_exclusive(
            "build",
            recv_type=str,
            need_subcmd=True,
            optional_value=True,
        )
    )
    build_sub.add_option("build-args", str)
    parser.add_mutually_exclusive(
        "check",
        recv_type=str,
        optional_value=True,
    )
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

        if box.unknown_args:
            for token in box.unknown_args:
                suggestions = box.suggestions.get(token, [])
                suggestion = suggestions[0][0] if suggestions else None
                return render_unknown_error(token, suggestion)
        if hasattr(box, "build"):
            return build_project(
                getattr(box, "build"),
                vars(box).get("build-args"),
            )
        if hasattr(box, "check"):
            return check_project(getattr(box, "check"))
        if hasattr(box, "new"):
            return BreezeProjectCreator.create_proj(
                cast(str, getattr(box, "new")),
                is_lib=bool(getattr(box, "lib", False)),
            )
        if hasattr(box, "version"):
            return render_version(version())
        if hasattr(box, "help"):
            return help_sth(getattr(box, "help"), parser)
    except BreezeArgParseError as err:
        return render_parse_error(err.token, err.msg)
    except BreezeBuildError as err:
        return render_command_error(str(err))


if __name__ == "__main__":
    main()
