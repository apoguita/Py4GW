"""
actions_inventory module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from time import monotonic
from typing import Callable

from .step_context import StepContext
from .step_selectors import resolve_agent_xy_from_step
from .step_utils import debug_log_recipe, log_recipe, parse_step_bool, parse_step_int, wait_after_step
from .inventory_recipe import (
    CONS_COMMON_MATERIAL_MODEL_IDS,
    NON_CONS_COMMON_MATERIAL_MODEL_IDS,
)

_SELECTOR_OVERRIDE_KEYS = (
    "point",
    "x",
    "y",
    "npc",
    "target",
    "name_contains",
    "agent_name",
    "model_id",
    "nearest",
)

DEFAULT_NPC_SELECTORS: dict[str, str] = {
    "merchant": "MERCHANT",
    "materials": "CRAFTING_MATERIAL_TRADER",
    "rare_materials": "RARE_MATERIAL_TRADER",
}

# Supported outposts with specific, known NPC encrypted-name selectors.
SUPPORTED_MAP_NPC_SELECTORS: dict[int, dict[str, str]] = {
    642: {  # Eye of the North
        "merchant": "MARYANN_MERCHANT",
        "materials": "IDA_MATERIAL_TRADER",
        "rare_materials": "ROLAND_RARE_MATERIAL_TRADER",
    },
    821: {  # Eye of the North (Wintersday)
        "merchant": "MARYANN_MERCHANT",
        "materials": "IDA_MATERIAL_TRADER",
        "rare_materials": "ROLAND_RARE_MATERIAL_TRADER",
    },
    641: {  # Tarnished Haven
        "merchant": "ADRIANA_MERCHANT",
        "materials": "ANDERS_MATERIAL_TRADER",
        "rare_materials": "HELENA_RARE_MATERIAL_TRADER",
    },
    643: {  # Sifhalla
        "merchant": "ABJORN_MERCHANT",
        "materials": "VATHI_MATERIAL_TRADER",
        "rare_materials": "BIRNA_RARE_MATERIAL_TRADER",
    },
    491: {  # Jokanur Diggings outpost
        "merchant": "LOKAI_MERCHANT",
        "materials": "GUUL_MATERIAL_TRADER",
        "rare_materials": "NEHGOYO_RARE_MATERIAL_TRADER",
    },
}

_PARTY_BACKEND_HERO_AI = "hero_ai"
_PARTY_BACKEND_SHARED = "shared"


def _resolve_party_backend() -> str:
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

    widget_handler = get_widget_handler()
    hero_ai_enabled = bool(widget_handler.is_widget_enabled("HeroAI"))

    if hero_ai_enabled:
        return _PARTY_BACKEND_HERO_AI
    return _PARTY_BACKEND_SHARED


def _wait_for_outbound_messages(
    ctx: StepContext,
    command_name: str,
    message_refs: list[tuple[str, int]],
    shared_command_type: int,
    *,
    wait_step_ms: int = 50,
    timeout_ms: int = 30_000,
):
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines

    if not message_refs:
        return

    pending: dict[tuple[str, int], None] = {}
    sender_email = Player.GetAccountEmail()
    for account_email, message_index in message_refs:
        if message_index < 0:
            log_recipe(ctx, f"{command_name}: failed to send to {account_email} (no free shared-memory slot).")
            continue
        pending[(account_email, message_index)] = None

    if not pending:
        return

    deadline = monotonic() + (max(0, timeout_ms) / 1000.0)
    while pending and monotonic() < deadline:
        completed: list[tuple[str, int]] = []
        for account_email, message_index in list(pending.keys()):
            message = GLOBAL_CACHE.ShMem.GetInbox(message_index)
            is_same_message = (
                bool(getattr(message, "Active", False))
                and str(getattr(message, "ReceiverEmail", "") or "") == account_email
                and str(getattr(message, "SenderEmail", "") or "") == sender_email
                and int(getattr(message, "Command", -1)) == int(shared_command_type)
            )
            if not is_same_message:
                completed.append((account_email, message_index))

        for key in completed:
            pending.pop(key, None)

        if pending:
            yield from Routines.Yield.wait(wait_step_ms)

    if pending:
        pending_accounts = ", ".join(sorted({account for account, _ in pending}))
        log_recipe(
            ctx,
            f"{command_name}: timeout waiting for multibox completion after {timeout_ms} ms. Pending: {pending_accounts}",
        )


def _iter_other_account_emails() -> list[str]:
    from Py4GWCoreLib import GLOBAL_CACHE, Player

    sender_email = Player.GetAccountEmail()
    account_emails: list[str] = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        account_email = str(getattr(account, "AccountEmail", "") or "")
        if not account_email or account_email == sender_email:
            continue
        account_emails.append(account_email)
    return account_emails


def _parse_widget_names(raw_widgets: object) -> list[str]:
    if isinstance(raw_widgets, str):
        candidates = [part.strip() for part in raw_widgets.split(",")]
    elif isinstance(raw_widgets, (list, tuple, set)):
        candidates = [str(part).strip() for part in raw_widgets]
    else:
        candidates = []

    seen: set[str] = set()
    names: list[str] = []
    for candidate in candidates:
        if not candidate:
            continue
        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        names.append(candidate)
    return names


def _yield_toggle_widgets(ctx: StepContext, *, enabled: bool):
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

    default_widgets = ["InventoryPlus"]
    names = _parse_widget_names(ctx.step.get("widgets", default_widgets))
    multibox = parse_step_bool(ctx.step.get("multibox", True), True)
    wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    timeout_ms = max(500, parse_step_int(ctx.step.get("multibox_timeout_ms", 30_000), 30_000))
    wait_ms = max(0, parse_step_int(ctx.step.get("ms", 0), 0))
    remember_key = str(ctx.step.get("remember_key", "") or "").strip()
    restore_key = str(ctx.step.get("restore_key", "") or "").strip()

    action_name = "enable_widgets" if enabled else "disable_widgets"
    shared_command = SharedCommandType.EnableWidget if enabled else SharedCommandType.DisableWidget

    def _toggle():
        handler = get_widget_handler()
        state_store = getattr(ctx.bot.config, "_modular_widget_state_store", None)
        if not isinstance(state_store, dict):
            state_store = {}
            setattr(ctx.bot.config, "_modular_widget_state_store", state_store)

        target_names = list(names)
        if enabled and restore_key:
            if restore_key in state_store:
                restored = state_store.get(restore_key, [])
                if isinstance(restored, (list, tuple)):
                    target_names = [str(name).strip() for name in restored if str(name).strip()]

        if not enabled and remember_key:
            target_names = [name for name in target_names if handler.is_widget_enabled(name)]
            state_store[remember_key] = list(target_names)

        if not target_names:
            log_recipe(ctx, f"{action_name}: skipped (no widget names).")
            yield
            return

        for widget_name in target_names:
            if enabled:
                handler.enable_widget(widget_name)
            else:
                handler.disable_widget(widget_name)

        if multibox:
            sender_email = Player.GetAccountEmail()
            sent_messages: list[tuple[str, int]] = []
            for account_email in _iter_other_account_emails():
                for widget_name in target_names:
                    message_index = GLOBAL_CACHE.ShMem.SendMessage(
                        sender_email,
                        account_email,
                        shared_command,
                        (0, 0, 0, 0),
                        (widget_name, "", "", ""),
                    )
                    sent_messages.append((account_email, int(message_index)))
            yield from _wait_for_outbound_messages(
                ctx,
                action_name,
                sent_messages,
                shared_command,
                wait_step_ms=wait_step_ms,
                timeout_ms=timeout_ms,
            )

        if wait_ms > 0:
            yield from Routines.Yield.wait(wait_ms)

        log_recipe(ctx, f"{action_name}: {'enabled' if enabled else 'disabled'} {target_names} (multibox={multibox}).")
        yield

    return _toggle


def _encode_material_model_filter(selected_models: set[int] | None) -> str:
    if not selected_models:
        return ""
    return ",".join(str(model_id) for model_id in sorted(selected_models))


def _step_has_explicit_agent_selector(step: dict) -> bool:
    return any(key in step for key in _SELECTOR_OVERRIDE_KEYS)


def _resolve_default_npc_selector(selector_kind: str) -> str:
    from Py4GWCoreLib import Map

    map_id = int(Map.GetMapID() or 0)
    map_selectors = SUPPORTED_MAP_NPC_SELECTORS.get(map_id)
    if map_selectors is not None:
        selected = map_selectors.get(selector_kind)
        if selected:
            return selected

    return DEFAULT_NPC_SELECTORS[selector_kind]


def _apply_default_npc_selector(step: dict, selector_kind: str) -> None:
    if _step_has_explicit_agent_selector(step):
        return
    step["npc"] = _resolve_default_npc_selector(selector_kind)


def _count_model_in_inventory(model_id: int) -> int:
    from Py4GWCoreLib import GLOBAL_CACHE

    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    count = 0
    for item_id in item_array:
        if int(GLOBAL_CACHE.Item.GetModelID(item_id)) == int(model_id):
            count += max(1, int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)))
    return int(count)


def _count_model_stacks_in_inventory(model_id: int) -> int:
    """Count physical item stacks/instances (not quantity/charges)."""
    from Py4GWCoreLib import GLOBAL_CACHE

    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    return int(
        sum(
            1
            for item_id in item_array
            if int(GLOBAL_CACHE.Item.GetModelID(item_id)) == int(model_id)
        )
    )


def _get_id_kit_count() -> int:
    from Py4GWCoreLib import ModelID

    return _count_model_stacks_in_inventory(ModelID.Identification_Kit.value) + _count_model_stacks_in_inventory(
        ModelID.Superior_Identification_Kit.value
    )


def _get_salvage_kit_count() -> int:
    from Py4GWCoreLib import ModelID

    return _count_model_stacks_in_inventory(ModelID.Salvage_Kit.value)


def _get_leftover_material_item_ids(batch_size: int = 10) -> list[int]:
    from Py4GWCoreLib import GLOBAL_CACHE

    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    leftovers: list[int] = []
    for item_id in item_array:
        if not GLOBAL_CACHE.Item.Type.IsMaterial(item_id):
            continue
        if GLOBAL_CACHE.Item.Type.IsRareMaterial(item_id):
            continue
        qty = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
        if 0 < qty < int(batch_size):
            leftovers.append(int(item_id))
    return leftovers


def _get_nonsalvageable_gold_item_ids() -> list[int]:
    from Py4GWCoreLib import GLOBAL_CACHE

    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sell_ids: list[int] = []
    for item_id in item_array:
        _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
        if rarity != "Gold":
            continue
        if not GLOBAL_CACHE.Item.Usage.IsIdentified(item_id):
            continue
        if GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id):
            continue
        sell_ids.append(int(item_id))
    return sell_ids


def _resolve_inventory_location_key(location_raw: str, return_map_id: int) -> str:
    key = str(location_raw or "auto").strip().lower()
    if key == "auto":
        if int(return_map_id or 0) in SUPPORTED_MAP_NPC_SELECTORS:
            return f"map_{int(return_map_id)}"
        return "guild_hall"
    if key == "guild_hall":
        return "guild_hall"
    if key.startswith("map_"):
        return key
    try:
        return f"map_{int(key)}"
    except (TypeError, ValueError):
        return "guild_hall"


def _resolve_inventory_material_mode(mode_raw: str) -> str:
    mode = str(mode_raw or "").strip().lower()
    aliases = {
        "sell_all_common_materials": "sell_all",
        "deposit_cons_sell_non_cons": "deposit_cons_sell_non_cons",
        "sell_non_cons_deposit_cons": "deposit_cons_sell_non_cons",
        "deposit_all": "deposit_all",
        "sell_all": "sell_all",
        "none": "none",
    }
    return aliases.get(mode, "deposit_cons_sell_non_cons")


def _yield_shared_leave_party(ctx: StepContext, multibox: bool) -> Callable[[], object]:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, SharedCommandType

    def _coro():
        if not multibox:
            ctx.bot.Party.LeaveParty()
            yield from ctx.bot.Wait._coro_for_time(1000)
            return

        sender_email = Player.GetAccountEmail()
        backend = _resolve_party_backend()
        sent_messages: list[tuple[str, int]] = []

        if backend == _PARTY_BACKEND_HERO_AI:
            debug_log_recipe(ctx, "inventory_setup: leave_party HeroAI backend; using shared dispatch.")
        elif backend == _PARTY_BACKEND_SHARED:
            debug_log_recipe(ctx, "inventory_setup: leave_party no HeroAI widget; using shared dispatch.")

        for account_email in _iter_other_account_emails():
            message_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                account_email,
                SharedCommandType.LeaveParty,
                (0, 0, 0, 0),
            )
            sent_messages.append((account_email, int(message_index)))

        ctx.bot.Party.LeaveParty()
        if sent_messages:
            yield from _wait_for_outbound_messages(
                ctx,
                "inventory_setup.leave_party",
                sent_messages,
                SharedCommandType.LeaveParty,
            )
        yield from ctx.bot.Wait._coro_for_time(1000)

    return _coro


def _yield_travel_gh(ctx: StepContext, multibox: bool, _wait_time: int) -> Callable[[], object]:
    from Py4GWCoreLib import GLOBAL_CACHE, Map, Player, SharedCommandType
    per_account_delay_ms = max(0, parse_step_int(ctx.step.get("per_account_delay_ms", 500), 500))

    def _coro():
        def _travel_local_gh():
            if not Map.IsGuildHall():
                yield from ctx.bot.Map._coro_travel_to_gh(wait_time=max(1000, int(_wait_time or 1000)))

        if not multibox:
            if not Map.IsGuildHall():
                yield from _travel_local_gh()
            return

        sender_email = Player.GetAccountEmail()
        backend = _resolve_party_backend()
        sent_messages: list[tuple[str, int]] = []

        if backend == _PARTY_BACKEND_HERO_AI:
            debug_log_recipe(ctx, "inventory_setup: travel_gh HeroAI backend; dispatching alts + local self-message.")
        elif backend == _PARTY_BACKEND_SHARED:
            debug_log_recipe(ctx, "inventory_setup: travel_gh no HeroAI widget; using shared dispatch.")

        for account_email in _iter_other_account_emails():
            message_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                account_email,
                SharedCommandType.TravelToGuildHall,
                (0, 0, 0, 0),
            )
            sent_messages.append((account_email, int(message_index)))
            if per_account_delay_ms > 0:
                yield from ctx.bot.Wait._coro_for_time(per_account_delay_ms)
        if sent_messages:
            yield from _wait_for_outbound_messages(
                ctx,
                "inventory_setup.travel_gh",
                sent_messages,
                SharedCommandType.TravelToGuildHall,
            )

        if not Map.IsGuildHall():
            yield from _travel_local_gh()

    return _coro


def _yield_restock_consumables(ctx: StepContext) -> Callable[[], object]:
    def _coro():
        from Py4GWCoreLib import Inventory

        if not Inventory.IsStorageOpen():
            Inventory.OpenXunlaiWindow()
            yield from ctx.bot.Wait._coro_for_time(1000)

        restock_specs = (
            ("birthday_cupcake", "restock_birthday_cupcake"),
            ("candy_apple", "restock_candy_apple"),
            ("honeycomb", "restock_honeycomb"),
            ("war_supplies", "restock_war_supplies"),
            ("essence_of_celerity", "restock_essence_of_celerity"),
            ("grail_of_might", "restock_grail_of_might"),
            ("armor_of_salvation", "restock_armor_of_salvation"),
            ("golden_egg", "restock_golden_egg"),
            ("candy_corn", "restock_candy_corn"),
            ("slice_of_pumpkin_pie", "restock_slice_of_pumpkin_pie"),
            ("drake_kabob", "restock_drake_kabob"),
            ("bowl_of_skalefin_soup", "restock_bowl_of_skalefin_soup"),
            ("pahnai_salad", "restock_pahnai_salad"),
        )

        for prop_name, method_name in restock_specs:
            if not ctx.bot.Properties.exists(prop_name):
                continue
            is_active = bool(ctx.bot.Properties.Get(prop_name, "active"))
            qty = int(ctx.bot.Properties.Get(prop_name, "restock_quantity") or 0)
            if not is_active or qty <= 0:
                continue
            method = getattr(ctx.bot.helpers.Restock, method_name, None)
            if callable(method):
                yield from method()
        yield

    return _coro


def _yield_inventory_setup(ctx: StepContext, step: dict) -> Callable[[], object]:
    from Py4GWCoreLib import GLOBAL_CACHE, Map, Player, Routines, SharedCommandType

    multibox = parse_step_bool(step.get("multibox", True), True)
    leave_party = parse_step_bool(step.get("leave_party", True), True)
    wait_time = max(1000, parse_step_int(step.get("ms", 5000), 5000))
    return_map_id = parse_step_int(step.get("return_map_id", 0), 0)
    location_key = _resolve_inventory_location_key(step.get("location", "auto"), return_map_id)
    id_kits_target = max(0, parse_step_int(step.get("id_kits_target", 3), 3))
    salvage_kits_target = max(0, parse_step_int(step.get("salvage_kits_target", 10), 10))
    buy_ectoplasm = parse_step_bool(step.get("buy_ectoplasm", False), False)
    use_storage_gold = parse_step_bool(step.get("use_storage_gold", False), False)
    start_storage_gold_threshold = max(0, parse_step_int(step.get("start_storage_gold_threshold", 900_000), 900_000))
    stop_storage_gold_threshold = max(0, parse_step_int(step.get("stop_storage_gold_threshold", 500_000), 500_000))
    material_mode = _resolve_inventory_material_mode(step.get("material_mode", "deposit_cons_sell_non_cons"))
    restock_consumables = parse_step_bool(step.get("restock_consumables", False), False)
    multibox_wait_step_ms = max(10, parse_step_int(step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(step.get("multibox_wait_timeout_ms", 30_000), 30_000))

    def _coro():
        sender_email = Player.GetAccountEmail()

        if location_key == "guild_hall":
            if leave_party:
                yield from _yield_shared_leave_party(ctx, multibox)()
            yield from _yield_travel_gh(ctx, multibox, wait_time)()
        elif return_map_id > 0 and int(Map.GetMapID() or 0) != return_map_id:
            yield from ctx.bot.Map._coro_travel(return_map_id, "")
            yield from ctx.bot.Wait._coro_for_time(wait_time)
            if multibox:
                yield from ctx.bot.helpers.Multibox.summon_all_accounts()
                yield from ctx.bot.Wait._coro_for_time(1500)

        selector_step = dict(step)
        _apply_default_npc_selector(selector_step, "merchant")
        merchant_xy = resolve_agent_xy_from_step(
            selector_step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if merchant_xy is None:
            log_recipe(ctx, "inventory_setup: failed to resolve Merchant coordinates.")
            yield
            return
        mx, my = merchant_xy

        sent_messages: list[tuple[str, int]] = []
        if multibox:
            for account_email in _iter_other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantItems,
                    (mx, my, float(id_kits_target), float(salvage_kits_target)),
                )
                sent_messages.append((account_email, int(message_index)))

        yield from ctx.bot.Move._coro_xy_and_interact_npc(mx, my, step.get("name", "Inventory Setup"))
        yield from ctx.bot.Wait._coro_for_time(1200)

        initial_id_kits = _get_id_kit_count()
        initial_salvage_kits = _get_salvage_kit_count()
        id_buy_budget = max(0, id_kits_target - initial_id_kits)
        salvage_buy_budget = max(0, salvage_kits_target - initial_salvage_kits)
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
            yield from _wait_for_outbound_messages(
                ctx,
                "inventory_setup.restock_kits",
                sent_messages,
                SharedCommandType.MerchantItems,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )

        if restock_consumables:
            yield from _yield_restock_consumables(ctx)()

        if material_mode != "none":
            selector_step = dict(step)
            _apply_default_npc_selector(selector_step, "materials")
            material_xy = resolve_agent_xy_from_step(
                selector_step,
                recipe_name=ctx.recipe_name,
                step_idx=ctx.step_idx,
                agent_kind="npc",
            )
            if material_xy is not None:
                tx, ty = material_xy
                if material_mode in ("sell_all", "deposit_cons_sell_non_cons"):
                    selected_models = None if material_mode == "sell_all" else set(NON_CONS_COMMON_MATERIAL_MODEL_IDS)
                    extra_data = ("sell", _encode_material_model_filter(selected_models), "", "")
                    sent_messages = []
                    if multibox:
                        for account_email in _iter_other_account_emails():
                            message_index = GLOBAL_CACHE.ShMem.SendMessage(
                                sender_email,
                                account_email,
                                SharedCommandType.MerchantMaterials,
                                (float(tx), float(ty), 0.0, 0.0),
                                extra_data,
                            )
                            sent_messages.append((account_email, int(message_index)))
                    yield from Routines.Yield.Merchant.SellMaterialsAtTrader(tx, ty, selected_models=selected_models)
                    if multibox:
                        yield from _wait_for_outbound_messages(
                            ctx,
                            "inventory_setup.sell_materials",
                            sent_messages,
                            SharedCommandType.MerchantMaterials,
                            wait_step_ms=multibox_wait_step_ms,
                            timeout_ms=multibox_wait_timeout_ms,
                        )

                if material_mode in ("deposit_all", "deposit_cons_sell_non_cons"):
                    selected_models = None if material_mode == "deposit_all" else set(CONS_COMMON_MATERIAL_MODEL_IDS)
                    extra_data = ("deposit", _encode_material_model_filter(selected_models), "0", "0")
                    sent_messages = []
                    if multibox:
                        for account_email in _iter_other_account_emails():
                            message_index = GLOBAL_CACHE.ShMem.SendMessage(
                                sender_email,
                                account_email,
                                SharedCommandType.MerchantMaterials,
                                (0.0, 0.0, 0.0, 0.0),
                                extra_data,
                            )
                            sent_messages.append((account_email, int(message_index)))
                    yield from Routines.Yield.Merchant.DepositMaterials(selected_models=selected_models, max_deposit_items=None)
                    if multibox:
                        yield from _wait_for_outbound_messages(
                            ctx,
                            "inventory_setup.deposit_materials",
                            sent_messages,
                            SharedCommandType.MerchantMaterials,
                            wait_step_ms=multibox_wait_step_ms,
                            timeout_ms=multibox_wait_timeout_ms,
                        )

        if buy_ectoplasm:
            selector_step = dict(step)
            _apply_default_npc_selector(selector_step, "rare_materials")
            rare_xy = resolve_agent_xy_from_step(
                selector_step,
                recipe_name=ctx.recipe_name,
                step_idx=ctx.step_idx,
                agent_kind="npc",
            )
            if rare_xy is not None:
                rx, ry = rare_xy
                sent_messages = []
                if multibox:
                    extra_data = ("buy_ectoplasm", "1" if use_storage_gold else "0", "0", "")
                    for account_email in _iter_other_account_emails():
                        message_index = GLOBAL_CACHE.ShMem.SendMessage(
                            sender_email,
                            account_email,
                            SharedCommandType.MerchantMaterials,
                            (float(rx), float(ry), float(start_storage_gold_threshold), float(stop_storage_gold_threshold)),
                            extra_data,
                        )
                        sent_messages.append((account_email, int(message_index)))
                yield from Routines.Yield.Merchant.BuyEctoplasm(
                    x=rx,
                    y=ry,
                    use_storage_gold=use_storage_gold,
                    start_threshold=start_storage_gold_threshold,
                    stop_threshold=stop_storage_gold_threshold,
                    max_ecto_to_buy=None,
                )
                if multibox:
                    yield from _wait_for_outbound_messages(
                        ctx,
                        "inventory_setup.buy_ectoplasm",
                        sent_messages,
                        SharedCommandType.MerchantMaterials,
                        wait_step_ms=multibox_wait_step_ms,
                        timeout_ms=multibox_wait_timeout_ms,
                    )

        if return_map_id > 0 and int(Map.GetMapID() or 0) != return_map_id:
            yield from ctx.bot.Map._coro_travel(return_map_id, "")
            yield from ctx.bot.Wait._coro_for_time(wait_time)

        if multibox and return_map_id > 0:
            yield from ctx.bot.helpers.Multibox.summon_all_accounts()
            yield from ctx.bot.Wait._coro_for_time(2000)
            yield from ctx.bot.helpers.Multibox.invite_all_accounts()
            yield from ctx.bot.Wait._coro_for_time(1000)

        yield

    return _coro
