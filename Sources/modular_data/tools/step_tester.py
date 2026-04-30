"""
Single-step modular node tester.

Lists registered modular step types, lets the user edit params, and runs one
inline modular phase through the native ModularBot runtime.
"""
from __future__ import annotations

import json
import traceback
from typing import Any

import PyImGui

from Py4GWCoreLib import Agent, Console, ConsoleLog, Map, Player
from Py4GWCoreLib.enums_src.Map_enums import outposts
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.modular import ModularBot
from Py4GWCoreLib.modular.actions import get_action_node_specs
from Py4GWCoreLib.modular.recipes.modular_block import build_inline_modular_phase


COMMON_PARAMS = ("name", "ms", "anchor", "debug")
PARAM_HINTS = {
    "delay": "ms",
    "delay_ms": "ms",
    "duration": "ms",
    "effect_id": "integer",
    "enabled": "true/false",
    "point": "[x, y]",
    "points": "[[x1, y1], [x2, y2]]",
    "id": "0x84 or [\"0x81\", \"0x84\"]",
    "model_id": "integer",
    "map_id": "integer",
    "poll_ms": "ms",
    "per_account_delay_ms": "ms",
    "quest_id": "integer",
    "target_map_id": "integer",
    "target_map_name": "optional",
    "slot": "1-8",
    "enemy": "ENEMY_KEY",
    "npc": "NPC_KEY",
    "gadget": "GADGET_KEY",
    "item": "ITEM_KEY",
    "hero_team": "priority or team key",
    "required_hero": "hero name or [\"hero\", ...]",
    "apply_templates": "true/false",
    "mode": "conset or pcons",
    "multibox": "true/false",
    "timeout_ms": "ms",
    "wait_ms": "ms",
    "x": "current x",
    "y": "current y",
}

SAFE_OUTPOST_MAP_ID = 642
COMMON_MODEL_DEFAULTS: dict[str, int] = {
    "birthday_cupcake": int(ModelID.Birthday_Cupcake.value),
    "lockpick": int(ModelID.Lockpick.value),
    "fow_scroll": int(ModelID.Passage_Scroll_Fow.value),
    "uw_scroll": int(ModelID.Passage_Scroll_Uw.value),
    "grail": int(ModelID.Grail_Of_Might.value),
    "essence": int(ModelID.Essence_Of_Celerity.value),
    "armor": int(ModelID.Armor_Of_Salvation.value),
    "war_supplies": int(ModelID.War_Supplies.value),
}

PARAM_DEFAULTS: dict[str, str] = {
    "amount": "1",
    "apply_templates": "true",
    "delay": "1000",
    "delay_ms": "1000",
    "duration": "1000",
    "effect_id": "0",
    "enabled": "true",
    "fill_with_henchmen": "true",
    "hero_team": "priority",
    "include_dead": "false",
    "leader_only": "false",
    "max_dist": "5000",
    "max_laps": "1",
    "minionless": "false",
    "mode": "pcons",
    "multibox": "true",
    "pause_on_combat": "true",
    "per_account_delay_ms": "500",
    "poll_ms": "250",
    "quest_id": "0",
    "required": "false",
    "set_target": "true",
    "skip_leader": "false",
    "slot": "1",
    "timeout_ms": "10000",
    "tolerance": "150",
    "wait_ms": "1000",
    "wait_for_loot": "false",
}

STEP_DEFAULTS: dict[str, dict[str, str]] = {
    "dialog": {"id": "0x84", "ms": "1000"},
    "dialogs": {"ids": "[\"0x84\"]", "ms": "1000"},
    "dialog_multibox": {"id": "0x84", "multibox": "true", "ms": "1000"},
    "drop_bundle": {"ms": "500"},
    "enter_challenge": {"delay_ms": "2000"},
    "exit_map": {"suppress_recovery_ms": "10000"},
    "flag_all_accounts": {"ms": "500"},
    "flag_heroes": {"ms": "500"},
    "follow_model": {"follow_range": "600", "timeout_ms": "10000"},
    "force_hero_state": {"state": "fight"},
    "load_party": {"hero_team": "priority", "required_hero": "", "apply_templates": "true"},
    "move": {"ms": "250"},
    "nudge": {"pulses": "1", "pulse_ms": "250"},
    "nudge_move": {"pulses": "1", "pulse_ms": "250"},
    "path_to_target": {"max_dist": "5000", "required": "false", "tolerance": "150"},
    "random_travel": {"leave_party": "true", "travel_wait_ms": "500"},
    "set_auto_combat": {"enabled": "true"},
    "set_auto_following": {"enabled": "true"},
    "set_auto_looting": {"enabled": "true"},
    "set_combat_engine": {"engine": "hero_ai"},
    "skip_cutscene": {"timeout_ms": "10000", "wait_ms": "1500"},
    "target_enemy": {"nearest": "true", "max_dist": "5000", "set_party_target": "true"},
    "travel": {"leave_party": "true"},
    "travel_gh": {"multibox": "true", "ms": "5000", "per_account_delay_ms": "500"},
    "upkeep_consumables": {"mode": "pcons", "multibox": "true", "poll_ms": "15000"},
    "upkeep_cons": {"multibox": "true", "poll_ms": "15000"},
    "upkeep_pcons": {"multibox": "true", "poll_ms": "15000"},
    "use_consumables": {"mode": "pcons", "multibox": "true"},
    "wait": {"ms": "1000", "anchor": "true"},
    "wait_all_accounts_same_map": {"timeout_ms": "60000", "poll_ms": "500", "require_same_district": "false"},
    "wait_for_map_load": {"target_map_id": ""},
    "wait_map_change": {"target_map_id": ""},
    "wait_map_load": {"target_map_id": ""},
    "wait_out_of_combat": {"ms": "1000"},
}

_search = ""
_selected_step_type = ""
_param_values: dict[str, str] = {}
_json_preview = ""
_status = ""
_debug_logging = False
_auto_stop_previous = True
_bot: ModularBot | None = None
_run_active = False


def _specs():
    return get_action_node_specs()


def _step_types() -> list[str]:
    needle = _search.strip().lower()
    names = sorted(_specs().keys())
    if needle:
        names = [name for name in names if needle in name.lower()]
    return names


def _selected_spec():
    if not _selected_step_type:
        return None
    return _specs().get(_selected_step_type)


def _params_for_selected() -> list[str]:
    spec = _selected_spec()
    allowed = list(getattr(spec, "allowed_params", ()) or [])
    params = list(COMMON_PARAMS)
    for param in allowed:
        if param not in params and param != "type":
            params.append(param)
    return params


def _safe_current_xy(offset_x: int = 0, offset_y: int = 0) -> tuple[int, int]:
    try:
        x, y = Player.GetXY()
        return int(x) + int(offset_x), int(y) + int(offset_y)
    except Exception:
        return int(offset_x), int(offset_y)


def _json_point(offset_x: int = 0, offset_y: int = 0) -> str:
    x, y = _safe_current_xy(offset_x=offset_x, offset_y=offset_y)
    return f"[{x}, {y}]"


def _json_points() -> str:
    x, y = _safe_current_xy()
    return f"[[{x}, {y}], [{x + 150}, {y + 150}]]"


def _current_map_id() -> int:
    try:
        return int(Map.GetMapID() or 0)
    except Exception:
        return 0


def _safe_outpost_map_id() -> int:
    map_id = _current_map_id()
    return map_id if map_id in outposts else SAFE_OUTPOST_MAP_ID


def _target_agent_id() -> int:
    try:
        return int(Player.GetTargetID() or 0)
    except Exception:
        return 0


def _target_model_id() -> int:
    agent_id = _target_agent_id()
    if agent_id <= 0:
        return 0
    try:
        return int(Agent.GetModelID(agent_id) or 0)
    except Exception:
        return 0


def _default_model_for_step(step_type: str) -> int:
    if step_type == "use_item":
        return COMMON_MODEL_DEFAULTS["birthday_cupcake"]
    if step_type == "loot_chest":
        return COMMON_MODEL_DEFAULTS["lockpick"]
    if step_type == "broadcast_summoning_stone":
        return int(ModelID.Legionnaire_Summoning_Crystal.value)
    return _target_model_id()


def _default_value_for_param(step_type: str, param: str) -> str:
    if param in ("point", "xy"):
        if step_type in ("flag_all_accounts", "flag_heroes"):
            return _json_point(offset_x=-100, offset_y=-100)
        return _json_point()
    if param in ("x", "y"):
        x, y = _safe_current_xy()
        return str(x if param == "x" else y)
    if param == "points":
        return _json_points()
    if param in ("map_id", "target_map_id", "return_map_id"):
        return str(_safe_outpost_map_id())
    if param == "model_id":
        model_id = _default_model_for_step(step_type)
        return str(model_id) if model_id > 0 else ""
    if param in ("agent_id", "target_id"):
        agent_id = _target_agent_id()
        return str(agent_id) if agent_id > 0 else "0"
    if param in PARAM_DEFAULTS:
        return PARAM_DEFAULTS[param]
    return ""


def _default_param_values(step_type: str) -> dict[str, str]:
    values: dict[str, str] = {
        "name": str(step_type or "").replace("_", " ").title(),
        "ms": "250",
    }
    for param in _params_for_selected():
        if param in values:
            continue
        default = _default_value_for_param(step_type, param)
        if default != "":
            values[param] = default
    values.update(STEP_DEFAULTS.get(step_type, {}))
    return values


def _set_selected(step_type: str) -> None:
    global _selected_step_type, _param_values, _status
    _selected_step_type = str(step_type or "")
    _param_values = _default_param_values(_selected_step_type)
    _status = f"Selected step: {_selected_step_type}"


def _stop_for_edit() -> None:
    global _run_active, _status
    if not _run_active:
        return
    if _bot is not None:
        _bot.stop(reason="Step tester input edit")
    _run_active = False
    _status = "Stopped active run because tester input changed."


def _coerce_value(raw: str) -> Any:
    text = str(raw or "").strip()
    if text == "":
        return None
    lowered = text.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if lowered in ("none", "null"):
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        return int(text, 0)
    except Exception:
        pass
    try:
        return float(text)
    except Exception:
        return text


def _current_step() -> dict[str, Any]:
    step: dict[str, Any] = {"type": _selected_step_type}
    for key, raw in _param_values.items():
        if key == "type" or str(raw or "").strip() == "":
            continue
        value = _coerce_value(raw)
        if value is not None:
            step[key] = value
    return step


def _refresh_preview() -> None:
    global _json_preview
    if not _selected_step_type:
        _json_preview = "{}"
        return
    _json_preview = json.dumps(_current_step(), indent=2, ensure_ascii=True)


def _build_bot(step: dict[str, Any]) -> ModularBot:
    phase = build_inline_modular_phase(
        display_name=f"Step Test: {step.get('type', '')}",
        name="Run Single Modular Step",
        steps=[dict(step)],
        recipe_name="StepTester",
        anchor=True,
    )
    return ModularBot(
        "ModularStepTester",
        [phase],
        loop=False,
        template="preserve",
        debug_logging=bool(_debug_logging),
        diagnostics_label="Modular Step Tester",
    )


def _run_step() -> None:
    global _bot, _status, _run_active
    if not _selected_step_type:
        _status = "Pick a step type first."
        return
    try:
        if _auto_stop_previous and _bot is not None:
            _bot.stop(reason="Step tester restart")
        step = _current_step()
        _bot = _build_bot(step)
        _bot.start()
        _run_active = True
        _status = f"Running {_selected_step_type}: {json.dumps(step, ensure_ascii=True)}"
    except Exception as exc:
        _run_active = False
        _status = f"Run failed: {exc}"
        ConsoleLog("Modular Step Tester", traceback.format_exc(), Console.MessageType.Error)


def _stop_step() -> None:
    global _status, _run_active
    if _bot is not None:
        _bot.stop(reason="Manual stop")
    _run_active = False
    _status = "Stopped."


def _quick_fill(param: str) -> None:
    global _status
    try:
        if param == "point":
            offset = -100 if _selected_step_type in ("flag_all_accounts", "flag_heroes") else 0
            _param_values[param] = _json_point(offset_x=offset, offset_y=offset)
        elif param in ("x", "y"):
            x, y = _safe_current_xy()
            _param_values[param] = str(x if param == "x" else y)
        elif param == "points":
            _param_values[param] = _json_points()
        elif param in ("map_id", "target_map_id"):
            _param_values[param] = str(_safe_outpost_map_id())
        elif param == "return_map_id":
            _param_values[param] = str(_safe_outpost_map_id())
        elif param == "model_id":
            model_id = _target_model_id() or _default_model_for_step(_selected_step_type)
            _param_values[param] = str(model_id) if model_id > 0 else ""
        elif param in ("agent_id", "target_id"):
            _param_values[param] = str(_target_agent_id())
        _status = f"Filled {param} from current game state."
    except Exception as exc:
        _status = f"Quick fill failed for {param}: {exc}"


def _apply_defaults_to_empty_params() -> None:
    for param in _params_for_selected():
        if str(_param_values.get(param, "") or "").strip():
            continue
        default = _default_value_for_param(_selected_step_type, param)
        if default != "":
            _param_values[param] = default


def _draw_common_model_buttons(param: str) -> None:
    for label, model_id in COMMON_MODEL_DEFAULTS.items():
        PyImGui.same_line(0, 6)
        if PyImGui.button(f"{label}##model_{param}_{label}"):
            _param_values[param] = str(int(model_id))


def _draw_step_picker() -> None:
    global _search
    _search = PyImGui.input_text("Search Steps", _search)
    PyImGui.separator()
    for idx, step_type in enumerate(_step_types()):
        selected = step_type == _selected_step_type
        if selected:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.22, 0.42, 0.22, 1.0))
        if PyImGui.button(f"{step_type}##step_type_{idx}"):
            _set_selected(step_type)
        if selected:
            PyImGui.pop_style_color(1)


def _draw_param_editor() -> None:
    global _debug_logging, _auto_stop_previous
    if not _selected_step_type:
        PyImGui.text("Select a step type.")
        return
    PyImGui.text(f"Step: {_selected_step_type}")
    spec = _selected_spec()
    category = ""
    if spec is not None and isinstance(getattr(spec, "metadata", None), dict):
        category = str(spec.metadata.get("category", "") or "")
    if category:
        PyImGui.text(f"Category: {category}")
    PyImGui.separator()
    for param in _params_for_selected():
        current = _param_values.get(param, "")
        hint = PARAM_HINTS.get(param, "")
        label = f"{param}{f' ({hint})' if hint else ''}##param_{param}"
        new_value = PyImGui.input_text(label, current)
        _param_values[param] = new_value
        if param in ("point", "points", "x", "y", "map_id", "target_map_id", "return_map_id", "model_id", "agent_id", "target_id"):
            PyImGui.same_line(0, 8)
            if PyImGui.button(f"Use Current##fill_{param}"):
                _quick_fill(param)
        if param == "model_id":
            _draw_common_model_buttons(param)

    PyImGui.separator()
    new_debug_logging = PyImGui.checkbox("Debug Logging", _debug_logging)
    _debug_logging = bool(new_debug_logging)
    _auto_stop_previous = PyImGui.checkbox("Stop Previous Before Run", _auto_stop_previous)
    if PyImGui.button("Fill Empty Defaults"):
        _apply_defaults_to_empty_params()
    PyImGui.same_line(0, 8)
    if PyImGui.button("Run Step"):
        _run_step()
    PyImGui.same_line(0, 8)
    if PyImGui.button("Stop"):
        _stop_step()
    PyImGui.same_line(0, 8)
    if PyImGui.button("Copy JSON"):
        _refresh_preview()
        PyImGui.set_clipboard_text(_json_preview)

    _refresh_preview()
    PyImGui.separator()
    PyImGui.text("JSON Preview")
    PyImGui.text_wrapped(_json_preview)


def get_bot():
    return _bot


def main():
    global _status, _run_active
    try:
        PyImGui.set_next_window_size((980, 680), PyImGui.ImGuiCond.FirstUseEver)
        if PyImGui.begin("Modular Step Tester"):
            if PyImGui.begin_table("step_tester_layout", 2, PyImGui.TableFlags.SizingStretchSame):
                PyImGui.table_next_column()
                _draw_step_picker()
                PyImGui.table_next_column()
                _draw_param_editor()
                PyImGui.end_table()
            if _status:
                PyImGui.separator()
                PyImGui.text_wrapped(_status)
        PyImGui.end()
        if _run_active and _bot is not None:
            _bot.update()
            if not _bot.is_running():
                _run_active = False
    except Exception as exc:
        _run_active = False
        _status = f"Step tester error: {exc}"
        ConsoleLog("Modular Step Tester", traceback.format_exc(), Console.MessageType.Error)
