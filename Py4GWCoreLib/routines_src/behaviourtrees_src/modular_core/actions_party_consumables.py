"""
actions_party_consumables module

This module provides consumable-related modular party step handlers.
"""
from __future__ import annotations

from .step_context import StepContext
from .step_utils import debug_log_recipe, parse_step_bool, parse_step_int, wait_after_step


def _consumable_specs(mode: str) -> list[tuple[int, str]]:
    from Py4GWCoreLib.enums import ModelID

    conset = [
        (int(ModelID.Essence_Of_Celerity.value), "Essence_of_Celerity_item_effect"),
        (int(ModelID.Grail_Of_Might.value), "Grail_of_Might_item_effect"),
        (int(ModelID.Armor_Of_Salvation.value), "Armor_of_Salvation_item_effect"),
    ]
    pcons = [
        (int(ModelID.Birthday_Cupcake.value), "Birthday_Cupcake_skill"),
        (int(ModelID.Golden_Egg.value), "Golden_Egg_skill"),
        (int(ModelID.Candy_Corn.value), "Candy_Corn_skill"),
        (int(ModelID.Candy_Apple.value), "Candy_Apple_skill"),
        (int(ModelID.Slice_Of_Pumpkin_Pie.value), "Pie_Induced_Ecstasy"),
        (int(ModelID.Drake_Kabob.value), "Drake_Skin"),
        (int(ModelID.Bowl_Of_Skalefin_Soup.value), "Skale_Vigor"),
        (int(ModelID.Pahnai_Salad.value), "Pahnai_Salad_item_effect"),
        (int(ModelID.War_Supplies.value), "Well_Supplied"),
    ]
    if mode == "conset":
        return conset
    if mode == "pcons":
        return pcons
    return conset + pcons


def _consumable_property_names(mode: str) -> tuple[str, ...]:
    conset = ("essence_of_celerity", "grail_of_might", "armor_of_salvation")
    pcons = (
        "birthday_cupcake",
        "golden_egg",
        "candy_corn",
        "candy_apple",
        "slice_of_pumpkin_pie",
        "drake_kabob",
        "bowl_of_skalefin_soup",
        "pahnai_salad",
        "war_supplies",
    )
    if mode == "conset":
        return conset
    if mode == "pcons":
        return pcons
    return conset + pcons


def _normalize_consumable_mode(raw_mode: object, default: str = "all") -> str:
    token = str(raw_mode or default).strip().lower()
    aliases = {
        "all": "all",
        "all_consumables": "all",
        "consumables": "all",
        "cons": "conset",
        "conset": "conset",
        "pcon": "pcons",
        "pcons": "pcons",
    }
    return aliases.get(token, "")


def _local_effect_active(effect_id: int) -> bool:
    if effect_id <= 0:
        return False
    try:
        from Py4GWCoreLib import GLOBAL_CACHE, Player

        return bool(GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), effect_id))
    except Exception:
        return False


def _use_local_consumable(model_id: int, effect_id: int) -> bool:
    if _local_effect_active(effect_id):
        return False
    try:
        from Py4GWCoreLib import GLOBAL_CACHE

        item_id = int(GLOBAL_CACHE.Inventory.GetFirstModelID(model_id) or 0)
        if item_id <= 0:
            return False
        GLOBAL_CACHE.Inventory.UseItem(item_id)
        return True
    except Exception:
        return False


def _skip_local_consumable_for_non_leader(ctx: StepContext, multibox: bool) -> bool:
    if multibox:
        return False

    leader_only = parse_step_bool(ctx.step.get("leader_only", True), True)
    if not leader_only:
        return False

    try:
        from Py4GWCoreLib import Party

        if not Party.IsPartyLoaded():
            return False

        player_count = int(Party.GetPlayerCount() or 0)
        if player_count <= 1:
            return False

        if not Party.IsPartyLeader():
            debug_log_recipe(
                ctx,
                "use_consumables local execution skipped on non-leader account (leader_only=true).",
            )
            return True
    except Exception as exc:
        debug_log_recipe(ctx, f"use_consumables leader_only guard failed: {exc}")

    return False


def _use_single_consumable(ctx: StepContext, model_id: int, effect_name: str, multibox: bool) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE

    effect_id = int(GLOBAL_CACHE.Skill.GetID(effect_name) or 0)
    if multibox:
        ctx.bot.Multibox.UseConsumable(model_id, effect_id)
        return

    def _use_local_consumable_runtime() -> None:
        from Py4GWCoreLib import GLOBAL_CACHE, Player

        if _skip_local_consumable_for_non_leader(ctx, multibox=False):
            return

        player_id = int(Player.GetAgentID() or 0)
        if (
            effect_id > 0
            and hasattr(GLOBAL_CACHE, "Effects")
            and callable(getattr(GLOBAL_CACHE.Effects, "HasEffect", None))
            and GLOBAL_CACHE.Effects.HasEffect(player_id, effect_id)
        ):
            debug_log_recipe(ctx, f"use_consumables skipped for model_id={model_id}: effect already active.")
            return

        item_id = int(GLOBAL_CACHE.Inventory.GetFirstModelID(model_id) or 0)
        if item_id <= 0:
            debug_log_recipe(ctx, f"use_consumables skipped for model_id={model_id}: item not found.")
            return

        GLOBAL_CACHE.Inventory.UseItem(item_id)
        debug_log_recipe(ctx, f"use_consumables used model_id={model_id} item_id={item_id}.")

    step_name = str(ctx.step.get("name", f"Use {effect_name}") or f"Use {effect_name}")
    ctx.bot.States.AddCustomState(_use_local_consumable_runtime, step_name)


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


def _account_map_id(account) -> int:
    map_obj = getattr(getattr(account, "AgentData", None), "Map", None)
    return int(getattr(account, "MapID", 0) or getattr(map_obj, "MapID", 0) or 0)


def _send_consumable_to_accounts(model_id: int, effect_id: int, *, include_self: bool = False) -> list[tuple[str, int]]:
    from Py4GWCoreLib import GLOBAL_CACHE, Map, Player, SharedCommandType

    sender_email = str(Player.GetAccountEmail() or "")
    current_map_id = int(Map.GetMapID() or 0)
    refs: list[tuple[str, int]] = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        email = str(getattr(account, "AccountEmail", "") or "")
        if not email or (email == sender_email and not include_self):
            continue
        if current_map_id > 0 and _account_map_id(account) != current_map_id:
            continue
        idx = GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            email,
            SharedCommandType.PCon,
            (int(model_id), int(effect_id), 0, 0),
        )
        refs.append((email, int(idx)))
    return refs


def _yield_upkeep_local(ctx: StepContext, specs: list[tuple[int, str]], poll_ms: int):
    from Py4GWCoreLib import GLOBAL_CACHE

    for model_id, effect_name in specs:
        effect_id = int(GLOBAL_CACHE.Skill.GetID(effect_name) or 0)
        if _use_local_consumable(model_id, effect_id):
            debug_log_recipe(ctx, f"upkeep_consumables used local model_id={model_id}.")
            yield from ctx.bot.Wait._coro_for_time(500)
    yield from ctx.bot.Wait._coro_for_time(poll_ms)


def _yield_upkeep_multibox(ctx: StepContext, specs: list[tuple[int, str]], mode: str, poll_ms: int):
    from Py4GWCoreLib import GLOBAL_CACHE

    for model_id, effect_name in specs:
        effect_id = int(GLOBAL_CACHE.Skill.GetID(effect_name) or 0)
        used_local = _use_local_consumable(model_id, effect_id)
        if used_local:
            debug_log_recipe(ctx, f"upkeep_consumables used local model_id={model_id}.")
            yield from ctx.bot.Wait._coro_for_time(500)
        if mode == "pcons" or not _local_effect_active(effect_id):
            refs = _send_consumable_to_accounts(model_id, effect_id)
            if refs:
                debug_log_recipe(ctx, f"upkeep_consumables sent model_id={model_id} to {len(refs)} account(s).")
            yield from ctx.bot.Wait._coro_for_time(1200 if mode == "conset" else 350)
    yield from ctx.bot.Wait._coro_for_time(poll_ms)


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
