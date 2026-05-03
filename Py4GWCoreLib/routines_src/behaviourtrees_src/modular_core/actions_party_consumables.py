"""
actions_party_consumables module

This module provides consumable-related modular party step handlers.
"""
from __future__ import annotations

from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_consumables import (
    add_use_single_consumable_state,
    consumable_property_names,
    consumable_specs,
    normalize_consumable_mode,
    should_skip_local_consumable_for_non_leader,
    yield_upkeep_local,
    yield_upkeep_multibox,
)

from .step_context import StepContext
from .step_utils import debug_log_recipe, parse_step_bool, parse_step_int, wait_after_step


def _consumable_specs(mode: str) -> list[tuple[int, str]]:
    return consumable_specs(mode)


def _consumable_property_names(mode: str) -> tuple[str, ...]:
    return consumable_property_names(mode)


def _normalize_consumable_mode(raw_mode: object, default: str = "all") -> str:
    mode = normalize_consumable_mode(raw_mode, default)
    return mode if mode in ("all", "conset", "pcons") else ""


def _local_effect_active(effect_id: int) -> bool:
    from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_consumables import local_effect_active

    return local_effect_active(effect_id)


def _use_local_consumable(model_id: int, effect_id: int) -> bool:
    from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_consumables import use_local_consumable

    return use_local_consumable(model_id, effect_id)


def _skip_local_consumable_for_non_leader(ctx: StepContext, multibox: bool) -> bool:
    if multibox:
        return False

    leader_only = parse_step_bool(ctx.step.get("leader_only", True), True)
    return should_skip_local_consumable_for_non_leader(
        leader_only=leader_only,
        log=lambda message: debug_log_recipe(ctx, message),
    )


def _use_single_consumable(ctx: StepContext, model_id: int, effect_name: str, multibox: bool) -> None:
    step_name = str(ctx.step.get("name", f"Use {effect_name}") or f"Use {effect_name}")
    leader_only = parse_step_bool(ctx.step.get("leader_only", True), True)
    add_use_single_consumable_state(
        ctx.bot,
        model_id=model_id,
        effect_name=effect_name,
        multibox=multibox,
        leader_only=leader_only,
        name=step_name,
        log=lambda message: debug_log_recipe(ctx, message),
    )


def handle_use_all_consumables(ctx: StepContext) -> None:
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    if _skip_local_consumable_for_non_leader(ctx, multibox):
        wait_after_step(ctx.bot, ctx.step)
        return
    if multibox:
        ctx.bot.Multibox.UseAllConsumables()
    else:
        ctx.bot.Items.UseAllConsumables()
    wait_after_step(ctx.bot, ctx.step)


def handle_use_conset(ctx: StepContext) -> None:
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    if _skip_local_consumable_for_non_leader(ctx, multibox):
        wait_after_step(ctx.bot, ctx.step)
        return
    if multibox:
        ctx.bot.Multibox.UseConset()
    else:
        ctx.bot.Items.UseConset()
    wait_after_step(ctx.bot, ctx.step)


def handle_use_pcons(ctx: StepContext) -> None:
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    if _skip_local_consumable_for_non_leader(ctx, multibox):
        wait_after_step(ctx.bot, ctx.step)
        return
    if multibox:
        ctx.bot.Multibox.UsePcons()
    else:
        ctx.bot.Items.UsePcons()
    wait_after_step(ctx.bot, ctx.step)


def handle_use_essence_of_celerity(ctx: StepContext) -> None:
    from Py4GWCoreLib.enums import ModelID

    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    _use_single_consumable(
        ctx,
        int(ModelID.Essence_Of_Celerity.value),
        "Essence_of_Celerity_item_effect",
        multibox,
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_use_grail_of_might(ctx: StepContext) -> None:
    from Py4GWCoreLib.enums import ModelID

    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    _use_single_consumable(
        ctx,
        int(ModelID.Grail_Of_Might.value),
        "Grail_of_Might_item_effect",
        multibox,
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_use_armor_of_salvation(ctx: StepContext) -> None:
    from Py4GWCoreLib.enums import ModelID

    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    _use_single_consumable(
        ctx,
        int(ModelID.Armor_Of_Salvation.value),
        "Armor_of_Salvation_item_effect",
        multibox,
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_use_consumables(ctx: StepContext) -> None:
    selector = str(ctx.step.get("mode", ctx.step.get("selector", "all")) or "all").strip().lower()
    aliases = {
        "all": "all",
        "all_consumables": "all",
        "use_all": "all",
        "conset": "conset",
        "pcons": "pcons",
        "essence": "essence",
        "essence_of_celerity": "essence",
        "grail": "grail",
        "grail_of_might": "grail",
        "armor": "armor",
        "armor_of_salvation": "armor",
    }
    normalized = aliases.get(selector)

    if normalized == "all":
        handle_use_all_consumables(ctx)
        return
    if normalized == "conset":
        handle_use_conset(ctx)
        return
    if normalized == "pcons":
        handle_use_pcons(ctx)
        return
    if normalized == "essence":
        handle_use_essence_of_celerity(ctx)
        return
    if normalized == "grail":
        handle_use_grail_of_might(ctx)
        return
    if normalized == "armor":
        handle_use_armor_of_salvation(ctx)
        return

    debug_log_recipe(
        ctx,
        f"use_consumables unsupported mode={selector!r}. Expected one of: all, conset, pcons, essence, grail, armor.",
    )
    wait_after_step(ctx.bot, ctx.step)


def _yield_upkeep_local(ctx: StepContext, specs: list[tuple[int, str]], poll_ms: int):
    yield from yield_upkeep_local(ctx.bot, specs, poll_ms, log=lambda message: debug_log_recipe(ctx, message))


def _yield_upkeep_multibox(ctx: StepContext, specs: list[tuple[int, str]], mode: str, poll_ms: int):
    yield from yield_upkeep_multibox(ctx.bot, specs, mode, poll_ms, log=lambda message: debug_log_recipe(ctx, message))


def _register_consumable_upkeep_background(
    ctx: StepContext,
    *,
    mode: str,
    multibox: bool,
    poll_ms: int,
) -> None:
    from Py4GWCoreLib import Map

    owner = getattr(ctx.bot, "_modular_owner", None)
    if owner is None or not hasattr(owner, "_background_generators"):
        debug_log_recipe(ctx, "upkeep_consumables requires ModularBot owner background support.")
        return

    start_map_id = int(Map.GetMapID() or 0)
    if start_map_id <= 0:
        debug_log_recipe(ctx, "upkeep_consumables skipped: current map is unavailable.")
        return
    specs = _consumable_specs(mode)
    key = f"upkeep_consumables:{mode}:{start_map_id}"
    for property_name in _consumable_property_names(mode):
        try:
            if ctx.bot.Properties.exists(property_name):
                ctx.bot.Properties.ApplyNow(property_name, "active", False)
        except Exception:
            pass

    def _background():
        while int(Map.GetMapID() or 0) == start_map_id:
            if bool(Map.IsExplorable()):
                if multibox:
                    yield from _yield_upkeep_multibox(ctx, specs, mode, poll_ms)
                else:
                    yield from _yield_upkeep_local(ctx, specs, poll_ms)
            else:
                yield from ctx.bot.Wait._coro_for_time(poll_ms)
        debug_log_recipe(ctx, f"upkeep_consumables stopped on map change from {start_map_id}.")

    owner._background_generators[key] = _background()
    debug_log_recipe(ctx, f"upkeep_consumables started mode={mode} multibox={multibox} map_id={start_map_id}.")


def handle_upkeep_consumables(ctx: StepContext) -> None:
    default_mode = "all"
    if ctx.step_type == "upkeep_cons":
        default_mode = "conset"
    elif ctx.step_type == "upkeep_pcons":
        default_mode = "pcons"
    mode = _normalize_consumable_mode(ctx.step.get("mode", ctx.step.get("selector", default_mode)), default_mode)
    if mode not in ("all", "conset", "pcons"):
        debug_log_recipe(ctx, f"upkeep_consumables unsupported mode={ctx.step.get('mode')!r}.")
        return
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    poll_ms = max(500, parse_step_int(ctx.step.get("poll_ms", ctx.step.get("interval_ms", 5000)), 5000))

    def _start_upkeep() -> None:
        _register_consumable_upkeep_background(ctx, mode=mode, multibox=multibox, poll_ms=poll_ms)

    ctx.bot.States.AddCustomState(_start_upkeep, ctx.step.get("name", f"Upkeep {mode.title()}"))
    wait_after_step(ctx.bot, ctx.step)
