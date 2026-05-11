import json
import os
import re
import time
from typing import Any, Callable, Dict, List, Optional

import Py4GW
from Py4GWCoreLib import Routines, PyImGui, Map, Agent, Dialog, Player

MODULE_NAME = "Dialog Monitor"

__widget__ = {
    "enabled": False,
    "category": "Dialog",
    "subcategory": "Monitor",
}

_ROOT_DIRECTORY = Py4GW.Console.get_projects_path()
_CONFIG_DIR = os.path.join(_ROOT_DIRECTORY, "Widgets", "Config")
_EXPORT_DIR = os.path.join(_ROOT_DIRECTORY, "Widgets", "Data", "Dialog", "Exports")
_DUMP_PREFIX = "DialogMonitor_dump_"

_HISTORY_LIMIT = 140
_INLINE_CHOICE_RE = re.compile(r"<a\s*=\s*([^>]+)>(.*?)</a>", re.IGNORECASE | re.DOTALL)
_STORAGE_SYNC_INTERVAL_SECONDS = 0.5
_QUERY_CACHE_TTL_SECONDS = 0.35
_HEAVY_QUERY_CACHE_TTL_SECONDS = 0.75
_TAB_LIVE = "Live"
_TAB_RECENT = "Recent"
_TAB_LOGS = "Logs"
_TAB_DEBUG = "Debug"
_LOGS_TAB_RAW = "Raw"
_LOGS_TAB_JOURNAL = "Journal"
_LOGS_TAB_BAR_ID = "DialogMonitorLogsTabsV2"
_DEFAULT_WINDOW_SIZE = (960.0, 720.0)
_PLAYER_NAME_PLACEHOLDER = "<character name>"
_REDACTION_BLOCKED_PLACEHOLDER = "<redaction unavailable; text hidden>"
_REDACTION_BLOCKED_REASON = "player-name redaction unavailable; telemetry text copy/export is blocked"


class _PlayerNameRedactionUnavailable(RuntimeError):
    pass


class _TimedValueCache:
    def __init__(self) -> None:
        self._entries: Dict[str, Dict[str, Any]] = {}

    def invalidate(self, key: Optional[str] = None) -> None:
        if key is None:
            self._entries.clear()
            return
        self._entries.pop(key, None)

    def get_or_refresh(
        self,
        key: str,
        *,
        ttl_seconds: float,
        fetcher: Callable[[], Any],
        now: Optional[float] = None,
    ) -> Any:
        current_time = time.time() if now is None else float(now)
        entry = self._entries.get(key)
        if entry is not None and (current_time - float(entry["ts"])) < max(0.0, float(ttl_seconds)):
            return entry["value"]
        value = fetcher()
        self._entries[key] = {"ts": current_time, "value": value}
        return value


class DialogMonitorState:
    def __init__(self) -> None:
        self.current_active = None
        self.current_choices = []
        self.last_selected_dialog_id = 0
        self.last_selected_seen = 0.0
        self.selected_npc_uid: Optional[str] = None
        self.search_history = ""
        self.search_ledger = ""
        self.last_persist_time = 0.0
        self.current_npc_uid = ""
        self.raw_log_source_index = 0
        self.raw_log_search = ""
        self.raw_log_limit = 120
        self.search_callback_journal = ""
        self.callback_source_index = 0
        self.selected_step_id = 0
        self.selected_tab = _TAB_LIVE
        self.selected_logs_tab = _LOGS_TAB_JOURNAL
        self.last_storage_sync_result: Dict[str, int] = {
            "raw_inserted": 0,
            "journal_inserted": 0,
            "steps_finalized": 0,
        }
        self.last_prune_result: Dict[str, int] = {
            "removed_raw_callbacks": 0,
            "removed_callback_journal": 0,
            "removed_dialog_steps": 0,
            "removed_dialog_choices": 0,
        }
        self.prune_days = 7.0
        self.prune_max_raw_rows = 50000
        self.prune_max_journal_rows = 50000
        self.prune_max_step_rows = 20000
        self.diagnostics_max_issues = 120
        self.last_sync_error = ""
        self.last_file_action_error = ""
        self.query_cache = _TimedValueCache()

    def select_tab(self, tab_name: str) -> None:
        if tab_name in (_TAB_LIVE, _TAB_RECENT, _TAB_LOGS, _TAB_DEBUG):
            self.selected_tab = tab_name

    def select_logs_tab(self, tab_name: str) -> None:
        if tab_name in (_LOGS_TAB_RAW, _LOGS_TAB_JOURNAL):
            self.selected_logs_tab = tab_name

    def select_npc_uid(self, npc_uid: Optional[str]) -> None:
        if npc_uid == self.selected_npc_uid:
            return
        self.selected_npc_uid = npc_uid
        self.selected_step_id = 0
        self.query_cache.invalidate()

    def sync_core_storage(self, *, now: Optional[float] = None) -> None:
        # Storage sync is intentionally throttled to avoid per-frame sqlite churn.
        current_time = time.time() if now is None else float(now)
        if (current_time - self.last_persist_time) < _STORAGE_SYNC_INTERVAL_SECONDS:
            return
        try:
            self.last_storage_sync_result = Dialog.sync_dialog_storage(
                include_raw=True,
                include_callback_journal=True,
            )
            self.last_sync_error = ""
            if any(int(value or 0) > 0 for value in self.last_storage_sync_result.values()):
                self.query_cache.invalidate()
        except Exception as exc:
            self.last_storage_sync_result = {
                "raw_inserted": 0,
                "journal_inserted": 0,
                "steps_finalized": 0,
            }
            self.last_sync_error = str(exc)
        self.last_persist_time = current_time

    def reset_session(self) -> None:
        self.current_active = None
        self.current_choices = []
        self.last_selected_dialog_id = 0
        self.last_selected_seen = 0.0
        self.current_npc_uid = ""
        self.selected_step_id = 0
        self.last_sync_error = ""
        self.last_file_action_error = ""
        self.query_cache.invalidate()

    def update_from_game(self, dialog_widget) -> None:
        active = dialog_widget.get_active_dialog()
        choices = dialog_widget.get_active_dialog_buttons()
        last_selected = dialog_widget.get_last_selected_dialog_id()

        if active is not None and not choices:
            choices = _extract_inline_choices_from_active(active)

        self.current_choices = choices
        self.current_active = active

        if active is None:
            self.current_npc_uid = ""
            return

        map_id = Map.GetMapID()
        model_id = Agent.GetModelID(active.agent_id) or 0
        npc_uid = f"{map_id}:{model_id}:{active.agent_id}"
        self.current_npc_uid = npc_uid

        if self.selected_npc_uid is None:
            self.selected_npc_uid = npc_uid

        if last_selected and last_selected != self.last_selected_dialog_id:
            self.last_selected_dialog_id = last_selected
            self.last_selected_seen = time.time()


def _parse_inline_choice_dialog_id(raw_value: Any) -> int:
    value = str(raw_value or "").strip()
    if not value:
        return 0
    try:
        return int(value, 0)
    except Exception:
        return 0


def _sanitize_inline_choice_label(value: Any) -> str:
    sanitizer = getattr(Dialog, "sanitize_dialog_text", None)
    if callable(sanitizer):
        try:
            text = str(sanitizer(value) or "")
        except Exception:
            text = str(value or "")
    else:
        text = str(value or "")
    text = _obfuscate_player_name_text(text)
    return text if text else "<empty>"


def _get_current_player_name() -> str:
    getter = getattr(Player, "GetName", None)
    if not callable(getter):
        return ""
    try:
        return str(getter() or "").strip()
    except Exception:
        return ""


def _get_player_name_for_redaction(*, fail_closed: bool = False, text: Any = None) -> str:
    player_name = _get_current_player_name()
    if fail_closed and text is not None and str(text):
        if not player_name:
            raise _PlayerNameRedactionUnavailable(_REDACTION_BLOCKED_REASON)
    return player_name


def _obfuscate_player_name_text(value: Any) -> str:
    text = "" if value is None else str(value)
    if not text:
        return ""
    player_name = _get_player_name_for_redaction(text=text)
    if not player_name:
        return _REDACTION_BLOCKED_PLACEHOLDER
    return re.sub(re.escape(player_name), _PLAYER_NAME_PLACEHOLDER, text, flags=re.IGNORECASE)


def _obfuscate_player_name_text_for_export(value: Any) -> str:
    text = "" if value is None else str(value)
    if not text:
        return text
    player_name = _get_player_name_for_redaction(fail_closed=True, text=text)
    return re.sub(re.escape(player_name), _PLAYER_NAME_PLACEHOLDER, text, flags=re.IGNORECASE)


def _obfuscate_player_name_value(value: Any, *, fail_closed: bool = False) -> Any:
    if isinstance(value, str):
        if fail_closed:
            return _obfuscate_player_name_text_for_export(value)
        return _obfuscate_player_name_text(value)
    if isinstance(value, list):
        return [_obfuscate_player_name_value(item, fail_closed=fail_closed) for item in value]
    if isinstance(value, tuple):
        return tuple(_obfuscate_player_name_value(item, fail_closed=fail_closed) for item in value)
    if isinstance(value, dict):
        return {key: _obfuscate_player_name_value(item, fail_closed=fail_closed) for key, item in value.items()}
    return value


def _current_privacy_status_message() -> str:
    if _get_current_player_name():
        return ""
    return "privacy mode: player name unavailable, dialog text is hidden and telemetry text copy/export is blocked"


class _InlineDialogChoice:
    def __init__(self, dialog_id: int, label: str) -> None:
        self.dialog_id = int(dialog_id)
        self.button_icon = 0
        self.message = label
        self.message_decoded = label
        self.message_decode_pending = False


def _extract_inline_choices_from_active_local(active: Any) -> List[Any]:
    raw_message = getattr(active, "raw_message", None)
    if raw_message is None:
        raw_message = getattr(active, "message", "")
    text = str(raw_message or "")
    if not text or "<a=" not in text.lower():
        return []

    choices: List[Any] = []
    seen: set[tuple[int, str]] = set()
    for match in _INLINE_CHOICE_RE.finditer(text):
        dialog_id = _parse_inline_choice_dialog_id(match.group(1))
        if dialog_id == 0:
            continue
        label = _sanitize_inline_choice_label(match.group(2))
        dedupe_key = (dialog_id, label)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        choices.append(_InlineDialogChoice(dialog_id, label))
    return choices


def _extract_inline_choices_from_active(active: Any) -> List[Any]:
    helper = getattr(Dialog, "extract_inline_dialog_choices_from_active", None)
    if callable(helper):
        try:
            result = helper(active)
            if result is not None:
                return list(result)
        except Exception:
            pass
    return _extract_inline_choices_from_active_local(active)


_state = DialogMonitorState()
_dialog_module = None
_dialog_api = None
_initialized = False


class _DialogCompatAPI:
    def __init__(self, dialog_module: Any) -> None:
        self._module = dialog_module
        self._widget = None

        getter = getattr(dialog_module, "get_dialog_widget", None)
        if callable(getter):
            try:
                self._widget = getter()
            except Exception:
                self._widget = None

        self._initialize = self._resolve("initialize", "Initialize")
        self._is_dialog_active = self._resolve("is_dialog_active", "IsDialogActive")
        self._get_active_dialog = self._resolve("get_active_dialog", "GetActiveDialog")
        self._get_active_dialog_buttons = self._resolve("get_active_dialog_buttons", "GetActiveDialogButtons")
        self._get_last_selected_dialog_id = self._resolve("get_last_selected_dialog_id", "GetLastSelectedDialogId")
        self._get_dialog_text_decoded = self._resolve("get_dialog_text_decoded", "GetDialogTextDecoded")
        self._get_dialog_event_logs = self._resolve("get_dialog_event_logs", "GetDialogEventLogs")
        self._get_dialog_event_logs_received = self._resolve("get_dialog_event_logs_received", "GetDialogEventLogsReceived")
        self._get_dialog_event_logs_sent = self._resolve("get_dialog_event_logs_sent", "GetDialogEventLogsSent")
        self._clear_dialog_event_logs = self._resolve("clear_dialog_event_logs", "ClearDialogEventLogs")
        self._get_dialog_callback_journal = self._resolve(
            "get_dialog_callback_journal",
            "GetDialogCallbackJournal",
        )
        self._get_dialog_callback_journal_received = self._resolve(
            "get_dialog_callback_journal_received",
            "GetDialogCallbackJournalReceived",
        )
        self._get_dialog_callback_journal_sent = self._resolve(
            "get_dialog_callback_journal_sent",
            "GetDialogCallbackJournalSent",
        )
        self._clear_dialog_callback_journal = self._resolve(
            "clear_dialog_callback_journal",
            "ClearDialogCallbackJournal",
        )
        self._clear_dialog_callback_journal_received = self._resolve(
            "clear_dialog_callback_journal_received",
            "ClearDialogCallbackJournalReceived",
        )
        self._clear_dialog_callback_journal_sent = self._resolve(
            "clear_dialog_callback_journal_sent",
            "ClearDialogCallbackJournalSent",
        )
        self._clear_dialog_event_logs_received = self._resolve(
            "clear_dialog_event_logs_received",
            "ClearDialogEventLogsReceived",
        )
        self._clear_dialog_event_logs_sent = self._resolve(
            "clear_dialog_event_logs_sent",
            "ClearDialogEventLogsSent",
        )

    def _resolve(self, *names: str) -> Optional[Callable[..., Any]]:
        for target in (self._widget, self._module):
            if target is None:
                continue
            for name in names:
                candidate = getattr(target, name, None)
                if callable(candidate):
                    return candidate
        return None

    def initialize(self) -> bool:
        if not callable(self._initialize):
            return False
        try:
            result = self._initialize()
            # Native C++ initialize() is void; reaching this point means success.
            if isinstance(result, bool):
                return result
            return True
        except Exception:
            return False

    def get_active_dialog(self):
        if not callable(self._get_active_dialog):
            return None
        try:
            return self._get_active_dialog()
        except Exception:
            return None

    def is_dialog_active(self) -> bool:
        if callable(self._is_dialog_active):
            try:
                return bool(self._is_dialog_active())
            except Exception:
                return False
        return self.get_active_dialog() is not None

    def get_active_dialog_buttons(self) -> List[Any]:
        if not callable(self._get_active_dialog_buttons):
            return []
        try:
            result = self._get_active_dialog_buttons()
        except Exception:
            return []
        return list(result) if result is not None else []

    def get_last_selected_dialog_id(self) -> int:
        if not callable(self._get_last_selected_dialog_id):
            return 0
        try:
            return int(self._get_last_selected_dialog_id() or 0)
        except Exception:
            return 0

    def get_dialog_text_decoded(self, dialog_id: int) -> str:
        if not callable(self._get_dialog_text_decoded):
            return ""
        try:
            value = self._get_dialog_text_decoded(dialog_id)
        except Exception:
            return ""
        return str(value) if value is not None else ""

    def get_dialog_event_logs(self) -> List[Any]:
        if not callable(self._get_dialog_event_logs):
            return []
        try:
            result = self._get_dialog_event_logs()
        except Exception:
            return []
        return list(result) if result is not None else []

    def get_dialog_event_logs_received(self) -> List[Any]:
        if callable(self._get_dialog_event_logs_received):
            try:
                result = self._get_dialog_event_logs_received()
            except Exception:
                result = []
            return list(result) if result is not None else []
        return [evt for evt in self.get_dialog_event_logs() if _event_incoming(evt)]

    def get_dialog_event_logs_sent(self) -> List[Any]:
        if callable(self._get_dialog_event_logs_sent):
            try:
                result = self._get_dialog_event_logs_sent()
            except Exception:
                result = []
            return list(result) if result is not None else []
        return [evt for evt in self.get_dialog_event_logs() if not _event_incoming(evt)]

    def clear_dialog_event_logs(self) -> None:
        if callable(self._clear_dialog_event_logs):
            try:
                self._clear_dialog_event_logs()
            except Exception:
                pass

    def clear_dialog_event_logs_received(self) -> None:
        if callable(self._clear_dialog_event_logs_received):
            try:
                self._clear_dialog_event_logs_received()
            except Exception:
                pass
            return
        if callable(self._clear_dialog_event_logs):
            try:
                self._clear_dialog_event_logs()
            except Exception:
                pass

    def clear_dialog_event_logs_sent(self) -> None:
        if callable(self._clear_dialog_event_logs_sent):
            try:
                self._clear_dialog_event_logs_sent()
            except Exception:
                pass
            return
        if callable(self._clear_dialog_event_logs):
            try:
                self._clear_dialog_event_logs()
            except Exception:
                pass

    def get_dialog_callback_journal(self) -> List[Any]:
        if not callable(self._get_dialog_callback_journal):
            return []
        try:
            result = self._get_dialog_callback_journal()
        except Exception:
            return []
        return list(result) if result is not None else []

    def get_dialog_callback_journal_received(self) -> List[Any]:
        if callable(self._get_dialog_callback_journal_received):
            try:
                result = self._get_dialog_callback_journal_received()
            except Exception:
                result = []
            return list(result) if result is not None else []
        return [evt for evt in self.get_dialog_callback_journal() if bool(getattr(evt, "incoming", True))]

    def get_dialog_callback_journal_sent(self) -> List[Any]:
        if callable(self._get_dialog_callback_journal_sent):
            try:
                result = self._get_dialog_callback_journal_sent()
            except Exception:
                result = []
            return list(result) if result is not None else []
        return [evt for evt in self.get_dialog_callback_journal() if not bool(getattr(evt, "incoming", True))]

    def clear_dialog_callback_journal(self) -> None:
        if callable(self._clear_dialog_callback_journal):
            try:
                self._clear_dialog_callback_journal()
            except Exception:
                pass

    def clear_dialog_callback_journal_received(self) -> None:
        if callable(self._clear_dialog_callback_journal_received):
            try:
                self._clear_dialog_callback_journal_received()
            except Exception:
                pass
            return
        if callable(self._clear_dialog_callback_journal):
            try:
                self._clear_dialog_callback_journal()
            except Exception:
                pass

    def clear_dialog_callback_journal_sent(self) -> None:
        if callable(self._clear_dialog_callback_journal_sent):
            try:
                self._clear_dialog_callback_journal_sent()
            except Exception:
                pass
            return
        if callable(self._clear_dialog_callback_journal):
            try:
                self._clear_dialog_callback_journal()
            except Exception:
                pass


def _format_dialog_id(dialog_id: int) -> str:
    return f"0x{dialog_id:08x}"


def _event_field(event: Any, name: str, index: int, default: Any) -> Any:
    if isinstance(event, dict):
        return event.get(name, default)
    if hasattr(event, name):
        return getattr(event, name)
    if isinstance(event, (tuple, list)) and len(event) > index:
        return event[index]
    return default


def _event_incoming(event: Any) -> bool:
    return bool(_event_field(event, "incoming", 2, False))


def _dialog_certainty_snapshot(event: Any, *, event_type: Optional[str] = None) -> Dict[str, Any]:
    dialog_id = int(_event_field(event, "dialog_id", 3, 0) or 0)
    context_dialog_id = int(_event_field(event, "context_dialog_id", 4, 0) or 0)
    dialog_id_authoritative = bool(_event_field(event, "dialog_id_authoritative", -1, False))
    context_dialog_id_inferred = bool(_event_field(event, "context_dialog_id_inferred", -1, False))
    resolved_event_type = str(event_type or _event_field(event, "event_type", 9, "") or "").strip().lower()

    if not dialog_id_authoritative and dialog_id != 0 and resolved_event_type != "recv_body":
        dialog_id_authoritative = True
    if not context_dialog_id_inferred and resolved_event_type == "recv_body" and context_dialog_id != 0:
        context_dialog_id_inferred = True

    if dialog_id_authoritative and dialog_id != 0:
        short_label = "authoritative"
        detail = "Direct dialog ID from the callback payload."
    elif context_dialog_id_inferred and context_dialog_id != 0:
        short_label = "inferred-context"
        detail = "Body context inferred from the last sent dialog choice."
    elif dialog_id != 0:
        short_label = "dialog-id"
        detail = "Dialog ID present but no explicit certainty flag was persisted."
    elif context_dialog_id != 0:
        short_label = "context-only"
        detail = "Only a context dialog ID is available."
    else:
        short_label = "no-id"
        detail = "No dialog ID context is available."

    return {
        "dialog_id": dialog_id,
        "context_dialog_id": context_dialog_id,
        "dialog_id_authoritative": dialog_id_authoritative,
        "context_dialog_id_inferred": context_dialog_id_inferred,
        "event_type": resolved_event_type,
        "short_label": short_label,
        "detail": detail,
    }


def _active_dialog_display_id(active: Any) -> int:
    certainty = _dialog_certainty_snapshot(active)
    if certainty["dialog_id_authoritative"] and certainty["dialog_id"] != 0:
        return int(certainty["dialog_id"])
    return int(certainty["context_dialog_id"])


def _dialog_msg_name(message_id: int) -> str:
    names = {
        0x100000A6: "kDialogBody",
        0x100000A3: "kDialogButton",
        0x30000014: "kSendAgentDialog",
        0x30000015: "kSendGadgetDialog",
    }
    return names.get(message_id, "unknown")


def _raw_dialog_hint(event: Any, message_id: int) -> str:
    event_dialog_id = int(_event_field(event, "dialog_id", 13, 0) or 0)
    event_agent_id = int(_event_field(event, "agent_id", 10, 0) or 0)
    if message_id == 0x100000A3:
        return (
            f"choice={_format_dialog_id(event_dialog_id)}"
            if event_dialog_id
            else "choice=<unknown>"
        )
    if message_id == 0x100000A6:
        return f"agent={event_agent_id}" if event_agent_id else "agent=<unknown>"
    if message_id in (0x30000014, 0x30000015):
        return (
            f"selected={_format_dialog_id(event_dialog_id)}"
            if event_dialog_id
            else "selected=<unknown>"
        )
    return ""


def _format_raw_log_line(event: Any) -> str:
    tick = int(_event_field(event, "tick", 0, 0))
    message_id = int(_event_field(event, "message_id", 1, 0))
    incoming = 1 if _event_incoming(event) else 0
    hint = _raw_dialog_hint(event, message_id)
    line = (
        f"tick={tick} msg=0x{message_id:08X}({_dialog_msg_name(message_id)}) "
        f"in={incoming}"
    )
    if hint:
        line += f" {hint}"
    return line


def _format_map_with_id(map_id: Any, map_name: Any) -> str:
    resolved_map_id = int(map_id or 0)
    resolved_map_name = str(map_name or "").strip()
    if resolved_map_id > 0 and resolved_map_name:
        return f"{resolved_map_name} ({resolved_map_id})"
    if resolved_map_id > 0:
        return f"<unknown> ({resolved_map_id})"
    return resolved_map_name if resolved_map_name else "<unknown>"


def _describe_persisted_row_context(row: Dict[str, Any]) -> tuple[str, str]:
    map_id = int(row.get("map_id", 0) or 0)
    map_name = str(row.get("map_name", "") or "")
    npc_uid = str(row.get("npc_uid_instance", "") or row.get("npc_uid", "") or "")
    npc_name = str(row.get("npc_name", "") or "").strip() or "<pending>"
    agent_id = int(row.get("agent_id", 0) or 0)

    map_line = f"map={_format_map_with_id(map_id, map_name)}"
    npc_line = f"npc={npc_name}"
    if npc_uid:
        npc_line += f" [{npc_uid}]"
    if agent_id:
        npc_line += f" agent={agent_id}"
    return map_line, npc_line


def _join_non_empty_lines(*parts: Any) -> str:
    return "\n".join(str(part) for part in parts if str(part or ""))


def _logs_tab_item_label(tab_name: str) -> str:
    if tab_name == _LOGS_TAB_JOURNAL:
        return "Journal##DialogMonitorLogsJournalV2"
    if tab_name == _LOGS_TAB_RAW:
        return "Raw##DialogMonitorLogsRawV2"
    return str(tab_name)


def _choice_label(choice) -> str:
    if getattr(choice, "message_decoded", ""):
        return _obfuscate_player_name_text(choice.message_decoded)
    if getattr(choice, "message_decode_pending", False):
        return "<decoding label...>"
    if getattr(choice, "message", ""):
        return _obfuscate_player_name_text(choice.message)
    return "<no label>"


def _choice_certainty_label(choice) -> str:
    if isinstance(choice, _InlineDialogChoice):
        return "[inline]"
    return "[authoritative]"


def _load_dialog_widget():
    global _dialog_module, _dialog_api
    if _dialog_api is not None:
        return _dialog_api

    # Use native bindings so this widget always receives raw (unsanitized) text.
    try:
        import PyDialog as native_dialog_module  # type: ignore
        _dialog_module = native_dialog_module.PyDialog
        _dialog_api = _DialogCompatAPI(_dialog_module)
        return _dialog_api
    except Exception:
        return None


def _ensure_initialized() -> bool:
    global _dialog_api, _initialized
    if _dialog_api is None:
        _dialog_api = _load_dialog_widget()
        if _dialog_api is None:
            return False
    if not _initialized:
        _initialized = _dialog_api.initialize()
    return _initialized


def _copy_dialog_id_button(dialog_id: int, widget_id: str) -> None:
    if PyImGui.button(f"Copy##{widget_id}"):
        PyImGui.set_clipboard_text(_format_dialog_id(dialog_id))


def _copy_choice_label_button(choice: Any, widget_id: str) -> None:
    if PyImGui.button(f"Copy Text##{widget_id}"):
        _copy_text_to_clipboard(_choice_label(choice))


def _same_line(spacing: float = 6.0) -> None:
    PyImGui.same_line(0.0, spacing)


def _cached_query(key: str, ttl_seconds: float, fetcher: Callable[[], Any]) -> Any:
    return _state.query_cache.get_or_refresh(key, ttl_seconds=ttl_seconds, fetcher=fetcher)


def _get_history_steps() -> List[Dict[str, Any]]:
    npc_uid = _state.selected_npc_uid or ""
    cache_key = f"history_steps:{npc_uid}"
    return list(
        _cached_query(
            cache_key,
            _QUERY_CACHE_TTL_SECONDS,
            lambda: Dialog.get_dialog_steps(
                npc_uid_instance=_state.selected_npc_uid,
                limit=_HISTORY_LIMIT,
                offset=0,
                include_choices=True,
                sync=False,
            ),
        )
    )


def _get_step_catalog() -> List[Dict[str, Any]]:
    return list(
        _cached_query(
            "step_catalog",
            _HEAVY_QUERY_CACHE_TTL_SECONDS,
            lambda: Dialog.get_dialog_steps(limit=400, include_choices=False, sync=False),
        )
    )


def _get_selected_npc_steps() -> List[Dict[str, Any]]:
    npc_uid = _state.selected_npc_uid or ""
    cache_key = f"npc_steps:{npc_uid}"
    return list(
        _cached_query(
            cache_key,
            _QUERY_CACHE_TTL_SECONDS,
            lambda: Dialog.get_dialog_steps(
                npc_uid_instance=_state.selected_npc_uid,
                limit=250,
                include_choices=True,
                sync=False,
            ),
        )
    )


def _get_selected_step(step_id: int) -> Optional[Dict[str, Any]]:
    if step_id <= 0:
        return None
    cache_key = f"selected_step:{step_id}"
    return _cached_query(
        cache_key,
        _QUERY_CACHE_TTL_SECONDS,
        lambda: Dialog.get_dialog_step(step_id, include_choices=True, sync=False),
    )


def _get_raw_log_rows(direction: str) -> List[Dict[str, Any]]:
    cache_key = f"raw_logs:{direction}:{_state.raw_log_limit}"
    return list(
        _cached_query(
            cache_key,
            _QUERY_CACHE_TTL_SECONDS,
            lambda: Dialog.get_persisted_raw_callbacks(
                direction=direction,
                limit=max(_state.raw_log_limit * 5, 200),
                offset=0,
                sync=False,
            ),
        )
    )


def _get_callback_journal_rows(direction: str) -> List[Dict[str, Any]]:
    npc_uid = _state.selected_npc_uid or ""
    cache_key = f"callback_journal:{direction}:{npc_uid}:{_state.raw_log_limit}"
    def _fetch_rows() -> List[Dict[str, Any]]:
        limit = max(_state.raw_log_limit * 4, 200)
        rows = list(
            Dialog.get_persisted_callback_journal(
                direction=direction,
                npc_uid=_state.selected_npc_uid,
                limit=limit,
                offset=0,
                sync=False,
            )
        )
        if rows or not _state.selected_npc_uid:
            return rows
        return list(
            Dialog.get_persisted_callback_journal(
                direction=direction,
                npc_uid=None,
                limit=limit,
                offset=0,
                sync=False,
            )
        )

    return list(
        _cached_query(
            cache_key,
            _QUERY_CACHE_TTL_SECONDS,
            _fetch_rows,
        )
    )


def _get_diagnostics_payload() -> Dict[str, Any]:
    npc_uid = _state.selected_npc_uid or ""
    cache_key = f"diagnostics:{npc_uid}:{int(_state.diagnostics_max_issues)}"
    return dict(
        _cached_query(
            cache_key,
            _HEAVY_QUERY_CACHE_TTL_SECONDS,
            lambda: Dialog.get_dialog_diagnostics(
                npc_uid_instance=_state.selected_npc_uid if _state.selected_npc_uid else None,
                limit=300,
                sync=False,
                max_issues=max(10, int(_state.diagnostics_max_issues)),
            ),
        )
    )


def _current_live_dialog_ids() -> List[int]:
    dialog_ids: set[int] = set()
    active = _state.current_active
    if active is not None:
        certainty = _dialog_certainty_snapshot(active)
        if certainty["dialog_id"]:
            dialog_ids.add(int(certainty["dialog_id"]))
        if certainty["context_dialog_id"]:
            dialog_ids.add(int(certainty["context_dialog_id"]))
    if _state.last_selected_dialog_id:
        dialog_ids.add(int(_state.last_selected_dialog_id))
    for choice in _state.current_choices:
        choice_dialog_id = int(getattr(choice, "dialog_id", 0) or 0)
        if choice_dialog_id:
            dialog_ids.add(choice_dialog_id)
    return sorted(dialog_ids)


def _copy_current_ids_to_clipboard() -> None:
    dialog_ids = _current_live_dialog_ids()
    if dialog_ids:
        PyImGui.set_clipboard_text("\n".join(_format_dialog_id(dialog_id) for dialog_id in dialog_ids))


def _copy_all_ids_to_clipboard() -> None:
    query_kwargs = {
        "limit": 1200,
        "offset": 0,
        "include_choices": True,
        "sync": False,
    }
    if _state.selected_npc_uid:
        query_kwargs["npc_uid_instance"] = _state.selected_npc_uid
    steps = Dialog.get_dialog_steps(**query_kwargs)
    all_ids: set[int] = set()
    for step in steps:
        body_id = int(step.get("body_dialog_id", 0) or 0)
        selected_id = int(step.get("selected_dialog_id", 0) or 0)
        if body_id:
            all_ids.add(body_id)
        if selected_id:
            all_ids.add(selected_id)
        for choice in step.get("choices", []):
            choice_id = int(choice.get("choice_dialog_id", 0) or 0)
            if choice_id:
                all_ids.add(choice_id)
    if all_ids:
        PyImGui.set_clipboard_text("\n".join(_format_dialog_id(dialog_id) for dialog_id in sorted(all_ids)))


def _copy_text_to_clipboard(text: Any) -> None:
    try:
        PyImGui.set_clipboard_text(_obfuscate_player_name_text_for_export(text))
        _state.last_file_action_error = ""
    except _PlayerNameRedactionUnavailable as exc:
        _state.last_file_action_error = str(exc)


def _copy_json_to_clipboard(payload: Any) -> None:
    try:
        PyImGui.set_clipboard_text(json.dumps(_obfuscate_player_name_value(payload, fail_closed=True), ensure_ascii=False))
        _state.last_file_action_error = ""
    except _PlayerNameRedactionUnavailable as exc:
        _state.last_file_action_error = str(exc)


def _write_obfuscated_json(path: str, payload: Any) -> None:
    sanitized_payload = _obfuscate_player_name_value(payload, fail_closed=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(sanitized_payload, handle, indent=2, ensure_ascii=False)


def _dump_monitor_snapshot() -> None:
    try:
        if not os.path.exists(_CONFIG_DIR):
            os.makedirs(_CONFIG_DIR, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        dump_path = os.path.join(_CONFIG_DIR, f"{_DUMP_PREFIX}{timestamp}.json")
        query_kwargs = {
            "limit": 2000,
            "offset": 0,
            "include_choices": True,
            "sync": False,
        }
        journal_kwargs = {
            "limit": 2000,
            "offset": 0,
            "direction": "all",
            "sync": False,
        }
        if _state.selected_npc_uid:
            query_kwargs["npc_uid_instance"] = _state.selected_npc_uid
            journal_kwargs["npc_uid"] = _state.selected_npc_uid
        payload = {
            "generated_at": time.time(),
            "selected_npc_uid": _state.selected_npc_uid,
            "steps": Dialog.get_dialog_steps(**query_kwargs),
            "callback_journal": Dialog.get_persisted_callback_journal(**journal_kwargs),
        }
        _write_obfuscated_json(dump_path, payload)
        _state.last_file_action_error = ""
    except Exception as exc:
        _state.last_file_action_error = str(exc)


def _export_raw_callbacks() -> None:
    try:
        os.makedirs(_EXPORT_DIR, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(_EXPORT_DIR, f"dialog_raw_{timestamp}.json")
        entries = Dialog.get_persisted_raw_callbacks(
            direction="all",
            limit=20000,
            offset=0,
            sync=True,
        )
        payload = {
            "generated_at": time.time(),
            "count": len(entries),
            "filters": {
                "direction": "all",
                "message_type": None,
                "limit": 20000,
                "offset": 0,
            },
            "entries": entries,
        }
        _write_obfuscated_json(path, payload)
        _state.last_file_action_error = ""
    except Exception as exc:
        _state.last_file_action_error = str(exc)


def _export_callback_journal() -> None:
    try:
        os.makedirs(_EXPORT_DIR, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(_EXPORT_DIR, f"dialog_journal_{timestamp}.json")
        entries = Dialog.get_persisted_callback_journal(
            npc_uid=_state.selected_npc_uid,
            direction="all",
            limit=20000,
            offset=0,
            sync=True,
        )
        payload = {
            "generated_at": time.time(),
            "count": len(entries),
            "filters": {
                "npc_uid": _state.selected_npc_uid,
                "direction": "all",
                "message_type": None,
                "limit": 20000,
                "offset": 0,
            },
            "entries": entries,
        }
        _write_obfuscated_json(path, payload)
        _state.last_file_action_error = ""
    except Exception as exc:
        _state.last_file_action_error = str(exc)


def _export_dialog_steps() -> None:
    try:
        os.makedirs(_EXPORT_DIR, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(_EXPORT_DIR, f"dialog_steps_{timestamp}.json")
        steps = Dialog.get_dialog_steps(
            npc_uid_instance=_state.selected_npc_uid,
            limit=12000,
            offset=0,
            include_choices=True,
            sync=True,
        )
        payload = {
            "generated_at": time.time(),
            "count": len(steps),
            "filters": {
                "map_id": None,
                "npc_uid_instance": _state.selected_npc_uid,
                "npc_uid_archetype": None,
                "body_dialog_id": None,
                "choice_dialog_id": None,
                "limit": 12000,
                "offset": 0,
            },
            "steps": steps,
        }
        _write_obfuscated_json(path, payload)
        _state.last_file_action_error = ""
    except Exception as exc:
        _state.last_file_action_error = str(exc)


def _draw_status_messages() -> None:
    sync_result = _state.last_storage_sync_result
    PyImGui.text(
        f"sync raw={int(sync_result.get('raw_inserted', 0))} "
        f"journal={int(sync_result.get('journal_inserted', 0))} "
        f"steps={int(sync_result.get('steps_finalized', 0))}"
    )
    privacy_status = _current_privacy_status_message()
    if privacy_status:
        PyImGui.text_wrapped(privacy_status)
    if _state.last_sync_error:
        PyImGui.text_wrapped(_obfuscate_player_name_text(f"sync error: {_state.last_sync_error}"))
    if _state.last_file_action_error:
        PyImGui.text_wrapped(_obfuscate_player_name_text(f"file action error: {_state.last_file_action_error}"))


def _supports_imgui_tabs() -> bool:
    return all(
        callable(getattr(PyImGui, name, None))
        for name in ("begin_tab_bar", "end_tab_bar", "begin_tab_item", "end_tab_item")
    )


def _draw_header_controls() -> None:
    PyImGui.text(MODULE_NAME)
    _same_line(12.0)
    active_tab_label = f"tab={_state.selected_tab}"
    if _state.selected_tab == _TAB_LOGS:
        active_tab_label += f" / {_state.selected_logs_tab}"
    PyImGui.text(active_tab_label)


def _draw_current_state_panel(active, last_selected_id: int, dialog_active: bool) -> None:
    PyImGui.text("Current State")
    PyImGui.separator()
    PyImGui.text(f"Dialog active: {dialog_active}")

    if active is None:
        PyImGui.text("No active dialog detected.")
        return

    certainty = _dialog_certainty_snapshot(active)
    PyImGui.text(f"Dialog certainty: {certainty['short_label']}")
    if certainty["dialog_id_authoritative"] and certainty["dialog_id"]:
        PyImGui.text(f"Active dialog ID: {_format_dialog_id(certainty['dialog_id'])} [authoritative]")
        _same_line()
        _copy_dialog_id_button(certainty["dialog_id"], "active_dialog")
    if certainty["context_dialog_id"]:
        context_label = "Context dialog ID"
        if certainty["context_dialog_id_inferred"]:
            context_label += " [inferred]"
        PyImGui.text(f"{context_label}: {_format_dialog_id(certainty['context_dialog_id'])}")
        _same_line()
        _copy_dialog_id_button(certainty["context_dialog_id"], "active_dialog_context")
    PyImGui.text_wrapped(certainty["detail"])

    PyImGui.text(f"Agent ID: {active.agent_id}")
    npc_name = Agent.GetNameByID(active.agent_id) if int(active.agent_id or 0) else ""
    PyImGui.text(f"NPC name: {npc_name if npc_name else '<pending>'}")
    map_id = Map.GetMapID()
    model_id = Agent.GetModelID(active.agent_id) or 0
    PyImGui.text(f"Map ID: {map_id}")
    PyImGui.text(f"Model ID: {model_id}")

    if last_selected_id:
        PyImGui.text(f"Last selected choice: {_format_dialog_id(last_selected_id)} [authoritative]")
        _same_line()
        _copy_dialog_id_button(last_selected_id, "last_selected")

    PyImGui.separator()
    PyImGui.text("Current message:")
    active_message = _obfuscate_player_name_text(active.message if active.message else "<empty>")
    PyImGui.text_wrapped(active_message)
    if PyImGui.button("Copy Message"):
        _copy_text_to_clipboard(active.message if active.message else "")


def _draw_history_panel() -> None:
    PyImGui.text("Recent History")
    PyImGui.separator()

    search = PyImGui.input_text("Search##history", _state.search_history, 64)
    if search != _state.search_history:
        _state.search_history = search
    needle = _state.search_history.lower().strip()

    steps = _get_history_steps()

    if PyImGui.begin_child("HistoryPanel", (0, 180), True, PyImGui.WindowFlags.NoFlag):
        now = time.time()
        shown = 0
        for step in steps:
            step_id = int(step.get("id", 0) or 0)
            body_id = int(step.get("body_dialog_id", 0) or 0)
            selected_id = int(step.get("selected_dialog_id", 0) or 0)
            body_text = str(step.get("body_text_raw", "") or "")
            display_body_text = _obfuscate_player_name_text(body_text)
            reason = str(step.get("finalized_reason", "") or "")
            created_at = float(step.get("created_at", 0.0) or 0.0)
            delta = (now - created_at) if created_at > 0 else 0.0
            map_line, npc_line = _describe_persisted_row_context(step)
            line = (
                f"[{delta:4.1f}s ago] step#{step_id} "
                f"body={_format_dialog_id(body_id)} selected={_format_dialog_id(selected_id)} "
                f"reason={reason}"
            )
            if needle and needle not in f"{line} {map_line} {npc_line} {display_body_text}".lower():
                continue
            PyImGui.text_wrapped(line)
            PyImGui.text_wrapped(map_line)
            PyImGui.text_wrapped(npc_line)
            if display_body_text:
                PyImGui.text_wrapped(display_body_text)
            shown += 1
            if shown >= _HISTORY_LIMIT:
                break
        if shown == 0:
            PyImGui.text("<no step history>")
    PyImGui.end_child()


def _draw_choice_panel(active, choices) -> None:
    PyImGui.text("Choices")
    PyImGui.separator()
    if not choices:
        PyImGui.text("<no choices detected>")
        return

    if PyImGui.begin_child("ChoicePanel", (0, 220), True, PyImGui.WindowFlags.NoFlag):
        for index, choice in enumerate(choices):
            label = _choice_label(choice)
            PyImGui.text(f"[{_format_dialog_id(choice.dialog_id)}] {_choice_certainty_label(choice)} {label}")
            _same_line()
            _copy_dialog_id_button(choice.dialog_id, f"choice_{choice.dialog_id}_{index}")
            _same_line()
            _copy_choice_label_button(choice, f"choice_text_{choice.dialog_id}_{index}")
    PyImGui.end_child()


def _draw_raw_logs_panel() -> None:
    PyImGui.text("Raw Callback Logs")
    PyImGui.separator()
    sources = ["All", "Received", "Sent"]
    _state.raw_log_source_index = PyImGui.combo("Source##rawlogs", _state.raw_log_source_index, sources)
    source_index = _state.raw_log_source_index
    direction = "all" if source_index == 0 else "received" if source_index == 1 else "sent"

    if _dialog_api is not None:
        _same_line(10.0)
        if PyImGui.button("Clear All"):
            _dialog_api.clear_dialog_event_logs()
            Dialog.clear_persisted_raw_callbacks(direction="all")
            _state.query_cache.invalidate()
        _same_line(6.0)
        if PyImGui.button("Clear Recv"):
            _dialog_api.clear_dialog_event_logs_received()
            Dialog.clear_persisted_raw_callbacks(direction="received")
            _state.query_cache.invalidate()
        _same_line(6.0)
        if PyImGui.button("Clear Sent"):
            _dialog_api.clear_dialog_event_logs_sent()
            Dialog.clear_persisted_raw_callbacks(direction="sent")
            _state.query_cache.invalidate()

    search = PyImGui.input_text("Search##rawlogs", _state.raw_log_search, 96)
    if search != _state.raw_log_search:
        _state.raw_log_search = search
    needle = _state.raw_log_search.lower().strip()

    log_rows = _get_raw_log_rows(direction)
    sync_result = _state.last_storage_sync_result
    PyImGui.text(
        f"stored rows={len(log_rows)} (last sync raw={int(sync_result.get('raw_inserted', 0))}, "
        f"journal={int(sync_result.get('journal_inserted', 0))}, "
        f"finalized={int(sync_result.get('steps_finalized', 0))})"
    )

    if PyImGui.begin_child("RawLogsPanel", (0, 340), True, PyImGui.WindowFlags.NoFlag):
        shown = 0
        for event in log_rows:
            line = _format_raw_log_line(event)
            map_line, npc_line = _describe_persisted_row_context(event)
            event_text = str(event.get("text_raw", "") or "") if isinstance(event, dict) else ""
            display_event_text = _obfuscate_player_name_text(event_text)
            if needle and needle not in f"{line} {map_line} {npc_line} {display_event_text}".lower():
                continue
            PyImGui.text_wrapped(line)
            PyImGui.text_wrapped(map_line)
            PyImGui.text_wrapped(npc_line)
            if display_event_text:
                PyImGui.text_wrapped(f"text={display_event_text}")
            _same_line()
            if PyImGui.small_button(f"Copy##raw_{_event_field(event, 'id', 7, shown)}"):
                _copy_text_to_clipboard(
                    _join_non_empty_lines(
                        line,
                        map_line,
                        npc_line,
                        f"text={display_event_text}" if display_event_text else "",
                    )
                )
            _same_line()
            if PyImGui.small_button(f"CopyJSON##raw_{_event_field(event, 'id', 7, shown)}"):
                if isinstance(event, dict):
                    _copy_json_to_clipboard(event)
                else:
                    _copy_text_to_clipboard(line)
            shown += 1
            if shown >= _state.raw_log_limit:
                break
        if shown == 0:
            PyImGui.text("<no raw logs>")
    PyImGui.end_child()


def _draw_callback_journal_panel() -> None:
    PyImGui.text("Callback Journal (Structured)")
    PyImGui.separator()
    sources = ["All", "Received", "Sent"]
    _state.callback_source_index = PyImGui.combo("Source##callback_journal", _state.callback_source_index, sources)
    source_index = _state.callback_source_index
    direction = "all" if source_index == 0 else "received" if source_index == 1 else "sent"

    _same_line(8.0)
    if PyImGui.button("Clear Journal (All NPCs)"):
        if _dialog_api is not None:
            if direction == "received":
                _dialog_api.clear_dialog_callback_journal_received()
            elif direction == "sent":
                _dialog_api.clear_dialog_callback_journal_sent()
            else:
                _dialog_api.clear_dialog_callback_journal()
        Dialog.clear_persisted_callback_journal(direction=direction)
        _state.query_cache.invalidate()

    search = PyImGui.input_text("Search##callback_journal", _state.search_callback_journal, 96)
    if search != _state.search_callback_journal:
        _state.search_callback_journal = search
    needle = _state.search_callback_journal.lower().strip()
    events = _get_callback_journal_rows(direction)
    PyImGui.text(f"stored events={len(events)}")

    if PyImGui.begin_child("CallbackJournalPanel", (0, 180), True, PyImGui.WindowFlags.NoFlag):
        now = time.time()
        shown = 0
        for event in events:
            event_id = int(event.get("id", 0) or 0)
            timestamp = float(event.get("ts", 0.0) or 0.0)
            message_id = int(event.get("message_id", 0) or 0)
            dialog_id = int(event.get("dialog_id", 0) or 0)
            context_dialog_id = int(event.get("context_dialog_id", 0) or 0)
            agent_id = int(event.get("agent_id", 0) or 0)
            event_type = str(event.get("event_type", "") or "")
            npc_uid = str(event.get("npc_uid", "") or "")
            event_text = str(event.get("text_raw", "") or "")
            display_event_text = _obfuscate_player_name_text(event_text)
            certainty = _dialog_certainty_snapshot(event, event_type=event_type)
            delta = (now - timestamp) if timestamp > 0 else 0.0
            map_line, npc_line = _describe_persisted_row_context(event)
            line = (
                f"[{delta:4.1f}s] {event_type} "
                f"msg=0x{message_id:08X} id={_format_dialog_id(dialog_id)} "
                f"ctx={_format_dialog_id(context_dialog_id)} "
                f"[{certainty['short_label']}] agent={agent_id}"
            )
            if needle:
                haystack = f"{line} {npc_uid} {map_line} {npc_line} {display_event_text}".lower()
                if needle not in haystack:
                    continue
            PyImGui.text_wrapped(line)
            PyImGui.text_wrapped(certainty["detail"])
            PyImGui.text_wrapped(map_line)
            PyImGui.text_wrapped(npc_line)
            if display_event_text:
                PyImGui.text_wrapped(f"text={display_event_text}")
            _same_line()
            if PyImGui.small_button(f"CopyLine##cb_{event_id}_{shown}"):
                _copy_text_to_clipboard(
                    _join_non_empty_lines(
                        line,
                        certainty["detail"],
                        map_line,
                        npc_line,
                        f"text={display_event_text}" if display_event_text else "",
                    )
                )
            _same_line()
            if PyImGui.small_button(f"CopyJSON##cb_{event_id}_{shown}"):
                _copy_json_to_clipboard(event)
            shown += 1
            if shown >= 120:
                break
        if shown == 0:
            PyImGui.text("<no callback journal events>")
    PyImGui.end_child()


def _draw_ledger_panel() -> None:
    PyImGui.text("Dialog Steps")
    PyImGui.separator()

    all_steps = _get_step_catalog()
    npc_stats: Dict[str, Dict[str, Any]] = {}
    for step in all_steps:
        uid = str(step.get("npc_uid_instance", "") or "")
        if not uid:
            continue
        stat = npc_stats.setdefault(
            uid,
            {
                "count": 0,
                "last_seen": 0.0,
                "map_id": int(step.get("map_id", 0) or 0),
                "map_name": str(step.get("map_name", "") or ""),
                "model_id": int(step.get("model_id", 0) or 0),
                "agent_id": int(step.get("agent_id", 0) or 0),
                "npc_name": str(step.get("npc_name", "") or ""),
            },
        )
        stat["count"] += 1
        stat["last_seen"] = max(float(step.get("created_at", 0.0) or 0.0), stat["last_seen"])
        if not stat["map_name"] and step.get("map_name"):
            stat["map_name"] = str(step.get("map_name", "") or "")
        if not stat["npc_name"] and step.get("npc_name"):
            stat["npc_name"] = str(step.get("npc_name", "") or "")

    npc_uids = sorted(npc_stats.keys(), key=lambda uid: npc_stats[uid]["last_seen"], reverse=True)
    if not npc_uids:
        PyImGui.text("No persisted dialog steps yet.")
        return

    selected_index = 0
    if _state.selected_npc_uid in npc_uids:
        selected_index = npc_uids.index(_state.selected_npc_uid)
    labels = []
    for uid in npc_uids:
        stat = npc_stats[uid]
        npc_display = stat["npc_name"] if stat["npc_name"] else uid
        map_display = _format_map_with_id(stat["map_id"], stat["map_name"])
        labels.append(
            f"{npc_display} [{uid}] ({stat['count']} steps, {map_display}, model {stat['model_id']}, agent {stat['agent_id']})"
        )
    new_index = PyImGui.combo("NPC##steps", selected_index, labels)
    _state.select_npc_uid(npc_uids[new_index])

    search = PyImGui.input_text("Search##steps", _state.search_ledger, 96)
    if search != _state.search_ledger:
        _state.search_ledger = search
    needle = _state.search_ledger.lower().strip()

    steps = _get_selected_npc_steps()

    if PyImGui.begin_child("StepsPanel", (0, 230), True, PyImGui.WindowFlags.NoFlag):
        now = time.time()
        for step in steps:
            step_id = int(step.get("id", 0) or 0)
            body_id = int(step.get("body_dialog_id", 0) or 0)
            selected_id = int(step.get("selected_dialog_id", 0) or 0)
            reason = str(step.get("finalized_reason", "") or "")
            body_text = str(step.get("body_text_raw", "") or "")
            display_body_text = _obfuscate_player_name_text(body_text)
            choices = step.get("choices", [])
            map_line, npc_line = _describe_persisted_row_context(step)
            line = (
                f"step#{step_id} body={_format_dialog_id(body_id)} "
                f"selected={_format_dialog_id(selected_id)} choices={len(choices)} reason={reason}"
            )
            if needle:
                haystack = f"{line} {map_line} {npc_line} {display_body_text}".lower()
                if needle not in haystack:
                    continue
            PyImGui.text_wrapped(line)
            PyImGui.text_wrapped(map_line)
            PyImGui.text_wrapped(npc_line)
            created_at = float(step.get("created_at", 0.0) or 0.0)
            if created_at > 0:
                PyImGui.text(f"age={now - created_at:4.1f}s")
            _same_line()
            if PyImGui.small_button(f"CopyStepJSON##{step_id}"):
                _copy_json_to_clipboard(step)
            _same_line()
            if PyImGui.small_button(f"SelectStep##{step_id}"):
                _state.selected_step_id = step_id
            if display_body_text:
                PyImGui.text_wrapped(f"body={display_body_text}")
        if not steps:
            PyImGui.text("<no steps for selected npc>")
    PyImGui.end_child()

    if _state.selected_step_id:
        selected_step = _get_selected_step(_state.selected_step_id)
        if selected_step:
            PyImGui.separator()
            PyImGui.text(f"Selected Step: {_state.selected_step_id}")
            map_line, npc_line = _describe_persisted_row_context(selected_step)
            PyImGui.text_wrapped(map_line)
            PyImGui.text_wrapped(npc_line)
            body_text = _obfuscate_player_name_text(selected_step.get("body_text_raw", "") or "")
            if body_text:
                PyImGui.text_wrapped(body_text)
            choice_rows = selected_step.get("choices", [])
            if choice_rows:
                PyImGui.text("Choices")
                for choice in choice_rows:
                    choice_id = int(choice.get("choice_dialog_id", 0) or 0)
                    choice_text = _obfuscate_player_name_text(choice.get("choice_text_raw", "") or "")
                    selected = bool(choice.get("selected", False))
                    selected_marker = " [selected]" if selected else ""
                    PyImGui.text_wrapped(
                        f"- {_format_dialog_id(choice_id)}{selected_marker} {choice_text if choice_text else '<empty>'}"
                    )


def _draw_diagnostics_panel(active, choices) -> None:
    PyImGui.text("Diagnostics")
    PyImGui.separator()

    _state.prune_days = max(0.0, float(PyImGui.input_float("Prune Age (days)", _state.prune_days)))
    _state.prune_max_raw_rows = max(100, int(PyImGui.input_int("Max Raw Rows", _state.prune_max_raw_rows)))
    _state.prune_max_journal_rows = max(100, int(PyImGui.input_int("Max Journal Rows", _state.prune_max_journal_rows)))
    _state.prune_max_step_rows = max(100, int(PyImGui.input_int("Max Step Rows", _state.prune_max_step_rows)))
    if PyImGui.button("Apply Age Prune"):
        _state.last_prune_result = Dialog.prune_dialog_logs(older_than_days=_state.prune_days)
        _state.query_cache.invalidate()
    _same_line(6.0)
    if PyImGui.button("Apply Cap Prune"):
        _state.last_prune_result = Dialog.prune_dialog_logs(
            max_raw_rows=_state.prune_max_raw_rows,
            max_journal_rows=_state.prune_max_journal_rows,
            max_step_rows=_state.prune_max_step_rows,
        )
        _state.query_cache.invalidate()
    PyImGui.separator()

    prune_result = _state.last_prune_result
    if any(int(value) > 0 for value in prune_result.values()):
        PyImGui.text(
            "Last prune removed: "
            f"raw={int(prune_result.get('removed_raw_callbacks', 0))}, "
            f"journal={int(prune_result.get('removed_callback_journal', 0))}, "
            f"steps={int(prune_result.get('removed_dialog_steps', 0))}, "
            f"choices={int(prune_result.get('removed_dialog_choices', 0))}"
        )
        PyImGui.separator()

    diagnostics: List[Dict[str, Any]] = []
    if active is None:
        diagnostics.append(
            {
                "severity": "info",
                "rule": "live_no_active_dialog",
                "message": "No active dialog.",
                "step_id": 0,
                "dialog_id": 0,
                "npc_uid": "",
            }
        )
    else:
        active_issue_id = _active_dialog_display_id(active)
        if not active.message:
            diagnostics.append(
                {
                    "severity": "warning",
                    "rule": "live_empty_active_message",
                    "message": "Active dialog has empty body text.",
                    "step_id": 0,
                    "dialog_id": active_issue_id,
                    "npc_uid": _state.current_npc_uid,
                }
            )
        if not choices:
            diagnostics.append(
                {
                    "severity": "info",
                    "rule": "live_no_active_choices",
                    "message": "Active dialog has no outgoing choices.",
                    "step_id": 0,
                    "dialog_id": active_issue_id,
                    "npc_uid": _state.current_npc_uid,
                }
            )
        else:
            if any(choice.message_decode_pending for choice in choices):
                diagnostics.append(
                    {
                        "severity": "info",
                        "rule": "live_choice_decode_pending",
                        "message": "One or more choice labels are still decoding.",
                        "step_id": 0,
                        "dialog_id": active_issue_id,
                        "npc_uid": _state.current_npc_uid,
                    }
                )
            if any(_choice_label(choice).startswith("<no") for choice in choices):
                diagnostics.append(
                    {
                        "severity": "warning",
                        "rule": "live_missing_choice_labels",
                        "message": "Some choices are missing labels.",
                        "step_id": 0,
                        "dialog_id": active_issue_id,
                        "npc_uid": _state.current_npc_uid,
                    }
                )

    payload = _get_diagnostics_payload()
    persisted_issues = list(payload.get("issues", []))
    diagnostics.extend(persisted_issues)

    if not diagnostics:
        PyImGui.text("No issues detected in observed data.")
        return

    severity_counts = {"error": 0, "warning": 0, "info": 0}
    for issue in diagnostics:
        severity = str(issue.get("severity", "info")).lower()
        if severity not in severity_counts:
            severity_counts[severity] = 0
        severity_counts[severity] += 1

    PyImGui.text(
        f"errors={int(severity_counts.get('error', 0))} "
        f"warnings={int(severity_counts.get('warning', 0))} "
        f"info={int(severity_counts.get('info', 0))} "
        f"(total {len(diagnostics)})"
    )

    if PyImGui.begin_child("DiagnosticsPanel", (0, 180), True, PyImGui.WindowFlags.NoFlag):
        for index, issue in enumerate(diagnostics):
            severity = str(issue.get("severity", "info")).upper()
            rule = str(issue.get("rule", "unknown"))
            message = str(issue.get("message", ""))
            step_id = int(issue.get("step_id", 0) or 0)
            dialog_id = int(issue.get("dialog_id", 0) or 0)
            npc_uid = str(issue.get("npc_uid", "") or "")

            context_parts = []
            if step_id:
                context_parts.append(f"step#{step_id}")
            if dialog_id:
                context_parts.append(_format_dialog_id(dialog_id))
            if npc_uid:
                context_parts.append(npc_uid)
            context_suffix = f" ({', '.join(context_parts)})" if context_parts else ""

            line = _obfuscate_player_name_text(f"[{severity}] {rule}: {message}{context_suffix}")
            PyImGui.text_wrapped(line)
            _same_line()
            if PyImGui.small_button(f"CopyJSON##diag_{index}"):
                _copy_json_to_clipboard(issue)
    PyImGui.end_child()


def _draw_live_status_strip(active, dialog_active: bool) -> None:
    PyImGui.text(f"active={dialog_active}")
    if active is None:
        return

    certainty = _dialog_certainty_snapshot(active)
    npc_name = Agent.GetNameByID(active.agent_id) if int(active.agent_id or 0) else ""
    map_id = Map.GetMapID()
    model_id = Agent.GetModelID(active.agent_id) or 0

    _same_line(12.0)
    PyImGui.text(f"npc={npc_name if npc_name else '<pending>'}")
    _same_line(12.0)
    PyImGui.text(f"agent={int(active.agent_id or 0)}")
    _same_line(12.0)
    PyImGui.text(f"map={int(map_id or 0)}")
    _same_line(12.0)
    PyImGui.text(f"model={int(model_id or 0)}")
    _same_line(12.0)
    PyImGui.text(f"certainty={certainty['short_label']}")
    if _state.last_selected_dialog_id:
        _same_line(12.0)
        PyImGui.text(f"last selected={_format_dialog_id(_state.last_selected_dialog_id)}")


def _draw_live_actions(active) -> None:
    if PyImGui.button("Copy Current IDs"):
        _copy_current_ids_to_clipboard()
    _same_line(6.0)
    if PyImGui.button("Copy Message"):
        _copy_text_to_clipboard(str(getattr(active, "message", "") or ""))
    _same_line(6.0)
    if PyImGui.button("Reload"):
        _state.reset_session()
        _state.last_persist_time = 0.0


def _draw_live_tab(active, dialog_active: bool) -> None:
    _draw_live_status_strip(active, dialog_active)
    PyImGui.separator()

    if PyImGui.begin_table("DialogMonitorLiveLayout", 2, PyImGui.TableFlags.Resizable):
        PyImGui.table_setup_column("Body", PyImGui.TableColumnFlags.WidthStretch, 0)
        PyImGui.table_setup_column("Choices", PyImGui.TableColumnFlags.WidthStretch, 0)
        PyImGui.table_next_row()

        PyImGui.table_set_column_index(0)
        _draw_current_state_panel(active, _state.last_selected_dialog_id, dialog_active)

        PyImGui.table_set_column_index(1)
        _draw_choice_panel(active, _state.current_choices)

        PyImGui.end_table()

    PyImGui.separator()
    _draw_live_actions(active)


def _draw_recent_tab() -> None:
    if PyImGui.button("Copy All IDs"):
        _copy_all_ids_to_clipboard()
    _same_line(6.0)
    if PyImGui.button("Export Steps"):
        _export_dialog_steps()
    PyImGui.separator()
    _draw_history_panel()
    PyImGui.separator()
    _draw_ledger_panel()


def _draw_logs_tab() -> None:
    if PyImGui.button("Export Journal"):
        _export_callback_journal()
    _same_line(6.0)
    if PyImGui.button("Export Raw"):
        _export_raw_callbacks()
    PyImGui.separator()

    if _supports_imgui_tabs():
        if PyImGui.begin_tab_bar(_LOGS_TAB_BAR_ID):
            if PyImGui.begin_tab_item(_logs_tab_item_label(_LOGS_TAB_JOURNAL)):
                _state.select_logs_tab(_LOGS_TAB_JOURNAL)
                _draw_callback_journal_panel()
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item(_logs_tab_item_label(_LOGS_TAB_RAW)):
                _state.select_logs_tab(_LOGS_TAB_RAW)
                _draw_raw_logs_panel()
                PyImGui.end_tab_item()
            PyImGui.end_tab_bar()
        return

    if PyImGui.button("Journal"):
        _state.select_logs_tab(_LOGS_TAB_JOURNAL)
    _same_line(6.0)
    if PyImGui.button("Raw"):
        _state.select_logs_tab(_LOGS_TAB_RAW)
    PyImGui.separator()
    if _state.selected_logs_tab == _LOGS_TAB_JOURNAL:
        _draw_callback_journal_panel()
    else:
        _draw_raw_logs_panel()


def _draw_debug_status_panel() -> None:
    if PyImGui.button("Dump JSON"):
        _dump_monitor_snapshot()
    PyImGui.separator()
    if _state.selected_npc_uid:
        PyImGui.text_wrapped(f"selected npc={_state.selected_npc_uid}")
    _draw_status_messages()


def _draw_debug_tab(active, choices) -> None:
    _draw_debug_status_panel()
    PyImGui.separator()
    _draw_diagnostics_panel(active, choices)


def _apply_window_defaults() -> None:
    setter = getattr(PyImGui, "set_next_window_size", None)
    if not callable(setter):
        return
    cond = getattr(getattr(PyImGui, "ImGuiCond", None), "FirstUseEver", 0)
    try:
        setter(_DEFAULT_WINDOW_SIZE, cond)
    except TypeError:
        try:
            setter(_DEFAULT_WINDOW_SIZE[0], _DEFAULT_WINDOW_SIZE[1])
        except Exception:
            pass
    except Exception:
        pass


def draw_widget() -> None:
    _apply_window_defaults()
    if not Routines.Checks.Map.MapValid():
        if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.NoFlag):
            PyImGui.text("Map not ready yet.")
        PyImGui.end()
        return

    if PyImGui.begin(MODULE_NAME):
        if not _ensure_initialized():
            PyImGui.text("Dialog system not initialized.")
            if PyImGui.button("Retry Initialize"):
                global _initialized
                _initialized = _dialog_api.initialize() if _dialog_api is not None else False
            PyImGui.end()
            return

        _state.update_from_game(_dialog_api)
        _state.sync_core_storage()
        dialog_active = _dialog_api.is_dialog_active() if _dialog_api is not None else False

        _draw_header_controls()
        PyImGui.separator()

        if _supports_imgui_tabs():
            if PyImGui.begin_tab_bar("DialogMonitorTabs"):
                if PyImGui.begin_tab_item(_TAB_LIVE):
                    _state.select_tab(_TAB_LIVE)
                    _draw_live_tab(_state.current_active, dialog_active)
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item(_TAB_RECENT):
                    _state.select_tab(_TAB_RECENT)
                    _draw_recent_tab()
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item(_TAB_LOGS):
                    _state.select_tab(_TAB_LOGS)
                    _draw_logs_tab()
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item(_TAB_DEBUG):
                    _state.select_tab(_TAB_DEBUG)
                    _draw_debug_tab(_state.current_active, _state.current_choices)
                    PyImGui.end_tab_item()
                PyImGui.end_tab_bar()
        else:
            if PyImGui.button(_TAB_LIVE):
                _state.select_tab(_TAB_LIVE)
            _same_line(6.0)
            if PyImGui.button(_TAB_RECENT):
                _state.select_tab(_TAB_RECENT)
            _same_line(6.0)
            if PyImGui.button(_TAB_LOGS):
                _state.select_tab(_TAB_LOGS)
            _same_line(6.0)
            if PyImGui.button(_TAB_DEBUG):
                _state.select_tab(_TAB_DEBUG)
            PyImGui.separator()

            if _state.selected_tab == _TAB_RECENT:
                _draw_recent_tab()
            elif _state.selected_tab == _TAB_LOGS:
                _draw_logs_tab()
            elif _state.selected_tab == _TAB_DEBUG:
                _draw_debug_tab(_state.current_active, _state.current_choices)
            else:
                _draw_live_tab(_state.current_active, dialog_active)

    PyImGui.end()


def configure() -> None:
    pass


def main() -> None:
    draw_widget()


if __name__ == "__main__":
    main()
