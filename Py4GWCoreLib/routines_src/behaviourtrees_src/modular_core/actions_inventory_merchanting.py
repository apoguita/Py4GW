"""
actions_inventory_merchanting module

This module provides merchant/trader-oriented inventory step handlers.
"""
from __future__ import annotations

from time import monotonic

from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_inventory import (
    add_buy_ectoplasm_state,
    add_deposit_materials_state,
    add_merchant_rules_execute_state,
    add_sell_item_ids_at_merchant_state,
    add_sell_materials_state,
    apply_default_npc_selector,
    get_leftover_material_item_ids,
    get_nonsalvageable_gold_item_ids,
    iter_other_account_emails,
    parse_widget_names,
)

from .step_registration import modular_step
from .step_context import StepContext
from .step_selectors import resolve_agent_xy_from_step
from .step_utils import log_recipe, parse_step_bool, parse_step_int, wait_after_step


def _resolve_material_models(raw_materials) -> set[int] | None:
    from Py4GWCoreLib.enums_src.Item_enums import MaterialMap
    from Py4GWCoreLib.enums_src.Model_enums import ModelID

    if raw_materials is None:
        return None
    values = raw_materials if isinstance(raw_materials, (list, tuple, set)) else [raw_materials]
    reverse_material_map = {material_name.lower(): int(model_id.value) for model_id, material_name in MaterialMap.items()}
    selected_models: set[int] = set()
    for raw_material in values:
        if isinstance(raw_material, str):
            material_key = raw_material.strip()
            model_enum = ModelID.__members__.get(material_key)
            if model_enum is not None:
                selected_models.add(int(model_enum.value))
                continue
            resolved_model = reverse_material_map.get(material_key.lower())
            if resolved_model is not None:
                selected_models.add(resolved_model)
                continue
        model_id = parse_step_int(raw_material, -1)
        if model_id >= 0:
            selected_models.add(model_id)
    return selected_models


def _npc_coords_resolver(ctx: StepContext, selector_step: dict, selector_kind: str, missing_message: str):
    def _coords():
        step_selector = dict(selector_step)
        apply_default_npc_selector(step_selector, selector_kind)
        log_recipe(ctx, f"{selector_kind}: selector={step_selector!r}")
        coords = resolve_agent_xy_from_step(
            step_selector,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            log_recipe(ctx, missing_message)
        return coords

    return _coords


def handle_sell_materials(ctx: StepContext) -> None:
    name = str(ctx.step.get("name", "Sell Materials") or "Sell Materials")
    wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))
    add_sell_materials_state(
        ctx.bot,
        coords_resolver=_npc_coords_resolver(ctx, dict(ctx.step), "materials", "sell_materials: failed to resolve Crafting Material Trader coordinates."),
        selected_models=_resolve_material_models(ctx.step.get("materials")),
        multibox=parse_step_bool(ctx.step.get("multibox", False), False),
        wait_step_ms=wait_step_ms,
        timeout_ms=timeout_ms,
        name=name,
        log=lambda message: log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_deposit_materials(ctx: StepContext) -> None:
    name = str(ctx.step.get("name", "Deposit Materials") or "Deposit Materials")
    max_deposit_items_raw = parse_step_int(ctx.step.get("max_deposit_items", 0), 0)
    exact_quantity_raw = parse_step_int(ctx.step.get("exact_quantity", 250), 250)
    add_deposit_materials_state(
        ctx.bot,
        selected_models=_resolve_material_models(ctx.step.get("materials")),
        max_deposit_items=max_deposit_items_raw if max_deposit_items_raw > 0 else None,
        exact_quantity=exact_quantity_raw if exact_quantity_raw > 0 else None,
        open_wait_ms=max(0, parse_step_int(ctx.step.get("open_wait_ms", 1000), 1000)),
        deposit_wait_ms=max(0, parse_step_int(ctx.step.get("deposit_wait_ms", 250), 250)),
        max_passes=max(1, parse_step_int(ctx.step.get("max_passes", 2), 2)),
        multibox=parse_step_bool(ctx.step.get("multibox", False), False),
        wait_step_ms=max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50)),
        timeout_ms=max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000)),
        name=name,
        log=lambda message: log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_sell_nonsalvageable_golds(ctx: StepContext) -> None:
    name = str(ctx.step.get("name", "Sell Non-Salvageable Golds") or "Sell Non-Salvageable Golds")
    add_sell_item_ids_at_merchant_state(
        ctx.bot,
        coords_resolver=_npc_coords_resolver(ctx, dict(ctx.step), "merchant", "sell_nonsalvageable_golds: failed to resolve Merchant coordinates."),
        item_ids_factory=get_nonsalvageable_gold_item_ids,
        empty_message="sell_nonsalvageable_golds: no eligible gold items.",
        complete_message=lambda count: f"sell_nonsalvageable_golds: sold {count} item(s).",
        multibox=parse_step_bool(ctx.step.get("multibox", False), False),
        shared_extra_data=("sell_nonsalvageable_golds", "", "", ""),
        wait_step_ms=max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50)),
        timeout_ms=max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000)),
        name=name,
        log=lambda message: log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_sell_leftover_materials(ctx: StepContext) -> None:
    batch_size = max(1, parse_step_int(ctx.step.get("batch_size", 10), 10))
    name = str(ctx.step.get("name", "Sell Leftover Materials") or "Sell Leftover Materials")
    add_sell_item_ids_at_merchant_state(
        ctx.bot,
        coords_resolver=_npc_coords_resolver(ctx, dict(ctx.step), "merchant", "sell_leftover_materials: failed to resolve Merchant coordinates."),
        item_ids_factory=lambda: get_leftover_material_item_ids(batch_size=batch_size),
        empty_message=f"sell_leftover_materials: no common material stacks below {batch_size}.",
        complete_message=lambda count: f"sell_leftover_materials: sold {count} stack(s) with qty < {batch_size}.",
        multibox=parse_step_bool(ctx.step.get("multibox", False), False),
        shared_extra_data=("sell_merchant_leftovers", "", str(batch_size), ""),
        wait_step_ms=max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50)),
        timeout_ms=max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000)),
        name=name,
        log=lambda message: log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_sell_scrolls(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE

    scroll_models = set(int(v) for v in ctx.step.get("scroll_models", [5594, 5595, 5611, 5853, 5975, 5976, 21233]))
    name = str(ctx.step.get("name", "Sell Scrolls") or "Sell Scrolls")

    def _scroll_item_ids() -> list[int]:
        bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
        return [int(item_id) for item_id in item_array if int(GLOBAL_CACHE.Item.GetModelID(item_id)) in scroll_models]

    add_sell_item_ids_at_merchant_state(
        ctx.bot,
        coords_resolver=_npc_coords_resolver(ctx, dict(ctx.step), "merchant", "sell_scrolls: failed to resolve Merchant coordinates."),
        item_ids_factory=_scroll_item_ids,
        empty_message="sell_scrolls: no matching scrolls.",
        complete_message=lambda count: f"sell_scrolls: sold {count} scroll(s).",
        multibox=parse_step_bool(ctx.step.get("multibox", False), False),
        shared_extra_data=("sell_scrolls", ",".join(str(mid) for mid in sorted(scroll_models)), "", ""),
        wait_step_ms=max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50)),
        timeout_ms=max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000)),
        name=name,
        log=lambda message: log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_buy_ectoplasm(ctx: StepContext) -> None:
    start_threshold = parse_step_int(ctx.step.get("start_storage_gold_threshold", 900_000), 900_000)
    stop_threshold = max(0, parse_step_int(ctx.step.get("stop_storage_gold_threshold", 500_000), 500_000))
    if start_threshold < stop_threshold:
        start_threshold = stop_threshold
    max_ecto_raw = parse_step_int(ctx.step.get("max_ecto_to_buy", 0), 0)
    add_buy_ectoplasm_state(
        ctx.bot,
        coords_resolver=_npc_coords_resolver(ctx, dict(ctx.step), "rare_materials", "buy_ectoplasm: failed to resolve Rare Material Trader coordinates."),
        use_storage_gold=parse_step_bool(ctx.step.get("use_storage_gold", True), True),
        start_storage_gold_threshold=start_threshold,
        stop_storage_gold_threshold=stop_threshold,
        max_ecto_to_buy=max_ecto_raw if max_ecto_raw > 0 else None,
        multibox=parse_step_bool(ctx.step.get("multibox", False), False),
        wait_step_ms=max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50)),
        timeout_ms=max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000)),
        name=str(ctx.step.get("name", "Buy Ectoplasm") or "Buy Ectoplasm"),
        log=lambda message: log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


def handle_merchant_rules_execute(ctx: StepContext) -> None:
    from Py4GWCoreLib import Player
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

    name = str(ctx.step.get("name", "Merchant Rules Execute") or "Merchant Rules Execute")
    multibox = parse_step_bool(ctx.step.get("multibox", True), True)
    local = parse_step_bool(ctx.step.get("local", True), True)
    auto_enable_widget = parse_step_bool(ctx.step.get("auto_enable_widget", True), True)
    widget_names = parse_widget_names(ctx.step.get("widget_names", ["MerchantRules", "Merchant Rules"])) or ["MerchantRules", "Merchant Rules"]
    request_id = str(ctx.step.get("request_id", "") or "").strip() or f"modular_{ctx.recipe_name}_{ctx.step_idx}_{int(monotonic() * 1000)}"

    def _target_emails() -> list[str]:
        sender_email = str(Player.GetAccountEmail() or "").strip()
        widget_handler = get_widget_handler()
        local_enabled = any(
            (info is not None and bool(getattr(info, "enabled", False)))
            for info in (widget_handler.get_widget_info(widget_name) for widget_name in widget_names)
        )
        emails: list[str] = []
        if local and (local_enabled or auto_enable_widget):
            emails.append(sender_email)
        elif local:
            log_recipe(ctx, "merchant_rules_execute: Merchant Rules widget is not enabled locally; executing multibox targets only.")
        if multibox:
            emails.extend(iter_other_account_emails())
        return list(dict.fromkeys(email for email in emails if email))

    add_merchant_rules_execute_state(
        ctx.bot,
        target_emails_factory=_target_emails,
        request_id=request_id[:60],
        include_protected=parse_step_bool(ctx.step.get("include_protected", False), False),
        instant_destroy=parse_step_bool(ctx.step.get("instant_destroy", False), False),
        auto_enable_widget=auto_enable_widget,
        widget_names=widget_names,
        wait_step_ms=max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50)),
        wait_timeout_ms=max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 90_000), 90_000)),
        enable_wait_ms=max(0, parse_step_int(ctx.step.get("enable_wait_ms", 350), 350)),
        wait_ms=max(0, parse_step_int(ctx.step.get("ms", 0), 0)),
        name=name,
        log=lambda message: log_recipe(ctx, message),
    )
    wait_after_step(ctx.bot, ctx.step)


modular_step(
    step_type="buy_ectoplasm",
    category="inventory",
    allowed_params=("max_ecto_to_buy", "ms", "multibox", "multibox_wait_step_ms", "multibox_wait_timeout_ms", "name", "npc", "start_storage_gold_threshold", "stop_storage_gold_threshold", "use_storage_gold"),
    node_class_name="BuyEctoplasmNode",
)(handle_buy_ectoplasm)
modular_step(
    step_type="deposit_materials",
    category="inventory",
    allowed_params=("deposit_wait_ms", "exact_quantity", "materials", "max_deposit_items", "max_passes", "ms", "multibox", "multibox_wait_step_ms", "multibox_wait_timeout_ms", "name", "open_wait_ms"),
    node_class_name="DepositMaterialsNode",
)(handle_deposit_materials)
modular_step(
    step_type="merchant_rules_execute",
    category="inventory",
    allowed_params=("auto_enable_widget", "enable_wait_ms", "include_protected", "instant_destroy", "local", "ms", "multibox", "multibox_wait_step_ms", "multibox_wait_timeout_ms", "name", "request_id", "widget_names"),
    node_class_name="MerchantRulesExecuteNode",
)(handle_merchant_rules_execute)
modular_step(
    step_type="sell_leftover_materials",
    category="inventory",
    allowed_params=("batch_size", "ms", "multibox", "multibox_wait_step_ms", "multibox_wait_timeout_ms", "name", "npc"),
    node_class_name="SellLeftoverMaterialsNode",
)(handle_sell_leftover_materials)
modular_step(
    step_type="sell_materials",
    category="inventory",
    allowed_params=("materials", "ms", "multibox", "multibox_wait_step_ms", "multibox_wait_timeout_ms", "name", "npc"),
    node_class_name="SellMaterialsNode",
)(handle_sell_materials)
modular_step(
    step_type="sell_nonsalvageable_golds",
    category="inventory",
    allowed_params=("ms", "multibox", "multibox_wait_step_ms", "multibox_wait_timeout_ms", "name", "npc"),
    node_class_name="SellNonsalvageableGoldsNode",
)(handle_sell_nonsalvageable_golds)
modular_step(
    step_type="sell_scrolls",
    category="inventory",
    allowed_params=("ms", "multibox", "multibox_wait_step_ms", "multibox_wait_timeout_ms", "name", "npc", "scroll_models"),
    node_class_name="SellScrollsNode",
)(handle_sell_scrolls)
