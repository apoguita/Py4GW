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
from .modular_actions import register_step as _register_shared_step


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
    """Register a single step via shared modular action handlers."""
    _register_shared_step(bot, step, step_idx, recipe_name="Mission")


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


