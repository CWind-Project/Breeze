from functools import lru_cache
from importlib import resources
import re
import tomllib
import unicodedata
from typing import Any, Iterable

from brich import Rich


_HELPER_ROOT = resources.files("breeze").joinpath("assets", "helper")
_LITERAL_RE = re.compile(r"\[[^\]\r\n]*\]|<[^>\r\n]*>")
_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


class _Message:
    def __init__(self) -> None:
        self._parts: list[str] = []
        self._replacements: dict[str, str] = {}

    def text(self, text: str, style: str = "") -> None:
        if not text:
            return
        pieces: list[str] = []
        cursor = 0
        for match in _LITERAL_RE.finditer(text):
            pieces.append(text[cursor:match.start()])
            token = f"\ue000{len(self._replacements)}\ue001"
            self._replacements[token] = match.group(0)
            pieces.append(token)
            cursor = match.end()
        pieces.append(text[cursor:])
        safe = "".join(pieces)
        self._parts.append(style + safe + ("<Reset>" if style else ""))

    def raw(self, text: str) -> None:
        self._parts.append(text)

    def emit(self) -> None:
        processed = Rich.process("".join(self._parts))
        for token, original in self._replacements.items():
            processed = processed.replace(token, original)
        print(processed)


@lru_cache(maxsize=None)
def _load(name: str) -> dict[str, Any]:
    if not name or any(not (char.isalnum() or char in "-_") for char in name):
        raise KeyError(name)
    resource = _HELPER_ROOT.joinpath(f"{name}.toml")
    return tomllib.loads(resource.read_text(encoding="utf-8"))


def _text(data: dict[str, Any], key: str, default: str = "") -> str:
    value = data.get(key, default)
    return value if isinstance(value, str) else default


def _lines(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _style(data: dict[str, Any], key: str) -> str:
    styles = data.get("style", {})
    if not isinstance(styles, dict):
        return ""
    value = styles.get(key, "")
    return value if isinstance(value, str) else ""


def _markup(data: dict[str, Any], key: str) -> str:
    markup = data.get("markup", {})
    if not isinstance(markup, dict):
        return ""
    value = markup.get(key, "")
    return value if isinstance(value, str) else ""


def _cell_width(text: str) -> int:
    width = 0
    for char in _ANSI_RE.sub("", text):
        if unicodedata.combining(char):
            continue
        width += 2 if unicodedata.east_asian_width(char) in {"W", "F", "A"} else 1
    return width


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _cell_width(text))


def _width(data: dict[str, Any], lines: list[tuple[str | None, str]]) -> int:
    configured = data.get("width", 0)
    content_width = max(
        (_cell_width(text) for text, _style_name in lines if text is not None),
        default=0,
    )
    return max(configured if isinstance(configured, int) else 0, content_width)


def _summary(name: str) -> str:
    return _text(_load(name), "summary")


def _box(data: dict[str, Any], lines: list[tuple[str | None, str]]) -> None:
    width = _width(data, lines)
    border = "+" + "-" * width + "+"
    border_style = _style(data, "border")
    message = _Message()
    message.text(border, border_style)
    message.raw("\n")
    for text, style in lines:
        if text is None:
            message.text(border, border_style)
            message.raw("\n")
            continue
        message.text("|", border_style)
        if style and text.startswith(" "):
            message.text(" ")
            message.text(text[1:], style)
        else:
            message.text(text, style)
        message.text(" " * max(0, width - _cell_width(text)))
        message.text("|", border_style)
        message.raw("\n")
    message.text(border, border_style)
    message.raw("\n")
    message.emit()


def version_text(version: str) -> str:
    return _text(_load("version"), "banner").replace("{version}", version)


def render_version(banner: str) -> int:
    print(banner)
    return 0


def render_welcome(entries: Iterable[tuple[str, str]]) -> int:
    data = _load("welcome")
    message = _Message()
    message.text(_text(data, "title"), _style(data, "title"))
    message.raw("\n\n")
    message.raw(_markup(data, "intro_subject"))
    message.text(_text(data, "intro_subject"))
    message.raw(_markup(data, "intro_text"))
    message.text(_text(data, "intro_text"))
    message.raw(_markup(data, "url"))
    message.text(_text(data, "url"))
    message.raw(_markup(data, "url_label"))
    message.text(_text(data, "url_label"))
    message.raw(_markup(data, "url_end"))
    message.raw("\n\n")
    message.text(_text(data, "usage_heading"), _style(data, "usage_heading"))
    message.raw("\n")
    message.text(_text(data, "usage_indent"))
    message.text(_text(data, "usage_command"), _style(data, "usage_command"))
    message.text(_text(data, "usage_suffix"))
    message.raw("\n\n")
    message.text(_text(data, "commands_heading"), _style(data, "commands_heading"))
    message.raw("\n")

    rows = [(display, _summary(name)) for name, display in entries]
    if rows:
        name_width = max(_cell_width(display) for display, _summary_text in rows)
        for display, summary in rows:
            message.raw("\n")
            message.text(_text(data, "command_indent"))
            message.text(_pad(display, name_width), _style(data, "command"))
            message.text(_text(data, "command_gap"))
            message.text(summary, _style(data, "summary"))
            message.raw("\n")
    message.raw("\n")
    message.emit()
    return 0


def render_command(name: str, options: Iterable[tuple[str, str]]) -> int:
    try:
        data = _load(name)
    except (FileNotFoundError, KeyError):
        return 1
    if not _text(data, "page_title") or not _text(data, "synopsis"):
        return 1

    body_style = _style(data, "body")
    heading_style = _style(data, "heading")
    body_indent = _text(data, "body_indent", "    ")
    lines = [
        (" " + _text(data, "page_title"), _style(data, "title")),
        (None, _style(data, "border")),
        ("", body_style),
        (" " + _text(data, "synopsis_heading"), heading_style),
        ("", body_style),
        (body_indent + _text(data, "synopsis"), body_style),
        ("", body_style),
        (None, _style(data, "border")),
        ("", body_style),
        (" " + _text(data, "description_heading"), heading_style),
        ("", body_style),
    ]
    lines.extend(
        (body_indent + description, body_style)
        for description in _lines(data, "description")
    )
    lines.extend([
        ("", body_style),
        (None, _style(data, "border")),
        ("", body_style),
        (" " + _text(data, "options_heading"), heading_style),
        ("", body_style),
    ])

    option_rows = []
    for option_name, display in options:
        try:
            option_data = _load(option_name)
            summary = _text(option_data, "verbose") or _text(option_data, "summary")
        except (FileNotFoundError, KeyError):
            summary = ""
        option_rows.append((display, summary))
    if option_rows:
        option_width = max(_cell_width(display) for display, _summary_text in option_rows)
        option_gap = _text(data, "option_gap", "    ")
        for display, summary in option_rows:
            lines.append(
                (
                    body_indent
                    + _pad(display, option_width)
                    + option_gap
                    + summary,
                    _style(data, "option"),
                )
            )
    else:
        lines.append((body_indent + _text(data, "empty_options"), body_style))
    lines.append(("", body_style))

    _box(data, lines)
    return 0


def _hint_name(data: dict[str, Any], token: str) -> str:
    label = _text(data, "hint_text_label", "Hint")
    return label + " " * max(0, len(token) - len(label))


def _error_heading(
        data: dict[str, Any],
        message: _Message,
        suffix: str,
) -> None:
    message.text(_text(data, "heading"), _style(data, "heading"))
    message.text(suffix)
    message.raw("\n")


def _error_field(
        message: _Message,
        data: dict[str, Any],
        label: str,
        text: str,
        token: str = "",
) -> None:
    message.text(" ")
    message.text(label)
    message.text(" ")
    if label == _text(data, "hint_label"):
        message.text(_hint_name(data, token))
        message.text(": ")
    else:
        message.text(text)
    if label == _text(data, "hint_label"):
        message.text(text)
    message.raw("\n")


def render_unknown_error(token: str, suggestion: str | None = None) -> int:
    data = _load("errors")
    unknown = data.get("unknown", {})
    if not isinstance(unknown, dict):
        unknown = {}
    message = _Message()
    _error_heading(data, message, _text(data, "heading_suffix_unknown"))
    message.text(" ")
    message.text(_text(data, "error_label"))
    message.text(" ")
    message.text(f"{token}: This is ")
    message.text(_text(data, "not_word"), _style(data, "not_word"))
    message.text(" a breeze command.")
    message.raw("\n")
    message.text(" ")
    message.text(_text(data, "hint_label"))
    message.text(" ")
    message.text(_hint_name(data, token))
    message.text(": ")
    message.text(_text(unknown, "hint_prefix"))
    message.text(_text(unknown, "hint_command"), _style(data, "hint_command"))
    message.text(_text(unknown, "hint_suffix"))
    message.raw("\n")
    if suggestion:
        message.raw("\n")
        message.text(_text(data, "suggestion_heading"), _style(data, "suggestion"))
        message.text(
            _text(data, "suggestion_suffix").format(suggestion=suggestion)
        )
        message.raw("\n        ")
    message.emit()
    return 1


def render_parse_error(token: str, error_message: str) -> int:
    data = _load("errors")
    message = _Message()
    _error_heading(data, message, _text(data, "heading_suffix_unknown"))
    message.text(" ")
    message.text(_text(data, "error_label"))
    message.text(" ")
    message.text(f"{token}: This Command Failed")
    message.raw("\n")
    _error_field(
        message,
        data,
        _text(data, "hint_label"),
        error_message,
        token,
    )
    message.emit()
    return 1


def render_target_error() -> int:
    data = _load("errors")
    target = data.get("target", {})
    if not isinstance(target, dict):
        target = {}
    message = _Message()
    _error_heading(data, message, _text(data, "heading_suffix_target"))
    message.text(_text(data, "target_error_indent", " "))
    message.text(_text(data, "error_label"))
    message.text(" ")
    message.text(_text(target, "failed"))
    message.raw("\n")
    message.text(_text(data, "target_message_indent", "     "))
    message.text(_text(data, "message_label", "Msg"))
    message.text(" : ")
    message.text(_text(target, "message"))
    message.raw("\n")
    _error_field(
        message,
        data,
        _text(data, "hint_label"),
        _text(target, "hint"),
    )
    message.emit()
    return 1


def parse_message(kind: str, **values: str) -> str:
    body = _load("errors").get("parse", {})
    if not isinstance(body, dict):
        return ""
    return _text(body, kind).format(**values)


def helper_summary(name: str) -> str:
    return _summary(name)


__all__ = [
    "helper_summary",
    "parse_message",
    "render_command",
    "render_parse_error",
    "render_target_error",
    "render_unknown_error",
    "render_version",
    "render_welcome",
    "version_text",
]
