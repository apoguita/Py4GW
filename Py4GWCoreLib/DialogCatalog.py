from __future__ import annotations

from types import SimpleNamespace
from typing import Optional

try:
    from .Dialog import sanitize_dialog_text
except Exception:
    from Dialog import sanitize_dialog_text  # type: ignore

try:
    import PyDialogCatalog
except Exception:  # pragma: no cover - runtime specific
    PyDialogCatalog = None


class DialogInfo:
    def __init__(self, native_info):
        self.native = native_info
        self.dialog_id = int(getattr(native_info, "dialog_id", 0) or 0)
        self.flags = int(getattr(native_info, "flags", 0) or 0)
        self.text = sanitize_dialog_text(getattr(native_info, "text", ""))


def _wrap_dialog_info(native_info) -> Optional[DialogInfo]:
    if native_info is None:
        return None
    if hasattr(native_info, "dialog_id"):
        return DialogInfo(native_info)
    if isinstance(native_info, dict):
        return DialogInfo(SimpleNamespace(**native_info))
    return None


def get_dialog_info(dialog_id: int) -> Optional[DialogInfo]:
    if PyDialogCatalog is None:
        return None
    return _wrap_dialog_info(PyDialogCatalog.PyDialogCatalog.get_dialog_info(dialog_id))


def get_dialog_text_decoded(dialog_id: int) -> str:
    if PyDialogCatalog is None:
        return ""
    return sanitize_dialog_text(PyDialogCatalog.PyDialogCatalog.get_dialog_text_decoded(dialog_id))
