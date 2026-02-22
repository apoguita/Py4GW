"""
Quest recipe - run a quest from a structured JSON data file.

Quest files:
    Sources/modular_bot/quests/<quest_name>.json

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


def _get_quests_dir() -> str:
    """Return the quests data directory path."""
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "quests"))


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


def _load_quest_data(quest_name: str) -> Dict[str, Any]:
    """
    Load quest data from ``Sources/modular_bot/quests/<quest_name>.json``.

    Args:
        quest_name: File name without extension (e.g. "ruins_of_surmia").

    Returns:
        Parsed JSON dict.
    """
    quests_dir = _get_quests_dir()
    filepath = os.path.join(quests_dir, f"{quest_name}.json")

    if not os.path.isfile(filepath):
        available = []
        if os.path.isdir(quests_dir):
            available = [f[:-5] for f in os.listdir(quests_dir) if f.endswith(".json")]
        raise FileNotFoundError(
            f"Quest data not found: {filepath}\n"
            f"Available quests: {available}"
        )

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_available_quests() -> List[str]:
    """
    Return all available quest names (without .json extension).

    Excludes non-quest support files such as ``hero_config.json``.
    """
    quests_dir = _get_quests_dir()
    if not os.path.isdir(quests_dir):
        return []

    names = []
    for filename in os.listdir(quests_dir):
        if not filename.endswith(".json"):
            continue
        if filename.lower() == "hero_config.json":
            continue
        names.append(filename[:-5])

    return sorted(names)


def _register_take_quest(bot: "Botting", take_quest: Optional[Dict[str, Any]]) -> None:
    """
    Register states to take quest from a specific NPC location.

    Expected take_quest keys:
    - quest_npc_location: [x, y]
    - dialog_id: int/hex string or list of int/hex strings
    - wait_ms: optional delay before dialog
    - name: optional step name
    """
    if not take_quest:
        return

    from Py4GWCoreLib import ConsoleLog, Player

    npc_location = take_quest.get("quest_npc_location")
    dialog_id_raw = take_quest.get("dialog_id")
    wait_ms = int(take_quest.get("wait_ms", 1000))
    name = take_quest.get("name", "Take Quest")
    if not isinstance(npc_location, list) or len(npc_location) != 2:
        ConsoleLog("Recipe:Quest", "Invalid take_quest.quest_npc_location; expected [x, y].")
        return
    if dialog_id_raw is None:
        ConsoleLog("Recipe:Quest", "Invalid take_quest.dialog_id; value is required.")
        return

    x, y = npc_location[0], npc_location[1]
    bot.Move.XYAndInteractNPC(x, y, name)
    bot.Wait.ForTime(wait_ms)

    dialog_ids_raw = dialog_id_raw if isinstance(dialog_id_raw, (list, tuple)) else [dialog_id_raw]
    dialog_ids: List[int] = []
    for value in dialog_ids_raw:
        try:
            dialog_ids.append(int(str(value), 0))
        except (TypeError, ValueError):
            ConsoleLog("Recipe:Quest", f"Invalid take_quest.dialog_id value: {value!r}")
            return

    for idx, dialog_id in enumerate(dialog_ids):
        bot.States.AddCustomState(lambda _d=dialog_id: Player.SendDialog(_d), f"Take Quest Dialog {idx + 1}")
        # Keep a short delay between multi-step quest dialogs
        bot.Wait.ForTime(wait_ms if len(dialog_ids) > 1 else 1000)


def _register_step(bot: "Botting", step: Dict[str, Any], step_idx: int) -> None:
    """Register a single step via shared modular action handlers."""
    _register_shared_step(bot, step, step_idx, recipe_name="Quest")


def quest_run(bot: "Botting", quest_name: str) -> None:
    """
    Register FSM states to run a quest from a JSON data file.

    Args:
        bot: Botting instance to register states on.
        quest_name: Quest data file name (without .json extension).
    """
    from Py4GWCoreLib import ConsoleLog

    data = _load_quest_data(quest_name)
    display_name = data.get("name", quest_name)
    max_heroes = data.get("max_heroes", 0)
    hero_team = str(data.get("hero_team", "") or "")
    take_quest = data.get("take_quest")
    steps = data.get("steps", [])

    travel_outpost_id = (take_quest or {}).get("outpost_id")

    # 1. Travel to outpost
    if travel_outpost_id:
        bot.Map.Travel(target_map_id=travel_outpost_id)

    # 2. Add heroes from config
    if max_heroes > 0:
        hero_ids = get_team_for_size(max_heroes, hero_team)
        if hero_ids:
            bot.Party.LeaveParty()
            bot.Party.AddHeroList(hero_ids)

    # 3. Take quest in outpost via NPC dialog
    _register_take_quest(bot, take_quest)

    # 4. Execute quest steps
    for idx, step in enumerate(steps):
        _register_step(bot, step, idx)

    ConsoleLog(
        "Recipe:Quest",
        f"Registered quest: {display_name} ({len(steps)} steps, outpost {travel_outpost_id})",
    )


def Quest(
    quest_name: str,
    name: Optional[str] = None,
) -> Phase:
    """
    Create a Phase that runs a quest from a JSON data file.

    Args:
        quest_name: File name without extension (e.g. "ruins_of_surmia").
        name: Optional display name (auto-generated from quest data if None).

    Returns:
        A Phase object ready to use in ModularBot.
    """
    if name is None:
        try:
            data = _load_quest_data(quest_name)
            name = str(data.get("name", quest_name))
        except FileNotFoundError:
            name = f"Quest: {quest_name}"

    return Phase(name, lambda bot: quest_run(bot, quest_name))

