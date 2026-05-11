from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional

import Py4GW  # type: ignore
from Py4GWCoreLib import Agent, Dialog, IniHandler, Player, PyImGui, Routines, Timer

MODULE_NAME = "Target Dialog Sender"
MODULE_ICON = "Textures/Module_Icons/Dialogs - Nightfall.png"

_INPUT_BASE_OPTIONS = ["Auto", "Hex", "Decimal"]
_SEND_MODE_OPTIONS = ["Normal", "Raw"]
_CHOICE_TEXT_MATCH_OPTIONS = ["Live Only", "Live + Fallback"]
_SETTINGS_SECTION = "Settings"
_DATA_SECTION = "Data"
_MAX_HISTORY_ENTRIES = 12
_SETTINGS_SAVE_DEBOUNCE_MS = 500

_PROJECT_ROOT = str(Py4GW.Console.get_projects_path() or "")
_CONFIG_DIR = os.path.join(_PROJECT_ROOT, "Widgets", "Config")
_INI_PATH = os.path.join(_CONFIG_DIR, "target_dialog_sender.ini")
os.makedirs(_CONFIG_DIR, exist_ok=True)


def _format_dialog_id(dialog_id: int) -> str:
    return f"0x{int(dialog_id) & 0xFFFFFFFF:X}"


def _normalize_dialog_input(value: str) -> str:
    return str(value or "").strip()


def _parse_dialog_id(value: str, input_base_index: int) -> Optional[int]:
    text = _normalize_dialog_input(value)
    if not text:
        return None

    try:
        if input_base_index == 1:
            return int(text.replace("0x", "").replace("0X", ""), 16)
        if input_base_index == 2:
            return int(text, 10)
        return int(text, 0)
    except Exception:
        return None


def _target_summary() -> str:
    target_id = int(Player.GetTargetID() or 0)
    if target_id <= 0:
        return "No current target"

    label = f"Target ID: {target_id}"
    try:
        name = Agent.GetNameByID(target_id)
        if name:
            label = f"{label} | {name}"
    except Exception:
        pass
    return label


@dataclass
class DialogSequenceConfig:
    name: str = ""
    input_base_index: int = 0
    send_mode_index: int = 0
    first_dialog_input: str = "0x84"
    second_dialog_input: str = ""
    use_second_dialog: bool = False
    second_dialog_delay_ms: int = 300
    retarget_before_send: bool = True

    def to_dict(self) -> dict:
        return {
            "name": str(self.name or ""),
            "input_base_index": int(self.input_base_index),
            "send_mode_index": int(self.send_mode_index),
            "first_dialog_input": str(self.first_dialog_input or ""),
            "second_dialog_input": str(self.second_dialog_input or ""),
            "use_second_dialog": bool(self.use_second_dialog),
            "second_dialog_delay_ms": max(0, int(self.second_dialog_delay_ms)),
            "retarget_before_send": bool(self.retarget_before_send),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "DialogSequenceConfig":
        return cls(
            name=str(payload.get("name", "") or ""),
            input_base_index=int(payload.get("input_base_index", 0) or 0),
            send_mode_index=int(payload.get("send_mode_index", 0) or 0),
            first_dialog_input=str(payload.get("first_dialog_input", "0x84") or ""),
            second_dialog_input=str(payload.get("second_dialog_input", "") or ""),
            use_second_dialog=bool(payload.get("use_second_dialog", False)),
            second_dialog_delay_ms=max(0, int(payload.get("second_dialog_delay_ms", 300) or 0)),
            retarget_before_send=bool(payload.get("retarget_before_send", True)),
        )


@dataclass
class PendingSendSequence:
    target_id: int = 0
    remaining_dialog_ids: List[int] = field(default_factory=list)
    send_mode_index: int = 0
    retarget_before_send: bool = True
    delay_ms: int = 300
    timer: Timer = field(default_factory=Timer)

    def clear(self) -> None:
        self.target_id = 0
        self.remaining_dialog_ids.clear()
        self.send_mode_index = 0
        self.retarget_before_send = True
        self.delay_ms = 300
        self.timer.Stop()

    def active(self) -> bool:
        return bool(self.remaining_dialog_ids)


@dataclass
class WidgetState:
    input_base_index: int = 0
    send_mode_index: int = 0
    first_dialog_input: str = "0x84"
    second_dialog_input: str = ""
    use_second_dialog: bool = False
    second_dialog_delay_ms: int = 300
    retarget_before_send: bool = True
    choice_text_input: str = ""
    choice_text_match_mode_index: int = 0
    status_text: str = "Ready."
    preset_name_input: str = ""
    selected_preset_index: int = 0
    selected_history_index: int = 0
    presets: List[DialogSequenceConfig] = field(default_factory=list)
    history: List[DialogSequenceConfig] = field(default_factory=list)
    ini_handler: IniHandler = field(default_factory=lambda: IniHandler(_INI_PATH))
    settings_dirty: bool = False
    save_timer: Timer = field(default_factory=Timer)
    pending: PendingSendSequence = field(default_factory=PendingSendSequence)


_state = WidgetState()


def _settings_snapshot() -> DialogSequenceConfig:
    return DialogSequenceConfig(
        input_base_index=_state.input_base_index,
        send_mode_index=_state.send_mode_index,
        first_dialog_input=_state.first_dialog_input,
        second_dialog_input=_state.second_dialog_input,
        use_second_dialog=_state.use_second_dialog,
        second_dialog_delay_ms=_state.second_dialog_delay_ms,
        retarget_before_send=_state.retarget_before_send,
    )


def _apply_sequence_config(config: DialogSequenceConfig, preserve_name: bool = False) -> None:
    _state.input_base_index = max(0, min(int(config.input_base_index), len(_INPUT_BASE_OPTIONS) - 1))
    _state.send_mode_index = max(0, min(int(config.send_mode_index), len(_SEND_MODE_OPTIONS) - 1))
    _state.first_dialog_input = str(config.first_dialog_input or "")
    _state.second_dialog_input = str(config.second_dialog_input or "")
    _state.use_second_dialog = bool(config.use_second_dialog)
    _state.second_dialog_delay_ms = max(0, int(config.second_dialog_delay_ms))
    _state.retarget_before_send = bool(config.retarget_before_send)
    if not preserve_name:
        _state.preset_name_input = str(config.name or "")


def _serialize_sequence_list(items: List[DialogSequenceConfig]) -> str:
    return json.dumps([item.to_dict() for item in items], separators=(",", ":"))


def _deserialize_sequence_list(payload: str) -> List[DialogSequenceConfig]:
    text = str(payload or "").strip()
    if not text:
        return []

    try:
        raw_items = json.loads(text)
    except Exception:
        return []

    if not isinstance(raw_items, list):
        return []

    parsed_items: List[DialogSequenceConfig] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        try:
            parsed_items.append(DialogSequenceConfig.from_dict(raw_item))
        except Exception:
            continue
    return parsed_items


def _save_state(force: bool = False) -> None:
    if not force and not _state.settings_dirty:
        return

    _state.ini_handler.write_key(_SETTINGS_SECTION, "input_base_index", _state.input_base_index)
    _state.ini_handler.write_key(_SETTINGS_SECTION, "send_mode_index", _state.send_mode_index)
    _state.ini_handler.write_key(_SETTINGS_SECTION, "first_dialog_input", _state.first_dialog_input)
    _state.ini_handler.write_key(_SETTINGS_SECTION, "second_dialog_input", _state.second_dialog_input)
    _state.ini_handler.write_key(_SETTINGS_SECTION, "use_second_dialog", _state.use_second_dialog)
    _state.ini_handler.write_key(_SETTINGS_SECTION, "second_dialog_delay_ms", _state.second_dialog_delay_ms)
    _state.ini_handler.write_key(_SETTINGS_SECTION, "retarget_before_send", _state.retarget_before_send)
    _state.ini_handler.write_key(_SETTINGS_SECTION, "choice_text_input", _state.choice_text_input)
    _state.ini_handler.write_key(_SETTINGS_SECTION, "choice_text_match_mode_index", _state.choice_text_match_mode_index)
    _state.ini_handler.write_key(_SETTINGS_SECTION, "preset_name_input", _state.preset_name_input)
    _state.ini_handler.write_key(_SETTINGS_SECTION, "selected_preset_index", _state.selected_preset_index)
    _state.ini_handler.write_key(_SETTINGS_SECTION, "selected_history_index", _state.selected_history_index)
    _state.ini_handler.write_key(_DATA_SECTION, "presets_json", _serialize_sequence_list(_state.presets))
    _state.ini_handler.write_key(_DATA_SECTION, "history_json", _serialize_sequence_list(_state.history))
    _state.settings_dirty = False
    _state.save_timer.Stop()


def _mark_settings_dirty() -> None:
    _state.settings_dirty = True
    _state.save_timer.Start()


def _flush_settings_if_needed() -> None:
    if not _state.settings_dirty:
        return
    if not _state.save_timer.HasElapsed(_SETTINGS_SAVE_DEBOUNCE_MS):
        return
    _save_state(force=True)


def _load_state() -> None:
    _state.input_base_index = max(
        0,
        min(
            _state.ini_handler.read_int(_SETTINGS_SECTION, "input_base_index", _state.input_base_index),
            len(_INPUT_BASE_OPTIONS) - 1,
        ),
    )
    _state.send_mode_index = max(
        0,
        min(
            _state.ini_handler.read_int(_SETTINGS_SECTION, "send_mode_index", _state.send_mode_index),
            len(_SEND_MODE_OPTIONS) - 1,
        ),
    )
    _state.first_dialog_input = _state.ini_handler.read_key(
        _SETTINGS_SECTION,
        "first_dialog_input",
        _state.first_dialog_input,
    )
    _state.second_dialog_input = _state.ini_handler.read_key(
        _SETTINGS_SECTION,
        "second_dialog_input",
        _state.second_dialog_input,
    )
    _state.use_second_dialog = _state.ini_handler.read_bool(
        _SETTINGS_SECTION,
        "use_second_dialog",
        _state.use_second_dialog,
    )
    _state.second_dialog_delay_ms = max(
        0,
        _state.ini_handler.read_int(
            _SETTINGS_SECTION,
            "second_dialog_delay_ms",
            _state.second_dialog_delay_ms,
        ),
    )
    _state.retarget_before_send = _state.ini_handler.read_bool(
        _SETTINGS_SECTION,
        "retarget_before_send",
        _state.retarget_before_send,
    )
    _state.choice_text_input = _state.ini_handler.read_key(
        _SETTINGS_SECTION,
        "choice_text_input",
        _state.choice_text_input,
    )
    _state.choice_text_match_mode_index = max(
        0,
        min(
            _state.ini_handler.read_int(
                _SETTINGS_SECTION,
                "choice_text_match_mode_index",
                _state.choice_text_match_mode_index,
            ),
            len(_CHOICE_TEXT_MATCH_OPTIONS) - 1,
        ),
    )
    _state.preset_name_input = _state.ini_handler.read_key(
        _SETTINGS_SECTION,
        "preset_name_input",
        _state.preset_name_input,
    )
    _state.presets = _deserialize_sequence_list(
        _state.ini_handler.read_key(_DATA_SECTION, "presets_json", "[]")
    )
    _state.history = _deserialize_sequence_list(
        _state.ini_handler.read_key(_DATA_SECTION, "history_json", "[]")
    )[:_MAX_HISTORY_ENTRIES]
    _state.selected_preset_index = max(
        0,
        min(
            _state.ini_handler.read_int(_SETTINGS_SECTION, "selected_preset_index", 0),
            max(0, len(_state.presets) - 1),
        ),
    )
    _state.selected_history_index = max(
        0,
        min(
            _state.ini_handler.read_int(_SETTINGS_SECTION, "selected_history_index", 0),
            max(0, len(_state.history) - 1),
        ),
    )
    _state.settings_dirty = False
    _state.save_timer.Stop()


def _preset_names() -> List[str]:
    return [preset.name or f"Preset {index + 1}" for index, preset in enumerate(_state.presets)]


def _sequence_label(config: DialogSequenceConfig) -> str:
    mode_name = _SEND_MODE_OPTIONS[max(0, min(config.send_mode_index, len(_SEND_MODE_OPTIONS) - 1))]
    ids = [str(config.first_dialog_input or "").strip() or "<?>"]
    if config.use_second_dialog and str(config.second_dialog_input or "").strip():
        ids.append(str(config.second_dialog_input).strip())
    return f"{mode_name}: {' -> '.join(ids)}"


def _history_labels() -> List[str]:
    return [_sequence_label(entry) for entry in _state.history]


def _save_current_as_preset() -> None:
    preset_name = str(_state.preset_name_input or "").strip()
    if not preset_name:
        _state.status_text = "Preset name is required."
        return

    config = _settings_snapshot()
    config.name = preset_name

    replaced = False
    for index, existing in enumerate(_state.presets):
        if existing.name.lower() == preset_name.lower():
            _state.presets[index] = config
            _state.selected_preset_index = index
            replaced = True
            break

    if not replaced:
        _state.presets.append(config)
        _state.selected_preset_index = len(_state.presets) - 1

    _save_state(force=True)
    _state.status_text = f"Saved preset '{preset_name}'."


def _load_selected_preset() -> None:
    if not _state.presets:
        _state.status_text = "No preset available to load."
        return

    selected_index = max(0, min(_state.selected_preset_index, len(_state.presets) - 1))
    preset = _state.presets[selected_index]
    _apply_sequence_config(preset)
    _state.selected_preset_index = selected_index
    _save_state(force=True)
    _state.status_text = f"Loaded preset '{preset.name}'."


def _delete_selected_preset() -> None:
    if not _state.presets:
        _state.status_text = "No preset available to delete."
        return

    selected_index = max(0, min(_state.selected_preset_index, len(_state.presets) - 1))
    preset_name = _state.presets[selected_index].name or f"Preset {selected_index + 1}"
    _state.presets.pop(selected_index)
    _state.selected_preset_index = max(0, min(selected_index, len(_state.presets) - 1))
    _save_state(force=True)
    _state.status_text = f"Deleted preset '{preset_name}'."


def _record_history_entry() -> None:
    entry = _settings_snapshot()
    entry.name = ""
    canonical = json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":"))

    deduped_history: List[DialogSequenceConfig] = []
    for history_entry in _state.history:
        if json.dumps(history_entry.to_dict(), sort_keys=True, separators=(",", ":")) != canonical:
            deduped_history.append(history_entry)

    _state.history = [entry] + deduped_history[: max(0, _MAX_HISTORY_ENTRIES - 1)]
    _state.selected_history_index = 0
    _save_state(force=True)


def _load_selected_history_entry() -> None:
    if not _state.history:
        _state.status_text = "No history entry available to load."
        return

    selected_index = max(0, min(_state.selected_history_index, len(_state.history) - 1))
    history_entry = _state.history[selected_index]
    _apply_sequence_config(history_entry, preserve_name=True)
    _state.selected_history_index = selected_index
    _save_state(force=True)
    _state.status_text = f"Loaded history entry '{_sequence_label(history_entry)}'."


def _clear_history() -> None:
    if not _state.history:
        _state.status_text = "History is already empty."
        return

    _state.history.clear()
    _state.selected_history_index = 0
    _save_state(force=True)
    _state.status_text = "Cleared dialog send history."


def _emit_dialog(dialog_id: int, target_id: int, send_mode_index: int, retarget_before_send: bool) -> None:
    if retarget_before_send and target_id > 0:
        Player.ChangeTarget(target_id)

    if send_mode_index == 1:
        Player.SendRawDialog(dialog_id)
        mode_name = "raw"
    else:
        Player.SendDialog(dialog_id)
        mode_name = "normal"

    _state.status_text = (
        f"Queued {mode_name} dialog {_format_dialog_id(dialog_id)}"
        f" for target {target_id}."
    )


def _validate_dialog_inputs() -> tuple[int, Optional[int], Optional[int], Optional[str]]:
    target_id = int(Player.GetTargetID() or 0)
    if target_id <= 0:
        return 0, None, None, "No target selected."

    first_dialog_id = _parse_dialog_id(_state.first_dialog_input, _state.input_base_index)
    if first_dialog_id is None:
        return 0, None, None, "First dialog ID is invalid."

    second_dialog_id: Optional[int] = None
    if _state.use_second_dialog:
        second_dialog_id = _parse_dialog_id(_state.second_dialog_input, _state.input_base_index)
        if second_dialog_id is None:
            return 0, None, None, "Second dialog ID is invalid."

    return target_id, first_dialog_id, second_dialog_id, None


def _resolve_choice_text_dialog_id(choice_text: str, match_mode_index: int) -> int:
    text = str(choice_text or "").strip()
    if not text:
        return 0

    try:
        if int(match_mode_index) == 1:
            return int(Dialog.get_active_dialog_choice_id_by_text_with_fallback(text) or 0)
        return int(Dialog.get_active_dialog_choice_id_by_text(text) or 0)
    except Exception:
        return 0


def _queue_choice_text_send() -> None:
    target_id = int(Player.GetTargetID() or 0)
    if target_id <= 0:
        _state.status_text = "No target selected."
        return

    choice_text = str(_state.choice_text_input or "").strip()
    if not choice_text:
        _state.status_text = "Choice text is required."
        return

    match_mode_index = max(0, min(int(_state.choice_text_match_mode_index), len(_CHOICE_TEXT_MATCH_OPTIONS) - 1))
    dialog_id = _resolve_choice_text_dialog_id(choice_text, match_mode_index)
    mode_label = _CHOICE_TEXT_MATCH_OPTIONS[match_mode_index].lower()

    if dialog_id == 0:
        _state.status_text = (
            f"Could not resolve current visible choice text '{choice_text}' "
            f"using {mode_label}."
        )
        return

    if _state.retarget_before_send and target_id > 0:
        Player.ChangeTarget(target_id)

    Player.SendDialog(dialog_id)
    _state.status_text = (
        f"Queued normal dialog {_format_dialog_id(dialog_id)} resolved from text "
        f"'{choice_text}' using {mode_label} for target {target_id}."
    )


def _queue_send_sequence() -> None:
    target_id, first_dialog_id, second_dialog_id, error = _validate_dialog_inputs()
    if error is not None or first_dialog_id is None:
        _state.status_text = error or "Unable to queue dialogs."
        return

    _state.pending.clear()

    _emit_dialog(
        first_dialog_id,
        target_id,
        _state.send_mode_index,
        _state.retarget_before_send,
    )

    if second_dialog_id is None:
        _record_history_entry()
        return

    _state.pending.target_id = target_id
    _state.pending.remaining_dialog_ids = [second_dialog_id]
    _state.pending.send_mode_index = _state.send_mode_index
    _state.pending.retarget_before_send = _state.retarget_before_send
    _state.pending.delay_ms = max(0, int(_state.second_dialog_delay_ms))
    _state.pending.timer.Start()
    _record_history_entry()
    _state.status_text = (
        f"Queued {_SEND_MODE_OPTIONS[_state.send_mode_index].lower()} sequence "
        f"{_format_dialog_id(first_dialog_id)} -> {_format_dialog_id(second_dialog_id)} "
        f"for target {target_id}."
    )


def _process_pending_sequence() -> None:
    if not _state.pending.active():
        return

    if not _state.pending.timer.HasElapsed(_state.pending.delay_ms):
        return

    next_dialog_id = _state.pending.remaining_dialog_ids.pop(0)
    _emit_dialog(
        next_dialog_id,
        _state.pending.target_id,
        _state.pending.send_mode_index,
        _state.pending.retarget_before_send,
    )

    if _state.pending.active():
        _state.pending.timer.Reset()
        return

    _state.pending.clear()


def _draw_help_text() -> None:
    PyImGui.text_wrapped(
        "Use the normal path to mirror Player.SendDialog(), or the raw path "
        "to mirror Player.SendRawDialog(). The second dialog, if enabled, is "
        "queued non-blockingly and sent after the configured delay. Presets and "
        "recent history are stored in Widgets/Config/target_dialog_sender.ini."
    )
    PyImGui.text_wrapped(
        "The choice-text sender always uses the normal Player.SendDialog() path. "
        "Live mode matches only the current visible choice labels, while fallback "
        "mode can also resolve the currently visible choice IDs through catalog "
        "and recent persisted history text."
    )


def _draw_preview() -> None:
    first_dialog_id = _parse_dialog_id(_state.first_dialog_input, _state.input_base_index)
    second_dialog_id = _parse_dialog_id(_state.second_dialog_input, _state.input_base_index)

    if first_dialog_id is not None:
        PyImGui.text(f"First parsed ID: {_format_dialog_id(first_dialog_id)} ({first_dialog_id})")
    else:
        PyImGui.text("First parsed ID: invalid")

    if _state.use_second_dialog:
        if second_dialog_id is not None:
            PyImGui.text(f"Second parsed ID: {_format_dialog_id(second_dialog_id)} ({second_dialog_id})")
        else:
            PyImGui.text("Second parsed ID: invalid")


def _draw_presets() -> None:
    PyImGui.separator()
    PyImGui.text("Presets")

    preset_name_input = str(PyImGui.input_text("Preset Name", _state.preset_name_input))
    if preset_name_input != _state.preset_name_input:
        _state.preset_name_input = preset_name_input
        _mark_settings_dirty()

    preset_names = _preset_names() or ["<no presets saved>"]
    preset_index = int(PyImGui.combo("Saved Presets", _state.selected_preset_index, preset_names))
    if preset_index != _state.selected_preset_index:
        _state.selected_preset_index = preset_index
        _mark_settings_dirty()

    if PyImGui.button("Save Current As Preset"):
        _save_current_as_preset()
    if PyImGui.button("Load Selected Preset"):
        _load_selected_preset()
    if PyImGui.button("Delete Selected Preset"):
        _delete_selected_preset()


def _draw_history() -> None:
    PyImGui.separator()
    PyImGui.text("Recent History")

    history_labels = _history_labels() or ["<no history yet>"]
    history_index = int(PyImGui.combo("Recent Sequences", _state.selected_history_index, history_labels))
    if history_index != _state.selected_history_index:
        _state.selected_history_index = history_index
        _mark_settings_dirty()

    if PyImGui.button("Load Selected History"):
        _load_selected_history_entry()
    if PyImGui.button("Clear History"):
        _clear_history()


def _draw_choice_text_sender() -> None:
    PyImGui.separator()
    PyImGui.text("Visible Choice Text")

    match_mode_index = int(
        PyImGui.combo("Choice Match Mode", _state.choice_text_match_mode_index, _CHOICE_TEXT_MATCH_OPTIONS)
    )
    if match_mode_index != _state.choice_text_match_mode_index:
        _state.choice_text_match_mode_index = match_mode_index
        _mark_settings_dirty()

    choice_text_input = str(PyImGui.input_text("Choice Text", _state.choice_text_input))
    if choice_text_input != _state.choice_text_input:
        _state.choice_text_input = choice_text_input
        _mark_settings_dirty()

    PyImGui.text_wrapped(
        "Sends the currently visible choice that matches this text. "
        "Fallback mode still sends only a currently visible choice ID."
    )

    if PyImGui.button("Send Visible Choice Text To Current Target"):
        _queue_choice_text_send()


def _draw_widget() -> None:
    if not PyImGui.begin(MODULE_NAME):
        PyImGui.end()
        return

    PyImGui.text(_target_summary())
    PyImGui.separator()

    send_mode_index = int(PyImGui.combo("ID Send Path", _state.send_mode_index, _SEND_MODE_OPTIONS))
    if send_mode_index != _state.send_mode_index:
        _state.send_mode_index = send_mode_index
        _mark_settings_dirty()

    input_base_index = int(PyImGui.combo("Input Base", _state.input_base_index, _INPUT_BASE_OPTIONS))
    if input_base_index != _state.input_base_index:
        _state.input_base_index = input_base_index
        _mark_settings_dirty()

    retarget_before_send = bool(
        PyImGui.checkbox("Retarget before each send", _state.retarget_before_send)
    )
    if retarget_before_send != _state.retarget_before_send:
        _state.retarget_before_send = retarget_before_send
        _mark_settings_dirty()

    PyImGui.separator()
    first_dialog_input = str(PyImGui.input_text("Dialog ID #1", _state.first_dialog_input))
    if first_dialog_input != _state.first_dialog_input:
        _state.first_dialog_input = first_dialog_input
        _mark_settings_dirty()

    use_second_dialog = bool(PyImGui.checkbox("Queue second dialog", _state.use_second_dialog))
    if use_second_dialog != _state.use_second_dialog:
        _state.use_second_dialog = use_second_dialog
        _mark_settings_dirty()

    if _state.use_second_dialog:
        second_dialog_input = str(
            PyImGui.input_text("Dialog ID #2", _state.second_dialog_input)
        )
        if second_dialog_input != _state.second_dialog_input:
            _state.second_dialog_input = second_dialog_input
            _mark_settings_dirty()

        second_dialog_delay_ms = max(
            0, int(PyImGui.input_int("Delay Before #2 (ms)", int(_state.second_dialog_delay_ms)))
        )
        if second_dialog_delay_ms != _state.second_dialog_delay_ms:
            _state.second_dialog_delay_ms = second_dialog_delay_ms
            _mark_settings_dirty()

    PyImGui.separator()
    _draw_preview()
    _draw_presets()
    _draw_history()
    _draw_choice_text_sender()
    PyImGui.separator()

    if PyImGui.button("Send Dialog To Current Target"):
        _queue_send_sequence()

    if _state.pending.active():
        remaining = max(0, _state.pending.delay_ms - int(_state.pending.timer.GetElapsedTime()))
        PyImGui.text(
            f"Pending second send: {_format_dialog_id(_state.pending.remaining_dialog_ids[0])} "
            f"in {remaining} ms"
        )
        if PyImGui.button("Cancel Pending Second Send"):
            _state.pending.clear()
            _state.status_text = "Cancelled pending second send."

    PyImGui.separator()
    _draw_help_text()
    PyImGui.separator()
    PyImGui.text_wrapped(f"Status: {_state.status_text}")

    PyImGui.end()


def tooltip() -> None:
    PyImGui.begin_tooltip()
    PyImGui.text("Target Dialog Sender")
    PyImGui.separator()
    PyImGui.text("Send one or two dialog IDs to the current target.")
    PyImGui.bullet_text("Supports normal Player.SendDialog path")
    PyImGui.bullet_text("Supports raw Player.SendRawDialog path")
    PyImGui.bullet_text("Supports visible choice-text sends in live and fallback modes")
    PyImGui.bullet_text("Second dialog is queued with a configurable delay")
    PyImGui.bullet_text("Hex and decimal inputs are both supported")
    PyImGui.bullet_text("Presets and recent history persist between sessions")
    PyImGui.end_tooltip()


def main() -> None:
    try:
        if not Routines.Checks.Map.MapValid():
            return
        _flush_settings_if_needed()
        _process_pending_sequence()
        if Routines.Checks.Map.IsMapReady():
            _draw_widget()
    except Exception as exc:
        _state.status_text = f"Error: {exc}"


_load_state()


if __name__ == "__main__":
    main()
