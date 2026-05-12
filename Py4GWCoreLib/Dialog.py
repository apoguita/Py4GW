from __future__ import annotations

import re
from typing import Any

try:
    import PyDialog
except Exception:  # pragma: no cover - runtime specific
    PyDialog = None


_COLOR_TAG_RE = re.compile(r"</?c(?:=[^>]*)?>", re.IGNORECASE)
_GENERIC_TAG_RE = re.compile(r"</?[A-Za-z][A-Za-z0-9:_-]*(?:\s+[^>]*)?>", re.IGNORECASE)
_LBRACKET_TOKEN_RE = re.compile(r"\[lbracket\]", re.IGNORECASE)
_RBRACKET_TOKEN_RE = re.compile(r"\[rbracket\]", re.IGNORECASE)
_ORPHAN_BREAK_TOKEN_RE = re.compile(r"(?<!\w)(?:brx|br)(?!\w)", re.IGNORECASE)
_ORPHAN_PARAGRAPH_TOKEN_RE = re.compile(r"(?<!\w)p(?!\w)")
_MISSING_SPACE_AFTER_PUNCT_RE = re.compile(r"([!?:;\)\]])([A-Za-z0-9])")
_MISSING_SPACE_ALPHA_NUM_RE = re.compile(r"([A-Za-z])(\d{2,})")
_MISSING_SPACE_NUM_ALPHA_RE = re.compile(r"(\d{2,})([A-Za-z])")
_MISSING_SPACE_CAMEL_RE = re.compile(r"([a-z])([A-Z])")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_INLINE_CHOICE_RE = re.compile(r"<a\s*=\s*([^>]+)>(.*?)</a>", re.IGNORECASE | re.DOTALL)


def _safe_call(default: Any, callback):
    try:
        return callback()
    except Exception:
        return default


def _call_native_dialog_method(method_name: str, default: Any, *args: Any, **kwargs: Any) -> Any:
    if PyDialog is None:
        return default
    method = getattr(PyDialog.PyDialog, method_name, None)
    if not callable(method):
        return default
    return _safe_call(default, lambda: method(*args, **kwargs))


def _coerce_native_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        return list(value)
    except TypeError:
        return []


def sanitize_dialog_text(value: str | None) -> str:
    if not value:
        return ""
    text = str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _LBRACKET_TOKEN_RE.sub("[", text)
    text = _RBRACKET_TOKEN_RE.sub("]", text)
    text = _COLOR_TAG_RE.sub("", text)
    text = _GENERIC_TAG_RE.sub("", text)
    text = _ORPHAN_BREAK_TOKEN_RE.sub(" ", text)
    text = _ORPHAN_PARAGRAPH_TOKEN_RE.sub(" ", text)
    text = _MISSING_SPACE_AFTER_PUNCT_RE.sub(r"\1 \2", text)
    text = _MISSING_SPACE_ALPHA_NUM_RE.sub(r"\1 \2", text)
    text = _MISSING_SPACE_NUM_ALPHA_RE.sub(r"\1 \2", text)
    text = _MISSING_SPACE_CAMEL_RE.sub(r"\1 \2", text)
    text = _CONTROL_CHARS_RE.sub("", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()


class ActiveDialogInfo:
    def __init__(self, native_active_dialog=None):
        self.native = native_active_dialog
        self.dialog_id = int(getattr(native_active_dialog, "dialog_id", 0) or 0)
        self.context_dialog_id = int(getattr(native_active_dialog, "context_dialog_id", 0) or 0)
        self.agent_id = int(getattr(native_active_dialog, "agent_id", 0) or 0)
        self.dialog_id_authoritative = bool(getattr(native_active_dialog, "dialog_id_authoritative", False))
        self.raw_message = str(getattr(native_active_dialog, "message", "") or "")
        self.message = sanitize_dialog_text(self.raw_message)


class DialogButtonInfo:
    def __init__(
        self,
        native_button_info=None,
        *,
        dialog_id: int = 0,
        button_icon: int = 0,
        message: str = "",
        message_decoded: str = "",
        message_decode_pending: bool = False,
    ):
        if native_button_info is not None:
            self.native = native_button_info
            self.dialog_id = int(getattr(native_button_info, "dialog_id", 0) or 0)
            self.button_icon = int(getattr(native_button_info, "button_icon", 0) or 0)
            self.message = sanitize_dialog_text(getattr(native_button_info, "message", ""))
            self.message_decoded = sanitize_dialog_text(getattr(native_button_info, "message_decoded", ""))
            self.message_decode_pending = bool(getattr(native_button_info, "message_decode_pending", False))
        else:
            self.native = None
            self.dialog_id = int(dialog_id)
            self.button_icon = int(button_icon)
            self.message = sanitize_dialog_text(message)
            self.message_decoded = sanitize_dialog_text(message_decoded)
            self.message_decode_pending = bool(message_decode_pending)


def _parse_inline_choice_dialog_id(raw_value: Any) -> int:
    value = str(raw_value or "").strip()
    if not value:
        return 0
    try:
        return int(value, 0)
    except Exception:
        return 0


def extract_inline_dialog_choices_from_text(body_text: str | None) -> list[DialogButtonInfo]:
    text = str(body_text or "")
    if not text or "<a=" not in text.lower():
        return []

    choices: list[DialogButtonInfo] = []
    seen: set[tuple[int, str]] = set()
    for match in _INLINE_CHOICE_RE.finditer(text):
        dialog_id = _parse_inline_choice_dialog_id(match.group(1))
        if dialog_id == 0:
            continue
        label = sanitize_dialog_text(match.group(2)) or "<empty>"
        dedupe_key = (dialog_id, label)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        choices.append(
            DialogButtonInfo(
                dialog_id=dialog_id,
                message=label,
                message_decoded=label,
                message_decode_pending=False,
            )
        )
    return choices


def get_active_dialog() -> ActiveDialogInfo | None:
    native_info = _call_native_dialog_method("get_active_dialog", None)
    if native_info is None:
        return None
    if (
        getattr(native_info, "dialog_id", 0) == 0
        and getattr(native_info, "context_dialog_id", 0) == 0
        and getattr(native_info, "agent_id", 0) == 0
    ):
        return None
    return ActiveDialogInfo(native_info)


def get_active_dialog_buttons() -> list[DialogButtonInfo]:
    native_list = _coerce_native_list(_call_native_dialog_method("get_active_dialog_buttons", []))
    buttons = [DialogButtonInfo(item) for item in native_list]
    if buttons:
        return buttons
    active = get_active_dialog()
    if active is None:
        return []
    return extract_inline_dialog_choices_from_text(active.raw_message)
