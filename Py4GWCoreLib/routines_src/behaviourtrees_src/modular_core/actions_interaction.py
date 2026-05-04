"""
actions_interaction module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from typing import Callable

from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_interaction import (
    add_dialog_multibox_state,
    add_dialog_state,
    add_dialog_with_model_state,
    add_dialogs_state,
    add_emote_state,
    add_interact_gadget_state,
    add_interact_item_state,
    add_interact_npc_state,
    add_interact_npc_at_xy_state,
    add_interact_quest_npc_state,
    add_key_press_state,
    add_loot_chest_state,
    add_skip_cutscene_state,
    add_use_item_state,
)

from .actions_party_toggles import (
    apply_auto_combat_state,
    apply_auto_looting_state,
    current_auto_combat_enabled,
    current_auto_looting_enabled,
)
from .step_registration import modular_step
from .step_context import StepContext
from .step_selectors import resolve_agent_xy_from_step, resolve_item_model_id_from_step
from .step_utils import wait_after_step


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

    def _coords():
        return resolve_agent_xy_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )

    add_interact_npc_state(ctx.bot, coords_resolver=_coords, name=str(name or "Interact NPC"))
    wait_after_step(ctx.bot, ctx.step)


def handle_dialog(ctx: StepContext) -> None:
    dialog_id = ctx.step["id"]
    name = ctx.step.get("name", "")

    def _coords():
        return resolve_agent_xy_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )

    add_dialog_state(ctx.bot, coords_resolver=_coords, dialog_id=dialog_id, name=str(name or "Dialog"))
    wait_after_step(ctx.bot, ctx.step)


def handle_dialog_with_model(ctx: StepContext) -> None:
    model_id = int(str(ctx.step["model_id"]), 0)
    dialog_id = int(str(ctx.step["id"]), 0)
    name = ctx.step.get("name", "")
    add_dialog_with_model_state(
        ctx.bot,
        model_id=model_id,
        dialog_id=dialog_id,
        name=str(name or "Dialog With Model"),
    )
    wait_after_step(ctx.bot, ctx.step)


def _recipe_log(recipe_name: str, message: str) -> None:
    from Py4GWCoreLib import ConsoleLog

    ConsoleLog(f"Recipe:{recipe_name}", message)


def handle_dialogs(ctx: StepContext) -> None:
    from Py4GWCoreLib import Player

    name = ctx.step.get("name", f"Dialogs {ctx.step_idx + 1}")
    interval_ms = int(ctx.step.get("interval_ms", 200))
    raw_ids = ctx.step.get("id", [])
    dialog_ids_raw = raw_ids if isinstance(raw_ids, (list, tuple)) else [raw_ids]

    dialog_ids: list[int] = []
    for value in dialog_ids_raw:
        try:
            dialog_ids.append(int(str(value), 0))
        except (TypeError, ValueError):
            _recipe_log(ctx.recipe_name, f"Invalid dialogs.id value at index {ctx.step_idx}: {value!r}")
            return

    def _coords():
        return resolve_agent_xy_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )

    add_dialogs_state(
        ctx.bot,
        coords_resolver=_coords,
        dialog_ids=dialog_ids,
        interval_ms=interval_ms,
        name=str(name),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_dialog_multibox(ctx: StepContext) -> None:
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
            _recipe_log(ctx.recipe_name, f"Invalid dialog_multibox.id value at index {ctx.step_idx}: {value!r}")
            return

    def _coords():
        return resolve_agent_xy_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )

    add_dialog_multibox_state(
        ctx.bot,
        coords_resolver=_coords,
        dialog_ids=dialog_ids,
        interval_ms=interval_ms,
        send_wait_step_ms=send_wait_step_ms,
        send_timeout_ms=send_timeout_ms,
        name=str(name),
        log=lambda message: _recipe_log(ctx.recipe_name, f"{message} step index {ctx.step_idx}"),
    )
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

    def _coords():
        return resolve_agent_xy_from_step(
            gadget_step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="gadget",
            default_max_dist=Range.Compass.value,
        )

    add_interact_gadget_state(ctx.bot, coords_resolver=_coords, name=str(ctx.step.get("name", "Interact Gadget")))
    wait_after_step(ctx.bot, ctx.step)


def handle_interact_gadget_at_xy(ctx: StepContext) -> None:
    from Py4GWCoreLib import Range

    name = ctx.step.get("name", "Interact Gadget")

    def _coords():
        return resolve_agent_xy_from_step(
            ctx.step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="gadget",
            default_max_dist=Range.Compass.value,
        )

    add_interact_gadget_state(ctx.bot, coords_resolver=_coords, name=str(name))
    wait_after_step(ctx.bot, ctx.step)


def handle_loot_chest(ctx: StepContext) -> None:
    from Py4GWCoreLib import Range

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

    def _coords():
        return resolve_agent_xy_from_step(
            chest_step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="gadget",
            default_max_dist=Range.Compass.value,
        )

    add_loot_chest_state(
        ctx.bot,
        coords_resolver=_coords,
        max_dist=max_dist,
        multibox=multibox,
        name=str(name),
        log=lambda message: _recipe_log(ctx.recipe_name, message),
    )
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

    add_interact_item_state(
        ctx.bot,
        model_id=model_id,
        has_model_filter=has_model_filter,
        max_dist=max_dist,
        name=str(ctx.step.get("name", "Interact Item")),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_use_item(ctx: StepContext) -> None:
    model_id = resolve_item_model_id_from_step(
        ctx.step,
        recipe_name=ctx.recipe_name,
        step_idx=ctx.step_idx,
    )
    if model_id is None:
        return

    add_use_item_state(ctx.bot, model_id=model_id)
    wait_after_step(ctx.bot, ctx.step)


def handle_interact_quest_npc(ctx: StepContext) -> None:
    add_interact_quest_npc_state(ctx.bot)
    wait_after_step(ctx.bot, ctx.step)


def handle_interact_nearest_npc(ctx: StepContext) -> None:
    from Py4GWCoreLib import Range

    nearest_step = dict(ctx.step)
    nearest_step["nearest"] = True
    if "max_dist" not in nearest_step:
        nearest_step["max_dist"] = Range.Compass.value
    def _coords():
        return resolve_agent_xy_from_step(
            nearest_step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
            default_max_dist=Range.Compass.value,
        )

    add_interact_npc_at_xy_state(ctx.bot, coords_resolver=_coords, name=str(ctx.step.get("name", "Interact Nearest NPC")))
    wait_after_step(ctx.bot, ctx.step)


def handle_skip_cutscene(ctx: StepContext) -> None:
    wait_ms = int(ctx.step.get("wait_ms", ctx.step.get("timeout_ms", 10000)))
    poll_ms = max(50, int(ctx.step.get("poll_ms", 250)))
    pre_skip_delay_ms = max(0, int(ctx.step.get("pre_skip_delay_ms", ctx.step.get("delay_ms", 3000))))

    add_skip_cutscene_state(ctx.bot, wait_ms=wait_ms, poll_ms=poll_ms, pre_skip_delay_ms=pre_skip_delay_ms)
    wait_after_step(ctx.bot, ctx.step)


def handle_key_press(ctx: StepContext) -> None:
    key_name = str(ctx.step["key"]).upper()
    if not add_key_press_state(
        ctx.bot,
        key_name=key_name,
        log=lambda message: _recipe_log(ctx.recipe_name, message),
    ):
        return
    wait_after_step(ctx.bot, ctx.step)


def handle_emote(ctx: StepContext) -> None:
    raw_command = str(
        ctx.step.get("command", ctx.step.get("emote", ctx.step.get("value", "kneel"))) or "kneel"
    ).strip()
    add_emote_state(ctx.bot, command=raw_command, name=ctx.step.get("name"))
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
    allowed_params=("delay_ms", "poll_ms", "pre_skip_delay_ms", "timeout_ms", "wait_ms"),
    node_class_name="SkipCutsceneNode",
)(handle_skip_cutscene)
modular_step(
    step_type="use_item",
    category="interaction",
    allowed_params=(),
    node_class_name="UseItemNode",
)(handle_use_item)
