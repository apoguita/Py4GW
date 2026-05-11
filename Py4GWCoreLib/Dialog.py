"""
Core Dialog wrapper for the native PyDialog C++ module.
This module provides dialog access helpers for use by widgets or scripts.

Layering in this module:
1. Live/native state via `PyDialog` (`get_active_dialog`, buttons, callback journal).
2. Static dialog metadata and decoded text via `DialogCatalog` when available.
3. Optional SQLite-backed history via the integrated dialog step pipeline.
4. Thin module-level wrapper functions at the bottom for ergonomic imports.

When changing behavior, keep those responsibilities separate. Most regressions here come
from mixing live UI state, static catalog lookups, and persisted history in the same path.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import sqlite3
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


def _import_optional_attr(relative_module: str, absolute_module: str, attr_name: str) -> Any:
    if __package__:
        try:
            module = importlib.import_module(relative_module, __package__)
            return getattr(module, attr_name)
        except Exception:
            pass
    try:
        module = importlib.import_module(absolute_module)
        return getattr(module, attr_name)
    except Exception:
        return None


def _safe_call(default: Any, callback: Callable[[], Any]) -> Any:
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


try:
    import PyDialog
except Exception:  # pragma: no cover - runtime environment specific
    PyDialog = None


# Text sanitation helpers.
def _get_dialog_catalog_widget():
    factory = _import_optional_attr(
        ".DialogCatalog",
        "DialogCatalog",
        "get_dialog_catalog_widget",
    )
    if not callable(factory):
        return None
    return _safe_call(None, factory)


_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_COLOR_TAG_RE = re.compile(r"</?c(?:=[^>]*)?>", re.IGNORECASE)
_GENERIC_TAG_RE = re.compile(r"</?[A-Za-z][A-Za-z0-9:_-]*(?:\s+[^>]*)?>")
_LBRACKET_TOKEN_RE = re.compile(r"\[lbracket\]", re.IGNORECASE)
_RBRACKET_TOKEN_RE = re.compile(r"\[rbracket\]", re.IGNORECASE)
_ORPHAN_BREAK_TOKEN_RE = re.compile(r"(?<!\w)(?:brx|br)(?!\w)", re.IGNORECASE)
_ORPHAN_PARAGRAPH_TOKEN_RE = re.compile(r"(?<!\w)p(?!\w)")
_MISSING_SPACE_AFTER_PUNCT_RE = re.compile(r"([!?:;\)\]])([A-Za-z0-9])")
_MISSING_SPACE_ALPHA_NUM_RE = re.compile(r"([A-Za-z])(\d{2,})")
_MISSING_SPACE_NUM_ALPHA_RE = re.compile(r"(\d{2,})([A-Za-z])")
_MISSING_SPACE_CAMEL_RE = re.compile(r"([a-z])([A-Z])")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_INLINE_CHOICE_RE = re.compile(r"<a\s*=\s*([^>]+)>(.*?)</a>", re.IGNORECASE | re.DOTALL)
_SENTINEL_CANONICAL = {
    "<empty>": "<empty>",
    "<no label>": "<no label>",
    "<decoding...>": "<decoding...>",
    "<decoding label...>": "<decoding label...>",
}
_SENTINEL_RE = re.compile(
    "|".join(re.escape(token) for token in _SENTINEL_CANONICAL.keys()),
    re.IGNORECASE,
)


def _protect_sentinel_placeholders(text: str) -> tuple[str, dict[str, str]]:
    protected: dict[str, str] = {}

    def _replace(match: re.Match[str]) -> str:
        placeholder = f"__PY4GW_SENTINEL_{len(protected)}__"
        canonical = _SENTINEL_CANONICAL.get(match.group(0).lower(), match.group(0))
        protected[placeholder] = canonical
        return placeholder

    return _SENTINEL_RE.sub(_replace, text), protected


def _sanitize_dialog_text(value: Optional[str]) -> str:
    """
    Normalize Guild Wars dialog text into a stable display/query form.

    This removes control characters and markup noise while preserving the
    project-specific sentinel placeholders used by the dialog monitor.
    """
    if not value:
        return ""
    text = str(value)
    # Preserve project-specific sentinel placeholders before stripping generic markup so callers
    # can still distinguish "empty" / "decoding" states after sanitation.
    text, protected_sentinels = _protect_sentinel_placeholders(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _LBRACKET_TOKEN_RE.sub("[", text)
    text = _RBRACKET_TOKEN_RE.sub("]", text)
    text = _COLOR_TAG_RE.sub("", text)
    text = _GENERIC_TAG_RE.sub("", text)
    # Some decoded GW strings leak markup tokens as plain words (e.g. "p", "brx").
    text = _ORPHAN_BREAK_TOKEN_RE.sub(" ", text)
    text = _ORPHAN_PARAGRAPH_TOKEN_RE.sub(" ", text)
    for placeholder, canonical in protected_sentinels.items():
        text = text.replace(placeholder, canonical)
    # Repair collapsed separators caused by removed formatting tags.
    text = _MISSING_SPACE_AFTER_PUNCT_RE.sub(r"\1 \2", text)
    text = _MISSING_SPACE_ALPHA_NUM_RE.sub(r"\1 \2", text)
    text = _MISSING_SPACE_NUM_ALPHA_RE.sub(r"\1 \2", text)
    text = _MISSING_SPACE_CAMEL_RE.sub(r"\1 \2", text)
    text = _CONTROL_CHARS_RE.sub("", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()


def sanitize_dialog_text(value: Optional[str]) -> str:
    """Public sanitizer for any GW dialog-related text."""
    return _sanitize_dialog_text(value)


def _normalize_dialog_choice_text(value: Optional[str]) -> str:
    return " ".join(_sanitize_dialog_text(value).strip().lower().split())


def _get_dialog_button_label(button: Any) -> str:
    if button is None:
        return ""
    decoded = getattr(button, "message_decoded", "")
    if decoded:
        return _sanitize_dialog_text(decoded)
    return _sanitize_dialog_text(getattr(button, "message", ""))


def _append_unique_dialog_choice_text(values: List[str], value: Optional[str]) -> None:
    text = _sanitize_dialog_text(value)
    if text and text not in values:
        values.append(text)


def _coerce_native_list(value: Any) -> List[Any]:
    """
    Normalize pybind/native list-like return values into a concrete Python list.

    This keeps runtime behavior defensive and gives static type checkers a stable
    iterable type for dynamic `getattr`-based native access paths.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        return list(value)
    except TypeError:
        return []


def _build_active_dialog_npc_filters(active_dialog: Optional["ActiveDialogInfo"]) -> Dict[str, Any]:
    """
    Build the current NPC instance/archetype filters for persisted history queries.

    These filters keep history-based dialog matching scoped to the live NPC so
    reused dialog ids from other actors do not bleed into the current screen.
    """
    if active_dialog is None:
        return {}

    agent_id = int(getattr(active_dialog, "agent_id", 0) or 0)
    if agent_id <= 0:
        return {}

    map_id = 0
    model_id = 0

    try:
        from .Map import Map
    except Exception:
        try:
            from Map import Map  # type: ignore
        except Exception:
            Map = None  # type: ignore

    try:
        from .Agent import Agent
    except Exception:
        try:
            from Agent import Agent  # type: ignore
        except Exception:
            Agent = None  # type: ignore

    if Map is not None:
        try:
            map_id = int(Map.GetMapID() or 0)
        except Exception:
            map_id = 0

    if Agent is not None:
        try:
            model_id = int(Agent.GetModelID(agent_id) or 0)
        except Exception:
            model_id = 0

    if map_id <= 0 or model_id <= 0:
        return {}

    # History lookups must stay scoped to the live NPC instance/archetype. Dialog ids are reused
    # broadly enough that cross-NPC history can otherwise relabel the current visible buttons.
    npc_uid_archetype = f"{map_id}:{model_id}"
    return {
        "npc_uid_instance": f"{npc_uid_archetype}:{agent_id}",
        "npc_uid_archetype": npc_uid_archetype,
    }


DEFAULT_DB_RELATIVE_PATH = os.path.join("Widgets", "Data", "Dialog", "dialog_journal.sqlite3")
DEFAULT_QUERY_LIMIT = 200
DEFAULT_TIMEOUT_MS = 8000
MAX_SEEN_EVENT_KEYS = 4096


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _event_field(event: Any, name: str, index: int, default: Any) -> Any:
    if isinstance(event, dict):
        return event.get(name, default)
    if hasattr(event, name):
        return getattr(event, name)
    if isinstance(event, (tuple, list)) and len(event) > index:
        return event[index]
    return default


def _event_bytes_hex(event: Any, name: str, index: int) -> str:
    data = _event_field(event, name, index, [])
    if data is None:
        return ""
    try:
        return "".join(f"{int(byte) & 0xFF:02x}" for byte in data)
    except Exception:
        return ""


def _event_bytes_list(event: Any, name: str, index: int) -> List[int]:
    data = _event_field(event, name, index, [])
    if data is None:
        return []
    if isinstance(data, str):
        text = data.strip().replace(" ", "")
        if not text:
            return []
        if len(text) % 2 != 0:
            text = "0" + text
        try:
            return [int(text[i : i + 2], 16) for i in range(0, len(text), 2)]
        except Exception:
            return []
    try:
        return [int(x) & 0xFF for x in data]
    except Exception:
        return []


def _u32_at(data: Sequence[int], offset: int) -> int:
    if len(data) < (offset + 4):
        return 0
    return (
        (int(data[offset]) & 0xFF)
        | ((int(data[offset + 1]) & 0xFF) << 8)
        | ((int(data[offset + 2]) & 0xFF) << 16)
        | ((int(data[offset + 3]) & 0xFF) << 24)
    )


def _dialog_raw_hints(message_id: int, w_bytes: Sequence[int]) -> Tuple[int, int, str]:
    # Restep: (dialog_id, agent_id, event_type)
    if message_id == 0x100000A3:  # kDialogButton
        return _u32_at(w_bytes, 8), 0, "recv_choice_raw"
    if message_id == 0x100000A6:  # kDialogBody
        return 0, _u32_at(w_bytes, 4), "recv_body_raw"
    if message_id in (0x30000014, 0x30000015):  # kSendAgentDialog / kSendGadgetDialog
        return _u32_at(w_bytes, 0), 0, "sent_choice_raw"
    return 0, 0, ""


def _normalize_direction_filter(direction: Optional[str]) -> Optional[bool]:
    if direction is None:
        return None
    value = str(direction).strip().lower()
    if not value or value in {"all", "both", "*"}:
        return None
    if value in {"recv", "received", "incoming", "in"}:
        return True
    if value in {"sent", "outgoing", "out"}:
        return False
    raise ValueError(f"Unsupported direction filter: {direction}")


def _parse_message_type_filter(message_type: Optional[Any]) -> Tuple[Optional[int], Optional[str]]:
    if message_type is None:
        return None, None
    if isinstance(message_type, bool):
        raise TypeError("message_type must be int or str, not bool")
    if isinstance(message_type, int):
        return int(message_type), None
    value = str(message_type).strip()
    if not value:
        return None, None
    try:
        return int(value, 0), None
    except ValueError:
        return None, value.lower()


def _normalize_npc_uid_filter(npc_uid: Optional[str]) -> Optional[str]:
    if npc_uid is None:
        return None
    value = str(npc_uid).strip()
    return value if value else None


def _sha1_key(payload: str) -> str:
    return hashlib.sha1(payload.encode("utf-8", errors="replace")).hexdigest()


def _resolve_project_root() -> str:
    try:
        import Py4GW

        getter = getattr(Py4GW.Console, "get_projects_path", None)
        if callable(getter):
            root = getter()
            if root:
                return os.path.abspath(root)
    except Exception:
        pass
    return os.getcwd()


def _build_npc_uid(map_id: int, model_id: int, agent_id: int) -> str:
    if not agent_id:
        return ""
    return f"{int(map_id)}:{int(model_id)}:{int(agent_id)}"


def _build_npc_archetype_uid(map_id: int, model_id: int) -> str:
    return f"{int(map_id)}:{int(model_id)}"


def _resolve_map_name(map_id: int) -> str:
    resolved_map_id = int(map_id or 0)
    if resolved_map_id <= 0:
        return ""
    try:
        from .Map import Map
    except Exception:
        try:
            from Map import Map  # type: ignore
        except Exception:
            return ""
    try:
        name = _safe_text(Map.GetMapName(resolved_map_id)).strip()
    except Exception:
        return ""
    if not name or name == "Unknown Map ID":
        return ""
    return name


def _resolve_current_map_id() -> int:
    try:
        from .Map import Map
    except Exception:
        try:
            from Map import Map  # type: ignore
        except Exception:
            return 0
    try:
        return int(Map.GetMapID() or 0)
    except Exception:
        return 0


def _resolve_model_id(agent_id: int) -> int:
    resolved_agent_id = int(agent_id or 0)
    if resolved_agent_id <= 0:
        return 0
    try:
        from .Agent import Agent
    except Exception:
        try:
            from Agent import Agent  # type: ignore
        except Exception:
            return 0
    try:
        return int(Agent.GetModelID(resolved_agent_id) or 0)
    except Exception:
        return 0


def _resolve_npc_name(agent_id: int) -> str:
    resolved_agent_id = int(agent_id or 0)
    if resolved_agent_id <= 0:
        return ""
    try:
        from .Agent import Agent
    except Exception:
        try:
            from Agent import Agent  # type: ignore
        except Exception:
            return ""
    try:
        return _safe_text(Agent.GetNameByID(resolved_agent_id)).strip()
    except Exception:
        return ""


class DialogStepSQLitePipeline:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._conn: Optional[sqlite3.Connection] = None
        self._db_path: Optional[str] = None
        self._step_timeout_ms = DEFAULT_TIMEOUT_MS
        self._pending_steps: Dict[str, Dict[str, Any]] = {}
        self._body_text_to_dialog_id: Dict[str, int] = {}
        self._dialog_id_to_body_text: Dict[int, Tuple[str, str]] = {}
        self._seen_keys: set[str] = set()
        self._seen_order: List[str] = []

    def configure(
        self,
        *,
        db_path: Optional[str] = None,
        step_timeout_ms: Optional[int] = None,
    ) -> str:
        with self._lock:
            if step_timeout_ms is not None and int(step_timeout_ms) > 0:
                self._step_timeout_ms = int(step_timeout_ms)
            if db_path:
                resolved = os.path.abspath(str(db_path))
                if self._conn is not None and self._db_path and resolved != self._db_path:
                    self._conn.close()
                    self._conn = None
                self._db_path = resolved
            self._ensure_connection()
            return self._db_path or ""

    def get_db_path(self) -> str:
        with self._lock:
            self._ensure_connection()
            return self._db_path or ""

    def sync(
        self,
        *,
        raw_events: Optional[Sequence[Any]] = None,
        callback_journal: Optional[Sequence[Any]] = None,
    ) -> Dict[str, int]:
        with self._lock:
            conn = self._ensure_connection()
            inserted_raw = 0
            inserted_journal = 0
            finalized_steps = 0
            latest_tick = 0
            with conn:
                if raw_events:
                    inserted_raw = self._insert_raw_callbacks(conn, raw_events)
                if callback_journal:
                    inserted_journal, finalized_steps, latest_tick = self._insert_callback_journal(conn, callback_journal)
                if latest_tick:
                    finalized_steps += self._finalize_stale_steps(conn, latest_tick, current_map_id=0)
                self._repair_persisted_step_rows(conn)
                self._backfill_display_names(conn)
            return {
                "raw_inserted": inserted_raw,
                "journal_inserted": inserted_journal,
                "steps_finalized": finalized_steps,
            }

    def flush_pending(self) -> int:
        with self._lock:
            conn = self._ensure_connection()
            finalized = 0
            with conn:
                keys = list(self._pending_steps.keys())
                for npc_uid in keys:
                    if self._finalize_step(conn, npc_uid, reason="flush", end_tick=0):
                        finalized += 1
            return finalized

    def get_raw_callbacks(
        self,
        *,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
        limit: int = DEFAULT_QUERY_LIMIT,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        incoming_filter = _normalize_direction_filter(direction)
        message_id_filter, event_type_filter = _parse_message_type_filter(message_type)
        limit = max(1, int(limit))
        offset = max(0, int(offset))

        where: List[str] = []
        params: List[Any] = []
        if incoming_filter is not None:
            where.append("incoming = ?")
            params.append(1 if incoming_filter else 0)
        if message_id_filter is not None:
            where.append("message_id = ?")
            params.append(message_id_filter)
        if event_type_filter:
            where.append("LOWER(event_type) = ?")
            params.append(event_type_filter)

        sql = (
            "SELECT id, tick, ts, message_id, incoming, map_id, map_name, agent_id, npc_name, model_id, npc_uid, "
            "dialog_id, context_dialog_id, event_type, text_raw FROM raw_callbacks"
        )
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._lock:
            conn = self._ensure_connection()
            rows = conn.execute(sql, params).fetchall()
            return [self._raw_row_to_dict(row) for row in rows]

    def clear_raw_callbacks(
        self,
        *,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
    ) -> int:
        incoming_filter = _normalize_direction_filter(direction)
        message_id_filter, event_type_filter = _parse_message_type_filter(message_type)

        where: List[str] = []
        params: List[Any] = []
        if incoming_filter is not None:
            where.append("incoming = ?")
            params.append(1 if incoming_filter else 0)
        if message_id_filter is not None:
            where.append("message_id = ?")
            params.append(message_id_filter)
        if event_type_filter:
            where.append("LOWER(event_type) = ?")
            params.append(event_type_filter)

        sql = "DELETE FROM raw_callbacks"
        if where:
            sql += " WHERE " + " AND ".join(where)

        with self._lock:
            conn = self._ensure_connection()
            with conn:
                cursor = conn.execute(sql, params)
            return int(cursor.rowcount or 0)

    def get_callback_journal(
        self,
        *,
        npc_uid: Optional[str] = None,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
        limit: int = DEFAULT_QUERY_LIMIT,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        incoming_filter = _normalize_direction_filter(direction)
        message_id_filter, event_type_filter = _parse_message_type_filter(message_type)
        npc_uid_filter = _normalize_npc_uid_filter(npc_uid)
        limit = max(1, int(limit))
        offset = max(0, int(offset))

        where: List[str] = []
        params: List[Any] = []
        if npc_uid_filter:
            where.append("npc_uid = ?")
            params.append(npc_uid_filter)
        if incoming_filter is not None:
            where.append("incoming = ?")
            params.append(1 if incoming_filter else 0)
        if message_id_filter is not None:
            where.append("message_id = ?")
            params.append(message_id_filter)
        if event_type_filter:
            where.append("LOWER(event_type) = ?")
            params.append(event_type_filter)

        sql = (
            "SELECT id, tick, ts, message_id, incoming, dialog_id, context_dialog_id, "
            "agent_id, map_id, map_name, model_id, npc_uid, npc_name, event_type, text_raw, text_decoded "
            "FROM callback_journal"
        )
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._lock:
            conn = self._ensure_connection()
            rows = conn.execute(sql, params).fetchall()
            return [self._callback_row_to_dict(row) for row in rows]

    def clear_callback_journal(
        self,
        *,
        npc_uid: Optional[str] = None,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
    ) -> int:
        incoming_filter = _normalize_direction_filter(direction)
        message_id_filter, event_type_filter = _parse_message_type_filter(message_type)
        npc_uid_filter = _normalize_npc_uid_filter(npc_uid)

        where: List[str] = []
        params: List[Any] = []
        if npc_uid_filter:
            where.append("npc_uid = ?")
            params.append(npc_uid_filter)
        if incoming_filter is not None:
            where.append("incoming = ?")
            params.append(1 if incoming_filter else 0)
        if message_id_filter is not None:
            where.append("message_id = ?")
            params.append(message_id_filter)
        if event_type_filter:
            where.append("LOWER(event_type) = ?")
            params.append(event_type_filter)

        sql = "DELETE FROM callback_journal"
        if where:
            sql += " WHERE " + " AND ".join(where)

        with self._lock:
            conn = self._ensure_connection()
            with conn:
                cursor = conn.execute(sql, params)
            return int(cursor.rowcount or 0)

    def get_dialog_steps(
        self,
        *,
        map_id: Optional[int] = None,
        npc_uid_instance: Optional[str] = None,
        npc_uid_archetype: Optional[str] = None,
        body_dialog_id: Optional[int] = None,
        choice_dialog_id: Optional[int] = None,
        limit: int = DEFAULT_QUERY_LIMIT,
        offset: int = 0,
        include_choices: bool = True,
    ) -> List[Dict[str, Any]]:
        limit = max(1, int(limit))
        offset = max(0, int(offset))
        where: List[str] = []
        params: List[Any] = []

        if map_id is not None:
            where.append("t.map_id = ?")
            params.append(int(map_id))
        if npc_uid_instance:
            where.append("t.npc_uid_instance = ?")
            params.append(str(npc_uid_instance))
        if npc_uid_archetype:
            where.append("t.npc_uid_archetype = ?")
            params.append(str(npc_uid_archetype))
        if body_dialog_id is not None:
            where.append("t.body_dialog_id = ?")
            params.append(int(body_dialog_id))
        if choice_dialog_id is not None:
            where.append("EXISTS (SELECT 1 FROM dialog_choices c WHERE c.step_id = t.id AND c.choice_dialog_id = ?)")
            params.append(int(choice_dialog_id))

        sql = (
            "SELECT t.id, t.start_tick, t.end_tick, t.map_id, t.map_name, t.agent_id, t.npc_name, t.model_id, "
            "t.npc_uid_instance, t.npc_uid_archetype, t.body_dialog_id, t.body_text_raw, "
            "t.body_text_decoded, t.selected_dialog_id, t.selected_source_message_id, "
            "t.finalized_reason, t.created_at FROM dialog_steps t"
        )
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY t.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._lock:
            conn = self._ensure_connection()
            rows = conn.execute(sql, params).fetchall()
            steps = [self._step_row_to_dict(row) for row in rows]
            if not include_choices or not steps:
                return steps

            step_ids = [step["id"] for step in steps]
            choices_by_step = self._get_choices_by_step_ids(conn, step_ids)
            for step in steps:
                step["choices"] = choices_by_step.get(step["id"], [])
            return steps

    def get_dialog_step(self, step_id: int, *, include_choices: bool = True) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._ensure_connection()
            row = conn.execute(
                "SELECT id, start_tick, end_tick, map_id, map_name, agent_id, npc_name, model_id, "
                "npc_uid_instance, npc_uid_archetype, body_dialog_id, body_text_raw, "
                "body_text_decoded, selected_dialog_id, selected_source_message_id, "
                "finalized_reason, created_at FROM dialog_steps WHERE id = ?",
                (int(step_id),),
            ).fetchone()
            if row is None:
                return None
            step = self._step_row_to_dict(row)
            if include_choices:
                step["choices"] = self.get_dialog_choices(int(step_id))
            return step

    def get_dialog_choices(self, step_id: int) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._ensure_connection()
            rows = conn.execute(
                "SELECT id, step_id, choice_index, choice_dialog_id, choice_text_raw, "
                "choice_text_decoded, skill_id, button_icon, decode_pending, selected, source_message_id "
                "FROM dialog_choices WHERE step_id = ? ORDER BY choice_index ASC, id ASC",
                (int(step_id),),
            ).fetchall()
            return [self._choice_row_to_dict(row) for row in rows]

    def export_raw_callbacks_json(
        self,
        path: str,
        *,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
        limit: int = 10000,
        offset: int = 0,
    ) -> int:
        entries = self.get_raw_callbacks(
            direction=direction,
            message_type=message_type,
            limit=limit,
            offset=offset,
        )
        payload = {
            "generated_at": time.time(),
            "count": len(entries),
            "filters": {
                "direction": direction,
                "message_type": message_type,
                "limit": int(limit),
                "offset": int(offset),
            },
            "entries": entries,
        }
        self._write_json(path, payload)
        return len(entries)

    def export_callback_journal_json(
        self,
        path: str,
        *,
        npc_uid: Optional[str] = None,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
        limit: int = 10000,
        offset: int = 0,
    ) -> int:
        entries = self.get_callback_journal(
            npc_uid=npc_uid,
            direction=direction,
            message_type=message_type,
            limit=limit,
            offset=offset,
        )
        payload = {
            "generated_at": time.time(),
            "count": len(entries),
            "filters": {
                "npc_uid": npc_uid,
                "direction": direction,
                "message_type": message_type,
                "limit": int(limit),
                "offset": int(offset),
            },
            "entries": entries,
        }
        self._write_json(path, payload)
        return len(entries)

    def export_dialog_steps_json(
        self,
        path: str,
        *,
        map_id: Optional[int] = None,
        npc_uid_instance: Optional[str] = None,
        npc_uid_archetype: Optional[str] = None,
        body_dialog_id: Optional[int] = None,
        choice_dialog_id: Optional[int] = None,
        limit: int = 5000,
        offset: int = 0,
    ) -> int:
        steps = self.get_dialog_steps(
            map_id=map_id,
            npc_uid_instance=npc_uid_instance,
            npc_uid_archetype=npc_uid_archetype,
            body_dialog_id=body_dialog_id,
            choice_dialog_id=choice_dialog_id,
            limit=limit,
            offset=offset,
            include_choices=True,
        )
        payload = {
            "generated_at": time.time(),
            "count": len(steps),
            "filters": {
                "map_id": map_id,
                "npc_uid_instance": npc_uid_instance,
                "npc_uid_archetype": npc_uid_archetype,
                "body_dialog_id": body_dialog_id,
                "choice_dialog_id": choice_dialog_id,
                "limit": int(limit),
                "offset": int(offset),
            },
            "steps": steps,
        }
        self._write_json(path, payload)
        return len(steps)

    def prune_dialog_logs(
        self,
        *,
        max_raw_rows: Optional[int] = None,
        max_journal_rows: Optional[int] = None,
        max_step_rows: Optional[int] = None,
        older_than_days: Optional[float] = None,
    ) -> Dict[str, int]:
        removed_raw = 0
        removed_journal = 0
        removed_steps = 0
        removed_choices = 0

        with self._lock:
            conn = self._ensure_connection()
            with conn:
                if older_than_days is not None and float(older_than_days) > 0:
                    cutoff = float(time.time()) - float(older_than_days) * 86400.0
                    removed_raw += int(conn.execute("DELETE FROM raw_callbacks WHERE ts < ?", (cutoff,)).rowcount or 0)
                    removed_journal += int(conn.execute("DELETE FROM callback_journal WHERE ts < ?", (cutoff,)).rowcount or 0)
                    old_step_rows = conn.execute(
                        "SELECT id FROM dialog_steps WHERE created_at < ? ORDER BY id ASC",
                        (cutoff,),
                    ).fetchall()
                    old_step_ids = [int(row[0]) for row in old_step_rows]
                    if old_step_ids:
                        removed_choices += self._delete_choices_for_step_ids(conn, old_step_ids)
                        removed_steps += int(
                            conn.execute(
                                f"DELETE FROM dialog_steps WHERE id IN ({','.join('?' for _ in old_step_ids)})",
                                old_step_ids,
                            ).rowcount
                            or 0
                        )

                if max_raw_rows is not None and int(max_raw_rows) >= 0:
                    removed_raw += self._trim_table(conn, "raw_callbacks", int(max_raw_rows))

                if max_journal_rows is not None and int(max_journal_rows) >= 0:
                    removed_journal += self._trim_table(conn, "callback_journal", int(max_journal_rows))

                if max_step_rows is not None and int(max_step_rows) >= 0:
                    overflow_ids = self._overflow_ids(conn, "dialog_steps", int(max_step_rows))
                    if overflow_ids:
                        removed_choices += self._delete_choices_for_step_ids(conn, overflow_ids)
                        removed_steps += int(
                            conn.execute(
                                f"DELETE FROM dialog_steps WHERE id IN ({','.join('?' for _ in overflow_ids)})",
                                overflow_ids,
                            ).rowcount
                            or 0
                        )

        return {
            "removed_raw_callbacks": removed_raw,
            "removed_callback_journal": removed_journal,
            "removed_dialog_steps": removed_steps,
            "removed_dialog_choices": removed_choices,
        }

    def _ensure_connection(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn

        if not self._db_path:
            self._db_path = os.path.join(_resolve_project_root(), DEFAULT_DB_RELATIVE_PATH)
        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        conn = sqlite3.connect(self._db_path, timeout=5.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        self._create_schema(conn)
        self._conn = conn
        return conn

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        self._create_base_schema(conn)
        self._migrate_legacy_step_schema(conn)
        self._ensure_display_name_columns(conn)
        self._create_current_step_schema(conn)
        self._create_display_name_indexes(conn)
        self._backfill_display_names(conn)

    def _create_base_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS raw_callbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_key TEXT NOT NULL UNIQUE,
                tick INTEGER NOT NULL,
                ts REAL NOT NULL,
                message_id INTEGER NOT NULL,
                incoming INTEGER NOT NULL,
                is_frame_message INTEGER NOT NULL DEFAULT 0,
                frame_id INTEGER NOT NULL DEFAULT 0,
                w_bytes_hex TEXT NOT NULL DEFAULT '',
                l_bytes_hex TEXT NOT NULL DEFAULT '',
                map_id INTEGER NOT NULL DEFAULT 0,
                map_name TEXT NOT NULL DEFAULT '',
                agent_id INTEGER NOT NULL DEFAULT 0,
                npc_name TEXT NOT NULL DEFAULT '',
                model_id INTEGER NOT NULL DEFAULT 0,
                npc_uid TEXT NOT NULL DEFAULT '',
                dialog_id INTEGER NOT NULL DEFAULT 0,
                context_dialog_id INTEGER NOT NULL DEFAULT 0,
                event_type TEXT NOT NULL DEFAULT '',
                text_raw TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS callback_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_key TEXT NOT NULL UNIQUE,
                tick INTEGER NOT NULL,
                ts REAL NOT NULL,
                message_id INTEGER NOT NULL,
                incoming INTEGER NOT NULL,
                dialog_id INTEGER NOT NULL DEFAULT 0,
                context_dialog_id INTEGER NOT NULL DEFAULT 0,
                agent_id INTEGER NOT NULL DEFAULT 0,
                map_id INTEGER NOT NULL DEFAULT 0,
                map_name TEXT NOT NULL DEFAULT '',
                model_id INTEGER NOT NULL DEFAULT 0,
                npc_uid TEXT NOT NULL DEFAULT '',
                npc_name TEXT NOT NULL DEFAULT '',
                event_type TEXT NOT NULL DEFAULT '',
                text_raw TEXT NOT NULL DEFAULT '',
                text_decoded TEXT NOT NULL DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_raw_tick ON raw_callbacks(tick);
            CREATE INDEX IF NOT EXISTS idx_raw_message ON raw_callbacks(message_id);
            CREATE INDEX IF NOT EXISTS idx_raw_npc_uid ON raw_callbacks(npc_uid);
            CREATE INDEX IF NOT EXISTS idx_raw_map_id ON raw_callbacks(map_id);

            CREATE INDEX IF NOT EXISTS idx_journal_tick ON callback_journal(tick);
            CREATE INDEX IF NOT EXISTS idx_journal_message ON callback_journal(message_id);
            CREATE INDEX IF NOT EXISTS idx_journal_npc_uid ON callback_journal(npc_uid);
            CREATE INDEX IF NOT EXISTS idx_journal_event_type ON callback_journal(event_type);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dialog_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_tick INTEGER NOT NULL,
                end_tick INTEGER NOT NULL DEFAULT 0,
                map_id INTEGER NOT NULL DEFAULT 0,
                map_name TEXT NOT NULL DEFAULT '',
                agent_id INTEGER NOT NULL DEFAULT 0,
                npc_name TEXT NOT NULL DEFAULT '',
                model_id INTEGER NOT NULL DEFAULT 0,
                npc_uid_instance TEXT NOT NULL DEFAULT '',
                npc_uid_archetype TEXT NOT NULL DEFAULT '',
                body_dialog_id INTEGER NOT NULL DEFAULT 0,
                body_text_raw TEXT NOT NULL DEFAULT '',
                body_text_decoded TEXT NOT NULL DEFAULT '',
                selected_dialog_id INTEGER NOT NULL DEFAULT 0,
                selected_source_message_id INTEGER NOT NULL DEFAULT 0,
                finalized_reason TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            )
            """
        )

    def _create_current_step_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS dialog_choices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                step_id INTEGER NOT NULL,
                choice_index INTEGER NOT NULL DEFAULT 0,
                choice_dialog_id INTEGER NOT NULL DEFAULT 0,
                choice_text_raw TEXT NOT NULL DEFAULT '',
                choice_text_decoded TEXT NOT NULL DEFAULT '',
                skill_id INTEGER NOT NULL DEFAULT 0,
                button_icon INTEGER NOT NULL DEFAULT 0,
                decode_pending INTEGER NOT NULL DEFAULT 0,
                selected INTEGER NOT NULL DEFAULT 0,
                source_message_id INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(step_id) REFERENCES dialog_steps(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_steps_map ON dialog_steps(map_id);
            CREATE INDEX IF NOT EXISTS idx_steps_npc_instance ON dialog_steps(npc_uid_instance);
            CREATE INDEX IF NOT EXISTS idx_steps_npc_archetype ON dialog_steps(npc_uid_archetype);
            CREATE INDEX IF NOT EXISTS idx_steps_body_dialog_id ON dialog_steps(body_dialog_id);
            CREATE INDEX IF NOT EXISTS idx_steps_created_at ON dialog_steps(created_at);
            CREATE INDEX IF NOT EXISTS idx_steps_map_name ON dialog_steps(map_name);
            CREATE INDEX IF NOT EXISTS idx_steps_npc_name ON dialog_steps(npc_name);

            CREATE INDEX IF NOT EXISTS idx_choices_step ON dialog_choices(step_id);
            CREATE INDEX IF NOT EXISTS idx_choices_dialog_id ON dialog_choices(choice_dialog_id);
            CREATE INDEX IF NOT EXISTS idx_choices_selected ON dialog_choices(selected);
            """
        )

    def _ensure_display_name_columns(self, conn: sqlite3.Connection) -> None:
        self._ensure_column(conn, "raw_callbacks", "map_name", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column(conn, "raw_callbacks", "npc_name", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column(conn, "callback_journal", "map_name", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column(conn, "callback_journal", "npc_name", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column(conn, "dialog_steps", "map_name", "TEXT NOT NULL DEFAULT ''")
        self._ensure_column(conn, "dialog_steps", "npc_name", "TEXT NOT NULL DEFAULT ''")

    def _ensure_column(self, conn: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
        columns = {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table_name})")}
        if column_name in columns:
            return
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")

    def _backfill_display_names(self, conn: sqlite3.Connection) -> None:
        self._backfill_table_display_names(conn, "raw_callbacks")
        self._backfill_table_display_names(conn, "callback_journal")
        self._backfill_table_display_names(conn, "dialog_steps")

    def _create_display_name_indexes(self, conn: sqlite3.Connection) -> None:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_map_name ON raw_callbacks(map_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_npc_name ON raw_callbacks(npc_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_journal_map_name ON callback_journal(map_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_journal_npc_name ON callback_journal(npc_name)")

    def _backfill_table_display_names(self, conn: sqlite3.Connection, table_name: str) -> None:
        rows = conn.execute(
            f"""
            SELECT id, map_id, IFNULL(map_name, ''), agent_id, IFNULL(npc_name, '')
            FROM {table_name}
            WHERE IFNULL(map_name, '') = '' OR IFNULL(npc_name, '') = ''
            """
        ).fetchall()
        if not rows:
            return

        map_cache: Dict[int, str] = {}
        npc_cache: Dict[int, str] = {}
        updates: List[Tuple[str, str, int]] = []
        for row_id, map_id, map_name, agent_id, npc_name in rows:
            resolved_map_id = int(map_id or 0)
            resolved_agent_id = int(agent_id or 0)
            next_map_name = _safe_text(map_name)
            next_npc_name = _safe_text(npc_name)
            if not next_map_name and resolved_map_id > 0:
                next_map_name = map_cache.setdefault(resolved_map_id, _resolve_map_name(resolved_map_id))
            if not next_npc_name and resolved_agent_id > 0:
                next_npc_name = npc_cache.setdefault(resolved_agent_id, _resolve_npc_name(resolved_agent_id))
            if next_map_name != _safe_text(map_name) or next_npc_name != _safe_text(npc_name):
                updates.append((next_map_name, next_npc_name, int(row_id)))
        if updates:
            conn.executemany(
                f"UPDATE {table_name} SET map_name = ?, npc_name = ? WHERE id = ?",
                updates,
            )

    def _migrate_legacy_step_schema(self, conn: sqlite3.Connection) -> None:
        table_names = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "dialog_turns" not in table_names and "dialog_choices" not in table_names:
            return

        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            if "dialog_turns" in table_names:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO dialog_steps (
                        id, start_tick, end_tick, map_id, agent_id, model_id,
                        npc_uid_instance, npc_uid_archetype, body_dialog_id,
                        body_text_raw, body_text_decoded, selected_dialog_id,
                        selected_source_message_id, finalized_reason, created_at
                    )
                    SELECT
                        id, start_tick, end_tick, map_id, agent_id, model_id,
                        npc_uid_instance, npc_uid_archetype, body_dialog_id,
                        body_text_raw, body_text_decoded, selected_dialog_id,
                        selected_source_message_id, finalized_reason, created_at
                    FROM dialog_turns
                    """
                )
                conn.execute("DROP TABLE dialog_turns")

            if "dialog_choices" in table_names:
                columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(dialog_choices)")}
                if "turn_id" in columns and "step_id" not in columns:
                    conn.execute("DROP INDEX IF EXISTS idx_choices_turn")
                    conn.execute("DROP INDEX IF EXISTS idx_choices_step")
                    conn.execute("ALTER TABLE dialog_choices RENAME TO dialog_choices_legacy")
                    conn.execute(
                        """
                        CREATE TABLE dialog_choices (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            step_id INTEGER NOT NULL,
                            choice_index INTEGER NOT NULL DEFAULT 0,
                            choice_dialog_id INTEGER NOT NULL DEFAULT 0,
                            choice_text_raw TEXT NOT NULL DEFAULT '',
                            choice_text_decoded TEXT NOT NULL DEFAULT '',
                            skill_id INTEGER NOT NULL DEFAULT 0,
                            button_icon INTEGER NOT NULL DEFAULT 0,
                            decode_pending INTEGER NOT NULL DEFAULT 0,
                            selected INTEGER NOT NULL DEFAULT 0,
                            source_message_id INTEGER NOT NULL DEFAULT 0,
                            FOREIGN KEY(step_id) REFERENCES dialog_steps(id) ON DELETE CASCADE
                        )
                        """
                    )
                    conn.execute(
                        """
                        INSERT INTO dialog_choices (
                            id, step_id, choice_index, choice_dialog_id, choice_text_raw,
                            choice_text_decoded, skill_id, button_icon, decode_pending,
                            selected, source_message_id
                        )
                        SELECT
                            c.id, c.turn_id, c.choice_index, c.choice_dialog_id, c.choice_text_raw,
                            c.choice_text_decoded, c.skill_id, c.button_icon, c.decode_pending,
                            c.selected, c.source_message_id
                        FROM dialog_choices_legacy c
                        WHERE EXISTS (
                            SELECT 1
                            FROM dialog_steps s
                            WHERE s.id = c.turn_id
                        )
                        """
                    )
                    conn.execute("DROP TABLE dialog_choices_legacy")
        finally:
            conn.execute("PRAGMA foreign_keys = ON")

    def _insert_raw_callbacks(self, conn: sqlite3.Connection, raw_events: Sequence[Any]) -> int:
        inserted = 0
        for event in raw_events:
            tick = _to_int(_event_field(event, "tick", 0, 0), 0)
            message_id = _to_int(_event_field(event, "message_id", 1, 0), 0)
            incoming = bool(_event_field(event, "incoming", 2, False))
            is_frame_message = bool(_event_field(event, "is_frame_message", 3, False))
            frame_id = _to_int(_event_field(event, "frame_id", 4, 0), 0)
            w_bytes = _event_bytes_list(event, "w_bytes", 5)
            w_bytes_hex = _event_bytes_hex(event, "w_bytes", 5)
            l_bytes_hex = _event_bytes_hex(event, "l_bytes", 6)
            dialog_id_hint, agent_id_hint, event_type_hint = _dialog_raw_hints(message_id, w_bytes)
            map_id = _to_int(_event_field(event, "map_id", 7, 0), 0)
            if map_id <= 0:
                map_id = _resolve_current_map_id()
            agent_id = _to_int(_event_field(event, "agent_id", 8, agent_id_hint), 0) or agent_id_hint
            model_id = _to_int(_event_field(event, "model_id", 9, 0), 0)
            if model_id <= 0 and agent_id > 0:
                model_id = _resolve_model_id(agent_id)
            npc_uid = _safe_text(_event_field(event, "npc_uid", 10, ""))
            if not npc_uid:
                npc_uid = _build_npc_uid(map_id, model_id, agent_id)
            dialog_id = _to_int(_event_field(event, "dialog_id", 11, dialog_id_hint), 0) or dialog_id_hint
            context_dialog_id = _to_int(_event_field(event, "context_dialog_id", 12, 0), 0)
            event_type = _safe_text(_event_field(event, "event_type", 13, event_type_hint)).strip().lower()
            if not event_type:
                event_type = event_type_hint
            text_raw = _safe_text(_event_field(event, "text_raw", 14, _event_field(event, "text", 15, "")))
            map_name = _safe_text(_event_field(event, "map_name", 16, "")).strip() or _resolve_map_name(map_id)
            npc_name = _safe_text(_event_field(event, "npc_name", 17, "")).strip() or _resolve_npc_name(agent_id)
            event_key = _sha1_key(
                f"raw|{tick}|{message_id}|{1 if incoming else 0}|{1 if is_frame_message else 0}|"
                f"{frame_id}|{w_bytes_hex}|{l_bytes_hex}"
            )
            if self._key_seen(event_key):
                continue
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO raw_callbacks (
                    event_key, tick, ts, message_id, incoming, is_frame_message, frame_id,
                    w_bytes_hex, l_bytes_hex, map_id, map_name, agent_id, npc_name, model_id, npc_uid,
                    dialog_id, context_dialog_id, event_type, text_raw
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_key,
                    tick,
                    float(time.time()),
                    message_id,
                    1 if incoming else 0,
                    1 if is_frame_message else 0,
                    frame_id,
                    w_bytes_hex,
                    l_bytes_hex,
                    map_id,
                    map_name,
                    agent_id,
                    npc_name,
                    model_id,
                    npc_uid,
                    dialog_id,
                    context_dialog_id,
                    event_type,
                    text_raw,
                ),
            )
            if int(cursor.rowcount or 0) > 0:
                inserted += 1
                self._remember_key(event_key)
        return inserted

    def _insert_callback_journal(
        self,
        conn: sqlite3.Connection,
        callback_journal: Sequence[Any],
    ) -> Tuple[int, int, int]:
        inserted = 0
        finalized = 0
        latest_tick = 0
        for event in callback_journal:
            normalized = self._normalize_callback_event(event)
            latest_tick = max(latest_tick, normalized["tick"])
            event_key = _sha1_key(
                "journal|{tick}|{message_id}|{incoming}|{dialog_id}|{context_dialog_id}|"
                "{agent_id}|{map_id}|{model_id}|{npc_uid}|{event_type}|{text_raw}".format(
                    tick=normalized["tick"],
                    message_id=normalized["message_id"],
                    incoming=1 if normalized["incoming"] else 0,
                    dialog_id=normalized["dialog_id"],
                    context_dialog_id=normalized["context_dialog_id"],
                    agent_id=normalized["agent_id"],
                    map_id=normalized["map_id"],
                    model_id=normalized["model_id"],
                    npc_uid=normalized["npc_uid"],
                    event_type=normalized["event_type"],
                    text_raw=normalized["text_raw"],
                )
            )
            if self._key_seen(event_key):
                continue
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO callback_journal (
                    event_key, tick, ts, message_id, incoming, dialog_id, context_dialog_id,
                    agent_id, map_id, map_name, model_id, npc_uid, npc_name, event_type, text_raw, text_decoded
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_key,
                    normalized["tick"],
                    float(time.time()),
                    normalized["message_id"],
                    1 if normalized["incoming"] else 0,
                    normalized["dialog_id"],
                    normalized["context_dialog_id"],
                    normalized["agent_id"],
                    normalized["map_id"],
                    normalized["map_name"],
                    normalized["model_id"],
                    normalized["npc_uid"],
                    normalized["npc_name"],
                    normalized["event_type"],
                    normalized["text_raw"],
                    normalized["text_decoded"],
                ),
            )
            if int(cursor.rowcount or 0) <= 0:
                continue
            inserted += 1
            self._remember_key(event_key)
            finalized += self._process_step_event(conn, normalized)
        return inserted, finalized, latest_tick

    def _normalize_callback_event(self, event: Any) -> Dict[str, Any]:
        tick = _to_int(_event_field(event, "tick", 0, 0), 0)
        message_id = _to_int(_event_field(event, "message_id", 1, 0), 0)
        incoming = bool(_event_field(event, "incoming", 2, False))
        dialog_id = _to_int(_event_field(event, "dialog_id", 3, 0), 0)
        context_dialog_id = _to_int(_event_field(event, "context_dialog_id", 4, 0), 0)
        agent_id = _to_int(_event_field(event, "agent_id", 5, 0), 0)
        map_id = _to_int(_event_field(event, "map_id", 6, 0), 0)
        model_id = _to_int(_event_field(event, "model_id", 7, 0), 0)
        npc_uid = _safe_text(_event_field(event, "npc_uid", 8, ""))
        event_type = _safe_text(_event_field(event, "event_type", 9, "")).strip().lower()
        text_raw = _safe_text(_event_field(event, "text", 10, ""))
        map_name = _safe_text(_event_field(event, "map_name", 11, "")).strip()
        npc_name = _safe_text(_event_field(event, "npc_name", 12, "")).strip()
        if not npc_uid:
            npc_uid = _build_npc_uid(map_id, model_id, agent_id)
        if not map_name:
            map_name = _resolve_map_name(map_id)
        if not npc_name:
            npc_name = _resolve_npc_name(agent_id)
        return {
            "tick": tick,
            "message_id": message_id,
            "incoming": incoming,
            "dialog_id": dialog_id,
            "context_dialog_id": context_dialog_id,
            "agent_id": agent_id,
            "map_id": map_id,
            "map_name": map_name,
            "model_id": model_id,
            "npc_uid": npc_uid,
            "npc_name": npc_name,
            "event_type": event_type,
            "text_raw": text_raw,
            "text_decoded": text_raw,
        }

    def _process_step_event(self, conn: sqlite3.Connection, event: Dict[str, Any]) -> int:
        finalized = self._finalize_stale_steps(conn, event["tick"], current_map_id=event["map_id"])
        event_type = event["event_type"]
        step_key = self._event_step_key(event)
        if not step_key:
            return finalized

        if event_type == "recv_body":
            self._remember_body_text_mapping(event)
            existing = self._pending_steps.get(step_key)
            if existing is not None:
                if self._should_hydrate_pending_step(existing, event):
                    self._hydrate_pending_step(existing, event)
                    return finalized
                if self._finalize_step(conn, step_key, reason="next_body", end_tick=event["tick"]):
                    finalized += 1
            self._pending_steps[step_key] = self._new_step_from_body(event)
            return finalized

        if event_type == "recv_choice":
            step = self._pending_steps.get(step_key)
            if step is None:
                if int(event.get("context_dialog_id", 0) or 0) == 0:
                    # Ignore contextless bootstrap choices; they create unresolved steps.
                    return finalized
                step = self._new_step_from_choice(event)
                self._pending_steps[step_key] = step
            self._hydrate_step_from_choice_context(step, event)
            self._append_choice(step, event)
            step["last_tick"] = event["tick"]
            return finalized

        if event_type == "sent_choice":
            step = self._pending_steps.get(step_key)
            if step is None:
                if int(event.get("context_dialog_id", 0) or 0) == 0:
                    # Ignore contextless bootstrap sends; wait for a resolvable step context.
                    return finalized
                step = self._new_step_from_choice(event)
                self._pending_steps[step_key] = step
            self._hydrate_step_from_choice_context(step, event)
            step["selected_dialog_id"] = event["dialog_id"]
            step["selected_source_message_id"] = event["message_id"]
            self._mark_choice_selected(step, event["dialog_id"], event["message_id"], event["text_decoded"])
            step["last_tick"] = event["tick"]
            if self._finalize_step(conn, step_key, reason="sent_choice", end_tick=event["tick"]):
                finalized += 1
            return finalized

        step = self._pending_steps.get(step_key)
        if step is not None:
            step["last_tick"] = max(step.get("last_tick", 0), event["tick"])
        return finalized

    def _event_step_key(self, event: Dict[str, Any]) -> str:
        npc_uid = _safe_text(event.get("npc_uid", "")).strip()
        if npc_uid:
            return npc_uid
        agent_id = int(event.get("agent_id", 0) or 0)
        if agent_id:
            return _build_npc_uid(
                int(event.get("map_id", 0) or 0),
                int(event.get("model_id", 0) or 0),
                agent_id,
            )
        return ""

    def _new_step_from_body(self, event: Dict[str, Any]) -> Dict[str, Any]:
        body_dialog_id = event["dialog_id"] or event["context_dialog_id"]
        if body_dialog_id == 0:
            inferred = self._infer_dialog_id_from_body_text(event.get("text_decoded", ""))
            if inferred:
                body_dialog_id = inferred
        npc_uid_instance = self._event_step_key(event)
        body_text_raw = event["text_raw"]
        body_text_decoded = event["text_decoded"]
        if body_dialog_id != 0 and (not body_text_raw or not body_text_decoded):
            cached_raw, cached_decoded = self._cached_body_text_for_dialog(body_dialog_id)
            body_text_raw = body_text_raw or cached_raw
            body_text_decoded = body_text_decoded or cached_decoded
        return {
            "start_tick": event["tick"],
            "last_tick": event["tick"],
            "map_id": event["map_id"],
            "map_name": event.get("map_name", "") or _resolve_map_name(int(event["map_id"] or 0)),
            "agent_id": event["agent_id"],
            "npc_name": event.get("npc_name", "") or _resolve_npc_name(int(event["agent_id"] or 0)),
            "model_id": event["model_id"],
            "npc_uid_instance": npc_uid_instance,
            "npc_uid_archetype": _build_npc_archetype_uid(event["map_id"], event["model_id"]),
            "body_dialog_id": body_dialog_id,
            "body_text_raw": body_text_raw,
            "body_text_decoded": body_text_decoded,
            "selected_dialog_id": 0,
            "selected_source_message_id": 0,
            "choices": [],
        }

    def _new_step_from_choice(self, event: Dict[str, Any]) -> Dict[str, Any]:
        npc_uid_instance = self._event_step_key(event)
        body_dialog_id = event["context_dialog_id"] if event["context_dialog_id"] else 0
        body_text_raw = ""
        body_text_decoded = ""
        if body_dialog_id != 0:
            body_text_raw, body_text_decoded = self._cached_body_text_for_dialog(body_dialog_id)
        return {
            "start_tick": event["tick"],
            "last_tick": event["tick"],
            "map_id": event["map_id"],
            "map_name": event.get("map_name", "") or _resolve_map_name(int(event["map_id"] or 0)),
            "agent_id": event["agent_id"],
            "npc_name": event.get("npc_name", "") or _resolve_npc_name(int(event["agent_id"] or 0)),
            "model_id": event["model_id"],
            "npc_uid_instance": npc_uid_instance,
            "npc_uid_archetype": _build_npc_archetype_uid(event["map_id"], event["model_id"]),
            "body_dialog_id": body_dialog_id,
            "body_text_raw": body_text_raw,
            "body_text_decoded": body_text_decoded,
            "selected_dialog_id": 0,
            "selected_source_message_id": 0,
            "choices": [],
        }

    def _append_choice(self, step: Dict[str, Any], event: Dict[str, Any]) -> None:
        step["choices"].append(
            {
                "choice_index": len(step["choices"]),
                "choice_dialog_id": event["dialog_id"],
                "choice_text_raw": event["text_raw"],
                "choice_text_decoded": event["text_decoded"],
                "skill_id": 0,
                "button_icon": 0,
                "decode_pending": 0,
                "selected": 0,
                "source_message_id": event["message_id"],
            }
        )

    def _hydrate_step_from_choice_context(self, step: Dict[str, Any], event: Dict[str, Any]) -> None:
        context_dialog_id = int(event.get("context_dialog_id", 0) or 0)
        if int(step.get("body_dialog_id", 0) or 0) == 0 and context_dialog_id != 0:
            step["body_dialog_id"] = context_dialog_id
        if int(step.get("map_id", 0) or 0) == 0:
            step["map_id"] = int(event.get("map_id", 0) or 0)
        if not _safe_text(step.get("map_name", "")):
            step["map_name"] = _safe_text(event.get("map_name", "")) or _resolve_map_name(int(event.get("map_id", 0) or 0))
        if int(step.get("agent_id", 0) or 0) == 0:
            step["agent_id"] = int(event.get("agent_id", 0) or 0)
        if not _safe_text(step.get("npc_name", "")):
            step["npc_name"] = _safe_text(event.get("npc_name", "")) or _resolve_npc_name(int(event.get("agent_id", 0) or 0))
        if int(step.get("model_id", 0) or 0) == 0:
            step["model_id"] = int(event.get("model_id", 0) or 0)
        if not _safe_text(step.get("npc_uid_instance", "")):
            step["npc_uid_instance"] = self._event_step_key(event)
        if not _safe_text(step.get("npc_uid_archetype", "")):
            step["npc_uid_archetype"] = _build_npc_archetype_uid(
                int(event.get("map_id", 0) or 0),
                int(event.get("model_id", 0) or 0),
            )
        dialog_id = int(step.get("body_dialog_id", 0) or 0)
        if dialog_id != 0 and (not _safe_text(step.get("body_text_raw")) or not _safe_text(step.get("body_text_decoded"))):
            cached_raw, cached_decoded = self._cached_body_text_for_dialog(dialog_id)
            if cached_raw and not _safe_text(step.get("body_text_raw")):
                step["body_text_raw"] = cached_raw
            if cached_decoded and not _safe_text(step.get("body_text_decoded")):
                step["body_text_decoded"] = cached_decoded

    def _should_hydrate_pending_step(self, step: Dict[str, Any], body_event: Dict[str, Any]) -> bool:
        current_body_id = int(step.get("body_dialog_id", 0) or 0)
        incoming_body_id = int((body_event.get("dialog_id", 0) or body_event.get("context_dialog_id", 0)) or 0)
        current_text = _safe_text(step.get("body_text_decoded", "")).strip()
        incoming_text = _safe_text(body_event.get("text_decoded", "")).strip()
        if current_body_id == 0 and (incoming_body_id != 0 or incoming_text):
            return True
        if current_body_id != 0 and incoming_body_id == current_body_id:
            if incoming_text and (not current_text or incoming_text == current_text):
                return True
        return False

    def _hydrate_pending_step(self, step: Dict[str, Any], body_event: Dict[str, Any]) -> None:
        incoming_body_id = int((body_event.get("dialog_id", 0) or body_event.get("context_dialog_id", 0)) or 0)
        if incoming_body_id != 0:
            step["body_dialog_id"] = incoming_body_id
        incoming_raw = _safe_text(body_event.get("text_raw", ""))
        incoming_decoded = _safe_text(body_event.get("text_decoded", ""))
        if incoming_raw and not _safe_text(step.get("body_text_raw", "")):
            step["body_text_raw"] = incoming_raw
        if incoming_decoded and not _safe_text(step.get("body_text_decoded", "")):
            step["body_text_decoded"] = incoming_decoded
        if int(step.get("map_id", 0) or 0) == 0:
            step["map_id"] = int(body_event.get("map_id", 0) or 0)
        if not _safe_text(step.get("map_name", "")):
            step["map_name"] = _safe_text(body_event.get("map_name", "")) or _resolve_map_name(int(body_event.get("map_id", 0) or 0))
        if int(step.get("agent_id", 0) or 0) == 0:
            step["agent_id"] = int(body_event.get("agent_id", 0) or 0)
        if not _safe_text(step.get("npc_name", "")):
            step["npc_name"] = _safe_text(body_event.get("npc_name", "")) or _resolve_npc_name(int(body_event.get("agent_id", 0) or 0))
        if int(step.get("model_id", 0) or 0) == 0:
            step["model_id"] = int(body_event.get("model_id", 0) or 0)
        if not _safe_text(step.get("npc_uid_instance", "")):
            step["npc_uid_instance"] = self._event_step_key(body_event)
        if not _safe_text(step.get("npc_uid_archetype", "")):
            step["npc_uid_archetype"] = _build_npc_archetype_uid(
                int(body_event.get("map_id", 0) or 0),
                int(body_event.get("model_id", 0) or 0),
            )
        step["last_tick"] = max(int(step.get("last_tick", 0) or 0), int(body_event.get("tick", 0) or 0))

    def _remember_body_text_mapping(self, body_event: Dict[str, Any]) -> None:
        dialog_id = int((body_event.get("dialog_id", 0) or body_event.get("context_dialog_id", 0)) or 0)
        raw = _safe_text(body_event.get("text_raw", ""))
        decoded = _safe_text(body_event.get("text_decoded", ""))
        if dialog_id != 0 and (raw or decoded):
            self._dialog_id_to_body_text[dialog_id] = (raw, decoded)
            key = self._body_text_key(decoded)
            if key:
                self._body_text_to_dialog_id[key] = dialog_id

    def _cached_body_text_for_dialog(self, dialog_id: int) -> Tuple[str, str]:
        value = self._dialog_id_to_body_text.get(int(dialog_id))
        if not value:
            return "", ""
        return _safe_text(value[0]), _safe_text(value[1])

    def _body_text_key(self, text: Any) -> str:
        value = _safe_text(text).strip()
        return value.lower() if value else ""

    def _infer_dialog_id_from_body_text(self, text: Any) -> int:
        key = self._body_text_key(text)
        if not key:
            return 0
        return int(self._body_text_to_dialog_id.get(key, 0) or 0)

    def _mark_choice_selected(self, step: Dict[str, Any], dialog_id: int, message_id: int, fallback_text: str) -> None:
        matched = False
        for choice in step["choices"]:
            if int(choice.get("choice_dialog_id", 0)) == int(dialog_id):
                choice["selected"] = 1
                choice["source_message_id"] = message_id
                matched = True
        if matched:
            return
        step["choices"].append(
            {
                "choice_index": len(step["choices"]),
                "choice_dialog_id": int(dialog_id),
                "choice_text_raw": _safe_text(fallback_text),
                "choice_text_decoded": _safe_text(fallback_text),
                "skill_id": 0,
                "button_icon": 0,
                "decode_pending": 0,
                "selected": 1,
                "source_message_id": int(message_id),
            }
        )

    def _finalize_stale_steps(self, conn: sqlite3.Connection, current_tick: int, current_map_id: int) -> int:
        finalized = 0
        keys = list(self._pending_steps.keys())
        for key in keys:
            step = self._pending_steps.get(key)
            if step is None:
                continue
            last_tick = int(step.get("last_tick", 0) or 0)
            map_id = int(step.get("map_id", 0) or 0)
            if current_map_id and map_id and map_id != current_map_id:
                if self._finalize_step(conn, key, reason="map_change", end_tick=current_tick):
                    finalized += 1
                continue
            if current_tick and last_tick and (current_tick - last_tick) > self._step_timeout_ms:
                if self._finalize_step(conn, key, reason="timeout", end_tick=current_tick):
                    finalized += 1
        return finalized

    def _finalize_step(self, conn: sqlite3.Connection, key: str, *, reason: str, end_tick: int) -> bool:
        step = self._pending_steps.pop(key, None)
        if step is None:
            return False

        body_dialog_id = int(step.get("body_dialog_id", 0) or 0)
        body_text_raw = _safe_text(step.get("body_text_raw", ""))
        body_text_decoded = _safe_text(step.get("body_text_decoded", ""))
        selected_dialog_id = int(step.get("selected_dialog_id", 0) or 0)
        choices = list(step.get("choices", []))
        map_id = int(step.get("map_id", 0) or 0)
        agent_id = int(step.get("agent_id", 0) or 0)
        model_id = int(step.get("model_id", 0) or 0)
        map_name = _safe_text(step.get("map_name", "")).strip() or _resolve_map_name(map_id)
        npc_name = _safe_text(step.get("npc_name", "")).strip() or _resolve_npc_name(agent_id)

        if body_dialog_id == 0 and body_text_decoded:
            inferred_id = self._infer_dialog_id_from_body_text(body_text_decoded)
            if inferred_id:
                body_dialog_id = inferred_id
                step["body_dialog_id"] = inferred_id

        if body_dialog_id != 0 and (not body_text_raw or not body_text_decoded):
            cached_raw, cached_decoded = self._cached_body_text_for_dialog(body_dialog_id)
            if cached_raw and not body_text_raw:
                body_text_raw = cached_raw
                step["body_text_raw"] = cached_raw
            if cached_decoded and not body_text_decoded:
                body_text_decoded = cached_decoded
                step["body_text_decoded"] = cached_decoded

        # Drop pure bootstrap noise: no body, no text, no choices, no user selection.
        if body_dialog_id == 0 and not body_text_decoded.strip() and not choices and selected_dialog_id == 0:
            return False

        cursor = conn.execute(
            """
            INSERT INTO dialog_steps (
                start_tick, end_tick, map_id, map_name, agent_id, npc_name, model_id, npc_uid_instance, npc_uid_archetype,
                body_dialog_id, body_text_raw, body_text_decoded, selected_dialog_id,
                selected_source_message_id, finalized_reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(step.get("start_tick", 0) or 0),
                int(end_tick or step.get("last_tick", 0) or 0),
                map_id,
                map_name,
                agent_id,
                npc_name,
                model_id,
                _safe_text(step.get("npc_uid_instance", "")),
                _safe_text(step.get("npc_uid_archetype", "")),
                body_dialog_id,
                body_text_raw,
                body_text_decoded,
                selected_dialog_id,
                int(step.get("selected_source_message_id", 0) or 0),
                _safe_text(reason),
                float(time.time()),
            ),
        )
        step_id = int(cursor.lastrowid or 0)
        if step_id <= 0:
            return False

        for index, choice in enumerate(step.get("choices", [])):
            conn.execute(
                """
                INSERT INTO dialog_choices (
                    step_id, choice_index, choice_dialog_id, choice_text_raw, choice_text_decoded,
                    skill_id, button_icon, decode_pending, selected, source_message_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    step_id,
                    int(choice.get("choice_index", index)),
                    int(choice.get("choice_dialog_id", 0) or 0),
                    _safe_text(choice.get("choice_text_raw", "")),
                    _safe_text(choice.get("choice_text_decoded", "")),
                    int(choice.get("skill_id", 0) or 0),
                    int(choice.get("button_icon", 0) or 0),
                    1 if bool(choice.get("decode_pending", False)) else 0,
                    1 if bool(choice.get("selected", False)) else 0,
                    int(choice.get("source_message_id", 0) or 0),
                ),
            )
        if body_dialog_id != 0 and body_text_decoded:
            key_by_text = self._body_text_key(body_text_decoded)
            if key_by_text:
                self._body_text_to_dialog_id[key_by_text] = body_dialog_id
            self._dialog_id_to_body_text[body_dialog_id] = (body_text_raw, body_text_decoded)
        return True

    def _repair_persisted_step_rows(self, conn: sqlite3.Connection) -> None:
        # 1) Backfill missing body dialog ids from exact body text matches for same NPC instance.
        conn.execute(
            """
            UPDATE dialog_steps
            SET body_dialog_id = (
                SELECT t2.body_dialog_id
                FROM dialog_steps t2
                WHERE t2.npc_uid_instance = dialog_steps.npc_uid_instance
                  AND t2.body_dialog_id <> 0
                  AND t2.body_text_decoded = dialog_steps.body_text_decoded
                ORDER BY t2.id DESC
                LIMIT 1
            )
            WHERE body_dialog_id = 0
              AND IFNULL(body_text_decoded, '') <> ''
              AND EXISTS (
                SELECT 1
                FROM dialog_steps t2
                WHERE t2.npc_uid_instance = dialog_steps.npc_uid_instance
                  AND t2.body_dialog_id <> 0
                  AND t2.body_text_decoded = dialog_steps.body_text_decoded
              )
            """
        )

        # 2) Backfill missing body text from same NPC+body dialog rows.
        conn.execute(
            """
            UPDATE dialog_steps
            SET body_text_raw = CASE
                    WHEN IFNULL(body_text_raw, '') <> '' THEN body_text_raw
                    ELSE COALESCE((
                        SELECT t2.body_text_raw
                        FROM dialog_steps t2
                        WHERE t2.npc_uid_instance = dialog_steps.npc_uid_instance
                          AND t2.body_dialog_id = dialog_steps.body_dialog_id
                          AND IFNULL(t2.body_text_raw, '') <> ''
                        ORDER BY t2.id DESC
                        LIMIT 1
                    ), '')
                END,
                body_text_decoded = CASE
                    WHEN IFNULL(body_text_decoded, '') <> '' THEN body_text_decoded
                    ELSE COALESCE((
                        SELECT t2.body_text_decoded
                        FROM dialog_steps t2
                        WHERE t2.npc_uid_instance = dialog_steps.npc_uid_instance
                          AND t2.body_dialog_id = dialog_steps.body_dialog_id
                          AND IFNULL(t2.body_text_decoded, '') <> ''
                        ORDER BY t2.id DESC
                        LIMIT 1
                    ), '')
                END
            WHERE body_dialog_id <> 0
              AND (IFNULL(body_text_raw, '') = '' OR IFNULL(body_text_decoded, '') = '')
            """
        )

    def _get_choices_by_step_ids(self, conn: sqlite3.Connection, step_ids: Sequence[int]) -> Dict[int, List[Dict[str, Any]]]:
        if not step_ids:
            return {}
        placeholders = ",".join("?" for _ in step_ids)
        rows = conn.execute(
            f"""
            SELECT id, step_id, choice_index, choice_dialog_id, choice_text_raw, choice_text_decoded,
                   skill_id, button_icon, decode_pending, selected, source_message_id
            FROM dialog_choices
            WHERE step_id IN ({placeholders})
            ORDER BY step_id ASC, choice_index ASC, id ASC
            """,
            list(step_ids),
        ).fetchall()
        out: Dict[int, List[Dict[str, Any]]] = {}
        for row in rows:
            choice = self._choice_row_to_dict(row)
            out.setdefault(int(choice["step_id"]), []).append(choice)
        return out

    def _overflow_ids(self, conn: sqlite3.Connection, table_name: str, max_rows: int) -> List[int]:
        row = conn.execute(f"SELECT COUNT(*) AS total FROM {table_name}").fetchone()
        total = int(row[0]) if row else 0
        overflow = max(0, total - int(max_rows))
        if overflow <= 0:
            return []
        rows = conn.execute(
            f"SELECT id FROM {table_name} ORDER BY id ASC LIMIT ?",
            (overflow,),
        ).fetchall()
        return [int(item[0]) for item in rows]

    def _trim_table(self, conn: sqlite3.Connection, table_name: str, max_rows: int) -> int:
        overflow_ids = self._overflow_ids(conn, table_name, max_rows)
        if not overflow_ids:
            return 0
        cursor = conn.execute(
            f"DELETE FROM {table_name} WHERE id IN ({','.join('?' for _ in overflow_ids)})",
            overflow_ids,
        )
        return int(cursor.rowcount or 0)

    def _delete_choices_for_step_ids(self, conn: sqlite3.Connection, step_ids: Sequence[int]) -> int:
        if not step_ids:
            return 0
        cursor = conn.execute(
            f"DELETE FROM dialog_choices WHERE step_id IN ({','.join('?' for _ in step_ids)})",
            list(step_ids),
        )
        return int(cursor.rowcount or 0)

    def _callback_row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": int(row["id"]),
            "tick": int(row["tick"]),
            "ts": float(row["ts"]),
            "message_id": int(row["message_id"]),
            "incoming": bool(row["incoming"]),
            "dialog_id": int(row["dialog_id"]),
            "context_dialog_id": int(row["context_dialog_id"]),
            "agent_id": int(row["agent_id"]),
            "map_id": int(row["map_id"]),
            "map_name": _safe_text(row["map_name"]),
            "model_id": int(row["model_id"]),
            "npc_uid": _safe_text(row["npc_uid"]),
            "npc_name": _safe_text(row["npc_name"]),
            "event_type": _safe_text(row["event_type"]),
            "text_raw": _safe_text(row["text_raw"]),
            "text_decoded": _safe_text(row["text_decoded"]),
        }

    def _raw_row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": int(row["id"]),
            "tick": int(row["tick"]),
            "ts": float(row["ts"]),
            "message_id": int(row["message_id"]),
            "incoming": bool(row["incoming"]),
            "map_id": int(row["map_id"]),
            "map_name": _safe_text(row["map_name"]),
            "agent_id": int(row["agent_id"]),
            "npc_name": _safe_text(row["npc_name"]),
            "model_id": int(row["model_id"]),
            "npc_uid": _safe_text(row["npc_uid"]),
            "dialog_id": int(row["dialog_id"]),
            "context_dialog_id": int(row["context_dialog_id"]),
            "event_type": _safe_text(row["event_type"]),
            "text_raw": _safe_text(row["text_raw"]),
        }

    def _step_row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": int(row["id"]),
            "start_tick": int(row["start_tick"]),
            "end_tick": int(row["end_tick"]),
            "map_id": int(row["map_id"]),
            "map_name": _safe_text(row["map_name"]),
            "agent_id": int(row["agent_id"]),
            "npc_name": _safe_text(row["npc_name"]),
            "model_id": int(row["model_id"]),
            "npc_uid_instance": _safe_text(row["npc_uid_instance"]),
            "npc_uid_archetype": _safe_text(row["npc_uid_archetype"]),
            "body_dialog_id": int(row["body_dialog_id"]),
            "body_text_raw": _safe_text(row["body_text_raw"]),
            "body_text_decoded": _safe_text(row["body_text_decoded"]),
            "selected_dialog_id": int(row["selected_dialog_id"]),
            "selected_source_message_id": int(row["selected_source_message_id"]),
            "finalized_reason": _safe_text(row["finalized_reason"]),
            "created_at": float(row["created_at"]),
        }

    def _choice_row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": int(row["id"]),
            "step_id": int(row["step_id"]),
            "choice_index": int(row["choice_index"]),
            "choice_dialog_id": int(row["choice_dialog_id"]),
            "choice_text_raw": _safe_text(row["choice_text_raw"]),
            "choice_text_decoded": _safe_text(row["choice_text_decoded"]),
            "skill_id": int(row["skill_id"]),
            "button_icon": int(row["button_icon"]),
            "decode_pending": bool(row["decode_pending"]),
            "selected": bool(row["selected"]),
            "source_message_id": int(row["source_message_id"]),
        }

    def _write_json(self, path: str, payload: Dict[str, Any]) -> None:
        out_path = os.path.abspath(str(path))
        out_dir = os.path.dirname(out_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def _key_seen(self, event_key: str) -> bool:
        return event_key in self._seen_keys

    def _remember_key(self, event_key: str) -> None:
        self._seen_keys.add(event_key)
        self._seen_order.append(event_key)
        if len(self._seen_order) <= MAX_SEEN_EVENT_KEYS:
            return
        overflow = len(self._seen_order) - MAX_SEEN_EVENT_KEYS
        stale = self._seen_order[:overflow]
        self._seen_order = self._seen_order[overflow:]
        for key in stale:
            self._seen_keys.discard(key)


_PIPELINE_INSTANCE: Optional[DialogStepSQLitePipeline] = None
_PIPELINE_INSTANCE_LOCK = threading.Lock()


def get_dialog_step_pipeline() -> DialogStepSQLitePipeline:
    global _PIPELINE_INSTANCE
    if _PIPELINE_INSTANCE is not None:
        return _PIPELINE_INSTANCE
    with _PIPELINE_INSTANCE_LOCK:
        if _PIPELINE_INSTANCE is None:
            _PIPELINE_INSTANCE = DialogStepSQLitePipeline()
        return _PIPELINE_INSTANCE


# Diagnostics helpers for persisted dialog history.
def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _build_diag_issue(
    *,
    severity: str,
    rule: str,
    message: str,
    npc_uid: str = "",
    step_id: int = 0,
    dialog_id: int = 0,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "severity": severity,
        "rule": rule,
        "message": message,
        "npc_uid": npc_uid,
        "step_id": int(step_id),
        "dialog_id": int(dialog_id),
        "details": details or {},
    }


def _analyze_dialog_steps(
    steps: List[Dict[str, Any]],
    *,
    max_issues: int = 250,
) -> Dict[str, Any]:
    """
    Run lightweight consistency checks over persisted dialog history rows.

    The diagnostics are intentionally conservative and meant for monitor/debug
    surfaces, not for blocking runtime behavior.
    """
    issues: List[Dict[str, Any]] = []

    for step in steps:
        step_id = _as_int(step.get("id", 0), 0)
        npc_uid = _as_text(step.get("npc_uid_instance", "")).strip()
        body_dialog_id = _as_int(step.get("body_dialog_id", 0), 0)
        selected_dialog_id = _as_int(step.get("selected_dialog_id", 0), 0)
        finalized_reason = _as_text(step.get("finalized_reason", "")).strip().lower()
        body_text = _as_text(step.get("body_text_raw", ""))
        choices = list(step.get("choices", []) or [])

        if body_dialog_id == 0 and choices:
            issues.append(
                _build_diag_issue(
                    severity="warning",
                    rule="orphan_choices_without_body",
                    message="Turn has choices but no body dialog id.",
                    npc_uid=npc_uid,
                    step_id=step_id,
                    dialog_id=0,
                    details={"choice_count": len(choices)},
                )
            )

        if body_dialog_id != 0 and not body_text.strip():
            issues.append(
                _build_diag_issue(
                    severity="warning",
                    rule="missing_body_text",
                    message="Turn body dialog id is set but body text is empty.",
                    npc_uid=npc_uid,
                    step_id=step_id,
                    dialog_id=body_dialog_id,
                )
            )

        if finalized_reason == "timeout":
            issues.append(
                _build_diag_issue(
                    severity="info",
                    rule="timeout_finalization",
                    message="Turn was finalized by timeout.",
                    npc_uid=npc_uid,
                    step_id=step_id,
                    dialog_id=body_dialog_id,
                )
            )

        choice_ids: List[int] = [
            _as_int(choice.get("choice_dialog_id", 0), 0)
            for choice in choices
            if _as_int(choice.get("choice_dialog_id", 0), 0) != 0
        ]

        if selected_dialog_id != 0 and selected_dialog_id not in set(choice_ids):
            issues.append(
                _build_diag_issue(
                    severity="error",
                    rule="selected_choice_not_offered",
                    message="Selected dialog id is not present in the offered choices for this step.",
                    npc_uid=npc_uid,
                    step_id=step_id,
                    dialog_id=selected_dialog_id,
                    details={"offered_choice_ids": choice_ids},
                )
            )

    issues.sort(
        key=lambda issue: (
            _DIAG_SEVERITY_ORDER.get(_as_text(issue.get("severity", "info")).lower(), 99),
            -_as_int(issue.get("step_id", 0), 0),
        )
    )

    if max_issues > 0:
        issues = issues[: int(max_issues)]

    summary = {"error": 0, "warning": 0, "info": 0, "total": len(issues)}
    for issue in issues:
        severity = _as_text(issue.get("severity", "info")).lower()
        if severity not in summary:
            summary[severity] = 0
        summary[severity] += 1

    return {
        "summary": summary,
        "issues": issues,
        "analyzed_steps": len(steps),
    }


class DialogInfo:
    """Python wrapper for native DialogInfo struct."""

    def __init__(self, native_dialog_info):
        self.native = native_dialog_info
        self.dialog_id = native_dialog_info.dialog_id
        self.flags = native_dialog_info.flags
        self.frame_type = native_dialog_info.frame_type
        self.event_handler = native_dialog_info.event_handler
        self.content_id = native_dialog_info.content_id
        self.property_id = native_dialog_info.property_id
        self.content = _sanitize_dialog_text(native_dialog_info.content)
        self.agent_id = native_dialog_info.agent_id

    def is_available(self) -> bool:
        return (self.flags & 0x1) != 0

    def __repr__(self) -> str:
        return f"DialogInfo(id=0x{self.dialog_id:04x}, available={self.is_available()})"


class ActiveDialogInfo:
    """Python wrapper for native ActiveDialogInfo struct."""

    def __init__(
        self,
        native_active_dialog=None,
        *,
        dialog_id: int = 0,
        context_dialog_id: int = 0,
        agent_id: int = 0,
        dialog_id_authoritative: bool = False,
        message: str = "",
        raw_message: str = "",
    ):
        if native_active_dialog is not None:
            self.native = native_active_dialog
            self.dialog_id = int(getattr(native_active_dialog, "dialog_id", 0))
            self.context_dialog_id = int(getattr(native_active_dialog, "context_dialog_id", 0))
            self.agent_id = int(getattr(native_active_dialog, "agent_id", 0))
            self.dialog_id_authoritative = bool(getattr(native_active_dialog, "dialog_id_authoritative", False))
            self.raw_message = str(getattr(native_active_dialog, "message", "") or "")
            self.message = _sanitize_dialog_text(self.raw_message)
        else:
            self.native = None
            self.dialog_id = dialog_id
            self.context_dialog_id = context_dialog_id
            self.agent_id = agent_id
            self.dialog_id_authoritative = dialog_id_authoritative
            self.raw_message = str(raw_message or message or "")
            self.message = _sanitize_dialog_text(message)

    def __repr__(self) -> str:
        return (
            "ActiveDialogInfo("
            f"dialog_id=0x{self.dialog_id:04x}, "
            f"context_dialog_id=0x{self.context_dialog_id:04x}, "
            f"authoritative={self.dialog_id_authoritative}, "
            f"agent_id={self.agent_id})"
        )


class DialogButtonInfo:
    """Python wrapper for native DialogButtonInfo struct."""

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
            self.dialog_id = native_button_info.dialog_id
            self.button_icon = native_button_info.button_icon
            self.message = _sanitize_dialog_text(native_button_info.message)
            self.message_decoded = _sanitize_dialog_text(native_button_info.message_decoded)
            self.message_decode_pending = native_button_info.message_decode_pending
        else:
            self.native = None
            self.dialog_id = dialog_id
            self.button_icon = button_icon
            self.message = _sanitize_dialog_text(message)
            self.message_decoded = _sanitize_dialog_text(message_decoded)
            self.message_decode_pending = message_decode_pending

    def __repr__(self) -> str:
        return f"DialogButtonInfo(dialog_id=0x{self.dialog_id:04x})"


# Inline choice extraction helpers.
def _parse_inline_choice_dialog_id(raw_value: Any) -> int:
    value = str(raw_value or "").strip()
    if not value:
        return 0
    try:
        return int(value, 0)
    except Exception:
        return 0


def _extract_inline_dialog_choices_from_text(body_text: Optional[str]) -> List[DialogButtonInfo]:
    """
    Extract `<a=...>...</a>` style inline choices from raw dialog body text.

    Some GW dialogs expose choices inline instead of through the native active
    button list, so this parser acts as the fallback source for those screens.
    """
    text = str(body_text or "")
    if not text or "<a=" not in text.lower():
        return []

    choices: List[DialogButtonInfo] = []
    seen: set[tuple[int, str]] = set()
    for match in _INLINE_CHOICE_RE.finditer(text):
        dialog_id = _parse_inline_choice_dialog_id(match.group(1))
        if dialog_id == 0:
            continue
        label = _sanitize_dialog_text(match.group(2))
        if not label:
            label = "<empty>"
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


def extract_inline_dialog_choices_from_text(body_text: Optional[str]) -> List[DialogButtonInfo]:
    """Parse inline GW dialog anchors like `<a=1>...</a>` from raw body text."""
    return _extract_inline_dialog_choices_from_text(body_text)


def _extract_raw_active_dialog_message(active_dialog: Any) -> str:
    if active_dialog is None:
        return ""

    raw_message = getattr(active_dialog, "raw_message", None)
    if raw_message is not None:
        return str(raw_message or "")

    native_dialog = getattr(active_dialog, "native", None)
    if native_dialog is not None:
        native_message = getattr(native_dialog, "message", None)
        if native_message is not None:
            return str(native_message or "")

    message = getattr(active_dialog, "message", None)
    if message is not None:
        return str(message or "")
    return ""


def extract_inline_dialog_choices_from_active(active_dialog: Any) -> List[DialogButtonInfo]:
    """Parse inline choices from either a wrapped ActiveDialogInfo or raw native active dialog object."""
    return _extract_inline_dialog_choices_from_text(_extract_raw_active_dialog_message(active_dialog))


class DialogTextDecodedInfo:
    """Python wrapper for decoded dialog text status."""

    def __init__(self, native_info):
        self.native = native_info
        self.dialog_id = native_info.dialog_id
        self.text = _sanitize_dialog_text(native_info.text)
        self.pending = native_info.pending


class DialogCallbackJournalEntry:
    """Python wrapper for native structured dialog callback journal entries."""

    def __init__(self, native_info):
        self.native = native_info
        self.tick = int(getattr(native_info, "tick", 0))
        self.message_id = int(getattr(native_info, "message_id", 0))
        self.incoming = bool(getattr(native_info, "incoming", False))
        self.dialog_id = int(getattr(native_info, "dialog_id", 0))
        self.context_dialog_id = int(getattr(native_info, "context_dialog_id", 0))
        self.agent_id = int(getattr(native_info, "agent_id", 0))
        self.map_id = int(getattr(native_info, "map_id", 0))
        self.model_id = int(getattr(native_info, "model_id", 0))
        self.dialog_id_authoritative = bool(getattr(native_info, "dialog_id_authoritative", False))
        self.context_dialog_id_inferred = bool(getattr(native_info, "context_dialog_id_inferred", False))
        self.npc_uid = str(getattr(native_info, "npc_uid", "") or "")
        self.event_type = str(getattr(native_info, "event_type", "") or "")
        # Keep callback journal text raw; callers decide whether/how to sanitize.
        self.text = str(getattr(native_info, "text", "") or "")


class DialogWidget:
    """
    High-level wrapper around the native PyDialog module.

    Use this class when you want one object that exposes live dialog state,
    static dialog metadata, callback journals, and optional persisted history.
    """

    def __init__(self) -> None:
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize the native dialog module if it is available."""
        if PyDialog is None:
            return False
        try:
            PyDialog.PyDialog.initialize()
            self._initialized = True
            return True
        except Exception:
            self._initialized = False
            return False

    def terminate(self) -> None:
        """Terminate the native dialog module and clear local initialized state."""
        if PyDialog is None:
            return
        try:
            PyDialog.PyDialog.terminate()
        finally:
            self._initialized = False

    def get_active_dialog(self) -> Optional[ActiveDialogInfo]:
        """
        Return the current live dialog body, or `None` when no dialog is active.

        This is the main entry point for live dialog automation.
        """
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

    def get_active_dialog_buttons(self) -> List[DialogButtonInfo]:
        """
        Return the currently visible dialog buttons for the active screen.

        Falls back to parsing inline body markup when the native button list is
        empty for dialogs that encode choices directly in the message text.
        """
        native_list = _coerce_native_list(_call_native_dialog_method("get_active_dialog_buttons", []))
        buttons = [DialogButtonInfo(item) for item in native_list]
        if buttons:
            return buttons
        # Some dialogs expose choices inline in the body markup instead of through the native
        # button list. Falling back here keeps the public API stable for those screens.
        native_active = _call_native_dialog_method("get_active_dialog", None)
        return extract_inline_dialog_choices_from_active(native_active)

    def get_last_selected_dialog_id(self) -> int:
        """Return the most recent dialog id sent through the native dialog API."""
        return int(_call_native_dialog_method("get_last_selected_dialog_id", 0) or 0)

    def _get_dialog_choice_catalog_text(self, dialog_id: int) -> str:
        if int(dialog_id) == 0:
            return ""
        try:
            dialog_info = self.get_dialog_info(int(dialog_id))
        except Exception:
            dialog_info = None
        if dialog_info is not None:
            content = _sanitize_dialog_text(getattr(dialog_info, "content", ""))
            if content:
                return content
        try:
            return _sanitize_dialog_text(self.get_dialog_text_decoded(int(dialog_id)))
        except Exception:
            return ""

    def _get_dialog_choice_history_texts(
        self,
        dialog_id: int,
        *,
        active_dialog: Optional[ActiveDialogInfo] = None,
        history_limit: int = 25,
    ) -> List[str]:
        """
        Collect historical labels for a choice dialog id from persisted dialog steps.

        This is a recovery helper for live screens whose visible button text is
        missing or undecoded.
        """
        if int(dialog_id) == 0:
            return []

        query_kwargs: Dict[str, Any] = {
            "choice_dialog_id": int(dialog_id),
            "limit": max(1, int(history_limit)),
            "offset": 0,
            "include_choices": True,
            "sync": False,
        }
        if active_dialog is not None:
            body_dialog_id = int(
                getattr(active_dialog, "context_dialog_id", 0)
                or getattr(active_dialog, "dialog_id", 0)
                or 0
            )
            if body_dialog_id != 0:
                query_kwargs["body_dialog_id"] = body_dialog_id
            # The active NPC/body filters are what make fallback matching safe enough to use for
            # automation. Without them, reused dialog ids from another NPC can match incorrectly.
            query_kwargs.update(_build_active_dialog_npc_filters(active_dialog))

        steps = self.get_dialog_steps(**query_kwargs)

        texts: List[str] = []
        for step in steps:
            for choice in list(step.get("choices", []) or []):
                if int(choice.get("choice_dialog_id", 0) or 0) != int(dialog_id):
                    continue
                _append_unique_dialog_choice_text(texts, choice.get("choice_text_decoded", ""))
                _append_unique_dialog_choice_text(texts, choice.get("choice_text_raw", ""))
        return texts

    def get_active_dialog_choice_id_by_text(self, text: Optional[str]) -> int:
        """Resolve a visible choice by its current on-screen label only."""
        needle = _normalize_dialog_choice_text(text)
        if not needle or not self.is_dialog_active():
            return 0

        for button in self.get_active_dialog_buttons():
            dialog_id = int(getattr(button, "dialog_id", 0) or 0)
            if dialog_id == 0:
                continue
            if _normalize_dialog_choice_text(_get_dialog_button_label(button)) == needle:
                return dialog_id
        return 0

    def get_active_dialog_choice_id_by_text_with_fallback(
        self,
        text: Optional[str],
        *,
        history_limit: int = 25,
    ) -> int:
        """
        Resolve a choice by text using live labels first, then catalog/history fallbacks.

        This is the safer automation helper when some labels are blank, inline,
        or still waiting for decode status to catch up.
        """
        needle = _normalize_dialog_choice_text(text)
        if not needle or not self.is_dialog_active():
            return 0

        buttons = list(self.get_active_dialog_buttons())
        if not buttons:
            return 0

        for button in buttons:
            dialog_id = int(getattr(button, "dialog_id", 0) or 0)
            if dialog_id == 0:
                continue
            if _normalize_dialog_choice_text(_get_dialog_button_label(button)) == needle:
                return dialog_id

        # Resolution order matters:
        # 1. live visible labels,
        # 2. static catalog / decoded dialog text,
        # 3. persisted history scoped to the current NPC/body.
        #
        # The earlier tiers are cheaper and less ambiguous. History is a recovery path only.
        for button in buttons:
            dialog_id = int(getattr(button, "dialog_id", 0) or 0)
            if dialog_id == 0:
                continue
            if _normalize_dialog_choice_text(self._get_dialog_choice_catalog_text(dialog_id)) == needle:
                return dialog_id

        active_dialog = self.get_active_dialog()
        try:
            self.sync_dialog_storage(include_raw=False, include_callback_journal=True)
        except Exception:
            pass

        for button in buttons:
            dialog_id = int(getattr(button, "dialog_id", 0) or 0)
            if dialog_id == 0:
                continue
            history_texts = self._get_dialog_choice_history_texts(
                dialog_id,
                active_dialog=active_dialog,
                history_limit=history_limit,
            )
            for candidate in history_texts:
                if _normalize_dialog_choice_text(candidate) == needle:
                    return dialog_id
        return 0

    def send_active_dialog_choice_by_text(self, text: Optional[str]) -> bool:
        """Send the live visible choice whose label matches `text`."""
        dialog_id = self.get_active_dialog_choice_id_by_text(text)
        if dialog_id == 0:
            return False

        try:
            from .Player import Player
        except Exception:
            try:
                from Player import Player  # type: ignore
            except Exception:
                return False

        try:
            Player.SendDialog(dialog_id)
            return True
        except Exception:
            return False

    def send_active_dialog_choice_by_text_with_fallback(
        self,
        text: Optional[str],
        *,
        history_limit: int = 25,
    ) -> bool:
        """Send a choice by text using the fallback resolution path when needed."""
        dialog_id = self.get_active_dialog_choice_id_by_text_with_fallback(
            text,
            history_limit=history_limit,
        )
        if dialog_id == 0:
            return False

        try:
            from .Player import Player
        except Exception:
            try:
                from Player import Player  # type: ignore
            except Exception:
                return False

        try:
            Player.SendDialog(dialog_id)
            return True
        except Exception:
            return False

    def get_dialog_text_decoded(self, dialog_id: int) -> str:
        """Return decoded text for a dialog id using the catalog when available."""
        catalog = _get_dialog_catalog_widget()
        if catalog is not None:
            return catalog.get_dialog_text_decoded(dialog_id)
        return _sanitize_dialog_text(_call_native_dialog_method("get_dialog_text_decoded", "", dialog_id))

    def is_dialog_text_decode_pending(self, dialog_id: int) -> bool:
        """Return whether a dialog id is still waiting for decoded text."""
        catalog = _get_dialog_catalog_widget()
        if catalog is not None:
            return catalog.is_dialog_text_decode_pending(dialog_id)
        return bool(_call_native_dialog_method("is_dialog_text_decode_pending", False, dialog_id))

    def is_dialog_active(self) -> bool:
        """Return whether the game currently reports an active dialog screen."""
        return bool(_call_native_dialog_method("is_dialog_active", False))

    def is_dialog_displayed(self, dialog_id: int) -> bool:
        return bool(_call_native_dialog_method("is_dialog_displayed", False, dialog_id))

    def get_dialog_text_decode_status(self) -> List[DialogTextDecodedInfo]:
        """Return decode status rows for dialog ids currently known to the runtime/catalog."""
        catalog = _get_dialog_catalog_widget()
        if catalog is not None:
            return catalog.get_dialog_text_decode_status()
        native_list = _coerce_native_list(_call_native_dialog_method("get_dialog_text_decode_status", []))
        return [DialogTextDecodedInfo(item) for item in native_list]

    def is_dialog_available(self, dialog_id: int) -> bool:
        catalog = _get_dialog_catalog_widget()
        if catalog is not None:
            return catalog.is_dialog_available(dialog_id)
        return bool(_call_native_dialog_method("is_dialog_available", False, dialog_id))

    def get_dialog_info(self, dialog_id: int) -> Optional[DialogInfo]:
        """Return static metadata for a dialog id, not the live active dialog screen."""
        catalog = _get_dialog_catalog_widget()
        if catalog is not None:
            return catalog.get_dialog_info(dialog_id)
        native_info = _call_native_dialog_method("get_dialog_info", None, dialog_id)
        if native_info is None:
            return None
        return DialogInfo(native_info)

    def enumerate_available_dialogs(self) -> List[DialogInfo]:
        """Enumerate the currently available static dialog catalog entries."""
        catalog = _get_dialog_catalog_widget()
        if catalog is not None:
            return catalog.enumerate_available_dialogs()
        native_list = _coerce_native_list(_call_native_dialog_method("enumerate_available_dialogs", []))
        return [DialogInfo(item) for item in native_list]

    def get_dialog_event_logs(self) -> List:
        return _call_native_dialog_method("get_dialog_event_logs", [])

    def get_dialog_event_logs_received(self) -> List:
        return _call_native_dialog_method("get_dialog_event_logs_received", [])

    def get_dialog_event_logs_sent(self) -> List:
        return _call_native_dialog_method("get_dialog_event_logs_sent", [])

    def clear_dialog_event_logs(self) -> None:
        _call_native_dialog_method("clear_dialog_event_logs", None)

    def clear_dialog_event_logs_received(self) -> None:
        _call_native_dialog_method("clear_dialog_event_logs_received", None)

    def clear_dialog_event_logs_sent(self) -> None:
        _call_native_dialog_method("clear_dialog_event_logs_sent", None)

    def get_dialog_callback_journal(self) -> List[DialogCallbackJournalEntry]:
        """Return the full structured callback journal exposed by the native layer."""
        native_list = _coerce_native_list(_call_native_dialog_method("get_dialog_callback_journal", []))
        return [DialogCallbackJournalEntry(item) for item in native_list]

    def get_dialog_callback_journal_received(self) -> List[DialogCallbackJournalEntry]:
        native_list = _coerce_native_list(_call_native_dialog_method("get_dialog_callback_journal_received", []))
        return [DialogCallbackJournalEntry(item) for item in native_list]

    def get_dialog_callback_journal_sent(self) -> List[DialogCallbackJournalEntry]:
        native_list = _coerce_native_list(_call_native_dialog_method("get_dialog_callback_journal_sent", []))
        return [DialogCallbackJournalEntry(item) for item in native_list]

    def clear_dialog_callback_journal(self) -> None:
        _call_native_dialog_method("clear_dialog_callback_journal", None)

    def clear_dialog_callback_journal_received(self) -> None:
        _call_native_dialog_method("clear_dialog_callback_journal_received", None)

    def clear_dialog_callback_journal_sent(self) -> None:
        _call_native_dialog_method("clear_dialog_callback_journal_sent", None)

    def get_callback_journal(
        self,
        npc_uid: Optional[str] = None,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
    ) -> List[DialogCallbackJournalEntry]:
        """
        Return filtered callback journal entries from the live native journal buffer.

        Use this when you need recent structured callback events without touching
        the SQLite-backed persisted history.
        """
        incoming_filter = _normalize_direction_filter(direction)
        message_id_filter, event_type_filter = _parse_message_type_filter(message_type)
        npc_uid_filter = _normalize_npc_uid_filter(npc_uid)

        if incoming_filter is True:
            entries = self.get_dialog_callback_journal_received()
        elif incoming_filter is False:
            entries = self.get_dialog_callback_journal_sent()
        else:
            entries = self.get_dialog_callback_journal()

        out: List[DialogCallbackJournalEntry] = []
        for entry in entries:
            if npc_uid_filter and entry.npc_uid != npc_uid_filter:
                continue
            if message_id_filter is not None and entry.message_id != message_id_filter:
                continue
            if event_type_filter and entry.event_type.lower() != event_type_filter:
                continue
            out.append(entry)
        return out

    def clear_callback_journal(
        self,
        npc_uid: Optional[str] = None,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
    ) -> None:
        """
        Clear live callback journal entries using the best available native API.

        When filtered clear is unavailable natively, this method falls back to
        the older coarse clear behavior.
        """
        incoming_filter = _normalize_direction_filter(direction)
        message_id_filter, event_type_filter = _parse_message_type_filter(message_type)
        npc_uid_filter = _normalize_npc_uid_filter(npc_uid)

        # Fast path keeps backward-compatible clear behavior.
        if npc_uid_filter is None and message_id_filter is None and event_type_filter is None:
            if incoming_filter is True:
                self.clear_dialog_callback_journal_received()
                return
            if incoming_filter is False:
                self.clear_dialog_callback_journal_sent()
                return
            self.clear_dialog_callback_journal()
            return

        if PyDialog is None:
            return

        clearer = getattr(PyDialog.PyDialog, "clear_dialog_callback_journal_filtered", None)
        if callable(clearer):
            clearer(
                npc_uid_filter,
                incoming_filter,
                message_id_filter,
                event_type_filter,
            )
            return

        # Legacy fallback: if filtered clear is unavailable, keep behavior conservative.
        if incoming_filter is True:
            self.clear_dialog_callback_journal_received()
        elif incoming_filter is False:
            self.clear_dialog_callback_journal_sent()
        else:
            self.clear_dialog_callback_journal()

    def _get_step_pipeline(self):
        """Return the integrated SQLite history pipeline instance."""
        return _safe_call(None, get_dialog_step_pipeline)

    def _call_step_pipeline_method(
        self,
        method_name: str,
        *,
        default: Any,
        sync: bool = False,
        sync_include_raw: bool = True,
        sync_include_callback_journal: bool = True,
        **kwargs: Any,
    ) -> Any:
        pipeline = self._get_step_pipeline()
        if pipeline is None:
            return default
        if sync:
            self.sync_dialog_storage(
                include_raw=sync_include_raw,
                include_callback_journal=sync_include_callback_journal,
            )
        method = getattr(pipeline, method_name, None)
        if not callable(method):
            return default
        return _safe_call(default, lambda: method(**kwargs))

    def configure_dialog_storage(
        self,
        *,
        db_path: Optional[str] = None,
        step_timeout_ms: Optional[int] = None,
    ) -> str:
        """Configure the SQLite-backed dialog step pipeline and return its DB path."""
        return str(
            self._call_step_pipeline_method(
                "configure",
                default="",
                db_path=db_path,
                step_timeout_ms=step_timeout_ms,
            )
        )

    def get_dialog_storage_path(self) -> str:
        """Return the configured SQLite database path for persisted dialog history."""
        return str(self._call_step_pipeline_method("get_db_path", default=""))

    def sync_dialog_storage(
        self,
        *,
        include_raw: bool = True,
        include_callback_journal: bool = True,
    ) -> Dict[str, int]:
        """
        Snapshot the live native logs into the SQLite-backed persisted dialog store.

        The returned counters are useful for monitors and maintenance scripts that
        want to know how many rows were inserted/finalized during the sync.
        """
        pipeline = self._get_step_pipeline()
        if pipeline is None:
            return {"raw_inserted": 0, "journal_inserted": 0, "steps_finalized": 0}
        # Sync is snapshot-based: pull the current native in-memory logs, let the pipeline
        # deduplicate/finalize them, then query persisted state separately.
        raw_events = self.get_dialog_event_logs() if include_raw else None
        callback_journal = self.get_dialog_callback_journal() if include_callback_journal else None
        return _safe_call(
            {"raw_inserted": 0, "journal_inserted": 0, "steps_finalized": 0},
            lambda: pipeline.sync(raw_events=raw_events, callback_journal=callback_journal),
        )

    def flush_dialog_storage(self) -> int:
        """Force any pending in-memory dialog steps to be finalized into SQLite."""
        return int(self._call_step_pipeline_method("flush_pending", default=0) or 0)

    def get_persisted_raw_callbacks(
        self,
        *,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
        limit: int = 200,
        offset: int = 0,
        sync: bool = True,
    ) -> List[Dict[str, Any]]:
        """Query persisted raw callback rows from the SQLite dialog store."""
        return list(
            self._call_step_pipeline_method(
                "get_raw_callbacks",
                default=[],
                sync=sync,
                direction=direction,
                message_type=message_type,
                limit=limit,
                offset=offset,
            )
        )

    def clear_persisted_raw_callbacks(
        self,
        *,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
    ) -> int:
        return int(
            self._call_step_pipeline_method(
                "clear_raw_callbacks",
                default=0,
                direction=direction,
                message_type=message_type,
            )
            or 0
        )

    def get_persisted_callback_journal(
        self,
        *,
        npc_uid: Optional[str] = None,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
        limit: int = 200,
        offset: int = 0,
        sync: bool = True,
    ) -> List[Dict[str, Any]]:
        """Query persisted structured callback journal rows from SQLite."""
        return list(
            self._call_step_pipeline_method(
                "get_callback_journal",
                default=[],
                sync=sync,
                npc_uid=npc_uid,
                direction=direction,
                message_type=message_type,
                limit=limit,
                offset=offset,
            )
        )

    def clear_persisted_callback_journal(
        self,
        *,
        npc_uid: Optional[str] = None,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
    ) -> int:
        return int(
            self._call_step_pipeline_method(
                "clear_callback_journal",
                default=0,
                npc_uid=npc_uid,
                direction=direction,
                message_type=message_type,
            )
            or 0
        )

    def get_dialog_steps(
        self,
        *,
        map_id: Optional[int] = None,
        npc_uid_instance: Optional[str] = None,
        npc_uid_archetype: Optional[str] = None,
        body_dialog_id: Optional[int] = None,
        choice_dialog_id: Optional[int] = None,
        limit: int = 200,
        offset: int = 0,
        include_choices: bool = True,
        sync: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Query persisted dialog steps from SQLite with optional filtering.

        A dialog step is one body screen plus the offered choices and any choice
        selected before the next body, timeout, or map change.
        """
        # Most callers want fresh persisted history by default. Hot UI paths can pass sync=False
        # when they already called `sync_dialog_storage()` for the current frame/tick.
        return list(
            self._call_step_pipeline_method(
                "get_dialog_steps",
                default=[],
                sync=sync,
                map_id=map_id,
                npc_uid_instance=npc_uid_instance,
                npc_uid_archetype=npc_uid_archetype,
                body_dialog_id=body_dialog_id,
                choice_dialog_id=choice_dialog_id,
                limit=limit,
                offset=offset,
                include_choices=include_choices,
            )
        )

    def get_dialog_step(
        self, step_id: int, *, include_choices: bool = True, sync: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Return one persisted dialog step by id."""
        result = self._call_step_pipeline_method(
            "get_dialog_step",
            default=None,
            sync=sync,
            step_id=int(step_id),
            include_choices=include_choices,
        )
        return result if isinstance(result, dict) else None

    def get_dialog_steps_by_map(
        self,
        map_id: int,
        *,
        limit: int = 200,
        offset: int = 0,
        include_choices: bool = True,
        sync: bool = True,
    ) -> List[Dict[str, Any]]:
        return self.get_dialog_steps(
            map_id=int(map_id),
            limit=limit,
            offset=offset,
            include_choices=include_choices,
            sync=sync,
        )

    def get_dialog_steps_by_npc_archetype(
        self,
        npc_uid_archetype: str,
        *,
        limit: int = 200,
        offset: int = 0,
        include_choices: bool = True,
        sync: bool = True,
    ) -> List[Dict[str, Any]]:
        return self.get_dialog_steps(
            npc_uid_archetype=npc_uid_archetype,
            limit=limit,
            offset=offset,
            include_choices=include_choices,
            sync=sync,
        )

    def get_dialog_steps_by_body_dialog_id(
        self,
        body_dialog_id: int,
        *,
        limit: int = 200,
        offset: int = 0,
        include_choices: bool = True,
        sync: bool = True,
    ) -> List[Dict[str, Any]]:
        return self.get_dialog_steps(
            body_dialog_id=int(body_dialog_id),
            limit=limit,
            offset=offset,
            include_choices=include_choices,
            sync=sync,
        )

    def get_dialog_steps_by_choice_dialog_id(
        self,
        choice_dialog_id: int,
        *,
        limit: int = 200,
        offset: int = 0,
        include_choices: bool = True,
        sync: bool = True,
    ) -> List[Dict[str, Any]]:
        return self.get_dialog_steps(
            choice_dialog_id=int(choice_dialog_id),
            limit=limit,
            offset=offset,
            include_choices=include_choices,
            sync=sync,
        )

    def get_dialog_choices(self, step_id: int, *, sync: bool = True) -> List[Dict[str, Any]]:
        """Return the persisted choice rows that belong to a dialog step."""
        return list(
            self._call_step_pipeline_method(
                "get_dialog_choices",
                default=[],
                sync=sync,
                step_id=int(step_id),
            )
        )

    def export_raw_callbacks_json(
        self,
        path: str,
        *,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
        limit: int = 10000,
        offset: int = 0,
        sync: bool = True,
    ) -> int:
        return int(
            self._call_step_pipeline_method(
                "export_raw_callbacks_json",
                default=0,
                sync=sync,
                path=path,
                direction=direction,
                message_type=message_type,
                limit=limit,
                offset=offset,
            )
            or 0
        )

    def export_callback_journal_json(
        self,
        path: str,
        *,
        npc_uid: Optional[str] = None,
        direction: Optional[str] = "all",
        message_type: Optional[Any] = None,
        limit: int = 10000,
        offset: int = 0,
        sync: bool = True,
    ) -> int:
        return int(
            self._call_step_pipeline_method(
                "export_callback_journal_json",
                default=0,
                sync=sync,
                path=path,
                npc_uid=npc_uid,
                direction=direction,
                message_type=message_type,
                limit=limit,
                offset=offset,
            )
            or 0
        )

    def export_dialog_steps_json(
        self,
        path: str,
        *,
        map_id: Optional[int] = None,
        npc_uid_instance: Optional[str] = None,
        npc_uid_archetype: Optional[str] = None,
        body_dialog_id: Optional[int] = None,
        choice_dialog_id: Optional[int] = None,
        limit: int = 5000,
        offset: int = 0,
        sync: bool = True,
    ) -> int:
        """Export persisted dialog steps to JSON and return the exported row count."""
        return int(
            self._call_step_pipeline_method(
                "export_dialog_steps_json",
                default=0,
                sync=sync,
                path=path,
                map_id=map_id,
                npc_uid_instance=npc_uid_instance,
                npc_uid_archetype=npc_uid_archetype,
                body_dialog_id=body_dialog_id,
                choice_dialog_id=choice_dialog_id,
                limit=limit,
                offset=offset,
            )
            or 0
        )

    def prune_dialog_logs(
        self,
        *,
        max_raw_rows: Optional[int] = None,
        max_journal_rows: Optional[int] = None,
        max_step_rows: Optional[int] = None,
        older_than_days: Optional[float] = None,
    ) -> Dict[str, int]:
        """Prune persisted raw, journal, and step rows from the SQLite store."""
        return dict(
            self._call_step_pipeline_method(
                "prune_dialog_logs",
                default={
                    "removed_raw_callbacks": 0,
                    "removed_callback_journal": 0,
                    "removed_dialog_steps": 0,
                    "removed_dialog_choices": 0,
                },
                max_raw_rows=max_raw_rows,
                max_journal_rows=max_journal_rows,
                max_step_rows=max_step_rows,
                older_than_days=older_than_days,
            )
        )

    def get_dialog_diagnostics(
        self,
        *,
        map_id: Optional[int] = None,
        npc_uid_instance: Optional[str] = None,
        npc_uid_archetype: Optional[str] = None,
        body_dialog_id: Optional[int] = None,
        choice_dialog_id: Optional[int] = None,
        limit: int = 200,
        offset: int = 0,
        sync: bool = True,
        max_issues: int = 250,
    ) -> Dict[str, Any]:
        """Run lightweight diagnostics over persisted dialog history rows."""
        steps = self.get_dialog_steps(
            map_id=map_id,
            npc_uid_instance=npc_uid_instance,
            npc_uid_archetype=npc_uid_archetype,
            body_dialog_id=body_dialog_id,
            choice_dialog_id=choice_dialog_id,
            limit=limit,
            offset=offset,
            include_choices=True,
            sync=sync,
        )
        return _analyze_dialog_steps(steps, max_issues=max_issues)

_dialog_widget_instance: Optional[DialogWidget] = None


# Module-level convenience wrappers.
def get_dialog_widget() -> DialogWidget:
    global _dialog_widget_instance
    if _dialog_widget_instance is None:
        # Keep a single widget wrapper so module-level helpers share the same lazy-initialized
        # native/catalog/pipeline access path instead of each call re-building state.
        _dialog_widget_instance = DialogWidget()
    return _dialog_widget_instance


def get_active_dialog() -> Optional[ActiveDialogInfo]:
    return get_dialog_widget().get_active_dialog()


def get_active_dialog_buttons() -> List[DialogButtonInfo]:
    return get_dialog_widget().get_active_dialog_buttons()


def get_last_selected_dialog_id() -> int:
    return get_dialog_widget().get_last_selected_dialog_id()


def get_active_dialog_choice_id_by_text(text: Optional[str]) -> int:
    return get_dialog_widget().get_active_dialog_choice_id_by_text(text)


def send_active_dialog_choice_by_text(text: Optional[str]) -> bool:
    return get_dialog_widget().send_active_dialog_choice_by_text(text)


def get_active_dialog_choice_id_by_text_with_fallback(
    text: Optional[str],
    *,
    history_limit: int = 25,
) -> int:
    return get_dialog_widget().get_active_dialog_choice_id_by_text_with_fallback(
        text,
        history_limit=history_limit,
    )


def send_active_dialog_choice_by_text_with_fallback(
    text: Optional[str],
    *,
    history_limit: int = 25,
) -> bool:
    return get_dialog_widget().send_active_dialog_choice_by_text_with_fallback(
        text,
        history_limit=history_limit,
    )


def get_dialog_text_decoded(dialog_id: int) -> str:
    return get_dialog_widget().get_dialog_text_decoded(dialog_id)


def is_dialog_text_decode_pending(dialog_id: int) -> bool:
    return get_dialog_widget().is_dialog_text_decode_pending(dialog_id)


def is_dialog_active() -> bool:
    return get_dialog_widget().is_dialog_active()


def is_dialog_displayed(dialog_id: int) -> bool:
    return get_dialog_widget().is_dialog_displayed(dialog_id)


def get_dialog_text_decode_status() -> List[DialogTextDecodedInfo]:
    return get_dialog_widget().get_dialog_text_decode_status()


def is_dialog_available(dialog_id: int) -> bool:
    return get_dialog_widget().is_dialog_available(dialog_id)


def get_dialog_info(dialog_id: int) -> Optional[DialogInfo]:
    return get_dialog_widget().get_dialog_info(dialog_id)


def enumerate_available_dialogs() -> List[DialogInfo]:
    return get_dialog_widget().enumerate_available_dialogs()


def get_dialog_event_logs() -> List:
    return get_dialog_widget().get_dialog_event_logs()


def get_dialog_event_logs_received() -> List:
    return get_dialog_widget().get_dialog_event_logs_received()


def get_dialog_event_logs_sent() -> List:
    return get_dialog_widget().get_dialog_event_logs_sent()


def clear_dialog_event_logs() -> None:
    get_dialog_widget().clear_dialog_event_logs()


def clear_dialog_event_logs_received() -> None:
    get_dialog_widget().clear_dialog_event_logs_received()


def clear_dialog_event_logs_sent() -> None:
    get_dialog_widget().clear_dialog_event_logs_sent()


def get_dialog_callback_journal() -> List[DialogCallbackJournalEntry]:
    return get_dialog_widget().get_dialog_callback_journal()


def get_dialog_callback_journal_received() -> List[DialogCallbackJournalEntry]:
    return get_dialog_widget().get_dialog_callback_journal_received()


def get_dialog_callback_journal_sent() -> List[DialogCallbackJournalEntry]:
    return get_dialog_widget().get_dialog_callback_journal_sent()


def clear_dialog_callback_journal() -> None:
    get_dialog_widget().clear_dialog_callback_journal()


def clear_dialog_callback_journal_received() -> None:
    get_dialog_widget().clear_dialog_callback_journal_received()


def clear_dialog_callback_journal_sent() -> None:
    get_dialog_widget().clear_dialog_callback_journal_sent()


def get_callback_journal(
    npc_uid: Optional[str] = None,
    direction: Optional[str] = "all",
    message_type: Optional[Any] = None,
) -> List[DialogCallbackJournalEntry]:
    return get_dialog_widget().get_callback_journal(
        npc_uid=npc_uid,
        direction=direction,
        message_type=message_type,
    )


def clear_callback_journal(
    npc_uid: Optional[str] = None,
    direction: Optional[str] = "all",
    message_type: Optional[Any] = None,
) -> None:
    get_dialog_widget().clear_callback_journal(
        npc_uid=npc_uid,
        direction=direction,
        message_type=message_type,
    )


def configure_dialog_storage(
    *,
    db_path: Optional[str] = None,
    step_timeout_ms: Optional[int] = None,
) -> str:
    return get_dialog_widget().configure_dialog_storage(
        db_path=db_path,
        step_timeout_ms=step_timeout_ms,
    )


def get_dialog_storage_path() -> str:
    return get_dialog_widget().get_dialog_storage_path()


def sync_dialog_storage(
    *,
    include_raw: bool = True,
    include_callback_journal: bool = True,
) -> Dict[str, int]:
    return get_dialog_widget().sync_dialog_storage(
        include_raw=include_raw,
        include_callback_journal=include_callback_journal,
    )


def flush_dialog_storage() -> int:
    return get_dialog_widget().flush_dialog_storage()


def get_persisted_raw_callbacks(
    *,
    direction: Optional[str] = "all",
    message_type: Optional[Any] = None,
    limit: int = 200,
    offset: int = 0,
    sync: bool = True,
) -> List[Dict[str, Any]]:
    return get_dialog_widget().get_persisted_raw_callbacks(
        direction=direction,
        message_type=message_type,
        limit=limit,
        offset=offset,
        sync=sync,
    )


def clear_persisted_raw_callbacks(
    *,
    direction: Optional[str] = "all",
    message_type: Optional[Any] = None,
) -> int:
    return get_dialog_widget().clear_persisted_raw_callbacks(
        direction=direction,
        message_type=message_type,
    )


def get_persisted_callback_journal(
    *,
    npc_uid: Optional[str] = None,
    direction: Optional[str] = "all",
    message_type: Optional[Any] = None,
    limit: int = 200,
    offset: int = 0,
    sync: bool = True,
) -> List[Dict[str, Any]]:
    return get_dialog_widget().get_persisted_callback_journal(
        npc_uid=npc_uid,
        direction=direction,
        message_type=message_type,
        limit=limit,
        offset=offset,
        sync=sync,
    )


def clear_persisted_callback_journal(
    *,
    npc_uid: Optional[str] = None,
    direction: Optional[str] = "all",
    message_type: Optional[Any] = None,
) -> int:
    return get_dialog_widget().clear_persisted_callback_journal(
        npc_uid=npc_uid,
        direction=direction,
        message_type=message_type,
    )


def get_dialog_steps(
    *,
    map_id: Optional[int] = None,
    npc_uid_instance: Optional[str] = None,
    npc_uid_archetype: Optional[str] = None,
    body_dialog_id: Optional[int] = None,
    choice_dialog_id: Optional[int] = None,
    limit: int = 200,
    offset: int = 0,
    include_choices: bool = True,
    sync: bool = True,
) -> List[Dict[str, Any]]:
    return get_dialog_widget().get_dialog_steps(
        map_id=map_id,
        npc_uid_instance=npc_uid_instance,
        npc_uid_archetype=npc_uid_archetype,
        body_dialog_id=body_dialog_id,
        choice_dialog_id=choice_dialog_id,
        limit=limit,
        offset=offset,
        include_choices=include_choices,
        sync=sync,
    )


def get_dialog_step(step_id: int, *, include_choices: bool = True, sync: bool = True) -> Optional[Dict[str, Any]]:
    return get_dialog_widget().get_dialog_step(
        step_id=step_id,
        include_choices=include_choices,
        sync=sync,
    )


def get_dialog_steps_by_map(
    map_id: int,
    *,
    limit: int = 200,
    offset: int = 0,
    include_choices: bool = True,
    sync: bool = True,
) -> List[Dict[str, Any]]:
    return get_dialog_widget().get_dialog_steps_by_map(
        map_id=map_id,
        limit=limit,
        offset=offset,
        include_choices=include_choices,
        sync=sync,
    )


def get_dialog_steps_by_npc_archetype(
    npc_uid_archetype: str,
    *,
    limit: int = 200,
    offset: int = 0,
    include_choices: bool = True,
    sync: bool = True,
) -> List[Dict[str, Any]]:
    return get_dialog_widget().get_dialog_steps_by_npc_archetype(
        npc_uid_archetype=npc_uid_archetype,
        limit=limit,
        offset=offset,
        include_choices=include_choices,
        sync=sync,
    )


def get_dialog_steps_by_body_dialog_id(
    body_dialog_id: int,
    *,
    limit: int = 200,
    offset: int = 0,
    include_choices: bool = True,
    sync: bool = True,
) -> List[Dict[str, Any]]:
    return get_dialog_widget().get_dialog_steps_by_body_dialog_id(
        body_dialog_id=body_dialog_id,
        limit=limit,
        offset=offset,
        include_choices=include_choices,
        sync=sync,
    )


def get_dialog_steps_by_choice_dialog_id(
    choice_dialog_id: int,
    *,
    limit: int = 200,
    offset: int = 0,
    include_choices: bool = True,
    sync: bool = True,
) -> List[Dict[str, Any]]:
    return get_dialog_widget().get_dialog_steps_by_choice_dialog_id(
        choice_dialog_id=choice_dialog_id,
        limit=limit,
        offset=offset,
        include_choices=include_choices,
        sync=sync,
    )


def get_dialog_choices(step_id: int, *, sync: bool = True) -> List[Dict[str, Any]]:
    return get_dialog_widget().get_dialog_choices(step_id=step_id, sync=sync)


def export_raw_callbacks_json(
    path: str,
    *,
    direction: Optional[str] = "all",
    message_type: Optional[Any] = None,
    limit: int = 10000,
    offset: int = 0,
    sync: bool = True,
) -> int:
    return get_dialog_widget().export_raw_callbacks_json(
        path=path,
        direction=direction,
        message_type=message_type,
        limit=limit,
        offset=offset,
        sync=sync,
    )


def export_callback_journal_json(
    path: str,
    *,
    npc_uid: Optional[str] = None,
    direction: Optional[str] = "all",
    message_type: Optional[Any] = None,
    limit: int = 10000,
    offset: int = 0,
    sync: bool = True,
) -> int:
    return get_dialog_widget().export_callback_journal_json(
        path=path,
        npc_uid=npc_uid,
        direction=direction,
        message_type=message_type,
        limit=limit,
        offset=offset,
        sync=sync,
    )


def export_dialog_steps_json(
    path: str,
    *,
    map_id: Optional[int] = None,
    npc_uid_instance: Optional[str] = None,
    npc_uid_archetype: Optional[str] = None,
    body_dialog_id: Optional[int] = None,
    choice_dialog_id: Optional[int] = None,
    limit: int = 5000,
    offset: int = 0,
    sync: bool = True,
) -> int:
    return get_dialog_widget().export_dialog_steps_json(
        path=path,
        map_id=map_id,
        npc_uid_instance=npc_uid_instance,
        npc_uid_archetype=npc_uid_archetype,
        body_dialog_id=body_dialog_id,
        choice_dialog_id=choice_dialog_id,
        limit=limit,
        offset=offset,
        sync=sync,
    )


def prune_dialog_logs(
    *,
    max_raw_rows: Optional[int] = None,
    max_journal_rows: Optional[int] = None,
    max_step_rows: Optional[int] = None,
    older_than_days: Optional[float] = None,
) -> Dict[str, int]:
    return get_dialog_widget().prune_dialog_logs(
        max_raw_rows=max_raw_rows,
        max_journal_rows=max_journal_rows,
        max_step_rows=max_step_rows,
        older_than_days=older_than_days,
    )


def get_dialog_diagnostics(
    *,
    map_id: Optional[int] = None,
    npc_uid_instance: Optional[str] = None,
    npc_uid_archetype: Optional[str] = None,
    body_dialog_id: Optional[int] = None,
    choice_dialog_id: Optional[int] = None,
    limit: int = 200,
    offset: int = 0,
    sync: bool = True,
    max_issues: int = 250,
) -> Dict[str, Any]:
    return get_dialog_widget().get_dialog_diagnostics(
        map_id=map_id,
        npc_uid_instance=npc_uid_instance,
        npc_uid_archetype=npc_uid_archetype,
        body_dialog_id=body_dialog_id,
        choice_dialog_id=choice_dialog_id,
        limit=limit,
        offset=offset,
        sync=sync,
        max_issues=max_issues,
    )
