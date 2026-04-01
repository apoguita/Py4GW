"""
Script Helper

Displays:
- Player coordinates as [x, y]
- Player map (id + name)
- Target coordinates as [x, y]
- Target encoded name tuple for copy/paste into blessing helper definitions
- Button to run mission recipe `script_helper.json`
"""

import PyImGui
import PyAgent
import json

from Py4GWCoreLib import Agent, Botting, ConsoleLog, Item, Map, Player
from Sources.modular_bot.recipes import mission_run
from Sources.modular_bot.recipes.modular_actions import register_step


_TEST_MISSION_NAME = "script_helper"
_test_bot = Botting("ScriptHelperTestRunner")
_test_running = False
_single_step_bot = Botting("ScriptHelperSingleStepRunner")
_single_step_running = False
_single_step_status = ""
_single_step_input = '{"type": "auto_path", "name": "move it", "points": [[]], "pause_on_combat": true},'
_single_step_payload = None
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
            # Avoid running auto-combat upkeep at the same time as HeroAI.
            bot.Properties.ApplyNow("auto_combat", "active", False)
    except Exception as exc:
        _debug_log(f"Engine upkeep sync failed: {exc}")


def _run_test_mission(bot: Botting) -> None:
    mission_run(bot, _TEST_MISSION_NAME)


_test_bot.SetMainRoutine(_run_test_mission)


def _run_single_step(bot: Botting) -> None:
    global _single_step_payload
    # Always add at least one state so Botting.Start() never fails with empty FSM.
    bot.States.AddCustomState(lambda: None, "Single Step Runner Guard")

    if _single_step_payload is None:
        return

    try:
        register_step(bot, _single_step_payload, 0, "ScriptHelperSingleStep")
    except Exception as exc:
        _debug_log(f"Single step registration failed: {exc}")
    finally:
        _single_step_payload = None


_single_step_bot.SetMainRoutine(_run_single_step)


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


def main():
    global _test_running, _single_step_input, _single_step_running, _single_step_payload, _single_step_status

    if PyImGui.begin("Script Helper"):
        player_x, player_y = Player.GetXY()
        map_id = Map.GetMapID()
        map_name = Map.GetMapName(map_id)
        target_id = Player.GetTargetID()

        player_coords = _fmt_xy(player_x, player_y)
        PyImGui.text(f"Player coordinates: {player_coords}")
        if PyImGui.button("Copy Player Coordinates"):
            PyImGui.set_clipboard_text(player_coords)

        PyImGui.text(f"Player map: [{map_id}] {map_name}")
        if PyImGui.button("Copy Player Map ID"):
            PyImGui.set_clipboard_text(str(map_id))
        if PyImGui.button("Run Test"):
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
            PyImGui.text(f"Target coordinates: {target_coords}")
            if PyImGui.button("Copy Target Coordinates"):
                PyImGui.set_clipboard_text(target_coords)
            PyImGui.text(f"Target name: {target_name}")
            if PyImGui.button("Copy Target Enum Entry"):
                PyImGui.set_clipboard_text(target_encoded)
            if Agent.IsItem(target_id):
                item_enum_entry = _fmt_item_enum_entry(target_id)
                if PyImGui.button("Copy Item Enum Entry"):
                    PyImGui.set_clipboard_text(item_enum_entry)
        else:
            PyImGui.text("Target coordinates: []")
            PyImGui.text("Target name: <none>")

        PyImGui.separator()
        PyImGui.text("Run Single Step")
        _single_step_input = PyImGui.input_text("Step JSON", _single_step_input, 0)
        if PyImGui.button("Execute Step"):
            raw = str(_single_step_input or "").strip()
            if raw.endswith(","):
                raw = raw[:-1].strip()
            try:
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise ValueError("Step JSON must be an object.")
                if not str(parsed.get("type", "")).strip():
                    raise ValueError("Step must include a non-empty 'type'.")
            except Exception as exc:
                _single_step_running = False
                _single_step_status = f"Invalid step JSON: {exc}"
                _debug_log(_single_step_status)
                parsed = None

            if parsed is not None:
                try:
                    _single_step_bot.Stop()
                    _single_step_bot.config.initialized = False
                    _single_step_bot.config.FSM.reset()
                    _sync_engine_upkeep(_single_step_bot)
                    _single_step_payload = parsed
                    _single_step_bot.Start()
                    _single_step_running = True
                    _single_step_status = f"Executing: {parsed.get('type')}"
                    _debug_log(f"Executing single step: {parsed}")
                except Exception as exc:
                    _single_step_running = False
                    _single_step_status = f"Failed to execute step: {exc}"
                    _debug_log(_single_step_status)
        if PyImGui.button("Copy Step JSON"):
            PyImGui.set_clipboard_text(str(_single_step_input or ""))
        if _single_step_status:
            PyImGui.text_wrapped(_single_step_status)

    PyImGui.end()
    _test_bot.Update()
    if _test_running and _test_bot.config.FSM.is_finished():
        _test_bot.Stop()
        _test_running = False
    _single_step_bot.Update()
    if _single_step_running and _single_step_bot.config.FSM.is_finished():
        _single_step_bot.Stop()
        _single_step_running = False
        _single_step_status = "Step execution finished."

