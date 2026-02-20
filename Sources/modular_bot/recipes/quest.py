"""
Quest recipe - run a quest from a structured JSON data file.

Quest files live in:
    Sources/modular_bot/quests/<quest_name>.json

Minimal quest template:
    {
      "name": "Quest Name",
      "max_heroes": 4,
      "take_quest": {
        "outpost_id": 30,
        "quest_npc_location": [0, 0],
        "dialog_id": "0x00000000",
        "wait_ms": 2000,
        "name": "Take Quest"
      },
      "steps": []
    }

Top-level quest block catalog:
    - take_quest (optional):
      {
        "outpost_id": 30,
        "quest_npc_location": [0, 0],
        "dialog_id": "0x00000000",
        "wait_ms": 2000,
        "name": "Take Quest"
      }

    take_quest options:
    - outpost_id: optional
    - quest_npc_location: required [x, y]
    - dialog_id: required; int, "0x...", or list of them
    - wait_ms: optional
    - name: optional

Step catalog (copy/paste):
    {"type": "path", "points": [[0, 0], [100, 100]], "name": "Path 1"}
    {"type": "auto_path", "points": [[0, 0], [100, 100]], "name": "AutoPath 1"}
    {"type": "wait", "ms": 1000}
    {"type": "wait_out_of_combat"}
    {"type": "wait_map_load", "map_id": 72}
    {"type": "move", "x": 0, "y": 0, "name": "Move"}
    {"type": "exit_map", "x": 0, "y": 0, "target_map_id": 0}
    {"type": "interact_npc", "x": 0, "y": 0, "name": "Talk NPC"}
    {"type": "interact_gadget", "ms": 2000}
    {"type": "interact_item", "ms": 2000}
    {"type": "interact_quest_npc", "ms": 5000}
    {"type": "interact_nearest_npc", "ms": 5000}
    {"type": "dialog", "x": 0, "y": 0, "id": 0, "name": "Dialog"}
    {"type": "dialogs", "x": 0, "y": 0, "id": ["0x2", "0x15", "0x3"], "name": "Dialogs"}
    {"type": "dialog_multibox", "id": 0}
    {"type": "skip_cinematic", "wait_ms": 500}
    {"type": "set_title", "id": 0}
    {"type": "flag_heroes", "x": 0, "y": 0, "ms": 2000}
    {"type": "unflag_heroes", "ms": 2000}
    {"type": "resign"}
    {"type": "wait_map_change", "target_map_id": 0}
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting

from ..phase import Phase


def _get_quests_dir() -> str:
    """Return the quests data directory path."""
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "quests"))


def _load_hero_config() -> Dict[str, Any]:
    """
    Load hero configuration from ``Sources/modular_bot/quests/hero_config.json``.

    Returns:
        Dict with keys ``party_4``, ``party_6``, ``party_8`` mapping
        to lists of hero IDs.
    """
    filepath = os.path.join(_get_quests_dir(), "hero_config.json")
    if not os.path.isfile(filepath):
        return {"party_4": [], "party_6": [], "party_8": []}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


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
    """Register a single quest step as FSM state(s)."""
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

    elif step_type == "dialogs":
        from Py4GWCoreLib import ConsoleLog, Player

        x, y = step["x"], step["y"]
        name = step.get("name", f"Dialogs {step_idx + 1}")
        interval_ms = int(step.get("interval_ms", 500))
        raw_ids = step.get("id", [])
        dialog_ids_raw = raw_ids if isinstance(raw_ids, (list, tuple)) else [raw_ids]

        dialog_ids: List[int] = []
        for value in dialog_ids_raw:
            try:
                dialog_ids.append(int(str(value), 0))
            except (TypeError, ValueError):
                ConsoleLog("Recipe:Quest", f"Invalid dialogs.id value at index {step_idx}: {value!r}")
                return

        bot.Move.XYAndInteractNPC(x, y, name)
        for idx, dialog_id in enumerate(dialog_ids):
            bot.States.AddCustomState(
                lambda _d=dialog_id: Player.SendDialog(_d),
                f"{name} [{idx + 1}/{len(dialog_ids)}]",
            )
            if idx < len(dialog_ids) - 1:
                bot.Wait.ForTime(interval_ms)

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

        bot.States.AddCustomState(_make_gadget_interact(), "Interact Gadget")
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

        bot.States.AddCustomState(_make_item_interact(), "Interact Item")
        bot.Wait.ForTime(ms)

    elif step_type == "interact_quest_npc":
        ms = step.get("ms", 5000)

        def _make_quest_interact():
            def _interact():
                from Py4GWCoreLib import AgentArray, Agent, Player
                ally_array = AgentArray.GetNPCMinipetArray()
                px, py = Player.GetXY()
                ally_array = AgentArray.Filter.ByDistance(ally_array, (px, py), 5000)
                quest_npcs = [a for a in ally_array if Agent.HasQuest(a)]
                if quest_npcs:
                    Player.Interact(quest_npcs[0], call_target=False)
            return _interact

        bot.States.AddCustomState(_make_quest_interact(), "Interact Quest NPC")
        bot.Wait.ForTime(ms)

    elif step_type == "interact_nearest_npc":
        ms = step.get("ms", 5000)

        def _make_npc_interact():
            def _interact():
                from Py4GWCoreLib import AgentArray, Player
                npc_array = AgentArray.GetNPCMinipetArray()
                px, py = Player.GetXY()
                npc_array = AgentArray.Filter.ByDistance(npc_array, (px, py), 800)
                if npc_array:
                    Player.Interact(npc_array[0], call_target=False)
            return _interact

        bot.States.AddCustomState(_make_npc_interact(), "Interact Nearest NPC")
        bot.Wait.ForTime(ms)

    elif step_type == "skip_cinematic":
        ms = step.get("wait_ms", 500)

        def _make_skip_cinematic():
            def _skip():
                from Py4GWCoreLib import Map
                if Map.IsInCinematic():
                    Map.SkipCinematic()
            return _skip

        bot.Wait.ForTime(ms)
        bot.States.AddCustomState(_make_skip_cinematic(), "Skip Cinematic")
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
        ConsoleLog("Recipe:Quest", f"Unknown step type: {step_type!r} at index {step_idx}")


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
    take_quest = data.get("take_quest")
    steps = data.get("steps", [])

    travel_outpost_id = (take_quest or {}).get("outpost_id")

    # 1. Travel to outpost
    if travel_outpost_id:
        bot.Map.Travel(target_map_id=travel_outpost_id)

    # 2. Add heroes from config
    if max_heroes > 0:
        hero_config = _load_hero_config()
        party_key = f"party_{max_heroes}"
        hero_ids = hero_config.get(party_key, [])
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

