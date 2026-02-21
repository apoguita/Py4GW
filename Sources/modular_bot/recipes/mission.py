"""
Mission recipe - run a mission from a structured JSON data file.

Mission files live in:
    Sources/modular_bot/missions/<mission_name>.json

Minimal mission template:
    {
      "name": "Mission Name",
      "outpost_id": 28,
      "max_heroes": 4,
      "entry": {"type": "enter_challenge", "delay": 3000, "target_map_id": 28},
      "steps": []
    }

Entry block catalog:
    - enter_challenge:
      {"type": "enter_challenge", "delay": 3000, "target_map_id": 0}
    - dialog:
      {"type": "dialog", "x": 0, "y": 0, "id": 0}
    - omit/null:
      no entry step

Step catalog (copy/paste):
    {"type": "path", "name": "Path 1", "points": [[0, 0], [100, 100]]}
    {"type": "auto_path", "name": "AutoPath 1", "points": [[0, 0], [100, 100]]}
    {"type": "auto_path_delayed", "name": "Delay Path", "points": [[0, 0], [100, 100]], "delay_ms": 35000}
    {"type": "wait", "ms": 1000}
    {"type": "wait_out_of_combat"}
    {"type": "wait_map_load", "map_id": 72}
    {"type": "move", "name": "Move", "x": 0, "y": 0}
    {"type": "exit_map", "x": 0, "y": 0, "target_map_id": 0}
    {"type": "interact_npc", "name": "Talk NPC", "x": 0, "y": 0}
    {"type": "interact_gadget", "ms": 2000}
    {"type": "interact_item", "ms": 2000}
    {"type": "interact_quest_npc", "ms": 5000}
    {"type": "interact_nearest_npc", "ms": 5000}
    {"type": "dialog", "name": "Dialog", "x": 0, "y": 0, "id": 0}
    {"type": "dialog_multibox", "id": 0}
    {"type": "skip_cinematic", "wait_ms": 500}
    {"type": "set_title", "id": 0}
    {"type": "key_press", "key": "F1", "ms": 1000}
    {"type": "force_hero_state", "state": "fight", "ms": 1000}
    {"type": "force_hero_state", "state": "guard", "ms": 1000}
    {"type": "force_hero_state", "state": "avoid", "ms": 1000}
    {"type": "force_hero_state", "behavior": 2, "ms": 1000}
    {"type": "flag_heroes", "x": 0, "y": 0, "ms": 2000}
    {"type": "unflag_heroes", "ms": 2000}
    {"type": "resign"}
    {"type": "wait_map_change", "target_map_id": 0}
    {"type": "set_auto_combat", "enabled": true}
    {"type": "set_auto_combat", "enabled": false}

Notes:
    - Formatting convention for JSON steps:
      one step object per line, with key order ``type``, then ``name``, then ``ms`` (if used),
      then all other arguments.
    - key_press supported keys: F1, F2, SPACE, ENTER, ESCAPE/ESC
    - force_hero_state values: fight, guard, avoid
      (or behavior: 0=fight, 1=guard, 2=avoid)
    - set_auto_combat enabled: true/false (toggles CustomBehaviors combat)

Two APIs:
    mission_run(bot, "the_great_northern_wall")
    Mission("the_great_northern_wall")
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting

from ..phase import Phase
from ..hero_setup import get_team_for_size, load_hero_teams


# ──────────────────────────────────────────────────────────────────────────────
# Mission data loader
# ──────────────────────────────────────────────────────────────────────────────

def _get_missions_dir() -> str:
    """Return the missions data directory path."""
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "missions"))


def _load_hero_config() -> Dict[str, Any]:
    """
    Load hero configuration used by modular recipes.

    Returns:
        Dict containing team keys mapped to hero ID lists.

    Resolution order:
        1) ``Sources/modular_bot/configs/<account_email>.json`` -> ``hero_teams``
        2) ``Sources/modular_bot/configs/default.json`` -> ``hero_teams``
        3) Legacy hero config paths
    """
    return load_hero_teams()


def _load_mission_data(mission_name: str) -> Dict[str, Any]:
    """
    Load mission data from ``Sources/modular_bot/missions/<mission_name>.json``.

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


def list_available_missions() -> List[str]:
    """
    Return all available mission names (without .json extension).

    Excludes non-mission support files such as ``hero_config.json``.
    """
    missions_dir = _get_missions_dir()
    if not os.path.isdir(missions_dir):
        return []

    names = []
    for filename in os.listdir(missions_dir):
        if not filename.endswith(".json"):
            continue
        if filename.lower() == "hero_config.json":
            continue
        names.append(filename[:-5])

    return sorted(names)


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

    elif step_type == "auto_path_delayed":
        points = [tuple(p) for p in step["points"]]
        name = step.get("name", f"AutoPathDelayed {step_idx + 1}")
        delay_ms = int(step.get("delay_ms", 35000))
        if delay_ms < 0:
            delay_ms = 0

        # Emulate delayed waypoint advance: move to one point, then pause.
        for point_i, (x, y) in enumerate(points):
            step_name = f"{name} [{point_i + 1}/{len(points)}]"
            bot.Move.XY(x, y, step_name)
            if point_i < len(points) - 1 and delay_ms > 0:
                bot.Wait.ForTime(delay_ms)

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

    elif step_type == "key_press":
        key_name = str(step["key"]).upper()
        key_map = {
            "F1": "F1",
            "F2": "F2",
            "SPACE": "Space",
            "ENTER": "Enter",
            "ESCAPE": "Escape",
            "ESC": "Escape",
        }
        mapped = key_map.get(key_name)
        if mapped is None:
            from Py4GWCoreLib import ConsoleLog
            ConsoleLog("Recipe:Mission", f"Unsupported key_press key: {key_name!r}")
        else:
            from Py4GWCoreLib import Keystroke, Key
            bot.States.AddCustomState(
                lambda _k=mapped: Keystroke.PressAndRelease(getattr(Key, _k).value),
                f"KeyPress {key_name}",
            )
            ms = int(step.get("ms", 1000))
            if ms > 0:
                bot.Wait.ForTime(ms)

    elif step_type == "force_hero_state":
        raw_state = str(step.get("state", "")).strip().lower()
        behavior_map = {
            "fight": 0,
            "guard": 1,
            "avoid": 2,
        }

        # Optional numeric behavior override (0=fight, 1=guard, 2=avoid)
        if "behavior" in step:
            try:
                behavior = int(step["behavior"])
            except (TypeError, ValueError):
                behavior = -1
        else:
            behavior = behavior_map.get(raw_state, -1)

        if behavior not in (0, 1, 2):
            from Py4GWCoreLib import ConsoleLog
            ConsoleLog(
                "Recipe:Mission",
                f"Invalid force_hero_state at index {step_idx}: state={raw_state!r}, behavior={step.get('behavior')!r}",
            )
        else:
            state_name = step.get("name", f"Force Hero State ({raw_state or behavior})")

            def _set_hero_behavior_all(behavior_value: int = behavior):
                from Py4GWCoreLib import Party
                for hero in Party.GetHeroes():
                    hero_agent_id = getattr(hero, "agent_id", 0)
                    if hero_agent_id:
                        Party.Heroes.SetHeroBehavior(hero_agent_id, behavior_value)

            bot.States.AddCustomState(_set_hero_behavior_all, state_name)
            ms = int(step.get("ms", 1000))
            if ms > 0:
                bot.Wait.ForTime(ms)

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

    elif step_type == "set_auto_combat":
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import (
            CustomBehaviorParty,
        )

        enabled_raw = step.get("enabled", True)
        if isinstance(enabled_raw, str):
            enabled = enabled_raw.strip().lower() in ("1", "true", "yes", "on")
        else:
            enabled = bool(enabled_raw)

        bot.States.AddCustomState(
            lambda e=enabled: CustomBehaviorParty().set_party_is_combat_enabled(e),
            f"Set CB Combat {'On' if enabled else 'Off'}",
        )

        if enabled:
            bot.Templates.Aggressive()
        else:
            bot.Templates.Pacifist()


    
    
    

        ms = int(step.get("ms", 500))
        if ms > 0:
            bot.Wait.ForTime(ms)

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
    hero_team = str(data.get("hero_team", "") or "")
    entry = data.get("entry")
    steps = data.get("steps", [])

    # ── 1. Travel to outpost ──────────────────────────────────────────
    if outpost_id:
        bot.Map.Travel(target_map_id=outpost_id)

    # ── 2. Add heroes from config ─────────────────────────────────────
    if max_heroes > 0:
        hero_ids = get_team_for_size(max_heroes, hero_team)
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


