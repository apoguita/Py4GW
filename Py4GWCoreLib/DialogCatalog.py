"""
Static dialog catalog wrapper for the native PyDialogCatalog C++ module.
This module owns static dialog metadata and text lookup helpers.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import List, Optional

try:
    from .Dialog import DialogInfo, DialogTextDecodedInfo, _sanitize_dialog_text
except Exception:
    from Dialog import DialogInfo, DialogTextDecodedInfo, _sanitize_dialog_text  # type: ignore

try:
    import PyDialogCatalog
except Exception as exc:  # pragma: no cover - runtime environment specific
    PyDialogCatalog = None
    _PYDIALOGCATALOG_IMPORT_ERROR = exc
else:
    _PYDIALOGCATALOG_IMPORT_ERROR = None


def _wrap_dialog_info(native_info) -> Optional[DialogInfo]:
    if native_info is None:
        return None
    if hasattr(native_info, "dialog_id"):
        return DialogInfo(native_info)
    if isinstance(native_info, dict):
        return DialogInfo(SimpleNamespace(**native_info))
    return None


def _wrap_decode_status(native_info) -> Optional[DialogTextDecodedInfo]:
    if native_info is None:
        return None
    if hasattr(native_info, "dialog_id"):
        return DialogTextDecodedInfo(native_info)
    if isinstance(native_info, dict):
        return DialogTextDecodedInfo(SimpleNamespace(**native_info))
    return None


class DialogCatalogWidget:
    """High-level wrapper around the native PyDialogCatalog module."""

    def is_dialog_available(self, dialog_id: int) -> bool:
        if PyDialogCatalog is None:
            return False
        return bool(PyDialogCatalog.PyDialogCatalog.is_dialog_available(dialog_id))

    def get_dialog_info(self, dialog_id: int) -> Optional[DialogInfo]:
        if PyDialogCatalog is None:
            return None
        return _wrap_dialog_info(PyDialogCatalog.PyDialogCatalog.get_dialog_info(dialog_id))

    def enumerate_available_dialogs(self) -> List[DialogInfo]:
        if PyDialogCatalog is None:
            return []
        native_list = PyDialogCatalog.PyDialogCatalog.enumerate_available_dialogs()
        out: List[DialogInfo] = []
        for item in native_list:
            wrapped = _wrap_dialog_info(item)
            if wrapped is not None:
                out.append(wrapped)
        return out

    def get_dialog_text_decoded(self, dialog_id: int) -> str:
        if PyDialogCatalog is None:
            return ""
        return _sanitize_dialog_text(PyDialogCatalog.PyDialogCatalog.get_dialog_text_decoded(dialog_id))

    def is_dialog_text_decode_pending(self, dialog_id: int) -> bool:
        if PyDialogCatalog is None:
            return False
        return bool(PyDialogCatalog.PyDialogCatalog.is_dialog_text_decode_pending(dialog_id))

    def get_dialog_text_decode_status(self) -> List[DialogTextDecodedInfo]:
        if PyDialogCatalog is None:
            return []
        native_list = PyDialogCatalog.PyDialogCatalog.get_dialog_text_decode_status()
        out: List[DialogTextDecodedInfo] = []
        for item in native_list:
            wrapped = _wrap_decode_status(item)
            if wrapped is not None:
                out.append(wrapped)
        return out

    def clear_cache(self) -> None:
        if PyDialogCatalog is None:
            return
        clearer = getattr(PyDialogCatalog.PyDialogCatalog, "clear_cache", None)
        if callable(clearer):
            clearer()


_dialog_catalog_widget: Optional[DialogCatalogWidget] = None


def get_dialog_catalog_widget() -> DialogCatalogWidget:
    global _dialog_catalog_widget
    if _dialog_catalog_widget is None:
        _dialog_catalog_widget = DialogCatalogWidget()
    return _dialog_catalog_widget


def is_dialog_available(dialog_id: int) -> bool:
    return get_dialog_catalog_widget().is_dialog_available(dialog_id)


def get_dialog_info(dialog_id: int) -> Optional[DialogInfo]:
    return get_dialog_catalog_widget().get_dialog_info(dialog_id)


def enumerate_available_dialogs() -> List[DialogInfo]:
    return get_dialog_catalog_widget().enumerate_available_dialogs()


def get_dialog_text_decoded(dialog_id: int) -> str:
    return get_dialog_catalog_widget().get_dialog_text_decoded(dialog_id)


def is_dialog_text_decode_pending(dialog_id: int) -> bool:
    return get_dialog_catalog_widget().is_dialog_text_decode_pending(dialog_id)


def get_dialog_text_decode_status() -> List[DialogTextDecodedInfo]:
    return get_dialog_catalog_widget().get_dialog_text_decode_status()


def clear_cache() -> None:
    get_dialog_catalog_widget().clear_cache()
