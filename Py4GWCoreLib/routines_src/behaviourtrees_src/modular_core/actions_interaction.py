"""
actions_interaction module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from typing import Callable

from .actions_party_toggles import (
    apply_auto_combat_state,
    apply_auto_looting_state,
    current_auto_combat_enabled,
    current_auto_looting_enabled,
)
from .step_registration import modular_step
from .step_context import StepContext
from .step_selectors import resolve_agent_xy_from_step, resolve_item_model_id_from_step
from .step_utils import cutscene_active, wait_after_step


def _wrap_dialog_with_auto_state_guard(ctx: StepContext, action_factory: Callable):
    def _guarded_dialog():
        looting_was_enabled = current_auto_looting_enabled(ctx.bot)
        combat_was_enabled = current_auto_combat_enabled(ctx.bot)
        pause_on_danger_exists = bool(ctx.bot.Properties.exists("pause_on_danger"))
        pause_on_danger_was_active = (
            bool(ctx.bot.Properties.IsActive("pause_on_danger")) if pause_on_danger_exists else False
        )

        if looting_was_enabled:
            apply_auto_looting_state(ctx.bot, False)
        if combat_was_enabled:
            apply_auto_combat_state(ctx.bot, False)

        try:
            yield from action_factory()
        finally:
            if looting_was_enabled:
                apply_auto_looting_state(ctx.bot, True)
            if combat_was_enabled:
                apply_auto_combat_state(ctx.bot, True)
            if pause_on_danger_exists:
                ctx.bot.Properties.ApplyNow("pause_on_danger", "active", pause_on_danger_was_active)

    return _guarded_dialog


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
        yield from ctx.bot.Move._coro_xy(x, y, step_name=name or "Interact NPC")
        if cutscene_active():
            return
        yield from ctx.bot.Interact._coro_with_npc_at_xy(x, y, step_name=name)

    ctx.bot.States.AddCustomState(_interact_npc, name or "Interact NPC")
    wait_after_step(ctx.bot, ctx.step)


def handle_dialog(ctx: StepContext) -> None:
    dialog_id = ctx.step["id"]
    name = ctx.step.get("name", "")

    def _dialog_core():
        coords = resolve_agent_xy_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            return
        x, y = coords
        yield from ctx.bot.Move._coro_xy(x, y, step_name=name or "Dialog")
        if cutscene_active():
            return
        yield from ctx.bot.Dialogs._coro_at_xy(x, y, dialog_id)

    ctx.bot.States.AddCustomState(_dialog_core, name or "Dialog")
    wait_after_step(ctx.bot, ctx.step)


def handle_dialog_with_model(ctx: StepContext) -> None:
    from Py4GWCoreLib import Agent, Routines

    model_id = int(str(ctx.step["model_id"]), 0)
    dialog_id = int(str(ctx.step["id"]), 0)
    name = ctx.step.get("name", "")

    def _dialog_with_model():
        agent_id = Routines.Agents.GetAgentIDByModelID(model_id)
        x, y = Agent.GetXY(agent_id)
        yield from ctx.bot.Move._coro_xy(x, y, step_name=name or "Dialog With Model")
        if cutscene_active():
            return
        yield from ctx.bot.Dialogs._coro_at_xy(x, y, dialog_id)

    ctx.bot.States.AddCustomState(_dialog_with_model, name or "Dialog With Model")
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

    def _dialogs_core():
        coords = resolve_agent_xy_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            return
        x, y = coords
        yield from ctx.bot.Move._coro_xy(x, y, step_name=name)
        if cutscene_active():
            return
        yield from ctx.bot.Interact._coro_with_npc_at_xy(x, y, step_name=name)
        if cutscene_active():
            return
        for idx, dialog_id in enumerate(dialog_ids):
            if cutscene_active():
                return
            Player.SendDialog(dialog_id)
            if idx < len(dialog_ids) - 1 and interval_ms > 0:
                yield from ctx.bot.Wait._coro_for_time(interval_ms)
                if cutscene_active():
                    return

    ctx.bot.States.AddCustomState(_dialogs_core, name)
    wait_after_step(ctx.bot, ctx.step)


def handle_dialog_multibox(ctx: StepContext) -> None:
    from Py4GWCoreLib import ConsoleLog, GLOBAL_CACHE, Player, Routines, SharedCommandType

    name = ctx.step.get("name", f"Dialog Multibox {ctx.step_idx + 1}")
    interval_ms = int(ctx.step.get("interval_ms", 200))
    send_wait_step_ms = max(10, int(ctx.step.get("multibox_wait_step_ms", 50)))
    send_timeout_ms = max(250, int(ctx.step.get("multibox_timeout_ms", 5000)))
    raw_ids = ctx.step.get("id", [])
    dialog_ids_raw = raw_ids if isinstance(raw_ids, (list, tuple)) else [raw_ids]

    dialog_ids: list[int] = []
    for value in dialog_ids_raw:
        try:
            dialog_ids.append(int(str(value), 0))
        except (TypeError, ValueError):
            ConsoleLog(f"Recipe:{ctx.recipe_name}", f"Invalid dialog_multibox.id value at index {ctx.step_idx}: {value!r}")
            return

    def _wait_for_send_dialog_to_target(sender_email: str, refs: list[tuple[str, int]]):
        if not refs:
            return

        from time import monotonic

        deadline = monotonic() + (send_timeout_ms / 1000.0)
        pending = {(email, idx) for email, idx in refs if idx >= 0}

        while pending and monotonic() < deadline:
            if cutscene_active():
                return
            completed: list[tuple[str, int]] = []
            for account_email, message_index in pending:
                message = GLOBAL_CACHE.ShMem.GetInbox(message_index)
                is_same_message = (
                    bool(getattr(message, "Active", False))
                    and str(getattr(message, "ReceiverEmail", "") or "") == account_email
                    and str(getattr(message, "SenderEmail", "") or "") == sender_email
                    and int(getattr(message, "Command", -1)) == int(SharedCommandType.SendDialogToTarget)
                )
                if not is_same_message:
                    completed.append((account_email, message_index))

            for key in completed:
                pending.discard(key)

            if pending:
                yield from Routines.Yield.wait(send_wait_step_ms)

    def _dialogs_multibox_core():
        coords = resolve_agent_xy_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is not None:
            x, y = coords
            yield from ctx.bot.Move._coro_xy(x, y, step_name=name)
            if cutscene_active():
                return
            yield from ctx.bot.Interact._coro_with_npc_at_xy(x, y, step_name=name)
            if cutscene_active():
                return

        sender_email = str(Player.GetAccountEmail() or "")
        target_id = int(Player.GetTargetID() or 0)
        if target_id <= 0:
            ConsoleLog(f"Recipe:{ctx.recipe_name}", f"dialog_multibox has no target at step index {ctx.step_idx}")
            return

        account_emails: list[str] = []
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            account_email = str(getattr(account, "AccountEmail", "") or "")
            if not account_email or account_email == sender_email:
                continue
            account_emails.append(account_email)

        for idx, dialog_id in enumerate(dialog_ids):
            if cutscene_active():
                return
            Player.SendDialog(dialog_id)

            sent_messages: list[tuple[str, int]] = []
            for account_email in account_emails:
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.SendDialogToTarget,
                    (float(target_id), float(dialog_id), 0.0, 0.0),
                )
                sent_messages.append((account_email, int(message_index)))

            yield from _wait_for_send_dialog_to_target(sender_email, sent_messages)
            if cutscene_active():
                return
            if idx < len(dialog_ids) - 1 and interval_ms > 0:
                yield from ctx.bot.Wait._coro_for_time(interval_ms)
                if cutscene_active():
                    return

    ctx.bot.States.AddCustomState(_dialogs_multibox_core, name)
    wait_after_step(ctx.bot, ctx.step)


def handle_interact_gadget(ctx: StepContext) -> None:
    from Py4GWCoreLib import Range

    gadget_step = dict(ctx.step)
    if (
        "point" not in gadget_step
        and "x" not in gadget_step
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
        if cutscene_active():
            return

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
        if cutscene_active():
            return

    ctx.bot.States.AddCustomState(_interact_gadget_at_xy, name)
    wait_after_step(ctx.bot, ctx.step)


def handle_loot_chest(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, ConsoleLog, Player, Routines, SharedCommandType, Range

    chest_step = dict(ctx.step)
    if (
        "point" not in chest_step
        and "x" not in chest_step
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
        if cutscene_active():
            return
        yield from ctx.bot.Wait._coro_for_time(250)
        if cutscene_active():
            return

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
        if cutscene_active():
            return

        Player.Interact(target, False)
        yield from Routines.Yield.wait(150)
        if cutscene_active():
            return

        if not multibox:
            yield
            return

        sender_email = str(Player.GetAccountEmail() or "")
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sender_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(sender_email) if sender_email else None
        sender_party_id = int(getattr(sender_account.AgentPartyData, "PartyID", 0) or 0) if sender_account else 0
        sender_map_id = int(getattr(sender_account.AgentData.Map, "MapID", 0) or 0) if sender_account else 0
        sender_region = int(getattr(sender_account.AgentData.Map, "Region", 0) or 0) if sender_account else 0
        sender_district = int(getattr(sender_account.AgentData.Map, "District", 0) or 0) if sender_account else 0
        sender_language = int(getattr(sender_account.AgentData.Map, "Language", 0) or 0) if sender_account else 0

        while _command_type_routine_in_message_is_active(sender_email, SharedCommandType.InteractWithTarget):
            if cutscene_active():
                return
            yield from Routines.Yield.wait(250)
        while _command_type_routine_in_message_is_active(sender_email, SharedCommandType.PickUpLoot):
            if cutscene_active():
                return
            yield from Routines.Yield.wait(1000)
        yield from Routines.Yield.wait(1000)
        if cutscene_active():
            return

        recipients_sent = 0
        for account in accounts:
            account_email = str(getattr(account, "AccountEmail", "") or "")
            if not account_email or account_email == sender_email:
                continue

            if sender_party_id > 0:
                account_party_id = int(getattr(account.AgentPartyData, "PartyID", 0) or 0)
                if account_party_id != sender_party_id:
                    continue

            account_map_id = int(getattr(account.AgentData.Map, "MapID", 0) or 0)
            account_region = int(getattr(account.AgentData.Map, "Region", 0) or 0)
            account_district = int(getattr(account.AgentData.Map, "District", 0) or 0)
            account_language = int(getattr(account.AgentData.Map, "Language", 0) or 0)
            if (
                sender_map_id > 0
                and (
                    account_map_id != sender_map_id
                    or account_region != sender_region
                    or account_district != sender_district
                    or account_language != sender_language
                )
            ):
                continue

            message_index = int(GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                account_email,
                SharedCommandType.InteractWithTarget,
                (target, 0, 0, 0),
            ))
            if message_index < 0:
                ConsoleLog(
                    f"Recipe:{ctx.recipe_name}",
                    (
                        "loot_chest multibox dispatch failed "
                        f"sender={sender_email} receiver={account_email} target={target} "
                        f"sender_party={sender_party_id} receiver_party={int(getattr(account.AgentPartyData, 'PartyID', 0) or 0)}"
                    ),
                )
                continue
            recipients_sent += 1
            yield from Routines.Yield.wait(3000)
            if cutscene_active():
                return

        if recipients_sent == 0:
            ConsoleLog(
                f"Recipe:{ctx.recipe_name}",
                (
                    "loot_chest multibox found no valid same-party same-map recipients; "
                    f"sender={sender_email} target={target} sender_party={sender_party_id} map={sender_map_id}"
                ),
            )

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
        if cutscene_active():
            return
        Player.Interact(target_ground_agent_id, call_target=False)
        yield from ctx.bot.Wait._coro_for_time(1000)
        if cutscene_active():
            return

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

        if cutscene_active():
            return
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
        if cutscene_active():
            return

    ctx.bot.States.AddCustomState(_interact_nearest_npc, ctx.step.get("name", "Interact Nearest NPC"))
    wait_after_step(ctx.bot, ctx.step)


def handle_skip_cutscene(ctx: StepContext) -> None:
    wait_ms = int(ctx.step.get("wait_ms", ctx.step.get("timeout_ms", 10000)))
    poll_ms = max(50, int(ctx.step.get("poll_ms", 250)))

    def _skip():
        from time import monotonic
        from Py4GWCoreLib import GLOBAL_CACHE, Map

        deadline = monotonic() + (max(0, wait_ms) / 1000.0)
        while monotonic() < deadline:
            if Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded() and Map.IsInCinematic():
                Map.SkipCinematic()
                Map.SkipCinematic()
                break
            yield from ctx.bot.Wait._coro_for_time(poll_ms)

        while Map.IsMapReady() and Map.IsInCinematic():
            yield from ctx.bot.Wait._coro_for_time(poll_ms)

    ctx.bot.States.AddCustomState(_skip, "Skip Cutscene")
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


def handle_emote(ctx: StepContext) -> None:
    from Py4GWCoreLib import Player

    raw_command = str(
        ctx.step.get("command", ctx.step.get("emote", ctx.step.get("value", "kneel"))) or "kneel"
    ).strip()
    command = raw_command[1:] if raw_command.startswith("/") else raw_command
    if not command:
        command = "kneel"

    ctx.bot.States.AddCustomState(
        lambda _cmd=command: Player.SendChatCommand(_cmd),
        ctx.step.get("name", f"Emote /{command}"),
    )
    wait_after_step(ctx.bot, ctx.step)


# Decorator-driven step registration bindings.
modular_step(
    step_type="dialog",
    category="interaction",
    allowed_params=("id", "name"),
    node_class_name="DialogNode",
)(handle_dialog)
modular_step(
    step_type="dialog_multibox",
    category="interaction",
    allowed_params=("id", "interval_ms", "multibox_timeout_ms", "multibox_wait_step_ms", "name"),
    node_class_name="DialogMultiboxNode",
)(handle_dialog_multibox)
modular_step(
    step_type="dialog_with_model",
    category="interaction",
    allowed_params=("id", "model_id", "name"),
    node_class_name="DialogWithModelNode",
)(handle_dialog_with_model)
modular_step(
    step_type="dialogs",
    category="interaction",
    allowed_params=("id", "interval_ms", "name"),
    node_class_name="DialogsNode",
)(handle_dialogs)
modular_step(
    step_type="emote",
    category="interaction",
    allowed_params=("command", "emote", "name", "value"),
    node_class_name="EmoteNode",
)(handle_emote)
modular_step(
    step_type="interact_gadget",
    category="interaction",
    allowed_params=("max_dist", "name", "nearest"),
    node_class_name="InteractGadgetNode",
)(handle_interact_gadget)
modular_step(
    step_type="interact_gadget_at_xy",
    category="interaction",
    allowed_params=("name",),
    node_class_name="InteractGadgetAtXyNode",
)(handle_interact_gadget_at_xy)
modular_step(
    step_type="interact_item",
    category="interaction",
    allowed_params=("max_dist", "name"),
    node_class_name="InteractItemNode",
)(handle_interact_item)
modular_step(
    step_type="interact_nearest_npc",
    category="interaction",
    allowed_params=("max_dist", "name", "nearest"),
    node_class_name="InteractNearestNpcNode",
)(handle_interact_nearest_npc)
modular_step(
    step_type="interact_npc",
    category="interaction",
    allowed_params=("name",),
    node_class_name="InteractNpcNode",
)(handle_interact_npc)
modular_step(
    step_type="interact_quest_npc",
    category="interaction",
    allowed_params=(),
    node_class_name="InteractQuestNpcNode",
)(handle_interact_quest_npc)
modular_step(
    step_type="key_press",
    category="interaction",
    allowed_params=("key",),
    node_class_name="KeyPressNode",
)(handle_key_press)
modular_step(
    step_type="loot_chest",
    category="interaction",
    allowed_params=("max_dist", "multibox", "name", "nearest"),
    node_class_name="LootChestNode",
)(handle_loot_chest)
modular_step(
    step_type="skip_cutscene",
    category="interaction",
    allowed_params=("poll_ms", "timeout_ms", "wait_ms"),
    node_class_name="SkipCutsceneNode",
)(handle_skip_cutscene)
modular_step(
    step_type="use_item",
    category="interaction",
    allowed_params=(),
    node_class_name="UseItemNode",
)(handle_use_item)
