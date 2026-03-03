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

from Py4GWCoreLib import Agent, Botting, ConsoleLog, Item, Map, Player
from Sources.modular_bot.recipes import mission_run


_TEST_MISSION_NAME = "script_helper"
_test_bot = Botting("ScriptHelperTestRunner")
_test_running = False


def _run_test_mission(bot: Botting) -> None:
    mission_run(bot, _TEST_MISSION_NAME)


_test_bot.SetMainRoutine(_run_test_mission)


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
    global _test_running

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
                _test_bot.Start()
                _test_running = True
                ConsoleLog("Script Helper", f"Started mission: {_TEST_MISSION_NAME}")
            except FileNotFoundError:
                _test_running = False
                ConsoleLog(
                    "Script Helper",
                    f"Mission file not found: Sources/modular_bot/missions/{_TEST_MISSION_NAME}.json",
                )

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

    PyImGui.end()
    _test_bot.Update()
    if _test_running and _test_bot.config.FSM.is_finished():
        _test_bot.Stop()
        _test_running = False

