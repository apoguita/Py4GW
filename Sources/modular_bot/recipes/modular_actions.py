"""
Shared step-action dispatcher for modular mission/quest recipes.

This file defines the union of actions supported by mission and quest recipes.
Every action supports an optional ``ms`` delay after execution (default: 500ms),
except ``wait`` where ``ms`` is the action itself.
"""

from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib import Botting


DEFAULT_STEP_DELAY_MS = 100


def _step_delay_ms(step: Dict[str, Any], default: int = DEFAULT_STEP_DELAY_MS) -> int:
    value = step.get("ms", default)
    try:
        ms = int(value)
    except (TypeError, ValueError):
        ms = default
    return ms if ms > 0 else 0


def _wait_after_step(bot: "Botting", step: Dict[str, Any]) -> None:
    ms = _step_delay_ms(step)
    if ms > 0:
        bot.Wait.ForTime(ms)


def register_step(bot: "Botting", step: Dict[str, Any], step_idx: int, recipe_name: str) -> None:
    """Register one JSON step onto the bot FSM."""
    from Py4GWCoreLib import ConsoleLog

    step_type = str(step.get("type", "")).strip()
    if not step_type:
        ConsoleLog(f"Recipe:{recipe_name}", f"Missing step type at index {step_idx}")
        return

    if step_type == "path":
        points = [tuple(p) for p in step["points"]]
        name = step.get("name", f"Path {step_idx + 1}")
        bot.Move.FollowPath(points, step_name=name)
        _wait_after_step(bot, step)

    elif step_type == "auto_path":
        points = [tuple(p) for p in step["points"]]
        name = step.get("name", f"AutoPath {step_idx + 1}")
        bot.Move.FollowAutoPath(points, step_name=name)
        _wait_after_step(bot, step)

    elif step_type == "auto_path_delayed":
        points = [tuple(p) for p in step["points"]]
        name = step.get("name", f"AutoPathDelayed {step_idx + 1}")
        delay_ms = int(step.get("delay_ms", 35000))
        if delay_ms < 0:
            delay_ms = 0
        for point_i, (x, y) in enumerate(points):
            step_name = f"{name} [{point_i + 1}/{len(points)}]"
            bot.Move.XY(x, y, step_name)
            if point_i < len(points) - 1 and delay_ms > 0:
                bot.Wait.ForTime(delay_ms)
        _wait_after_step(bot, step)

    elif step_type == "wait":
        bot.Wait.ForTime(_step_delay_ms(step))

    elif step_type == "wait_out_of_combat":
        bot.Wait.UntilOutOfCombat()
        _wait_after_step(bot, step)

    elif step_type == "wait_map_load":
        map_id = step["map_id"]
        bot.Wait.ForMapLoad(target_map_id=map_id)
        _wait_after_step(bot, step)

    elif step_type == "move":
        x, y = step["x"], step["y"]
        name = step.get("name", "")
        bot.Move.XY(x, y, name)
        _wait_after_step(bot, step)

    elif step_type == "exit_map":
        x, y = step["x"], step["y"]
        target_map_id = step.get("target_map_id", 0)
        bot.Move.XYAndExitMap(x, y, target_map_id)
        _wait_after_step(bot, step)

    elif step_type == "interact_npc":
        x, y = step["x"], step["y"]
        name = step.get("name", "")
        bot.Move.XYAndInteractNPC(x, y, name)
        _wait_after_step(bot, step)

    elif step_type == "dialog":
        x, y = step["x"], step["y"]
        dialog_id = step["id"]
        name = step.get("name", "")
        bot.Dialogs.AtXY(x, y, dialog_id, name)
        _wait_after_step(bot, step)

    elif step_type == "dialogs":
        from Py4GWCoreLib import Player

        x, y = step["x"], step["y"]
        name = step.get("name", f"Dialogs {step_idx + 1}")
        interval_ms = int(step.get("interval_ms", 500))
        raw_ids = step.get("id", [])
        dialog_ids_raw = raw_ids if isinstance(raw_ids, (list, tuple)) else [raw_ids]

        dialog_ids: list[int] = []
        for value in dialog_ids_raw:
            try:
                dialog_ids.append(int(str(value), 0))
            except (TypeError, ValueError):
                ConsoleLog(f"Recipe:{recipe_name}", f"Invalid dialogs.id value at index {step_idx}: {value!r}")
                return

        bot.Move.XYAndInteractNPC(x, y, name)
        for idx, dialog_id in enumerate(dialog_ids):
            bot.States.AddCustomState(
                lambda _d=dialog_id: Player.SendDialog(_d),
                f"{name} [{idx + 1}/{len(dialog_ids)}]",
            )
            if idx < len(dialog_ids) - 1 and interval_ms > 0:
                bot.Wait.ForTime(interval_ms)
        _wait_after_step(bot, step)

    elif step_type == "dialog_multibox":
        dialog_id = step["id"]
        bot.Multibox.SendDialogToTarget(dialog_id)
        _wait_after_step(bot, step)

    elif step_type == "interact_gadget":
        def _interact():
            from Py4GWCoreLib import AgentArray, Player

            gadget_array = AgentArray.GetGadgetArray()
            px, py = Player.GetXY()
            gadget_array = AgentArray.Filter.ByDistance(gadget_array, (px, py), 800)
            if gadget_array:
                Player.Interact(gadget_array[0], call_target=False)

        bot.States.AddCustomState(_interact, "Interact Gadget")
        _wait_after_step(bot, step)

    elif step_type == "interact_item":
        def _interact():
            from Py4GWCoreLib import AgentArray, Player

            item_array = AgentArray.GetItemArray()
            px, py = Player.GetXY()
            item_array = AgentArray.Filter.ByDistance(item_array, (px, py), 1200)
            if item_array:
                item_array = AgentArray.Sort.ByDistance(item_array, (px, py))
                Player.Interact(item_array[0], call_target=False)

        bot.States.AddCustomState(_interact, "Interact Item")
        _wait_after_step(bot, step)

    elif step_type == "interact_quest_npc":
        def _interact():
            from Py4GWCoreLib import AgentArray, Agent, Player

            ally_array = AgentArray.GetNPCMinipetArray()
            px, py = Player.GetXY()
            ally_array = AgentArray.Filter.ByDistance(ally_array, (px, py), 5000)
            quest_npcs = [a for a in ally_array if Agent.HasQuest(a)]
            if quest_npcs:
                Player.Interact(quest_npcs[0], call_target=False)

        bot.States.AddCustomState(_interact, "Interact Quest NPC")
        _wait_after_step(bot, step)

    elif step_type == "interact_nearest_npc":
        def _interact():
            from Py4GWCoreLib import AgentArray, Player

            npc_array = AgentArray.GetNPCMinipetArray()
            px, py = Player.GetXY()
            npc_array = AgentArray.Filter.ByDistance(npc_array, (px, py), 800)
            if npc_array:
                Player.Interact(npc_array[0], call_target=False)

        bot.States.AddCustomState(_interact, "Interact Nearest NPC")
        _wait_after_step(bot, step)

    elif step_type == "skip_cinematic":
        # Backward compatible pre-wait key + standardized post-step ms.
        pre_wait_ms = int(step.get("wait_ms", 500))
        if pre_wait_ms > 0:
            bot.Wait.ForTime(pre_wait_ms)

        def _skip():
            from Py4GWCoreLib import Map
            if Map.IsInCinematic():
                Map.SkipCinematic()

        bot.States.AddCustomState(_skip, "Skip Cinematic")
        _wait_after_step(bot, step)

    elif step_type == "set_title":
        title_id = step["id"]
        bot.Player.SetTitle(title_id)
        _wait_after_step(bot, step)

    elif step_type == "drop_bundle":
        from Py4GWCoreLib import Keystroke, Key
        bot.States.AddCustomState(lambda: Keystroke.PressAndRelease(getattr(Key, "F2").value), "F2 Drop Bundle")
        bot.Wait.ForTime(200)
        bot.States.AddCustomState(lambda: Keystroke.PressAndRelease(getattr(Key, "F1").value), "F1 Drop Bundle")
        bot.Wait.ForTime(200)
        _wait_after_step(bot, step)

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
            ConsoleLog(f"Recipe:{recipe_name}", f"Unsupported key_press key: {key_name!r}")
            return

        from Py4GWCoreLib import Keystroke, Key
        bot.States.AddCustomState(
            lambda _k=mapped: Keystroke.PressAndRelease(getattr(Key, _k).value),
            f"KeyPress {key_name}",
        )
        _wait_after_step(bot, step)

    elif step_type == "force_hero_state":
        raw_state = str(step.get("state", "")).strip().lower()
        behavior_map = {
            "fight": 0,
            "guard": 1,
            "avoid": 2,
        }

        if "behavior" in step:
            try:
                behavior = int(step["behavior"])
            except (TypeError, ValueError):
                behavior = -1
        else:
            behavior = behavior_map.get(raw_state, -1)

        if behavior not in (0, 1, 2):
            ConsoleLog(
                f"Recipe:{recipe_name}",
                f"Invalid force_hero_state at index {step_idx}: state={raw_state!r}, behavior={step.get('behavior')!r}",
            )
            return

        state_name = step.get("name", f"Force Hero State ({raw_state or behavior})")

        def _set_hero_behavior_all(behavior_value: int = behavior):
            from Py4GWCoreLib import Party
            for hero in Party.GetHeroes():
                hero_agent_id = getattr(hero, "agent_id", 0)
                if hero_agent_id:
                    Party.Heroes.SetHeroBehavior(hero_agent_id, behavior_value)

        bot.States.AddCustomState(_set_hero_behavior_all, state_name)
        _wait_after_step(bot, step)

    elif step_type == "flag_heroes":
        x, y = step["x"], step["y"]
        bot.Party.FlagAllHeroes(x, y)
        _wait_after_step(bot, step)

    elif step_type == "unflag_heroes":
        bot.Party.UnflagAllHeroes()
        _wait_after_step(bot, step)

    elif step_type == "resign":
        bot.Multibox.ResignParty()
        _wait_after_step(bot, step)

    elif step_type == "wait_map_change":
        target_map_id = step["target_map_id"]
        bot.Wait.ForMapToChange(target_map_id=target_map_id)
        _wait_after_step(bot, step)

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
        _wait_after_step(bot, step)

    else:
        ConsoleLog(f"Recipe:{recipe_name}", f"Unknown step type: {step_type!r} at index {step_idx}")

