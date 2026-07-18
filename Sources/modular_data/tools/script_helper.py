"""
Modular JSON Script Helper.

Runtime widget/tool for recording canonical JSON steps while playing. It is
intentionally recording-only: it does not replay steps or instantiate bot
runners.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

import PyAgent
import PyImGui

try:
    import PyDialog
except Exception:
    PyDialog = None

from Py4GWCoreLib import Agent
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Item
from Py4GWCoreLib import Map
from Py4GWCoreLib import Player
from Py4GWCoreLib.modular.domain.target_registry import ENEMY_TARGETS
from Py4GWCoreLib.modular.domain.target_registry import GADGET_TARGETS
from Py4GWCoreLib.modular.domain.target_registry import NPC_TARGETS


_DEFAULT_RECIPE_NAME = "New Recording"
_DEFAULT_RELATIVE_PATH = "missions/new_recording.json"

_recipe_name = _DEFAULT_RECIPE_NAME
_relative_save_path = _DEFAULT_RELATIVE_PATH
_auto_capture_dialogs = True
_dialog_init_attempted = False
_dialog_init_ok = False
_dialog_init_last_attempt = 0.0
_dialog_last_tick = 0
_recorded_steps: list[dict[str, Any]] = []
_captured_npc_entries: dict[str, str] = {}
_captured_enemy_entries: dict[str, str] = {}
_captured_gadget_entries: dict[str, str] = {}
_captured_item_entries: dict[str, str] = {}
_status = ""
_last_action_ts: float | None = None

_exit_recording_active = False
_exit_recording_waiting_load = False
_exit_record_last_x = 0
_exit_record_last_y = 0
_exit_record_source_map_id = 0
_exit_record_source_map_name = ""

_travel_recording_active = False
_travel_record_source_map_id = 0

DEBUG_LOGGING = False


def _debug_log(message: str) -> None:
    if DEBUG_LOGGING:
        ConsoleLog("Script Helper", message)


def _modular_data_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _fmt_xy(x: float, y: float) -> str:
    return f"[{int(x)}, {int(y)}]"


def _enum_key_from_name(name: str, default_prefix: str) -> str:
    cleaned = []
    previous_was_underscore = False
    for ch in (name or "").upper():
        if ch.isalnum():
            cleaned.append(ch)
            previous_was_underscore = False
        elif not previous_was_underscore:
            cleaned.append("_")
            previous_was_underscore = True
    key = "".join(cleaned).strip("_")
    return key or default_prefix


def _safe_display_name(name: str) -> str:
    return str(name or "").replace("\\", "\\\\").replace('"', '\\"')


def _target_enum_entry(agent_id: int) -> tuple[str | None, str | None, str]:
    if agent_id <= 0 or not Agent.IsValid(agent_id):
        return None, None, ""
    enc_name = PyAgent.PyAgent.GetAgentEncName(agent_id) or []
    display_name = Agent.GetNameByID(agent_id) or ""
    enc_name_str = ", ".join(str(int(value)) for value in enc_name)
    enum_key = _enum_key_from_name(display_name, "TARGET")
    enum_entry = f'"{enum_key}": ((({enc_name_str}),), "{_safe_display_name(display_name)}"),'
    return enum_key, enum_entry, display_name


def _target_registry_for_kind(kind: str) -> dict[str, object]:
    if kind == "enemy":
        return ENEMY_TARGETS
    if kind == "gadget":
        return GADGET_TARGETS
    return NPC_TARGETS


def _captured_entries_for_kind(kind: str) -> dict[str, str]:
    if kind == "enemy":
        return _captured_enemy_entries
    if kind == "gadget":
        return _captured_gadget_entries
    return _captured_npc_entries


def _capture_target_enum(kind: str, agent_id: int) -> tuple[str | None, str | None, str]:
    key, entry, display_name = _target_enum_entry(agent_id)
    if key and entry:
        _captured_entries_for_kind(kind)[key] = entry
    return key, entry, display_name


def _target_registry_title(kind: str) -> str:
    if kind == "enemy":
        return "ENEMY_TARGETS"
    if kind == "gadget":
        return "GADGET_TARGETS"
    return "NPC_TARGETS"


def _target_registry_file_hint() -> str:
    return "Py4GWCoreLib/modular/domain/target_registry.py"


def _item_enum_entry(agent_id: int) -> tuple[str | None, str | None, str, int]:
    if agent_id <= 0 or not Agent.IsValid(agent_id) or not Agent.IsItem(agent_id):
        return None, None, "", 0
    item_id = int(Agent.GetItemAgentItemID(agent_id))
    model_id = int(Item.GetModelID(item_id)) if item_id > 0 else 0
    display_name = Agent.GetNameByID(agent_id) or (f"Item {model_id}" if model_id > 0 else "Item")
    enum_key = _enum_key_from_name(display_name, "ITEM")
    enum_entry = f'"{enum_key}": ({model_id}, "{_safe_display_name(display_name)}"),'
    return enum_key, enum_entry, display_name, model_id


def _ensure_dialog_initialized() -> bool:
    global _dialog_init_attempted, _dialog_init_last_attempt, _dialog_init_ok
    if PyDialog is None or not hasattr(PyDialog, "PyDialog"):
        return False
    if _dialog_init_attempted and _dialog_init_ok:
        return _dialog_init_ok
    now = time.monotonic()
    if _dialog_init_attempted and now - _dialog_init_last_attempt < 5.0:
        return False
    _dialog_init_attempted = True
    _dialog_init_last_attempt = now
    try:
        init_fn = getattr(PyDialog.PyDialog, "initialize", None)
        if init_fn is not None:
            init_fn()
        _dialog_init_ok = True
    except Exception as exc:
        _dialog_init_ok = False
        _debug_log(f"PyDialog initialize failed: {exc}")
    return _dialog_init_ok


def _active_dialog_options() -> list[tuple[int, str]]:
    if not _ensure_dialog_initialized():
        return []
    getter = getattr(PyDialog.PyDialog, "get_active_dialog_buttons", None)
    if getter is None:
        return []
    options: list[tuple[int, str]] = []
    seen: set[int] = set()
    for button in getter() or []:
        dialog_id = int(getattr(button, "dialog_id", 0) or 0)
        if dialog_id <= 0 or dialog_id in seen:
            continue
        seen.add(dialog_id)
        message = str(getattr(button, "message_decoded", "") or getattr(button, "message", "") or "").strip()
        options.append((dialog_id, message))
    return options


def _sync_dialog_cursor_to_latest() -> None:
    global _dialog_last_tick
    if not _ensure_dialog_initialized():
        return
    getter = getattr(PyDialog.PyDialog, "get_dialog_callback_journal_sent", None)
    if getter is None:
        return
    entries = getter() or []
    if entries:
        _dialog_last_tick = max(_dialog_last_tick, max(int(getattr(entry, "tick", 0) or 0) for entry in entries))


def _poll_dialog_recorder() -> None:
    global _dialog_last_tick, _status
    if not _auto_capture_dialogs or not _ensure_dialog_initialized():
        return
    getter = getattr(PyDialog.PyDialog, "get_dialog_callback_journal_sent", None)
    if getter is None:
        return
    max_tick = _dialog_last_tick
    captured = 0
    for entry in getter() or []:
        tick = int(getattr(entry, "tick", 0) or 0)
        if tick <= _dialog_last_tick:
            continue
        max_tick = max(max_tick, tick)
        if str(getattr(entry, "event_type", "") or "") != "sent_choice":
            continue
        dialog_id = int(getattr(entry, "dialog_id", 0) or 0)
        if dialog_id <= 0:
            continue
        _record_dialog_step(dialog_id)
        captured += 1
    _dialog_last_tick = max_tick
    if captured:
        _status = f"Captured {captured} dialog click(s)."


def _record_dialog_step(dialog_id: int) -> None:
    target_id = int(Player.GetTargetID() or 0)
    npc_key, npc_entry, display_name = _capture_target_enum("npc", target_id)
    selector: dict[str, Any]
    if npc_key and npc_entry:
        selector = {"npc": npc_key}
    else:
        selector = {"nearest": True}

    dialog_value = f"0x{int(dialog_id):X}"
    step: dict[str, Any] = {"type": "interact", "action": "dialog", "target": "npc", "id": dialog_value}
    step.update(selector)
    if target_id > 0 and Agent.IsValid(target_id):
        x, y = Agent.GetXY(target_id)
        step["point"] = [int(x), int(y)]
    if display_name:
        step["name"] = f"Dialog - {display_name}"

    last = _recorded_steps[-1] if _recorded_steps else None
    if isinstance(last, dict) and last.get("type") == "interact" and last.get("action") == "dialog":
        same_selector = (
            ("npc" in selector and last.get("npc") == selector["npc"])
            or ("nearest" in selector and bool(last.get("nearest")))
        )
        if same_selector:
            ids = last.get("ids")
            if not isinstance(ids, list):
                previous = last.pop("id", None)
                ids = [previous] if previous is not None else []
                last["ids"] = ids
            ids.append(dialog_value)
            _mark_last_action_now()
            return

    _add_step(step)


def _add_step(step: dict[str, Any]) -> None:
    _recorded_steps.append(step)
    _mark_last_action_now()


def _mark_last_action_now() -> None:
    global _last_action_ts
    _last_action_ts = time.monotonic()


def _elapsed_wait_ms_since_last_action(default_ms: int = 1000) -> int:
    if _last_action_ts is None:
        return default_ms
    return max(100, int((time.monotonic() - _last_action_ts) * 1000.0))


def _recipe_payload() -> dict[str, Any]:
    return {
        "name": _recipe_name.strip() or _DEFAULT_RECIPE_NAME,
        "steps": [dict(step) for step in _recorded_steps],
    }


def _recipe_json() -> str:
    payload = _recipe_payload()
    lines = ["{", f'  "name": {json.dumps(payload["name"])},', '  "steps": [']
    step_lines = [json.dumps(step, ensure_ascii=False, separators=(", ", ": ")) for step in payload["steps"]]
    for index, line in enumerate(step_lines):
        suffix = "," if index < len(step_lines) - 1 else ""
        lines.append(f"    {line}{suffix}")
    lines.append("  ]")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _steps_text() -> str:
    return "\n".join(json.dumps(step, ensure_ascii=False, separators=(", ", ": ")) for step in _recorded_steps)


def _captured_entry_encoded_tuple(entry: str) -> tuple[int, ...] | None:
    try:
        start = entry.index("(((") + 3
        end = entry.index("),),", start)
        raw = entry[start:end].strip()
        if not raw:
            return ()
        return tuple(int(value.strip()) for value in raw.split(",") if value.strip())
    except (ValueError, TypeError):
        return None


def _registry_encoded_tuples(value: object) -> set[tuple[int, ...]]:
    if value is None:
        return set()
    encoded_names = getattr(value, "encoded_names", None)
    if encoded_names is not None:
        return {tuple(int(part) for part in encoded_name) for encoded_name in encoded_names}
    if not isinstance(value, tuple) or not value:
        return set()
    encoded_raw = value[0]
    if not encoded_raw:
        return set()
    try:
        if isinstance(encoded_raw[0], int):
            return {tuple(int(part) for part in encoded_raw)}
        return {tuple(int(part) for part in encoded_name) for encoded_name in encoded_raw}
    except (TypeError, ValueError, IndexError):
        return set()


def _encoded_tuple_text(encoded: tuple[int, ...]) -> str:
    return "(" + ", ".join(str(value) for value in encoded) + ")"


def _target_registry_update_lines(kind: str, captured: dict[str, str]) -> list[str]:
    title = _target_registry_title(kind)
    registry = _target_registry_for_kind(kind)
    lines: list[str] = []
    for key, entry in sorted(captured.items()):
        encoded = _captured_entry_encoded_tuple(entry)
        if encoded is None:
            continue
        existing_encoded = _registry_encoded_tuples(registry.get(key))
        if key in registry and encoded in existing_encoded:
            continue
        encoded_text = _encoded_tuple_text(encoded)
        if key in registry:
            lines.append(f"extend {title} {key} with {encoded_text}")
        else:
            lines.append(f"add {key} with {encoded_text} to {title}")
    return lines


def _target_registry_action(kind: str, key: str | None, entry: str | None) -> str:
    if not key or not entry:
        return ""
    lines = _target_registry_update_lines(kind, {key: entry})
    if not lines:
        return "already indexed"
    return lines[0]


def _captured_enum_entries_text() -> str:
    lines: list[str] = []
    for kind, captured in (
        ("enemy", _captured_enemy_entries),
        ("gadget", _captured_gadget_entries),
        ("npc", _captured_npc_entries),
    ):
        updates = _target_registry_update_lines(kind, captured)
        if not updates:
            continue
        lines.extend(updates)
    if _captured_item_entries:
        lines.append("")
        lines.append("# Captured item model IDs")
        lines.extend(value for _key, value in sorted(_captured_item_entries.items()))
    if not lines:
        return "No target registry updates needed."
    return _target_registry_file_hint() + "\n" + "\n".join(lines).strip()


def _registry_appendix() -> str:
    lines: list[str] = []
    for kind, captured in (
        ("enemy", _captured_enemy_entries),
        ("gadget", _captured_gadget_entries),
        ("npc", _captured_npc_entries),
    ):
        updates = _target_registry_update_lines(kind, captured)
        if not updates:
            continue
        lines.extend(updates)
    if _captured_item_entries:
        lines.append("")
        lines.append("# Captured item model IDs")
        lines.extend(value for _key, value in sorted(_captured_item_entries.items()))
    if not lines:
        return ""
    return _target_registry_file_hint() + "\n" + "\n".join(lines).strip()


def _recipe_json_with_appendix() -> str:
    appendix = _registry_appendix()
    if not appendix:
        return _recipe_json()
    return _recipe_json() + "\n" + appendix + "\n"


def _save_recipe() -> str:
    relative = re.sub(r"^[\\/]+", "", _relative_save_path.strip() or _DEFAULT_RELATIVE_PATH)
    if not relative.lower().endswith(".json"):
        relative += ".json"
    path = (_modular_data_root() / relative).resolve()
    root = _modular_data_root().resolve()
    if root not in path.parents and path != root:
        raise ValueError("Save path must stay inside Sources/modular_data.")
    os.makedirs(path.parent, exist_ok=True)
    path.write_text(_recipe_json(), encoding="utf-8", newline="\n")
    return str(path)


def _start_exit_map_recording() -> None:
    global _exit_recording_active, _exit_recording_waiting_load
    global _exit_record_last_x, _exit_record_last_y, _exit_record_source_map_id, _exit_record_source_map_name, _status
    x, y = Player.GetXY()
    _exit_record_last_x = int(x)
    _exit_record_last_y = int(y)
    _exit_record_source_map_id = int(Map.GetMapID() or 0)
    _exit_record_source_map_name = str(Map.GetMapName(_exit_record_source_map_id) or "").strip()
    _exit_recording_active = True
    _exit_recording_waiting_load = False
    _status = f"Exit-map recording started at [{_exit_record_last_x}, {_exit_record_last_y}]."


def _poll_exit_map_recording() -> None:
    global _exit_recording_active, _exit_recording_waiting_load, _exit_record_last_x, _exit_record_last_y, _status
    if not _exit_recording_active:
        return
    x, y = Player.GetXY()
    ix, iy = int(x), int(y)
    if not _exit_recording_waiting_load:
        if ix != 0 or iy != 0:
            _exit_record_last_x = ix
            _exit_record_last_y = iy
            return
        _exit_recording_waiting_load = True
        _status = f"Exit-map recording: load detected, using [{_exit_record_last_x}, {_exit_record_last_y}]."
        return
    if ix == 0 and iy == 0:
        return
    target_map_id = int(Map.GetMapID() or 0)
    if target_map_id <= 0 or target_map_id == _exit_record_source_map_id:
        _exit_recording_active = False
        _exit_recording_waiting_load = False
        _status = "Exit-map recording canceled; map did not change."
        return
    name_suffix = _exit_record_source_map_name or str(_exit_record_source_map_id or "Map")
    _add_step(
        {
            "type": "route",
            "name": f"Exit {name_suffix}",
            "mode": "exit",
            "point": [int(_exit_record_last_x), int(_exit_record_last_y)],
            "target_map_id": target_map_id,
        }
    )
    _exit_recording_active = False
    _exit_recording_waiting_load = False
    _status = f"Recorded route exit to target_map_id {target_map_id}."


def _start_travel_recording() -> None:
    global _travel_recording_active, _travel_record_source_map_id, _status
    _travel_record_source_map_id = int(Map.GetMapID() or 0)
    _travel_recording_active = True
    _status = f"Travel recording started from map {_travel_record_source_map_id}. Travel now."


def _poll_travel_recording() -> None:
    global _travel_recording_active, _status
    if not _travel_recording_active:
        return
    current_map_id = int(Map.GetMapID() or 0)
    if current_map_id <= 0 or current_map_id == _travel_record_source_map_id:
        return
    _add_step({"type": "map", "name": "Travel", "action": "travel", "target_map_id": current_map_id})
    _travel_recording_active = False
    _status = f"Recorded map travel to target_map_id {current_map_id}."


def _record_route_point() -> None:
    global _status
    x, y = Player.GetXY()
    point = [int(x), int(y)]
    if _recorded_steps and _recorded_steps[-1].get("type") == "route" and _recorded_steps[-1].get("mode") == "move":
        points = _recorded_steps[-1].setdefault("points", [])
        if not points or points[-1] != point:
            points.append(point)
            _mark_last_action_now()
        _status = f"Appended route point {point} ({len(points)} total)."
        return
    _add_step({"type": "route", "name": "Route", "mode": "move", "points": [point]})
    _status = f"Started route at {point}."


def _record_interact_target(target: str) -> None:
    global _status
    target_id = int(Player.GetTargetID() or 0)
    if target_id <= 0 or not Agent.IsValid(target_id):
        _status = "No target selected."
        return
    if target == "npc" and (Agent.IsItem(target_id) or Agent.IsGadget(target_id) or target_id in AgentArray.GetEnemyArray()):
        _status = "Target is not an NPC."
        return
    if target == "gadget" and not Agent.IsGadget(target_id):
        _status = "Target is not a gadget."
        return
    if target == "item" and not Agent.IsItem(target_id):
        _status = "Target is not an item."
        return

    if target == "item":
        item_key, item_entry, item_name, model_id = _item_enum_entry(target_id)
        if item_key and item_entry:
            _captured_item_entries[item_key] = item_entry
        if model_id <= 0:
            _status = "Unable to resolve target item model_id."
            return
        _add_step({"type": "interact", "name": f"Pick {item_name}", "target": "item", "model_id": int(model_id)})
        _status = f"Recorded interact item model_id {model_id}."
        return

    key, entry, display_name = _capture_target_enum(target, target_id)
    x, y = Agent.GetXY(target_id)
    step: dict[str, Any] = {
        "type": "interact",
        "name": f"Interact {display_name or target.title()}",
        "target": target,
        "point": [int(x), int(y)],
    }
    if key and entry:
        if target == "npc":
            step["npc"] = key
        else:
            step["gadget"] = key
    _add_step(step)
    registry_status = _target_registry_action(target, key, entry)
    suffix = f" ({key}; {registry_status})" if key and registry_status else ""
    _status = f"Recorded interact {target}{suffix}."


def _record_enemy_blacklist(mode: str) -> None:
    global _status
    target_id = int(Player.GetTargetID() or 0)
    if target_id <= 0 or not Agent.IsValid(target_id) or target_id not in AgentArray.GetEnemyArray():
        _status = "Target is not an enemy."
        return
    key, entry, display_name = _capture_target_enum("enemy", target_id)
    if not key or not entry:
        _status = "Could not build enemy selector."
        return
    _add_step({"type": "behavior", "name": f"{mode.title()} {display_name}", "action": "enemy_blacklist", "mode": mode, "enemy": key})
    registry_status = _target_registry_action("enemy", key, entry)
    _status = f"Recorded enemy_blacklist {mode} for {display_name or key} ({registry_status})."


def _record_party_load() -> None:
    global _status
    party_size = int(Map.GetMaxPartySize() or 8)
    party_size = party_size if party_size in {4, 6, 8} else 8
    _add_step({"type": "party", "name": "Load Party", "action": "load", "max_heroes": party_size})
    _status = f"Recorded priority party load for max_heroes={party_size}."


def _grid_button(label: str, index: int, columns: int = 3, help_text: str = "") -> bool:
    clicked = PyImGui.button(label)
    if help_text and PyImGui.is_item_hovered():
        PyImGui.set_tooltip(help_text)
    if (index + 1) % columns != 0:
        PyImGui.same_line(0, 4)
    return clicked


def main() -> None:
    global _recipe_name, _relative_save_path, _auto_capture_dialogs, _recorded_steps, _status
    global _captured_npc_entries, _captured_enemy_entries, _captured_gadget_entries, _captured_item_entries
    global _dialog_last_tick, _last_action_ts, _exit_recording_active, _exit_recording_waiting_load
    global _travel_recording_active

    _poll_dialog_recorder()
    _poll_exit_map_recording()
    _poll_travel_recording()

    if not PyImGui.begin("Modular Script Helper"):
        PyImGui.end()
        return

    _recipe_name = PyImGui.input_text("Recipe Name", _recipe_name, 128)
    _relative_save_path = PyImGui.input_text("Save Path", _relative_save_path, 260)
    _auto_capture_dialogs = PyImGui.checkbox("Auto Capture Dialog Clicks", _auto_capture_dialogs)
    PyImGui.text(f"Recorded steps: {len(_recorded_steps)}")
    captured_enum_count = (
        len(_captured_npc_entries)
        + len(_captured_enemy_entries)
        + len(_captured_gadget_entries)
        + len(_captured_item_entries)
    )
    PyImGui.text(
        f"Captured enums: {captured_enum_count} "
        f"(npc {len(_captured_npc_entries)}, gadget {len(_captured_gadget_entries)}, "
        f"enemy {len(_captured_enemy_entries)}, item {len(_captured_item_entries)})"
    )

    PyImGui.separator()
    PyImGui.text("Export")
    if _grid_button("Copy JSON", 0, help_text="Copy full recipe JSON plus missing target-registry appendix."):
        PyImGui.set_clipboard_text(_recipe_json_with_appendix())
        _status = "Copied recipe JSON."
    if _grid_button("Copy Steps", 1, help_text="Copy recorded step objects only, one per line."):
        PyImGui.set_clipboard_text(_steps_text())
        _status = "Copied recorded steps."
    if _grid_button("Copy Enums", 2, help_text="Copy every captured NPC/gadget/enemy/item enum entry."):
        PyImGui.set_clipboard_text(_captured_enum_entries_text())
        _status = "Copied captured enum entries."
    if _grid_button("Save JSON", 0, help_text="Save recipe JSON under Sources/modular_data."):
        try:
            _status = f"Saved recipe to {_save_recipe()}."
        except Exception as exc:
            _status = f"Save failed: {exc}"
    if _grid_button("Clear", 1, help_text="Clear steps and captured registry appendix entries."):
        _recorded_steps = []
        _captured_npc_entries = {}
        _captured_enemy_entries = {}
        _captured_gadget_entries = {}
        _captured_item_entries = {}
        _dialog_last_tick = 0
        _sync_dialog_cursor_to_latest()
        _last_action_ts = None
        _exit_recording_active = False
        _exit_recording_waiting_load = False
        _travel_recording_active = False
        _status = "Recorder cleared."

    PyImGui.separator()
    PyImGui.text("Movement")
    if _grid_button("Route Point", 0, help_text="Append current player XY to the current route step or start a new route."):
        _record_route_point()
    if _grid_button("Exit Map", 1, help_text="Monitor portal transition and record a route exit step."):
        if _exit_recording_active:
            _status = "Exit-map recording is already active."
        else:
            _start_exit_map_recording()
    if _grid_button("Travel", 2, help_text="Monitor the next map change and record a map travel step."):
        if _travel_recording_active:
            _status = "Travel recording is already active."
        else:
            _start_travel_recording()
    if _grid_button("Wait", 0, help_text="Record a wait using elapsed time since the last recorded step."):
        wait_ms = _elapsed_wait_ms_since_last_action()
        _add_step({"type": "wait", "action": "wait", "ms": int(wait_ms)})
        _status = f"Recorded wait {wait_ms} ms."
    if _grid_button("Wait Map", 1, help_text="Record wait_for_map_load for the current map."):
        map_id = int(Map.GetMapID() or 0)
        if map_id <= 0:
            _status = "Unable to resolve current map id."
        else:
            _add_step({"type": "map", "action": "wait_for_map_load", "map_id": map_id})
            _status = f"Recorded wait_for_map_load for map_id {map_id}."

    PyImGui.text("Interaction")
    if _grid_button("NPC", 0):
        _record_interact_target("npc")
    if _grid_button("Gadget", 1):
        _record_interact_target("gadget")
    if _grid_button("Item", 2):
        _record_interact_target("item")

    PyImGui.text("Quest / Party / Behavior")
    if _grid_button("Party Load", 0):
        _record_party_load()
    if _grid_button("Resign", 1):
        _add_step({"type": "party", "action": "resign"})
        _status = "Recorded resign."
    if _grid_button("/kneel", 2):
        _add_step({"type": "wait", "action": "emote", "command": "kneel"})
        _status = "Recorded /kneel emote."
    if _grid_button("Anchor", 0):
        _add_step({"type": "wait", "name": "Anchor", "action": "wait", "ms": 100, "anchor": True})
        _status = "Recorded anchor checkpoint."
    if _grid_button("Blacklist Enemy", 1):
        _record_enemy_blacklist("add")
    if _grid_button("Unblacklist Enemy", 2):
        _record_enemy_blacklist("remove")
    if _grid_button("Flag Heroes", 0):
        x, y = Player.GetXY()
        _add_step(
            {
                "type": "party",
                "name": "Flag Heroes",
                "action": "flag_heroes",
                "point": [int(x), int(y)],
            }
        )
        _status = f"Recorded hero flag at [{int(x)}, {int(y)}]."
    if _grid_button("Unflag Heroes", 1):
        _add_step({"type": "party", "name": "Unflag Heroes", "action": "unflag_heroes"})
        _status = "Recorded hero unflag."

    if _exit_recording_active:
        phase = "waiting for map ready" if _exit_recording_waiting_load else "waiting for map load"
        PyImGui.text(f"Exit-map recorder: {phase}")
    if _travel_recording_active:
        PyImGui.text("Travel recorder: waiting for map change")
    if _status:
        PyImGui.text_wrapped(_status)

    PyImGui.separator()
    PyImGui.text("Quick Copy")
    player_x, player_y = Player.GetXY()
    map_id = int(Map.GetMapID() or 0)
    map_name = str(Map.GetMapName(map_id) or "")
    target_id = int(Player.GetTargetID() or 0)
    PyImGui.text(f"Player: {_fmt_xy(player_x, player_y)} | Map: [{map_id}] {map_name}")
    if _grid_button("Copy XY", 0):
        PyImGui.set_clipboard_text(_fmt_xy(player_x, player_y))
    if _grid_button("Copy Map", 1):
        PyImGui.set_clipboard_text(str(map_id))
    if target_id > 0 and Agent.IsValid(target_id):
        target_x, target_y = Agent.GetXY(target_id)
        PyImGui.text(f"Target: [{target_id}] {Agent.GetNameByID(target_id) or ''} @ {_fmt_xy(target_x, target_y)}")
        if _grid_button("Copy Target XY", 0, help_text="Copy targeted agent coordinates [x, y]."):
            PyImGui.set_clipboard_text(_fmt_xy(target_x, target_y))
        if _grid_button("Copy Target Key", 1, help_text="Copy encoded target registry key for the current target."):
            key, _entry, _name = _target_enum_entry(target_id)
            PyImGui.set_clipboard_text(key or "")
        if _grid_button("Copy Target Enum", 2, help_text="Copy encoded enum entry for the current target."):
            _key, entry, _name = _target_enum_entry(target_id)
            PyImGui.set_clipboard_text(entry or "")
        if Agent.IsItem(target_id):
            if _grid_button("Copy Item Enum", 0, help_text="Copy item enum entry for the targeted item model_id."):
                _item_key, item_entry, _item_name, _model_id = _item_enum_entry(target_id)
                PyImGui.set_clipboard_text(item_entry or "")

    options = _active_dialog_options()
    if options:
        PyImGui.separator()
        PyImGui.text("Active Dialog Options")
        for index, (dialog_id, message) in enumerate(options):
            PyImGui.text(f"0x{int(dialog_id):X}: {message[:96]}")
            PyImGui.same_line(0, 4)
            if PyImGui.button(f"Record##dialog_{dialog_id}_{index}"):
                _record_dialog_step(dialog_id)
                _status = f"Recorded dialog 0x{int(dialog_id):X}."
            PyImGui.same_line(0, 4)
            if PyImGui.button(f"Copy##dialog_{dialog_id}_{index}"):
                PyImGui.set_clipboard_text(f"0x{int(dialog_id):X}")

    PyImGui.end()
