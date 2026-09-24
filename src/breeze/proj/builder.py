import os
import shlex
import shutil
import subprocess
import tomllib
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from brich import Rich


class BreezeBuildError(RuntimeError):
    pass


def _project_root(path: str | Path | None) -> Path:
    start = Path.cwd() if path is None else Path(path).expanduser()
    try:
        resolved = start.resolve()
    except OSError as exc:
        raise BreezeBuildError(f"cannot resolve project path: {exc}") from exc
    if not resolved.exists():
        raise BreezeBuildError(f"project path does not exist: {resolved}")
    if not resolved.is_dir():
        raise BreezeBuildError(f"project path is not a directory: {resolved}")
    for root in (resolved, *resolved.parents):
        if (root / "Breeze.toml").is_file():
            return root
    raise BreezeBuildError(f"Breeze.toml not found from: {resolved}")


def _is_library(root: Path) -> bool:
    manifest = root / "Breeze.toml"
    try:
        data = tomllib.loads(manifest.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise BreezeBuildError(f"cannot read {manifest}: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise BreezeBuildError(f"invalid {manifest}: {exc}") from exc
    entry = data.get("entry")
    if not isinstance(entry, dict):
        raise BreezeBuildError(f"invalid {manifest}: missing [entry]")
    return entry.get("is_lib") is True


def _frontend_command() -> list[str]:
    executable = shutil.which("cwindf")
    if not executable:
        raise BreezeBuildError("cwindf was not found on PATH")
    return [executable]


def _run(command: list[str]) -> int:
    try:
        return subprocess.run(command, check=False).returncode
    except OSError as exc:
        raise BreezeBuildError(f"cannot run {command[0]}: {exc}") from exc


def _split_args(value: str | None, option: str) -> list[str]:
    if not value:
        return []
    try:
        return shlex.split(value)
    except ValueError as exc:
        raise BreezeBuildError(f"invalid {option}: {exc}") from exc


def _frontend_args(is_lib: bool) -> list[str]:
    args = ["--project"]
    if is_lib:
        args.extend(["--emit", "share"])
    return args


@contextmanager
def _project_cwd(path: Path) -> Iterator[None]:
    if path == Path.cwd().resolve():
        yield
        return
    previous = Path.cwd()
    try:
        os.chdir(path)
    except OSError as exc:
        raise BreezeBuildError(f"cannot enter project path {path}: {exc}") from exc
    try:
        yield
    finally:
        os.chdir(previous)


def _requested_path(path: str | Path | None) -> Path:
    try:
        return (Path.cwd() if path is None else Path(path).expanduser()).resolve()
    except OSError as exc:
        raise BreezeBuildError(f"cannot resolve project path: {exc}") from exc


def check_project(
        path: str | Path | None = None,
        frontend_args: str | None = None,
) -> int:
    root = _project_root(path)
    is_lib = _is_library(root)
    extra = _split_args(frontend_args, "--frontend-args")
    requested = _requested_path(path)
    with _project_cwd(requested):
        return _run([
            *_frontend_command(),
            *_frontend_args(is_lib),
            *extra,
        ])


def _cwindc_path() -> Path:
    from cwind_frontend.home import install_root

    root = install_root()
    if root is None:
        raise BreezeBuildError("cannot locate the CWind installation root")
    name = "cwindc.exe" if os.name == "nt" else "cwindc"
    path = root / "build" / name
    if not path.is_file():
        raise BreezeBuildError(f"cwindc was not found: {path}")
    return path


def frontend_help() -> int:
    return _run([*_frontend_command(), "--help"])


def backend_help() -> int:
    return _run([str(_cwindc_path()), "--help"])


def build_project(
        path: str | Path | None = None,
        build_args: str | None = None,
        frontend_args: str | None = None,
) -> int:
    root = _project_root(path)
    is_lib = _is_library(root)
    extra = _split_args(build_args, "--build-args")
    frontend_extra = _split_args(frontend_args, "--frontend-args")

    requested = _requested_path(path)
    with _project_cwd(requested):
        result = _run([
            *_frontend_command(),
            *_frontend_args(is_lib),
            *frontend_extra,
        ])
    if result != 0:
        return result

    project_json = root / "target" / "project.json"
    if not project_json.is_file():
        raise BreezeBuildError(f"cwindf did not create: {project_json}")

    command = [str(_cwindc_path()), *extra]
    if is_lib:
        command.extend(["--emit", "share"])
    command.append(str(project_json))
    result = _run(command)
    if result == 0:
        Rich.print("[<Bold><Underline>Breeze<Reset>] Done")
    return result


__all__ = [
    "BreezeBuildError",
    "backend_help",
    "build_project",
    "check_project",
    "frontend_help",
]
