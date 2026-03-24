from __future__ import annotations

from typing import Callable

from .step_context import StepContext
from .step_selectors import resolve_agent_xy_from_step, resolve_item_model_id_from_step
from .step_utils import wait_after_step


def handle_interact_npc(ctx: StepContext) -> None:
    name = ctx.step.get("name", "")

    def _interact_npc():
        coords = resolve_agent_xy_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            return
        x, y = coords
        yield from ctx.bot.Move._coro_xy_and_interact_npc(x, y, name)

    ctx.bot.States.AddCustomState(_interact_npc, name or "Interact NPC")
    wait_after_step(ctx.bot, ctx.step)


def handle_dialog(ctx: StepContext) -> None:
    dialog_id = ctx.step["id"]
    name = ctx.step.get("name", "")

    def _dialog():
        coords = resolve_agent_xy_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            return
        x, y = coords
        yield from ctx.bot.Dialogs._coro_at_xy(x, y, dialog_id)

    ctx.bot.States.AddCustomState(_dialog, name or "Dialog")
    wait_after_step(ctx.bot, ctx.step)


def handle_dialog_with_model(ctx: StepContext) -> None:
    model_id = int(str(ctx.step["model_id"]), 0)
    dialog_id = int(str(ctx.step["id"]), 0)
    name = ctx.step.get("name", "")
    ctx.bot.Dialogs.WithModel(model_id, dialog_id, name)
    wait_after_step(ctx.bot, ctx.step)


def handle_dialogs(ctx: StepContext) -> None:
    from Py4GWCoreLib import ConsoleLog, Player

    name = ctx.step.get("name", f"Dialogs {ctx.step_idx + 1}")
    interval_ms = int(ctx.step.get("interval_ms", 200))
    raw_ids = ctx.step.get("id", [])
    dialog_ids_raw = raw_ids if isinstance(raw_ids, (list, tuple)) else [raw_ids]

    dialog_ids: list[int] = []
    for value in dialog_ids_raw:
        try:
            dialog_ids.append(int(str(value), 0))
        except (TypeError, ValueError):
            ConsoleLog(f"Recipe:{ctx.recipe_name}", f"Invalid dialogs.id value at index {ctx.step_idx}: {value!r}")
            return

    def _dialogs():
        coords = resolve_agent_xy_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            return
        x, y = coords
        yield from ctx.bot.Move._coro_xy_and_interact_npc(x, y, name)
        for idx, dialog_id in enumerate(dialog_ids):
            Player.SendDialog(dialog_id)
            if idx < len(dialog_ids) - 1 and interval_ms > 0:
                yield from ctx.bot.Wait._coro_for_time(interval_ms)

    ctx.bot.States.AddCustomState(_dialogs, name)
    wait_after_step(ctx.bot, ctx.step)


def handle_dialog_multibox(ctx: StepContext) -> None:
    ctx.bot.Multibox.SendDialogToTarget(ctx.step["id"])
    wait_after_step(ctx.bot, ctx.step)


def handle_interact_gadget(ctx: StepContext) -> None:
    from Py4GWCoreLib import Range

    gadget_step = dict(ctx.step)
    if (
        "x" not in gadget_step
        and "y" not in gadget_step
        and "gadget" not in gadget_step
        and "target" not in gadget_step
        and "name_contains" not in gadget_step
        and "agent_name" not in gadget_step
        and "model_id" not in gadget_step
        and "nearest" not in gadget_step
    ):
        gadget_step["nearest"] = True
    if "max_dist" not in gadget_step:
        gadget_step["max_dist"] = Range.Compass.value

    def _interact_gadget():
        coords = resolve_agent_xy_from_step(
            gadget_step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="gadget",
            default_max_dist=Range.Compass.value,
        )
        if coords is None:
            return
        x, y = coords
        yield from ctx.bot.Interact._coro_with_gadget_at_xy(x, y)

    ctx.bot.States.AddCustomState(_interact_gadget, ctx.step.get("name", "Interact Gadget"))
    wait_after_step(ctx.bot, ctx.step)


def handle_interact_gadget_at_xy(ctx: StepContext) -> None:
    from Py4GWCoreLib import Range

    name = ctx.step.get("name", "Interact Gadget")

    def _interact_gadget_at_xy():
        coords = resolve_agent_xy_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="gadget",
            default_max_dist=Range.Compass.value,
        )
        if coords is None:
            return
        x, y = coords
        yield from ctx.bot.Interact._coro_with_gadget_at_xy(x, y)

    ctx.bot.States.AddCustomState(_interact_gadget_at_xy, name)
    wait_after_step(ctx.bot, ctx.step)


def handle_loot_chest(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, ConsoleLog, Player, Routines, SharedCommandType, Range

    chest_step = dict(ctx.step)
    if (
        "x" not in chest_step
        and "y" not in chest_step
        and "gadget" not in chest_step
        and "target" not in chest_step
        and "name_contains" not in chest_step
        and "agent_name" not in chest_step
        and "model_id" not in chest_step
        and "nearest" not in chest_step
    ):
        chest_step["nearest"] = True
    if "max_dist" not in chest_step:
        chest_step["max_dist"] = Range.Compass.value

    name = ctx.step.get("name", "Loot Chest")
    max_dist = float(ctx.step.get("max_dist", Range.Compass.value))
    multibox_raw = ctx.step.get("multibox", False)
    multibox = (
        multibox_raw.strip().lower() in ("1", "true", "yes", "on")
        if isinstance(multibox_raw, str)
        else bool(multibox_raw)
    )

    if max_dist <= 0:
        max_dist = 2500.0

    def _command_type_routine_in_message_is_active(account_email, shared_command_type):
        index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
        if index == -1 or message is None:
            return False
        if message.Command != shared_command_type:
            return False
        return True

    def _loot():
        coords = resolve_agent_xy_from_step(
            chest_step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="gadget",
            default_max_dist=Range.Compass.value,
        )
        if coords is None:
            yield
            return
        x, y = coords
        yield from ctx.bot.Move._coro_xy(x, y, name)
        yield from ctx.bot.Wait._coro_for_time(250)

        chests = AgentArray.GetGadgetArray()
        chests = AgentArray.Filter.ByDistance(chests, (x, y), max_dist)
        chests = AgentArray.Sort.ByDistance(chests, Player.GetXY())
        if not chests:
            ConsoleLog(f"Recipe:{ctx.recipe_name}", f"loot_chest found no chest near ({x}, {y})")
            yield
            return

        target = int(chests[0])
        Player.ChangeTarget(target)
        yield from Routines.Yield.wait(150)

        Player.Interact(target, False)
        yield from Routines.Yield.wait(150)

        if not multibox:
            yield
            return

        sender_email = Player.GetAccountEmail()
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()

        while _command_type_routine_in_message_is_active(sender_email, SharedCommandType.InteractWithTarget):
            yield from Routines.Yield.wait(250)
        while _command_type_routine_in_message_is_active(sender_email, SharedCommandType.PickUpLoot):
            yield from Routines.Yield.wait(1000)
        yield from Routines.Yield.wait(1000)

        for account in accounts:
            account_email = str(getattr(account, "AccountEmail", "") or "")
            if not account_email or account_email == sender_email:
                continue

            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                account_email,
                SharedCommandType.InteractWithTarget,
                (target, 0, 0, 0),
            )
            yield from Routines.Yield.wait(3000)

        yield

    ctx.bot.States.AddCustomState(_loot, name)
    wait_after_step(ctx.bot, ctx.step)


def handle_interact_item(ctx: StepContext) -> None:
    from Py4GWCoreLib import  Range
    max_dist_raw = ctx.step.get("max_dist", Range.Compass.value)
    try:
        max_dist = float(max_dist_raw)
    except (TypeError, ValueError):
        max_dist = 1200.0
    if max_dist <= 0:
        max_dist = 1200.0

    model_id = resolve_item_model_id_from_step(
        ctx.step,
        recipe_name=ctx.recipe_name,
        step_idx=ctx.step_idx,
    )
    has_model_filter = model_id is not None

    def _interact():
        from Py4GWCoreLib import Agent, AgentArray, Item, Player

        item_array = AgentArray.GetItemArray()
        px, py = Player.GetXY()
        item_array = AgentArray.Filter.ByDistance(item_array, (px, py), max_dist)
        if not item_array:
            yield
            return

        item_array = AgentArray.Sort.ByDistance(item_array, (px, py))
        target_ground_agent_id = 0
        if not has_model_filter:
            target_ground_agent_id = int(item_array[0])
        else:
            me = int(Player.GetAgentID())
            for ground_agent_id in item_array:
                owner = int(Agent.GetItemAgentOwnerID(ground_agent_id))
                if owner not in (0, me):
                    continue

                item_id = int(Agent.GetItemAgentItemID(ground_agent_id))
                if item_id <= 0:
                    continue

                if int(Item.GetModelID(item_id)) == model_id:
                    target_ground_agent_id = int(ground_agent_id)
                    break

        if target_ground_agent_id <= 0:
            yield
            return

        item_x, item_y = Agent.GetXY(target_ground_agent_id)
        yield from ctx.bot.Move._coro_xy(item_x, item_y, ctx.step.get("name", "Interact Item"))
        Player.Interact(target_ground_agent_id, call_target=False)
        yield from ctx.bot.Wait._coro_for_time(1000)

    ctx.bot.States.AddCustomState(_interact, "Interact Item")
    wait_after_step(ctx.bot, ctx.step)


def handle_use_item(ctx: StepContext) -> None:
    model_id = resolve_item_model_id_from_step(
        ctx.step,
        recipe_name=ctx.recipe_name,
        step_idx=ctx.step_idx,
    )
    if model_id is None:
        return

    def _use() -> None:
        from Py4GWCoreLib import GLOBAL_CACHE

        item_id = int(GLOBAL_CACHE.Inventory.GetFirstModelID(model_id))
        if item_id > 0:
            GLOBAL_CACHE.Inventory.UseItem(item_id)

    ctx.bot.States.AddCustomState(_use, f"UseItem {model_id}")
    wait_after_step(ctx.bot, ctx.step)


def handle_interact_quest_npc(ctx: StepContext) -> None:
    def _interact() -> None:
        from Py4GWCoreLib import Agent, AgentArray, Player

        ally_array = AgentArray.GetNPCMinipetArray()
        px, py = Player.GetXY()
        ally_array = AgentArray.Filter.ByDistance(ally_array, (px, py), 5000)
        quest_npcs = [a for a in ally_array if Agent.HasQuest(a)]
        if quest_npcs:
            Player.Interact(quest_npcs[0], call_target=False)

    ctx.bot.States.AddCustomState(_interact, "Interact Quest NPC")
    wait_after_step(ctx.bot, ctx.step)


def handle_interact_nearest_npc(ctx: StepContext) -> None:
    from Py4GWCoreLib import Range

    nearest_step = dict(ctx.step)
    nearest_step["nearest"] = True
    if "max_dist" not in nearest_step:
        nearest_step["max_dist"] = Range.Compass.value
    def _interact_nearest_npc():
        coords = resolve_agent_xy_from_step(
            nearest_step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
            default_max_dist=Range.Compass.value,
        )
        if coords is None:
            return
        x, y = coords
        yield from ctx.bot.Interact._coro_with_npc_at_xy(x, y)

    ctx.bot.States.AddCustomState(_interact_nearest_npc, ctx.step.get("name", "Interact Nearest NPC"))
    wait_after_step(ctx.bot, ctx.step)


def handle_skip_cinematic(ctx: StepContext) -> None:
    pre_wait_ms = int(ctx.step.get("wait_ms", 500))
    if pre_wait_ms > 0:
        ctx.bot.Wait.ForTime(pre_wait_ms)

    def _skip() -> None:
        from Py4GWCoreLib import Map

        if Map.IsInCinematic():
            Map.SkipCinematic()

    ctx.bot.States.AddCustomState(_skip, "Skip Cinematic")
    wait_after_step(ctx.bot, ctx.step)


def handle_key_press(ctx: StepContext) -> None:
    from Py4GWCoreLib import ConsoleLog, Key, Keystroke

    key_name = str(ctx.step["key"]).upper()
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
        ConsoleLog(f"Recipe:{ctx.recipe_name}", f"Unsupported key_press key: {key_name!r}")
        return

    ctx.bot.States.AddCustomState(
        lambda _k=mapped: Keystroke.PressAndRelease(getattr(Key, _k).value),
        f"KeyPress {key_name}",
    )
    wait_after_step(ctx.bot, ctx.step)


HANDLERS: dict[str, Callable[[StepContext], None]] = {
    "interact_npc": handle_interact_npc,
    "dialog": handle_dialog,
    "dialog_with_model": handle_dialog_with_model,
    "dialogs": handle_dialogs,
    "dialog_multibox": handle_dialog_multibox,
    "interact_gadget": handle_interact_gadget,
    "interact_gadget_at_xy": handle_interact_gadget_at_xy,
    "loot_chest": handle_loot_chest,
    "interact_item": handle_interact_item,
    "use_item": handle_use_item,
    "interact_quest_npc": handle_interact_quest_npc,
    "interact_nearest_npc": handle_interact_nearest_npc,
    "skip_cinematic": handle_skip_cinematic,
    "key_press": handle_key_press,
}
