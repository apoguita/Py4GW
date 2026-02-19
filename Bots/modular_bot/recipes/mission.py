"""
Mission recipe — Run a mission from a structured JSON data file.

Mission data files define a sequence of steps (move, wait, interact,
dialog, etc.) that the bot executes in order. Combat is handled by
CustomBehaviors.

JSON format (stored in Bots/modular_bot/missions/<name>.json):

    {
        "name": "The Great Northern Wall",
        "outpost_id": 28,
        "hard_mode": true,
        "entry": {
            "type": "enter_challenge",
            "delay": 3000
        },
        "steps": [
            {"type": "path",              "points": [[5770, -12799], [5085, -12095]]},
            {"type": "auto_path",         "points": [[6269, -10220], [3830, -6054]]},
            {"type": "wait",              "ms": 5000},
            {"type": "wait_out_of_combat"},
            {"type": "wait_map_load",     "map_id": 72},
            {"type": "interact_npc",      "x": -3389, "y": 4087},
            {"type": "dialog",            "x": -3389, "y": 4087, "id": 133},
            {"type": "exit_map",          "x": 5580, "y": 946, "target_map_id": 380},
            {"type": "move",              "x": 769, "y": 6564}
        ]
    }

Entry types:
    - "enter_challenge": calls bot.Map.EnterChallenge(delay)
    - "dialog":          moves to NPC and sends dialog to enter mission
    - null/missing:      no special entry (already in mission zone)

Step types:
    - "path":              Follow exact path (list of [x,y] points)
    - "auto_path":         Follow auto-pathed path (list of [x,y] waypoints)
    - "wait":              Wait fixed time (ms)
    - "wait_out_of_combat": Wait until no enemies in aggro
    - "wait_map_load":     Wait for specific map to load
    - "move":              Move to single coordinate (x, y)
    - "exit_map":          Move to coordinate and exit to target map
    - "interact_npc":      Move to NPC at (x,y) and interact
    - "interact_gadget":   Interact with nearest gadget (wait ms)
    - "interact_item":     Interact with nearest item (wait ms)
    - "interact_quest_npc": Interact with nearest NPC that has a quest marker (wait ms)
    - "interact_nearest_npc": Interact with nearest NPC (wait ms)
    - "dialog":            Move to (x,y) and send dialog ID
    - "dialog_multibox":   Send dialog to all accounts
    - "skip_cinematic":    Wait for cinematic to start, then skip it
    - "set_title":         Set active title by ID
    - "resign":            Resign party
    - "wait_map_change":   Wait for map to change to target

Two APIs:
    # Direct function
    mission_run(bot, "the_great_northern_wall")

    # Phase factory
    Mission("the_great_northern_wall")
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting

from ..phase import Phase


# ──────────────────────────────────────────────────────────────────────────────
# Mission data loader
# ──────────────────────────────────────────────────────────────────────────────

def _get_missions_dir() -> str:
    """Return the missions data directory path."""
    import Py4GW
    return os.path.join(
        Py4GW.Console.get_projects_path(),
        "Bots", "modular_bot", "missions",
    )


def _load_hero_config() -> Dict[str, Any]:
    """
    Load hero configuration from ``Bots/modular_bot/missions/hero_config.json``.

    Returns:
        Dict with keys ``"party_4"``, ``"party_6"``, ``"party_8"`` mapping
        to lists of hero IDs.
    """
    filepath = os.path.join(_get_missions_dir(), "hero_config.json")
    if not os.path.isfile(filepath):
        return {"party_4": [], "party_6": [], "party_8": []}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_mission_data(mission_name: str) -> Dict[str, Any]:
    """
    Load mission data from ``Bots/modular_bot/missions/<mission_name>.json``.

    Args:
        mission_name: File name without extension (e.g. "the_great_northern_wall").

    Returns:
        Parsed JSON dict.
    """
    missions_dir = _get_missions_dir()
    filepath = os.path.join(missions_dir, f"{mission_name}.json")

    if not os.path.isfile(filepath):
        available = []
        if os.path.isdir(missions_dir):
            available = [f[:-5] for f in os.listdir(missions_dir) if f.endswith(".json")]
        raise FileNotFoundError(
            f"Mission data not found: {filepath}\n"
            f"Available missions: {available}"
        )

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────────────────────────────────────
# Step executor — converts JSON steps to Botting API calls
# ──────────────────────────────────────────────────────────────────────────────

def _register_entry(bot: "Botting", entry: Optional[Dict[str, Any]]) -> None:
    """Register mission entry states (enter_challenge, dialog, etc.)."""
    if entry is None:
        return

    entry_type = entry.get("type", "")

    if entry_type == "enter_challenge":
        delay = entry.get("delay", 3000)
        target_map_id = entry.get("target_map_id", 0)
        bot.Map.EnterChallenge(delay=delay, target_map_id=target_map_id)

    elif entry_type == "dialog":
        x = entry["x"]
        y = entry["y"]
        dialog_id = entry["id"]
        bot.Dialogs.AtXY(x, y, dialog_id, "Enter Mission")

    else:
        from Py4GWCoreLib import ConsoleLog
        ConsoleLog("Recipe:Mission", f"Unknown entry type: {entry_type!r}")


def _register_step(bot: "Botting", step: Dict[str, Any], step_idx: int) -> None:
    """Register a single mission step as FSM state(s)."""
    step_type = step.get("type", "")

    if step_type == "path":
        points = [tuple(p) for p in step["points"]]
        name = step.get("name", f"Path {step_idx + 1}")
        bot.Move.FollowPath(points, step_name=name)

    elif step_type == "auto_path":
        points = [tuple(p) for p in step["points"]]
        name = step.get("name", f"AutoPath {step_idx + 1}")
        bot.Move.FollowAutoPath(points, step_name=name)

    elif step_type == "wait":
        ms = step.get("ms", 1000)
        bot.Wait.ForTime(ms)

    elif step_type == "wait_out_of_combat":
        bot.Wait.UntilOutOfCombat()

    elif step_type == "wait_map_load":
        map_id = step["map_id"]
        bot.Wait.ForMapLoad(target_map_id=map_id)

    elif step_type == "move":
        x, y = step["x"], step["y"]
        name = step.get("name", "")
        bot.Move.XY(x, y, name)

    elif step_type == "exit_map":
        x, y = step["x"], step["y"]
        target_map_id = step.get("target_map_id", 0)
        bot.Move.XYAndExitMap(x, y, target_map_id)

    elif step_type == "interact_npc":
        x, y = step["x"], step["y"]
        name = step.get("name", "")
        bot.Move.XYAndInteractNPC(x, y, name)

    elif step_type == "dialog":
        x, y = step["x"], step["y"]
        dialog_id = step["id"]
        name = step.get("name", "")
        bot.Dialogs.AtXY(x, y, dialog_id, name)

    elif step_type == "dialog_multibox":
        dialog_id = step["id"]
        bot.Multibox.SendDialogToTarget(dialog_id)

    elif step_type == "interact_gadget":
        ms = step.get("ms", 2000)

        def _make_gadget_interact():
            def _interact():
                from Py4GWCoreLib import AgentArray, Player
                gadget_array = AgentArray.GetGadgetArray()
                px, py = Player.GetXY()
                gadget_array = AgentArray.Filter.ByDistance(gadget_array, (px, py), 800)
                if gadget_array:
                    Player.Interact(gadget_array[0], call_target=False)
            return _interact

        bot.States.AddCustomState(_make_gadget_interact(), f"Interact Gadget")
        bot.Wait.ForTime(ms)

    elif step_type == "interact_item":
        ms = step.get("ms", 2000)

        def _make_item_interact():
            def _interact():
                from Py4GWCoreLib import AgentArray, Player
                item_array = AgentArray.GetItemArray()
                px, py = Player.GetXY()
                item_array = AgentArray.Filter.ByDistance(item_array, (px, py), 1200)
                if item_array:
                    item_array = AgentArray.Sort.ByDistance(item_array, (px, py))
                    Player.Interact(item_array[0], call_target=False)
            return _interact

        bot.States.AddCustomState(_make_item_interact(), f"Interact Item")
        bot.Wait.ForTime(ms)

    elif step_type == "interact_quest_npc":
        ms = step.get("ms", 5000)

        def _make_quest_interact(wait_ms):
            def _interact():
                from Py4GWCoreLib import AgentArray, Agent, Player
                ally_array = AgentArray.GetNPCMinipetArray()
                px, py = Player.GetXY()
                ally_array = AgentArray.Filter.ByDistance(ally_array, (px, py), 5000)
                quest_npcs = [a for a in ally_array if Agent.HasQuest(a)]
                if quest_npcs:
                    Player.Interact(quest_npcs[0], call_target=False)
            return _interact

        bot.States.AddCustomState(_make_quest_interact(ms), f"Interact Quest NPC")
        bot.Wait.ForTime(ms)

    elif step_type == "interact_nearest_npc":
        ms = step.get("ms", 5000)

        def _make_npc_interact(wait_ms):
            def _interact():
                from Py4GWCoreLib import AgentArray, Player
                npc_array = AgentArray.GetNPCMinipetArray()
                px, py = Player.GetXY()
                npc_array = AgentArray.Filter.ByDistance(npc_array, (px, py), 800)
                if npc_array:
                    Player.Interact(npc_array[0], call_target=False)
            return _interact

        bot.States.AddCustomState(_make_npc_interact(ms), f"Interact Nearest NPC")
        bot.Wait.ForTime(ms)

    elif step_type == "skip_cinematic":
        ms = step.get("wait_ms", 500)

        def _make_skip_cinematic(wait_ms):
            def _skip():
                from Py4GWCoreLib import Map
                if Map.IsInCinematic():
                    Map.SkipCinematic()
            return _skip

        bot.Wait.ForTime(ms)
        bot.States.AddCustomState(_make_skip_cinematic(ms), "Skip Cinematic")
        bot.Wait.ForTime(1000)

    elif step_type == "set_title":
        title_id = step["id"]
        bot.Player.SetTitle(title_id)

    elif step_type == "flag_heroes":
        x, y = step["x"], step["y"]
        ms = step.get("ms", 2000)
        bot.Party.FlagAllHeroes(x, y)
        bot.Wait.ForTime(ms)

    elif step_type == "unflag_heroes":
        ms = step.get("ms", 2000)
        bot.Party.UnflagAllHeroes()
        bot.Wait.ForTime(ms)

    elif step_type == "resign":
        bot.Multibox.ResignParty()

    elif step_type == "wait_map_change":
        target_map_id = step["target_map_id"]
        bot.Wait.ForMapToChange(target_map_id=target_map_id)

    else:
        from Py4GWCoreLib import ConsoleLog
        ConsoleLog("Recipe:Mission", f"Unknown step type: {step_type!r} at index {step_idx}")


# ──────────────────────────────────────────────────────────────────────────────
# Direct function — registers FSM states on a Botting instance
# ──────────────────────────────────────────────────────────────────────────────

def mission_run(bot: "Botting", mission_name: str) -> None:
    """
    Register FSM states to run a mission from a JSON data file.

    Args:
        bot:          Botting instance to register states on.
        mission_name: Mission data file name (without .json extension).
    """
    from Py4GWCoreLib import ConsoleLog

    data = _load_mission_data(mission_name)
    display_name = data.get("name", mission_name)
    outpost_id = data.get("outpost_id")
    max_heroes = data.get("max_heroes", 0)
    entry = data.get("entry")
    steps = data.get("steps", [])

    # ── 1. Travel to outpost ──────────────────────────────────────────
    if outpost_id:
        bot.Map.Travel(target_map_id=outpost_id)

    # ── 2. Add heroes from config ─────────────────────────────────────
    if max_heroes > 0:
        hero_config = _load_hero_config()
        party_key = f"party_{max_heroes}"
        hero_ids = hero_config.get(party_key, [])
        if hero_ids:
            bot.Party.LeaveParty()
            bot.Party.AddHeroList(hero_ids)

    # ── 3. Enter mission ──────────────────────────────────────────────
    if entry:
        _register_entry(bot, entry)

    # ── 4. Execute steps ──────────────────────────────────────────────
    for idx, step in enumerate(steps):
        _register_step(bot, step, idx)

    ConsoleLog(
        "Recipe:Mission",
        f"Registered mission: {display_name} ({len(steps)} steps, outpost {outpost_id})",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Phase factory — returns a Phase for ModularBot
# ──────────────────────────────────────────────────────────────────────────────

def Mission(
    mission_name: str,
    name: Optional[str] = None,
) -> Phase:
    """
    Create a Phase that runs a mission from a JSON data file.

    Args:
        mission_name: File name without extension (e.g. "the_great_northern_wall").
        name:         Optional display name (auto-generated from mission data if None).

    Returns:
        A Phase object ready to use in ModularBot.
    """
    # Try to load the display name from the data file
    if name is None:
        try:
            data = _load_mission_data(mission_name)
            name = str(data.get("name", mission_name))
        except FileNotFoundError:
            name = f"Mission: {mission_name}"

    return Phase(name, lambda bot: mission_run(bot, mission_name))

