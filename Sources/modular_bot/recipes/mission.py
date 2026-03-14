"""
Mission recipe - run a mission from a structured JSON data file.

Mission files:
    Sources/modular_bot/missions/<mission_name>.json

Action reference:
    Sources/modular_bot/recipes/README_actionlist.md
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting

from ..phase import Phase
from ..hero_setup import get_team_for_size, load_hero_teams
from .inventory_recipe import build_auto_inventory_guard_step
from .modular_actions import register_step as _register_shared_step
from .runner_common import count_expanded_steps, register_recipe_context, register_repeated_steps


def _get_missions_dir() -> str:
    """Return the missions data directory path."""
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "missions"))


def _load_hero_config() -> Dict[str, Any]:
    """Load hero configuration used by modular recipes."""
    return load_hero_teams()


def _load_mission_data(mission_name: str) -> Dict[str, Any]:
    """Load mission data from Sources/modular_bot/missions/<mission_name>.json."""
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
    """Return all available mission names (without .json extension)."""
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


def _register_entry(bot: "Botting", entry: Optional[Dict[str, Any]]) -> None:
    """Register mission entry states (enter_challenge, dialog, etc.)."""
    if entry is None:
        return

    entry_type = entry.get("type", "")

    if entry_type == "enter_challenge":
        from Py4GWCoreLib import Keystroke, Key, Map
        bot.States.AddCustomState(lambda: Map.EnterChallenge(), "Trigger Enter Challenge")
        bot.Wait.ForTime(2000)
        bot.States.AddCustomState(
            lambda: Keystroke.PressAndRelease(getattr(Key, "Enter").value),
            "Confirm Enter Challenge",
        )
        bot.Wait.ForMapToChange()

    elif entry_type == "dialog":
        x = entry["x"]
        y = entry["y"]
        dialog_id = entry["id"]
        bot.Dialogs.AtXY(x, y, dialog_id, "Enter Mission")

    else:
        from Py4GWCoreLib import ConsoleLog
        ConsoleLog("Recipe:Mission", f"Unknown entry type: {entry_type!r}")


def _register_step(bot: "Botting", step: Dict[str, Any], step_idx: int) -> None:
    """Register a single step via shared modular action handlers."""
    _register_shared_step(bot, step, step_idx, recipe_name="Mission")


def mission_run(bot: "Botting", mission_name: str) -> None:
    """Register FSM states to run a mission from a JSON data file."""
    from Py4GWCoreLib import ConsoleLog, Party

    data = _load_mission_data(mission_name)
    display_name = data.get("name", mission_name)
    outpost_id = data.get("outpost_id")
    max_heroes = data.get("max_heroes", 0)
    hero_team = str(data.get("hero_team", "") or "")
    entry = data.get("entry")
    steps = data.get("steps", [])
    inventory_guard_step = build_auto_inventory_guard_step("mission", data)
    total_steps = count_expanded_steps(steps) + (1 if inventory_guard_step and inventory_guard_step.get("check_on_start", True) else 0)
    register_recipe_context(bot, str(display_name), total_steps=total_steps)

    # 1) Travel to outpost
    if outpost_id:
        bot.Party.LeaveParty()
        bot.Map.Travel(target_map_id=outpost_id)

    if inventory_guard_step and inventory_guard_step.get("check_on_start", True):
        _register_shared_step(bot, inventory_guard_step, 0, recipe_name="Mission")

    # 2) Add heroes from config
    if max_heroes > 0:
        hero_ids = get_team_for_size(max_heroes, hero_team)
        if hero_ids:
            bot.Party.AddHeroList(hero_ids)
            bot.Wait.UntilCondition(
                lambda _expected=len(hero_ids): Party.IsPartyLoaded() and Party.GetHeroCount() >= _expected,
                duration=250,
            )
            bot.Wait.ForTime(500)

    def _set_anchor_to_current_phase_header() -> None:
        owner = getattr(bot, "_modular_owner", None)
        if owner is None or not hasattr(owner, "set_anchor"):
            return

        fsm = bot.config.FSM
        current_state = getattr(fsm, "current_state", None)
        states = getattr(fsm, "states", None)
        if current_state is None or not states:
            return

        try:
            idx = states.index(current_state)
        except ValueError:
            return

        for i in range(idx, -1, -1):
            state_name = str(getattr(states[i], "name", "") or "")
            if state_name.startswith("[H]"):
                owner.set_anchor(state_name)
                return

    # 3) Enter mission (anchor exactly before EnterChallenge)
    if entry and entry.get("type", "") == "enter_challenge":
        bot.States.AddCustomState(_set_anchor_to_current_phase_header, "Set Anchor Before Enter Challenge")
        _register_entry(bot, entry)
    elif outpost_id:
        bot.States.AddCustomState(_set_anchor_to_current_phase_header, "Set Anchor Before Enter Challenge")
        _register_entry(
            bot,
            {"type": "enter_challenge", "delay": 5000, "target_map_id": int(outpost_id or 0)},
        )
        if entry:
            _register_entry(bot, entry)

    # 4) Execute steps
    total_registered_steps = register_repeated_steps(
        bot,
        recipe_name="Mission",
        steps=steps,
        register_step=_register_step,
    )

    ConsoleLog(
        "Recipe:Mission",
        f"Registered mission: {display_name} ({total_registered_steps} expanded steps from {len(steps)} source steps, outpost {outpost_id})",
    )


def Mission(
    mission_name: str,
    name: Optional[str] = None,
    anchor: bool = False,
) -> Phase:
    """Create a Phase that runs a mission from a JSON data file."""
    if name is None:
        try:
            data = _load_mission_data(mission_name)
            name = str(data.get("name", mission_name))
        except FileNotFoundError:
            name = f"Mission: {mission_name}"

    return Phase(name, lambda bot: mission_run(bot, mission_name), anchor=anchor)
