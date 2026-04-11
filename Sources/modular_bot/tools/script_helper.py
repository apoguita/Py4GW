"""
Script Helper

Displays:
- Dialog recorder controls
- Player/target quick copy helpers
- Active dialog options
- Dialog click recorder (auto captures sent dialog ids)
"""

import json
import time

import PyAgent
import PyImGui

try:
    import PyDialog
except Exception:
    PyDialog = None

from Py4GWCoreLib import Agent, AgentArray, Botting, ConsoleLog, Item, Map, Party, Player
from Sources.modular_bot.recipes import mission_run
from Sources.modular_bot.recipes.modular_actions import register_step
from Sources.modular_bot.recipes.target_enums import ENEMY_TARGETS, GADGET_TARGETS, NPC_TARGETS


_TEST_MISSION_NAME = "script_helper"
_test_bot = Botting("ScriptHelperTestRunner")
_test_running = False
_replay_bot = Botting("ModularBotHelperReplay")
_replay_running = False
_replay_status = ""
_replay_steps_payload: list[dict] | None = None

_dialog_copy_status = ""
_dialog_init_attempted = False
_dialog_init_ok = False

_dialog_recorder_enabled = True
_dialog_last_tick = 0
_dialog_recorder_steps: list[dict] = []
_dialog_recorder_npc_entries: dict[str, str] = {}
_dialog_recorder_enemy_entries: dict[str, str] = {}
_dialog_recorder_gadget_entries: dict[str, str] = {}
_dialog_recorder_item_entries: dict[str, str] = {}
_dialog_recorder_status = ""
_dialog_recorder_last_action_ts: float | None = None
_exit_recording_active = False
_exit_recording_waiting_load = False
_exit_record_start_x = 0
_exit_record_start_y = 0
_exit_record_last_x = 0
_exit_record_last_y = 0
_exit_record_source_map_id = 0
_exit_record_source_map_name = ""
_travel_recording_active = False
_travel_record_source_map_id = 0
_travel_record_source_map_name = ""

DEBUG_LOGGING = False


def _debug_log(message: str) -> None:
    if not DEBUG_LOGGING:
        return
    ConsoleLog("Script Helper", message)


def _sync_engine_upkeep(bot: Botting) -> None:
    """Keep helper runner from unintentionally toggling HeroAI off."""
    try:
        from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

        handler = get_widget_handler()
        hero_ai_enabled = bool(handler.is_widget_enabled("HeroAI"))
        if bot.Properties.exists("hero_ai"):
            bot.Properties.ApplyNow("hero_ai", "active", hero_ai_enabled)
        if hero_ai_enabled and bot.Properties.exists("auto_combat"):
            bot.Properties.ApplyNow("auto_combat", "active", False)
    except Exception as exc:
        _debug_log(f"Engine upkeep sync failed: {exc}")


def _run_test_mission(bot: Botting) -> None:
    mission_run(bot, _TEST_MISSION_NAME)


_test_bot.SetMainRoutine(_run_test_mission)


def _prepare_replay_step(step: dict) -> dict:
    replay_step = dict(step)
    step_type = str(replay_step.get("type", "") or "").strip().lower()

    if step_type in ("path", "auto_path", "auto_path_delayed"):
        replay_step.setdefault("wait_for_loot", True)
    if step_type in ("auto_path", "auto_path_delayed"):
        replay_step.setdefault("pause_on_combat", True)

    return replay_step


def _run_replay(bot: Botting) -> None:
    global _replay_steps_payload
    bot.States.AddCustomState(lambda: None, "Replay Guard")
    if not _replay_steps_payload:
        return

    step_idx = 0
    register_step(bot, {"type": "set_auto_combat", "enabled": True, "name": "Replay: Combat On"}, step_idx, "Replay")
    step_idx += 1
    register_step(
        bot,
        {"type": "set_auto_looting", "enabled": True, "name": "Replay: Looting On"},
        step_idx,
        "Replay",
    )
    step_idx += 1

    for source_step in _replay_steps_payload:
        if not isinstance(source_step, dict):
            continue
        prepared = _prepare_replay_step(source_step)
        register_step(bot, prepared, step_idx, "Replay")
        step_idx += 1

    _replay_steps_payload = None


_replay_bot.SetMainRoutine(_run_replay)


def _fmt_xy(x: float, y: float) -> str:
    return f"[{int(x)}, {int(y)}]"


def _enum_key_from_name(name: str, default_prefix: str) -> str:
    cleaned = []
    previous_was_underscore = False
    for ch in (name or "").upper():
        if ch.isalnum():
            cleaned.append(ch)
            previous_was_underscore = False
            continue
        if not previous_was_underscore:
            cleaned.append("_")
            previous_was_underscore = True
    key = "".join(cleaned).strip("_")
    return key or default_prefix


def _fmt_target_enum_entry(agent_id: int) -> str:
    enc_name = PyAgent.PyAgent.GetAgentEncName(agent_id) or []
    display_name = Agent.GetNameByID(agent_id) or ""
    enc_name_str = ", ".join(str(int(value)) for value in enc_name)
    enum_key = _enum_key_from_name(display_name, "TARGET")
    safe_display_name = display_name.replace("\\", "\\\\").replace('"', '\\"')
    return f"\"{enum_key}\": ((({enc_name_str}),), \"{safe_display_name}\"),"


def _fmt_item_enum_entry(agent_id: int) -> str:
    item_id = int(Agent.GetItemAgentItemID(agent_id))
    model_id = int(Item.GetModelID(item_id)) if item_id > 0 else 0
    display_name = Agent.GetNameByID(agent_id) or (f"Item {model_id}" if model_id > 0 else "Item")
    enum_key = _enum_key_from_name(display_name, "ITEM")
    safe_display_name = display_name.replace("\\", "\\\\").replace('"', '\\"')
    return f"\"{enum_key}\": ({model_id}, \"{safe_display_name}\"),"


def _build_target_item_enum_and_model(agent_id: int) -> tuple[str | None, str | None, str, int]:
    if agent_id <= 0 or not Agent.IsValid(agent_id) or not Agent.IsItem(agent_id):
        return None, None, "", 0
    item_id = int(Agent.GetItemAgentItemID(agent_id))
    model_id = int(Item.GetModelID(item_id)) if item_id > 0 else 0
    display_name = Agent.GetNameByID(agent_id) or (f"Item {model_id}" if model_id > 0 else "Item")
    enum_key = _enum_key_from_name(display_name, "ITEM")
    safe_display_name = display_name.replace("\\", "\\\\").replace('"', '\\"')
    enum_entry = f"\"{enum_key}\": ({model_id}, \"{safe_display_name}\"),"
    return enum_key, enum_entry, display_name, model_id


def _ensure_dialog_initialized() -> bool:
    global _dialog_init_attempted, _dialog_init_ok
    if PyDialog is None or not hasattr(PyDialog, "PyDialog"):
        return False

    if _dialog_init_attempted:
        return _dialog_init_ok

    _dialog_init_attempted = True
    try:
        init_fn = getattr(PyDialog.PyDialog, "initialize", None)
        if init_fn is not None:
            init_fn()
        _dialog_init_ok = True
    except Exception as exc:
        _dialog_init_ok = False
        _debug_log(f"PyDialog initialize failed: {exc}")
    return _dialog_init_ok


def _get_active_dialog_options() -> list[tuple[int, str]]:
    if not _ensure_dialog_initialized():
        return []

    getter = getattr(PyDialog.PyDialog, "get_active_dialog_buttons", None)
    if getter is None:
        return []

    raw_buttons = getter() or []
    options: list[tuple[int, str]] = []
    seen: set[int] = set()
    for button in raw_buttons:
        dialog_id = int(getattr(button, "dialog_id", 0) or 0)
        if dialog_id <= 0 or dialog_id in seen:
            continue
        seen.add(dialog_id)
        message = str(getattr(button, "message_decoded", "") or getattr(button, "message", "") or "").strip()
        options.append((dialog_id, message))
    return options


def _build_target_npc_enum() -> tuple[str | None, str | None, str]:
    target_id = int(Player.GetTargetID() or 0)
    if target_id <= 0 or not Agent.IsValid(target_id):
        return None, None, ""

    display_name = Agent.GetNameByID(target_id) or ""
    enum_key = _enum_key_from_name(display_name, "NPC")
    enc_name = PyAgent.PyAgent.GetAgentEncName(target_id) or []
    enc_name_str = ", ".join(str(int(value)) for value in enc_name)
    safe_display_name = display_name.replace("\\", "\\\\").replace('"', '\\"')
    enum_entry = f"\"{enum_key}\": ((({enc_name_str}),), \"{safe_display_name}\"),"
    return enum_key, enum_entry, display_name


def _build_target_gadget_enum() -> tuple[str | None, str | None, str]:
    target_id = int(Player.GetTargetID() or 0)
    if target_id <= 0 or not Agent.IsValid(target_id) or not Agent.IsGadget(target_id):
        return None, None, ""

    display_name = Agent.GetNameByID(target_id) or "Gadget"
    enum_key = _enum_key_from_name(display_name, "GADGET")
    enc_name = PyAgent.PyAgent.GetAgentEncName(target_id) or []
    enc_name_str = ", ".join(str(int(value)) for value in enc_name)
    safe_display_name = display_name.replace("\\", "\\\\").replace('"', '\\"')
    enum_entry = f"\"{enum_key}\": ((({enc_name_str}),), \"{safe_display_name}\"),"
    return enum_key, enum_entry, display_name


def _build_target_enemy_enum() -> tuple[str | None, str | None, str]:
    target_id = int(Player.GetTargetID() or 0)
    if target_id <= 0 or not Agent.IsValid(target_id):
        return None, None, ""
    if Agent.IsItem(target_id) or Agent.IsGadget(target_id):
        return None, None, ""
    if target_id not in AgentArray.GetEnemyArray():
        return None, None, ""

    display_name = Agent.GetNameByID(target_id) or "Enemy"
    enum_key = _enum_key_from_name(display_name, "ENEMY")
    enc_name = PyAgent.PyAgent.GetAgentEncName(target_id) or []
    enc_name_str = ", ".join(str(int(value)) for value in enc_name)
    safe_display_name = display_name.replace("\\", "\\\\").replace('"', '\\"')
    enum_entry = f"\"{enum_key}\": ((({enc_name_str}),), \"{safe_display_name}\"),"
    return enum_key, enum_entry, display_name


def _append_dialog_recorder_step(dialog_id: int) -> None:
    global _dialog_recorder_steps
    npc_key, enum_entry, display_name = _build_target_npc_enum()
    if npc_key and enum_entry:
        _dialog_recorder_npc_entries[npc_key] = enum_entry
        base_selector = {"npc": npc_key}
    else:
        base_selector = {"nearest": True}

    new_id = f"0x{int(dialog_id):X}"
    step = {"type": "dialog", "id": new_id}
    step.update(base_selector)
    if display_name:
        step["name"] = f"Dialog - {display_name}"

    merged = False
    if _dialog_recorder_steps:
        last = _dialog_recorder_steps[-1]
        same_npc = False
        if "npc" in base_selector:
            same_npc = last.get("npc") == base_selector["npc"]
        elif "nearest" in base_selector:
            same_npc = bool(last.get("nearest", False))

        if same_npc:
            if last.get("type") == "dialog":
                previous_id = str(last.get("id", "")).strip()
                upgraded = {"type": "dialogs", "id": [previous_id, new_id]}
                if "npc" in base_selector:
                    upgraded["npc"] = base_selector["npc"]
                else:
                    upgraded["nearest"] = True
                if last.get("name"):
                    upgraded["name"] = last["name"]
                _dialog_recorder_steps[-1] = upgraded
                merged = True
            elif last.get("type") == "dialogs":
                ids = last.get("id")
                if isinstance(ids, list):
                    ids.append(new_id)
                    merged = True

    if not merged:
        _add_recorded_step(step)


def _poll_dialog_recorder() -> None:
    global _dialog_last_tick, _dialog_recorder_status
    if not _dialog_recorder_enabled:
        return
    if not _ensure_dialog_initialized():
        return

    getter = getattr(PyDialog.PyDialog, "get_dialog_callback_journal_sent", None)
    if getter is None:
        return

    entries = getter() or []
    max_tick = _dialog_last_tick
    captured = 0
    for entry in entries:
        tick = int(getattr(entry, "tick", 0) or 0)
        if tick <= _dialog_last_tick:
            continue
        max_tick = max(max_tick, tick)

        if str(getattr(entry, "event_type", "") or "") != "sent_choice":
            continue
        dialog_id = int(getattr(entry, "dialog_id", 0) or 0)
        if dialog_id <= 0:
            continue

        _append_dialog_recorder_step(dialog_id)
        captured += 1

    _dialog_last_tick = max_tick
    if captured > 0:
        _dialog_recorder_status = f"Captured {captured} dialog click(s)."


def _sync_dialog_journal_cursor_to_latest() -> None:
    """
    Advance recorder cursor to the latest known dialog journal tick.
    This prevents old entries from being recaptured after clearing.
    """
    global _dialog_last_tick
    if not _ensure_dialog_initialized():
        return
    getter = getattr(PyDialog.PyDialog, "get_dialog_callback_journal_sent", None)
    if getter is None:
        return
    entries = getter() or []
    if not entries:
        return
    latest_tick = max(int(getattr(entry, "tick", 0) or 0) for entry in entries)
    _dialog_last_tick = max(_dialog_last_tick, latest_tick)


def _dialog_recorder_npc_data_text() -> str:
    lines: list[str] = []
    if _dialog_recorder_npc_entries:
        ordered_npc = sorted(_dialog_recorder_npc_entries.items(), key=lambda kv: kv[0])
        lines.extend(value for _, value in ordered_npc)
    if _dialog_recorder_enemy_entries:
        ordered_enemy = sorted(_dialog_recorder_enemy_entries.items(), key=lambda kv: kv[0])
        lines.extend(value for _, value in ordered_enemy)
    if _dialog_recorder_gadget_entries:
        ordered_gadget = sorted(_dialog_recorder_gadget_entries.items(), key=lambda kv: kv[0])
        lines.extend(value for _, value in ordered_gadget)
    if _dialog_recorder_item_entries:
        ordered_item = sorted(_dialog_recorder_item_entries.items(), key=lambda kv: kv[0])
        lines.extend(value for _, value in ordered_item)
    if not lines:
        return ""
    return "\n".join(lines)


def _dialog_recorder_payload() -> str:
    lines = ["{", '  "name": "dialog_recorded",', '  "steps": [']
    step_lines = _dialog_recorder_steps_single_line_list()
    for index, line in enumerate(step_lines):
        suffix = "," if index < len(step_lines) - 1 else ""
        lines.append(f"    {line}{suffix}")
    lines.append("  ]")
    lines.append("}")
    return "\n".join(lines)


def _collect_used_selector_keys() -> tuple[set[str], set[str], set[str]]:
    used_npcs: set[str] = set()
    used_enemies: set[str] = set()
    used_gadgets: set[str] = set()
    for step in _dialog_recorder_steps:
        if not isinstance(step, dict):
            continue
        npc_value = step.get("npc")
        enemy_value = step.get("enemy")
        gadget_value = step.get("gadget")
        if isinstance(npc_value, str) and npc_value.strip():
            used_npcs.add(npc_value.strip())
        if isinstance(enemy_value, str) and enemy_value.strip():
            used_enemies.add(enemy_value.strip())
        if isinstance(gadget_value, str) and gadget_value.strip():
            used_gadgets.add(gadget_value.strip())
    return used_npcs, used_enemies, used_gadgets


def _captured_entry_encoded_tuple(entry: str) -> tuple[int, ...] | None:
    try:
        start = entry.index("(((") + 3
        end = entry.index("),),", start)
    except ValueError:
        return None

    raw_numbers = entry[start:end]
    values: list[int] = []
    for token in raw_numbers.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            values.append(int(token))
        except ValueError:
            return None
    if not values:
        return None
    return tuple(values)


def _registry_encoded_tuples(value: object) -> set[tuple[int, ...]]:
    encoded_set: set[tuple[int, ...]] = set()

    if value is None:
        return encoded_set

    # AgentTargetDefinition path
    encoded_names = getattr(value, "encoded_names", None)
    if isinstance(encoded_names, tuple):
        for encoded in encoded_names:
            if isinstance(encoded, tuple) and encoded:
                try:
                    encoded_set.add(tuple(int(v) for v in encoded))
                except Exception:
                    pass
        if encoded_set:
            return encoded_set

    # Legacy tuple path: (encoded_names_raw, display_name)
    if isinstance(value, tuple) and len(value) == 2:
        encoded_names_raw = value[0]
        if isinstance(encoded_names_raw, tuple):
            if encoded_names_raw and all(isinstance(v, int) for v in encoded_names_raw):
                encoded_set.add(tuple(int(v) for v in encoded_names_raw))
                return encoded_set
            for encoded in encoded_names_raw:
                if isinstance(encoded, tuple) and encoded:
                    try:
                        encoded_set.add(tuple(int(v) for v in encoded))
                    except Exception:
                        pass
    return encoded_set


def _missing_and_extend_keys(
    used_keys: set[str],
    captured_entries: dict[str, str],
    registry: dict[str, object],
) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    extend: list[str] = []
    for key in sorted(used_keys):
        if key not in registry:
            missing.append(key)
            continue

        captured_entry = captured_entries.get(key)
        if not captured_entry:
            continue
        captured_encoded = _captured_entry_encoded_tuple(captured_entry)
        if captured_encoded is None:
            continue
        existing = _registry_encoded_tuples(registry.get(key))
        if captured_encoded not in existing:
            extend.append(key)
    return missing, extend


def _missing_enum_appendix_text() -> str:
    used_npcs, used_enemies, used_gadgets = _collect_used_selector_keys()
    missing_enemies, extend_enemies = _missing_and_extend_keys(used_enemies, _dialog_recorder_enemy_entries, ENEMY_TARGETS)
    missing_gadgets, extend_gadgets = _missing_and_extend_keys(used_gadgets, _dialog_recorder_gadget_entries, GADGET_TARGETS)
    missing_npcs, extend_npcs = _missing_and_extend_keys(used_npcs, _dialog_recorder_npc_entries, NPC_TARGETS)

    lines: list[str] = []
    lines.append("")
    lines.append("#ADD/EXTEND these ENEMIES to modularBot")
    if missing_enemies or extend_enemies:
        for key in missing_enemies + extend_enemies:
            entry = _dialog_recorder_enemy_entries.get(key)
            if entry:
                lines.append(entry)
            else:
                lines.append(f'# MISSING_CAPTURE: "{key}"')
    else:
        lines.append("# none")

    lines.append("")
    lines.append("#ADD/EXTEND these GADGETS to modularBot")
    if missing_gadgets or extend_gadgets:
        for key in missing_gadgets + extend_gadgets:
            entry = _dialog_recorder_gadget_entries.get(key)
            if entry:
                lines.append(entry)
            else:
                lines.append(f'# MISSING_CAPTURE: "{key}"')
    else:
        lines.append("# none")

    lines.append("")
    lines.append("#ADD/EXTEND these NPCs to modularBot")
    if missing_npcs or extend_npcs:
        for key in missing_npcs + extend_npcs:
            entry = _dialog_recorder_npc_entries.get(key)
            if entry:
                lines.append(entry)
            else:
                lines.append(f'# MISSING_CAPTURE: "{key}"')
    else:
        lines.append("# none")

    return "\n".join(lines)


def _dialog_recorder_payload_with_appendix() -> str:
    return _dialog_recorder_payload() + _missing_enum_appendix_text()


def _dialog_recorder_steps_single_line_list() -> list[str]:
    return [json.dumps(step, separators=(", ", ": ")) for step in _dialog_recorder_steps]


def _dialog_recorder_steps_single_line_text() -> str:
    return "\n".join(_dialog_recorder_steps_single_line_list())


def _extract_subject_from_step_name(step_name: str, prefixes: tuple[str, ...]) -> str:
    raw = str(step_name or "").strip()
    for prefix in prefixes:
        if raw.lower().startswith(prefix.lower()):
            subject = raw[len(prefix):].strip(" -")
            return subject
    return raw


def _prettify_selector_label(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    text = raw.replace("_", " ").strip()
    if text.upper() == text:
        return text.title()
    return text


def _infer_autopath_name_from_follow_step(step: dict) -> str:
    step_type = str(step.get("type", "") or "").strip().lower()
    step_name = str(step.get("name", "") or "").strip()

    if step_type in ("dialog", "dialogs"):
        if "npc" in step:
            return f"To {_prettify_selector_label(step['npc'])}"
        subject = _extract_subject_from_step_name(step_name, ("Dialog",))
        return f"To {subject}" if subject else "To Dialog"
    if step_type == "interact_gadget":
        if "gadget" in step:
            return f"To {_prettify_selector_label(step['gadget'])}"
        subject = _extract_subject_from_step_name(step_name, ("Interact",))
        return f"To {subject}" if subject else "To Gadget"
    if step_type in ("interact_npc", "interact_quest_npc", "interact_nearest_npc"):
        if "npc" in step:
            return f"To {_prettify_selector_label(step['npc'])}"
        if "target" in step:
            return f"To {_prettify_selector_label(step['target'])}"
        return "To NPC"
    if step_type == "interact_item":
        return "To Item"
    if step_type == "exit_map":
        return "To Exit"
    if step_type == "travel":
        return "To Travel"
    if step_name:
        return f"To {step_name}"
    return "Path"


def _apply_name_to_previous_open_autopath(follow_step: dict) -> None:
    if not _dialog_recorder_steps:
        return
    last = _dialog_recorder_steps[-1]
    if str(last.get("type", "")).strip().lower() != "auto_path":
        return
    if str(last.get("name", "")).strip():
        return
    last["name"] = _infer_autopath_name_from_follow_step(follow_step)


def _add_recorded_step(step: dict) -> None:
    global _dialog_recorder_last_action_ts
    step_type = str(step.get("type", "") or "").strip().lower()
    if step_type != "auto_path":
        _apply_name_to_previous_open_autopath(step)
    _dialog_recorder_steps.append(step)
    _dialog_recorder_last_action_ts = time.monotonic()


def _mark_last_action_now() -> None:
    global _dialog_recorder_last_action_ts
    _dialog_recorder_last_action_ts = time.monotonic()


def _elapsed_wait_ms_since_last_action(default_ms: int = 1000) -> int:
    if _dialog_recorder_last_action_ts is None:
        return int(default_ms)
    elapsed_ms = int((time.monotonic() - _dialog_recorder_last_action_ts) * 1000.0)
    # Keep generated waits practical and readable.
    elapsed_ms = max(100, elapsed_ms)
    return int(round(elapsed_ms / 100.0) * 100)


def _build_load_party_step(minionless: bool = False) -> dict:
    party_size = int(Map.GetMaxPartySize() or 0)
    if party_size <= 0:
        party_size = int(Party.GetPartySize() or 0)
    if party_size >= 8:
        max_heroes = 8
        team = "party_8"
    elif party_size >= 6:
        max_heroes = 6
        team = "party_6_no_spirits_minions" if minionless else "party_6"
    elif party_size >= 4:
        max_heroes = 4
        team = "party_4"
    else:
        max_heroes = 6
        team = "party_6_no_spirits_minions" if minionless else "party_6"

    step = {
        "type": "load_party",
        "name": "Load Party",
        "max_heroes": int(max_heroes),
        "team": team,
    }
    if minionless:
        step["minionless"] = True
    return step


def _start_exit_map_recording() -> None:
    global _exit_recording_active, _exit_recording_waiting_load
    global _exit_record_start_x, _exit_record_start_y, _exit_record_last_x, _exit_record_last_y
    global _exit_record_source_map_id, _exit_record_source_map_name
    global _dialog_recorder_status

    x, y = Player.GetXY()
    _exit_record_start_x = int(x)
    _exit_record_start_y = int(y)
    _exit_record_last_x = int(x)
    _exit_record_last_y = int(y)
    _exit_record_source_map_id = int(Map.GetMapID() or 0)
    _exit_record_source_map_name = str(Map.GetMapName(_exit_record_source_map_id) or "").strip()
    _exit_recording_active = True
    _exit_recording_waiting_load = False
    _dialog_recorder_status = (
        f"Exit-map recording started at [{_exit_record_start_x}, {_exit_record_start_y}]. "
        "Waiting for 0,0 (map load)."
    )


def _poll_exit_map_recording() -> None:
    global _exit_recording_active, _exit_recording_waiting_load, _dialog_recorder_status
    global _exit_record_last_x, _exit_record_last_y
    if not _exit_recording_active:
        return

    if not _exit_recording_waiting_load:
        x, y = Player.GetXY()
        ix, iy = int(x), int(y)
        if ix != 0 or iy != 0:
            _exit_record_last_x = ix
            _exit_record_last_y = iy
        if ix == 0 and iy == 0:
            _exit_recording_waiting_load = True
            _dialog_recorder_status = (
                f"Exit-map recording: load detected at 0,0. "
                f"Using last pre-load xy [{_exit_record_last_x}, {_exit_record_last_y}]. "
                "Waiting for map ready."
            )
        return

    if not Map.IsMapReady():
        return

    target_map_id = int(Map.GetMapID() or 0)
    if target_map_id <= 0:
        return

    if target_map_id == int(_exit_record_source_map_id):
        _exit_recording_active = False
        _exit_recording_waiting_load = False
        _dialog_recorder_status = "Exit-map recording canceled (map did not change)."
        return

    name_suffix = _exit_record_source_map_name or str(_exit_record_source_map_id or "Map")
    step = {
        "type": "exit_map",
        "name": f"Leave {name_suffix}",
        "x": int(_exit_record_last_x),
        "y": int(_exit_record_last_y),
        "target_map_id": int(target_map_id),
    }
    _add_recorded_step(step)
    _exit_recording_active = False
    _exit_recording_waiting_load = False
    _dialog_recorder_status = f"Recorded exit_map to target_map_id {target_map_id}."


def _start_travel_recording() -> None:
    global _travel_recording_active, _travel_record_source_map_id, _travel_record_source_map_name, _dialog_recorder_status
    _travel_record_source_map_id = int(Map.GetMapID() or 0)
    _travel_record_source_map_name = str(Map.GetMapName(_travel_record_source_map_id) or "").strip()
    _travel_recording_active = True
    _dialog_recorder_status = f"Travel recording started from map {_travel_record_source_map_id}. Travel now..."


def _poll_travel_recording() -> None:
    global _travel_recording_active, _dialog_recorder_status
    if not _travel_recording_active:
        return
    if not Map.IsMapReady():
        return

    current_map_id = int(Map.GetMapID() or 0)
    if current_map_id <= 0 or current_map_id == int(_travel_record_source_map_id):
        return

    destination_map_name = str(Map.GetMapName(current_map_id) or "").strip()
    step = {
        "type": "travel",
        "name": f"Travel to {destination_map_name or current_map_id}",
        "target_map_id": int(current_map_id),
    }
    _add_recorded_step(step)
    _travel_recording_active = False
    _dialog_recorder_status = f"Recorded travel to target_map_id {current_map_id}."


def _grid_button(label: str, index: int, columns: int = 3, help_text: str = "") -> bool:
    clicked = PyImGui.button(label)
    if help_text and PyImGui.is_item_hovered():
        PyImGui.set_tooltip(help_text)
    if (index + 1) % columns != 0:
        PyImGui.same_line(0, 4)
    return clicked


def main():
    global _test_running, _replay_running, _replay_status
    global _dialog_copy_status, _dialog_recorder_enabled, _dialog_recorder_status
    global _dialog_recorder_steps, _dialog_recorder_npc_entries, _dialog_recorder_enemy_entries
    global _dialog_recorder_gadget_entries, _dialog_recorder_item_entries, _dialog_last_tick
    global _dialog_recorder_last_action_ts
    global _exit_recording_active, _exit_recording_waiting_load
    global _travel_recording_active
    global _replay_steps_payload

    _poll_dialog_recorder()
    _poll_exit_map_recording()
    _poll_travel_recording()

    if PyImGui.begin("ModularBot Helper"):
        PyImGui.text("Dialog Recorder")
        _dialog_recorder_enabled = PyImGui.checkbox("Auto Capture Clicked Dialogs", _dialog_recorder_enabled)
        PyImGui.text(f"Recorded steps: {len(_dialog_recorder_steps)}")

        PyImGui.text("Copy/Clear")
        if _grid_button("Copy Recorder JSON", 0, help_text="Copy mission JSON plus missing ENEMY/NPC/GADGET appendix."):
            PyImGui.set_clipboard_text(_dialog_recorder_payload_with_appendix())
            _dialog_recorder_status = "Copied recorder JSON."
        if _grid_button("Copy Recorder Steps", 1, help_text="Copy recorded steps only, one JSON object per line."):
            PyImGui.set_clipboard_text(_dialog_recorder_steps_single_line_text())
            _dialog_recorder_status = "Copied recorder steps."
        if _grid_button("Clear Recorder", 2, help_text="Reset recorded steps, captured enums, and active monitors."):
            _dialog_recorder_steps = []
            _dialog_recorder_npc_entries = {}
            _dialog_recorder_enemy_entries = {}
            _dialog_recorder_gadget_entries = {}
            _dialog_recorder_item_entries = {}
            _dialog_last_tick = 0
            _sync_dialog_journal_cursor_to_latest()
            _dialog_recorder_last_action_ts = None
            _exit_recording_active = False
            _exit_recording_waiting_load = False
            _travel_recording_active = False
            _dialog_recorder_status = "Dialog recorder cleared (old dialog journal entries ignored)."

        PyImGui.text("Replay")
        if _grid_button("Replay Recorded Steps", 0, 2, help_text="Execute recorded steps with active combat-engine hooks."):
            if not _dialog_recorder_steps:
                _replay_status = "Replay skipped: no recorded steps."
            else:
                try:
                    _replay_bot.Stop()
                    _replay_bot.config.initialized = False
                    _replay_bot.config.FSM.reset()
                    _sync_engine_upkeep(_replay_bot)
                    payload = [dict(step) for step in _dialog_recorder_steps if isinstance(step, dict)]
                    _replay_steps_payload = payload
                    _replay_bot.Start()
                    _replay_running = True
                    _replay_status = f"Replay started ({len(payload)} step(s))."
                except Exception as exc:
                    _replay_running = False
                    _replay_status = f"Replay failed to start: {exc}"
        if _grid_button("Stop Replay", 1, 2, help_text="Stop replay runner immediately."):
            _replay_bot.Stop()
            _replay_running = False
            _replay_steps_payload = None
            _replay_status = "Replay stopped."
        if _replay_status:
            PyImGui.text_wrapped(_replay_status)

        PyImGui.text("Record Actions")
        PyImGui.text("Movement")
        if _grid_button("Record AutoPath", 0, help_text="Add current player XY to the active auto_path (or start a new one)."):
            px, py = Player.GetXY()
            ix, iy = int(px), int(py)
            if _dialog_recorder_steps and str(_dialog_recorder_steps[-1].get("type", "")).strip().lower() == "auto_path":
                points = _dialog_recorder_steps[-1].setdefault("points", [])
                if not points or points[-1] != [ix, iy]:
                    points.append([ix, iy])
                    _mark_last_action_now()
                _dialog_recorder_status = f"Appended auto_path point [{ix}, {iy}] ({len(points)} total)."
            else:
                step = {
                    "type": "auto_path",
                    "name": "",
                    "points": [[ix, iy]],
                }
                _add_recorded_step(step)
                _dialog_recorder_status = f"Started auto_path with point [{ix}, {iy}]."
        if _grid_button("Record Exit Map", 1, help_text="Track movement into portal and record exit_map with last pre-load XY + target map."):
            if _exit_recording_active:
                _dialog_recorder_status = "Exit-map recording already active."
            else:
                _start_exit_map_recording()
        if _grid_button("Record Map Travel", 2, help_text="Record a travel step after map changes to a new loaded map."):
            if _travel_recording_active:
                _dialog_recorder_status = "Travel recording already active."
            else:
                _start_travel_recording()
        if _grid_button("Record Wait", 0, help_text="Add wait using elapsed time since last recorded action."):
            wait_ms = _elapsed_wait_ms_since_last_action(default_ms=1000)
            step = {"type": "wait", "ms": int(wait_ms)}
            _add_recorded_step(step)
            _dialog_recorder_status = f"Recorded wait: {int(wait_ms)} ms."
        if _grid_button("Record wait_for_map_load", 1, help_text="Add wait_for_map_load with the current map id."):
            current_map_id = int(Map.GetMapID() or 0)
            if current_map_id <= 0:
                _dialog_recorder_status = "Unable to resolve current map id."
            else:
                step = {"type": "wait_for_map_load", "map_id": int(current_map_id)}
                _add_recorded_step(step)
                _dialog_recorder_status = f"Recorded wait_for_map_load for map_id {int(current_map_id)}."
        if _grid_button("Record skip_cutscene", 2, help_text="Add skip_cutscene step (alias of skip_cinematic)."):
            step = {"type": "skip_cutscene"}
            _add_recorded_step(step)
            _dialog_recorder_status = "Recorded skip_cutscene."

        PyImGui.text("Interactions")
        if _grid_button("Record Interact NPC", 0, help_text="Requires targeted NPC/ally. Records interact_npc using captured NPC selector."):
            target_id = int(Player.GetTargetID() or 0)
            if target_id <= 0 or not Agent.IsValid(target_id):
                _dialog_recorder_status = "No target selected."
            elif Agent.IsItem(target_id) or Agent.IsGadget(target_id) or target_id in AgentArray.GetEnemyArray():
                _dialog_recorder_status = "Target is not an NPC."
            else:
                npc_key, npc_entry, npc_name = _build_target_npc_enum()
                if npc_key and npc_entry:
                    _dialog_recorder_npc_entries[npc_key] = npc_entry
                    step = {
                        "type": "interact_npc",
                        "name": f"Interact {npc_name or 'NPC'}",
                        "npc": npc_key,
                    }
                else:
                    nx, ny = Agent.GetXY(target_id)
                    step = {
                        "type": "interact_npc",
                        "name": "Interact NPC",
                        "x": int(nx),
                        "y": int(ny),
                    }
                _add_recorded_step(step)
                _dialog_recorder_status = f"Recorded interact_npc for {npc_name or 'target'}."
        if _grid_button("Record Interact Nearby NPC", 1, help_text="Add interact_npc step that targets nearest NPC within 1000 range."):
            step = {"type": "interact_npc", "nearest": True, "max_dist": 1000}
            _add_recorded_step(step)
            _dialog_recorder_status = "Recorded interact_npc nearest (max_dist=1000)."
        if _grid_button("Record Interact Gadget", 2, help_text="Requires targeted gadget. Records selector key + exact XY."):
            target_id = int(Player.GetTargetID() or 0)
            if target_id <= 0 or not Agent.IsValid(target_id):
                _dialog_recorder_status = "No target selected."
            elif not Agent.IsGadget(target_id):
                _dialog_recorder_status = "Target is not a gadget."
            else:
                gx, gy = Agent.GetXY(target_id)
                gadget_key, gadget_entry, gadget_name = _build_target_gadget_enum()
                if gadget_key and gadget_entry:
                    _dialog_recorder_gadget_entries[gadget_key] = gadget_entry
                    step = {
                        "type": "interact_gadget",
                        "name": f"Interact {gadget_name}",
                        "gadget": gadget_key,
                        "x": int(gx),
                        "y": int(gy),
                    }
                else:
                    step = {
                        "type": "interact_gadget",
                        "name": "Interact Gadget",
                        "x": int(gx),
                        "y": int(gy),
                    }
                _add_recorded_step(step)
                _dialog_recorder_status = f"Recorded interact_gadget at [{int(gx)}, {int(gy)}]."
        if _grid_button("Record Item", 0, help_text="Requires targeted item. Records interact_item with model_id."):
            target_id = int(Player.GetTargetID() or 0)
            if target_id <= 0 or not Agent.IsValid(target_id):
                _dialog_recorder_status = "No target selected."
            elif not Agent.IsItem(target_id):
                _dialog_recorder_status = "Target is not an item."
            else:
                item_key, item_entry, item_name, model_id = _build_target_item_enum_and_model(target_id)
                if item_key and item_entry:
                    _dialog_recorder_item_entries[item_key] = item_entry
                if model_id <= 0:
                    _dialog_recorder_status = "Unable to resolve target item model_id."
                else:
                    step = {
                        "type": "interact_item",
                        "name": f"Pick {item_name}",
                        "model_id": int(model_id),
                    }
                    _add_recorded_step(step)
                    _dialog_recorder_status = f"Recorded interact_item model_id {int(model_id)}."
        if _grid_button("Record Enemy", 0, help_text="Requires targeted enemy. Records target_enemy using captured enemy selector."):
            target_id = int(Player.GetTargetID() or 0)
            if target_id <= 0 or not Agent.IsValid(target_id):
                _dialog_recorder_status = "No target selected."
            elif Agent.IsItem(target_id) or Agent.IsGadget(target_id) or target_id not in AgentArray.GetEnemyArray():
                _dialog_recorder_status = "Target is not an enemy."
            else:
                enemy_key, enemy_entry, enemy_name = _build_target_enemy_enum()
                if enemy_key and enemy_entry:
                    _dialog_recorder_enemy_entries[enemy_key] = enemy_entry
                    step = {
                        "type": "path_to_target",
                        "name": f"Target {enemy_name}",
                        "enemy": enemy_key,
                    }
                else:
                    model_id = int(Agent.GetModelID(target_id) or 0)
                    target_name = str(Agent.GetNameByID(target_id) or "").strip()
                    step = {
                        "type": "target_enemy",
                        "name": f"Target {target_name or 'Enemy'}",
                    }
                    if model_id > 0:
                        step["model_id"] = model_id
                    if target_name:
                        step["target"] = target_name
                _add_recorded_step(step)
                _dialog_recorder_status = f"Recorded target_enemy for {enemy_name or 'target'}."

        PyImGui.text("Utility / Party")
        if _grid_button("Record Resign", 0, help_text="Add a resign step."):
            step = {"type": "resign"}
            _add_recorded_step(step)
            _dialog_recorder_status = "Recorded resign."
        if _grid_button("Record /kneel", 1, help_text="Add emote step that sends /kneel."):
            step = {"type": "emote", "command": "kneel"}
            _add_recorded_step(step)
            _dialog_recorder_status = "Recorded emote /kneel."
        if _grid_button("Record load_party", 2, help_text="Add load_party step with detected party size (4/6/8)."):
            step = _build_load_party_step(minionless=False)
            _add_recorded_step(step)
            _dialog_recorder_status = (
                f"Recorded load_party: max_heroes={int(step['max_heroes'])}, team={step['team']}."
            )
        if _grid_button("Record load_party_minionless", 0, help_text="Add load_party minionless step (6-man uses no spirits/minions team)."):
            step = _build_load_party_step(minionless=True)
            _add_recorded_step(step)
            _dialog_recorder_status = (
                f"Recorded load_party_minionless: max_heroes={int(step['max_heroes'])}, team={step['team']}."
            )
        if _exit_recording_active:
            phase = "waiting map ready" if _exit_recording_waiting_load else "waiting for 0,0"
            PyImGui.text(f"Exit-map monitor: {phase}")
        if _travel_recording_active:
            PyImGui.text("Travel monitor: waiting for map change")
        if _dialog_recorder_status:
            PyImGui.text_wrapped(_dialog_recorder_status)

        PyImGui.separator()
        PyImGui.text("Static Helpers")
        player_x, player_y = Player.GetXY()
        map_id = Map.GetMapID()
        map_name = Map.GetMapName(map_id)
        target_id = Player.GetTargetID()

        player_coords = _fmt_xy(player_x, player_y)
        PyImGui.text(f"Player: {player_coords} | Map: [{map_id}] {map_name}")
        if _grid_button("Copy Player XY", 0, help_text="Copy your current player coordinates [x, y]."):
            PyImGui.set_clipboard_text(player_coords)
        if _grid_button("Copy Map ID", 1, help_text="Copy current map id."):
            PyImGui.set_clipboard_text(str(map_id))
        if _grid_button("Run Test", 2, help_text="Run Sources/modular_bot/missions/script_helper.json."):
            try:
                _test_bot.Stop()
                _test_bot.config.initialized = False
                _test_bot.config.FSM.reset()
                _sync_engine_upkeep(_test_bot)
                _test_bot.Start()
                _test_running = True
                _debug_log(f"Started mission: {_TEST_MISSION_NAME}")
            except FileNotFoundError:
                _test_running = False
                _debug_log(f"Mission file not found: Sources/modular_bot/missions/{_TEST_MISSION_NAME}.json")

        if target_id and Agent.IsValid(target_id):
            target_x, target_y = Agent.GetXY(target_id)
            target_coords = _fmt_xy(target_x, target_y)
            target_name = Agent.GetNameByID(target_id) or "<unnamed>"
            target_encoded = _fmt_target_enum_entry(target_id)
            PyImGui.text(f"Target: {target_name} @ {target_coords}")

            if _grid_button("Copy Target XY", 0, help_text="Copy targeted agent coordinates [x, y]."):
                PyImGui.set_clipboard_text(target_coords)
            if _grid_button("Copy Target Enum", 1, help_text="Copy encoded enum entry for the current target."):
                PyImGui.set_clipboard_text(target_encoded)
            if Agent.IsItem(target_id):
                item_enum_entry = _fmt_item_enum_entry(target_id)
                if _grid_button("Copy Item Enum", 2, help_text="Copy item enum entry for targeted item model_id."):
                    PyImGui.set_clipboard_text(item_enum_entry)
        else:
            PyImGui.text("Target: <none>")

        PyImGui.separator()
        PyImGui.text("Active Dialog Options")
        if PyDialog is None:
            PyImGui.text_wrapped("PyDialog module unavailable in this runtime.")
        else:
            try:
                dialog_options = _get_active_dialog_options()
                if _dialog_init_attempted and not _dialog_init_ok:
                    PyImGui.text_wrapped("PyDialog failed to initialize. Check injection log.")
                if dialog_options:
                    for index, (dialog_id, text) in enumerate(dialog_options, start=1):
                        display_text = text if text else "<no text>"
                        PyImGui.text_wrapped(f"{index}. 0x{dialog_id:X} - {display_text}")
                        if PyImGui.button(f"Copy##active_dialog_{dialog_id}_{index}"):
                            PyImGui.set_clipboard_text(f"0x{dialog_id:X} | {display_text}")
                            _dialog_copy_status = f"Copied 0x{dialog_id:X}"
                else:
                    PyImGui.text("No active dialog options.")
            except Exception as exc:
                PyImGui.text_wrapped(f"Failed to read active dialog options: {exc}")
        if _dialog_copy_status:
            PyImGui.text(_dialog_copy_status)

    PyImGui.end()
    _test_bot.Update()
    if _test_running and _test_bot.config.FSM.is_finished():
        _test_bot.Stop()
        _test_running = False
    _replay_bot.Update()
    if _replay_running and _replay_bot.config.FSM.is_finished():
        _replay_bot.Stop()
        _replay_running = False
        _replay_status = "Replay finished."
