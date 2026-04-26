"""
actions_inventory_handlers module

This module provides inventory-oriented modular step handlers.
"""
from __future__ import annotations

from .actions_inventory import (
    CONS_COMMON_MATERIAL_MODEL_IDS,
    NON_CONS_COMMON_MATERIAL_MODEL_IDS,
    _apply_default_npc_selector,
    _get_id_kit_count,
    _get_salvage_kit_count,
    _iter_other_account_emails,
    _wait_for_outbound_messages,
    _yield_inventory_setup,
    _yield_toggle_widgets,
)
from .contracts import StepNodeRequest
from .node_registry import get_action_node_builder
from .step_registration import modular_step
from .step_context import StepContext
from .step_selectors import resolve_agent_xy_from_step
from .step_utils import (
    debug_log_recipe,
    log_recipe,
    parse_step_bool,
    parse_step_int,
    wait_after_step,
)


def handle_restock_kits(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType

    selector_step = dict(ctx.step)

    name = ctx.step.get("name", "Restock Kits")
    multibox_raw = ctx.step.get("multibox", False)
    multibox_wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))

    try:
        id_kits_target = int(ctx.step.get("id_kits", 2))
    except (TypeError, ValueError):
        id_kits_target = 2

    try:
        salvage_kits_target = int(ctx.step.get("salvage_kits", 8))
    except (TypeError, ValueError):
        salvage_kits_target = 8

    multibox = (
        multibox_raw.strip().lower() in ("1", "true", "yes", "on")
        if isinstance(multibox_raw, str)
        else bool(multibox_raw)
    )

    if id_kits_target < 0:
        id_kits_target = 0
    if salvage_kits_target < 0:
        salvage_kits_target = 0

    def _restock_local():
        step_selector = dict(selector_step)
        _apply_default_npc_selector(step_selector, "merchant")
        coords = resolve_agent_xy_from_step(
            step_selector,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            yield
            return
        x, y = coords
        yield from ctx.bot.Move._coro_xy_and_interact_npc(x, y, name)
        yield from ctx.bot.Wait._coro_for_time(1200)

        # Recompute kit counts each purchase pass, but cap by initial deficit
        # so stale cache reads cannot cause overbuy.
        initial_id_kits_in_inv = _get_id_kit_count()
        initial_salvage_kits_in_inv = _get_salvage_kit_count()
        id_buy_budget = max(0, id_kits_target - initial_id_kits_in_inv)
        salvage_buy_budget = max(0, salvage_kits_target - initial_salvage_kits_in_inv)
        id_bought = 0
        salvage_bought = 0

        for _ in range(2):
            id_remaining_by_observed = max(0, id_kits_target - _get_id_kit_count())
            salvage_remaining_by_observed = max(0, salvage_kits_target - _get_salvage_kit_count())
            id_remaining_by_budget = max(0, id_buy_budget - id_bought)
            salvage_remaining_by_budget = max(0, salvage_buy_budget - salvage_bought)

            id_kits_to_buy = min(id_remaining_by_observed, id_remaining_by_budget)
            salvage_kits_to_buy = min(salvage_remaining_by_observed, salvage_remaining_by_budget)

            if id_kits_to_buy <= 0 and salvage_kits_to_buy <= 0:
                break

            yield from Routines.Yield.Merchant.BuyIDKits(id_kits_to_buy)
            yield from Routines.Yield.Merchant.BuySalvageKits(salvage_kits_to_buy)
            id_bought += id_kits_to_buy
            salvage_bought += salvage_kits_to_buy
            yield from Routines.Yield.wait(150)

        if multibox:
            sender_email = Player.GetAccountEmail()
            account_emails = _iter_other_account_emails()
            sent_messages: list[tuple[str, int]] = []
            for account_email in account_emails:
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantItems,
                    (x, y, float(id_kits_target), float(salvage_kits_target)),
                )
                sent_messages.append((account_email, int(message_index)))
            yield from _wait_for_outbound_messages(
                ctx,
                "restock_kits",
                sent_messages,
                SharedCommandType.MerchantItems,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )

        yield

    ctx.bot.States.AddCustomState(_restock_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_restock_cons(ctx: StepContext) -> None:
    from Py4GWCoreLib import Inventory

    name = ctx.step.get("name", "Restock Consumables")
    restock_specs = (
        ("birthday_cupcake", "BirthdayCupcake"),
        ("candy_apple", "CandyApple"),
        ("honeycomb", "Honeycomb"),
        ("war_supplies", "WarSupplies"),
        ("essence_of_celerity", "EssenceOfCelerity"),
        ("grail_of_might", "GrailOfMight"),
        ("armor_of_salvation", "ArmorOfSalvation"),
        ("golden_egg", "GoldenEgg"),
        ("candy_corn", "CandyCorn"),
        ("slice_of_pumpkin_pie", "SliceOfPumpkinPie"),
        ("drake_kabob", "DrakeKabob"),
        ("bowl_of_skalefin_soup", "BowlOfSkalefinSoup"),
        ("pahnai_salad", "PahnaiSalad"),
    )

    ctx.bot.States.AddCustomState(
        lambda: Inventory.OpenXunlaiWindow() if not Inventory.IsStorageOpen() else None,
        f"{name} Open Xunlai",
    )
    ctx.bot.Wait.ForTime(1000)

    def _enable_restock_properties() -> None:
        for prop_name, _ in restock_specs:
            if not ctx.bot.Properties.exists(prop_name):
                continue
            is_active = bool(ctx.bot.Properties.Get(prop_name, "active"))
            qty = int(ctx.bot.Properties.Get(prop_name, "restock_quantity") or 0)
            if not is_active and qty > 0:
                ctx.bot.Properties.Enable(prop_name)

    ctx.bot.States.AddCustomState(_enable_restock_properties, f"{name} Enable Properties")

    scheduled = 0
    for _, method_name in restock_specs:
        method = getattr(ctx.bot.Items.Restock, method_name, None)
        if callable(method):
            method()
            scheduled += 1

    if scheduled == 0:
        ctx.bot.States.AddCustomState(
            lambda: debug_log_recipe(ctx, "restock_cons found no restock methods to execute."),
            f"{name} Warn: No Restock Methods",
        )

    wait_after_step(ctx.bot, ctx.step)


def handle_inventory_setup(ctx: StepContext) -> None:
    ctx.bot.States.AddCustomState(_yield_inventory_setup(ctx, ctx.step), ctx.step.get("name", "Inventory Setup"))
    wait_after_step(ctx.bot, ctx.step)


def handle_inventory_guard(ctx: StepContext) -> None:
    name = ctx.step.get("name", "Inventory Guard")
    id_kits_min = max(0, parse_step_int(ctx.step.get("id_kits_min", ctx.step.get("id_kits_target", 3)), 3))
    salvage_kits_min = max(
        0,
        parse_step_int(ctx.step.get("salvage_kits_min", ctx.step.get("salvage_kits_target", 10)), 10),
    )

    def _guard():
        current_id_kits = _get_id_kit_count()
        current_salvage_kits = _get_salvage_kit_count()
        if current_id_kits >= id_kits_min and current_salvage_kits >= salvage_kits_min:
            log_recipe(
                ctx,
                f"inventory_guard: skipped (id_kits={current_id_kits}, salvage_kits={current_salvage_kits}, mins={id_kits_min}/{salvage_kits_min}).",
            )
            yield
            return

        log_recipe(
            ctx,
            f"inventory_guard: triggering setup (id_kits={current_id_kits}, salvage_kits={current_salvage_kits}, mins={id_kits_min}/{salvage_kits_min}).",
        )
        yield from _yield_inventory_setup(ctx, ctx.step)()

    ctx.bot.States.AddCustomState(_guard, name)
    wait_after_step(ctx.bot, ctx.step)


def handle_inventory_cleanup(ctx: StepContext) -> None:
    """Composite action for BDS-style GH cleanup/restock/reform sequence."""
    from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

    multibox = parse_step_bool(ctx.step.get("multibox", True), True)
    raw_map_id = ctx.step.get("map_id", None)
    map_id: int | None
    if raw_map_id is None:
        map_id = None
    elif isinstance(raw_map_id, str) and raw_map_id.strip().lower() in ("", "none", "null"):
        map_id = None
    else:
        parsed_map_id = max(0, parse_step_int(raw_map_id, 0))
        map_id = parsed_map_id if parsed_map_id > 0 else None
    id_kits = max(0, parse_step_int(ctx.step.get("id_kits", 3), 3))
    salvage_kits = max(0, parse_step_int(ctx.step.get("salvage_kits", 10), 10))
    batch_size = max(1, parse_step_int(ctx.step.get("batch_size", 10), 10))
    state: dict[str, int] = {"origin_map_id": 0}

    cleanup_steps: list[dict] = [
        {"type": "__capture_origin_map", "name": "Capture Origin Map"},
        {"type": "leave_party", "name": "Leave Party", "multibox": multibox},
        {"type": "travel_gh", "name": "Travel GH", "multibox": multibox, "ms": 7000},
        {
            "type": "deposit_materials",
            "name": "Store Craft Mats",
            "materials": list(CONS_COMMON_MATERIAL_MODEL_IDS),
            "exact_quantity": 0,
            "open_wait_ms": 3000,
            "max_passes": 3,
            "multibox": multibox,
            "ms": 500,
        },
        {
            "type": "sell_materials",
            "name": "Sell Non-Cons Trader Mats",
            "materials": list(NON_CONS_COMMON_MATERIAL_MODEL_IDS),
            "multibox": multibox,
        },
        {"type": "sell_nonsalvageable_golds", "name": "Sell Non-Salv Golds", "npc": "MERCHANT", "multibox": multibox},
        {
            "type": "sell_leftover_materials",
            "name": "Sell <10 Common Mats",
            "npc": "MERCHANT",
            "batch_size": batch_size,
            "multibox": multibox,
        },
        {
            "type": "restock_kits",
            "name": "Restock Kits",
            "npc": "MERCHANT",
            "id_kits": id_kits,
            "salvage_kits": salvage_kits,
            "multibox": multibox,
        },
    ]

    if map_id is None:
        cleanup_steps.append({"type": "__travel_back_origin_map", "name": "Travel Back To Origin", "ms": 4000})
    else:
        cleanup_steps.append({"type": "travel", "name": f"Travel to map {map_id}", "target_map_id": map_id, "ms": 4000})

    if multibox:
        cleanup_steps.extend(
            [
                {"type": "summon_all_accounts", "name": "Summon Alts", "ms": 5000},
                {"type": "invite_all_accounts", "name": "Invite Alts"},
            ]
        )
    else:
        log_recipe(ctx, "inventory_cleanup: multibox disabled, skipping summon/invite steps.")

    for sub_idx, step in enumerate(cleanup_steps):
        step_type = str(step.get("type", "")).strip()
        if step_type == "__capture_origin_map":
            def _capture_origin():
                from Py4GWCoreLib import Map
                state["origin_map_id"] = int(Map.GetMapID() or 0)
                log_recipe(ctx, f"inventory_cleanup: captured origin map_id={state['origin_map_id']}.")
            ctx.bot.States.AddCustomState(_capture_origin, str(step.get("name", "Capture Origin Map")))
            continue
        if step_type == "__travel_back_origin_map":
            def _travel_back_origin():
                from Py4GWCoreLib import Map
                target_map_id = int(state.get("origin_map_id", 0) or 0)
                if target_map_id <= 0:
                    log_recipe(ctx, "inventory_cleanup: no captured origin map; skipping return travel.")
                    yield
                    return
                if int(Map.GetMapID() or 0) != target_map_id:
                    yield from ctx.bot.Map._coro_travel(target_map_id, "")
                yield
            ctx.bot.States.AddCustomState(_travel_back_origin, str(step.get("name", "Travel Back To Origin")))
            wait_after_step(ctx.bot, step)
            continue

        builder = get_action_node_builder(step_type)
        if builder is None:
            log_recipe(ctx, f"inventory_cleanup: missing handler for sub-step {step_type!r}.")
            continue
        owner = getattr(ctx.bot, "_modular_owner", None)
        if owner is None:
            log_recipe(ctx, "inventory_cleanup: no modular owner; cannot run native sub-step node.")
            continue

        sub_request = StepNodeRequest(
            owner=owner,
            bot=ctx.bot,
            phase_name=str(getattr(owner, "_active_phase_name", "") or ""),
            recipe_name=ctx.recipe_name,
            step=dict(step),
            step_idx=int(sub_idx),
            step_total=int(len(cleanup_steps)),
            step_type=step_type,
            step_display=str(step.get("name", step_type)),
            restart_state="",
        )
        sub_tree = builder(sub_request)

        def _run_subtree(_tree=sub_tree):
            while True:
                state = BehaviorTree.Node._normalize_state(_tree.tick())
                if state in (None, BehaviorTree.NodeState.FAILURE):
                    return
                if state == BehaviorTree.NodeState.RUNNING:
                    yield
                    continue
                return

        ctx.bot.States.AddCustomState(_run_subtree, str(step.get("name", step_type)))

    wait_after_step(ctx.bot, ctx.step)


def handle_disable_widgets(ctx: StepContext) -> None:
    name = str(ctx.step.get("name", "Disable Widgets") or "Disable Widgets")
    ctx.bot.States.AddCustomState(_yield_toggle_widgets(ctx, enabled=False), name)
    wait_after_step(ctx.bot, ctx.step)


def handle_enable_widgets(ctx: StepContext) -> None:
    name = str(ctx.step.get("name", "Enable Widgets") or "Enable Widgets")
    ctx.bot.States.AddCustomState(_yield_toggle_widgets(ctx, enabled=True), name)
    wait_after_step(ctx.bot, ctx.step)


# Decorator-driven step registration bindings.
modular_step(
    step_type="disable_widgets",
    category="inventory",
    allowed_params=("ms", "multibox", "multibox_timeout_ms", "multibox_wait_step_ms", "name", "remember_key", "restore_key", "widgets"),
    node_class_name="DisableWidgetsNode",
)(handle_disable_widgets)
modular_step(
    step_type="enable_widgets",
    category="inventory",
    allowed_params=("ms", "multibox", "multibox_timeout_ms", "multibox_wait_step_ms", "name", "remember_key", "restore_key", "widgets"),
    node_class_name="EnableWidgetsNode",
)(handle_enable_widgets)
modular_step(
    step_type="inventory_cleanup",
    category="inventory",
    allowed_params=("batch_size", "id_kits", "map_id", "multibox", "salvage_kits"),
    node_class_name="InventoryCleanupNode",
)(handle_inventory_cleanup)
modular_step(
    step_type="inventory_guard",
    category="inventory",
    allowed_params=(
        "buy_ectoplasm",
        "id_kits_min",
        "id_kits_target",
        "leave_party",
        "location",
        "material_mode",
        "ms",
        "multibox",
        "multibox_wait_step_ms",
        "multibox_wait_timeout_ms",
        "name",
        "npc",
        "per_account_delay_ms",
        "restock_consumables",
        "return_map_id",
        "salvage_kits_min",
        "salvage_kits_target",
        "start_storage_gold_threshold",
        "stop_storage_gold_threshold",
        "use_storage_gold",
    ),
    node_class_name="InventoryGuardNode",
)(handle_inventory_guard)
modular_step(
    step_type="inventory_setup",
    category="inventory",
    allowed_params=(
        "buy_ectoplasm",
        "id_kits_target",
        "leave_party",
        "location",
        "material_mode",
        "ms",
        "multibox",
        "multibox_wait_step_ms",
        "multibox_wait_timeout_ms",
        "name",
        "npc",
        "restock_consumables",
        "return_map_id",
        "salvage_kits_target",
        "start_storage_gold_threshold",
        "stop_storage_gold_threshold",
        "use_storage_gold",
    ),
    node_class_name="InventorySetupNode",
)(handle_inventory_setup)
modular_step(
    step_type="restock_cons",
    category="inventory",
    allowed_params=("name",),
    node_class_name="RestockConsNode",
)(handle_restock_cons)
modular_step(
    step_type="restock_kits",
    category="inventory",
    allowed_params=("id_kits", "multibox", "multibox_wait_step_ms", "multibox_wait_timeout_ms", "name", "npc", "salvage_kits"),
    node_class_name="RestockKitsNode",
)(handle_restock_kits)
