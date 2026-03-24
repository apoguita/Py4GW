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

_PARTY_BACKEND_CB = "custom_behaviors"
_PARTY_BACKEND_HERO_AI = "hero_ai"
_PARTY_BACKEND_SHARED = "shared"


def _resolve_party_backend() -> str:
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

    widget_handler = get_widget_handler()
    cb_enabled = bool(widget_handler.is_widget_enabled("CustomBehaviors"))
    hero_ai_enabled = bool(widget_handler.is_widget_enabled("HeroAI"))

    if cb_enabled and not hero_ai_enabled:
        return _PARTY_BACKEND_CB
    if hero_ai_enabled and not cb_enabled:
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

    default_widgets = ["InventoryPlus", "CustomBehaviors"]
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


def _get_id_kit_count() -> int:
    from Py4GWCoreLib import ModelID

    return _count_model_in_inventory(ModelID.Identification_Kit.value) + _count_model_in_inventory(
        ModelID.Superior_Identification_Kit.value
    )


def _get_salvage_kit_count() -> int:
    from Py4GWCoreLib import ModelID

    return _count_model_in_inventory(ModelID.Salvage_Kit.value)


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


def _yield_cb_leave_party(ctx: StepContext, multibox: bool) -> Callable[[], object]:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, SharedCommandType

    def _coro():
        if not multibox:
            ctx.bot.Party.LeaveParty()
            yield from ctx.bot.Wait._coro_for_time(1000)
            return

        sender_email = Player.GetAccountEmail()
        backend = _resolve_party_backend()
        used_cb_scheduler = False
        sent_messages: list[tuple[str, int]] = []

        if backend == _PARTY_BACKEND_CB:
            from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
            from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants

            yield from ctx.bot.Wait._coro_until_condition(lambda: CustomBehaviorParty().is_ready_for_action(), duration=100)
            ok = bool(CustomBehaviorParty().schedule_action(PartyCommandConstants.leave_current_party))
            if ok:
                used_cb_scheduler = True
                yield from ctx.bot.Wait._coro_until_condition(lambda: CustomBehaviorParty().is_ready_for_action(), duration=100)
                debug_log_recipe(ctx, "inventory_setup: leave_party via CustomBehaviors scheduler.")
            else:
                debug_log_recipe(ctx, "inventory_setup: leave_party CB scheduler not ready; using shared fallback.")

        if backend == _PARTY_BACKEND_HERO_AI:
            debug_log_recipe(ctx, "inventory_setup: leave_party HeroAI backend; using shared dispatch.")
        elif backend == _PARTY_BACKEND_SHARED:
            debug_log_recipe(ctx, "inventory_setup: leave_party ambiguous/no engine; using shared dispatch.")

        if not used_cb_scheduler:
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

    def _coro():
        def _send_local_gh_message():
            sender_email = Player.GetAccountEmail()
            message_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                sender_email,
                SharedCommandType.TravelToGuildHall,
                (0, 0, 0, 0),
            )
            refs = [(sender_email, int(message_index))]
            yield from _wait_for_outbound_messages(
                ctx,
                "inventory_setup.travel_gh.local",
                refs,
                SharedCommandType.TravelToGuildHall,
            )

        if not multibox:
            if not Map.IsGuildHall():
                yield from _send_local_gh_message()
            return

        sender_email = Player.GetAccountEmail()
        backend = _resolve_party_backend()
        used_cb_scheduler = False
        sent_messages: list[tuple[str, int]] = []

        if backend == _PARTY_BACKEND_CB:
            from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
            from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants

            yield from ctx.bot.Wait._coro_until_condition(lambda: CustomBehaviorParty().is_ready_for_action(), duration=100)
            ok = bool(CustomBehaviorParty().schedule_action(PartyCommandConstants.travel_gh))
            if ok:
                used_cb_scheduler = True
                yield from ctx.bot.Wait._coro_until_condition(lambda: CustomBehaviorParty().is_ready_for_action(), duration=100)
                debug_log_recipe(ctx, "inventory_setup: travel_gh via CustomBehaviors scheduler.")
            else:
                debug_log_recipe(ctx, "inventory_setup: travel_gh CB scheduler not ready; using shared fallback.")

        if backend == _PARTY_BACKEND_HERO_AI:
            debug_log_recipe(ctx, "inventory_setup: travel_gh HeroAI backend; dispatching alts + local self-message.")
        elif backend == _PARTY_BACKEND_SHARED:
            debug_log_recipe(ctx, "inventory_setup: travel_gh ambiguous/no engine; using shared dispatch.")

        if not used_cb_scheduler:
            for account_email in _iter_other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.TravelToGuildHall,
                    (0, 0, 0, 0),
                )
                sent_messages.append((account_email, int(message_index)))
            if sent_messages:
                yield from _wait_for_outbound_messages(
                    ctx,
                    "inventory_setup.travel_gh",
                    sent_messages,
                    SharedCommandType.TravelToGuildHall,
                )

            if not Map.IsGuildHall():
                yield from _send_local_gh_message()
        else:
            if not Map.IsGuildHall():
                yield from _send_local_gh_message()

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
                yield from _yield_cb_leave_party(ctx, multibox)()
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

        for _ in range(2):
            id_kits_to_buy = max(0, id_kits_target - _get_id_kit_count())
            salvage_kits_to_buy = max(0, salvage_kits_target - _get_salvage_kit_count())
            if id_kits_to_buy <= 0 and salvage_kits_to_buy <= 0:
                break
            yield from Routines.Yield.Merchant.BuyIDKits(id_kits_to_buy)
            yield from Routines.Yield.Merchant.BuySalvageKits(salvage_kits_to_buy)
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


def handle_restock_kits(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, ModelID, Player, Routines, SharedCommandType

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
        def _count_model_in_inventory(model_id: int) -> int:
            bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
            item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
            count = 0
            for item_id in item_array:
                if int(GLOBAL_CACHE.Item.GetModelID(item_id)) == int(model_id):
                    count += max(1, int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)))
            return int(count)

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

        # Recompute kit counts each purchase pass to avoid stale cache snapshots.
        for _ in range(2):
            id_kits_in_inv = _count_model_in_inventory(ModelID.Identification_Kit.value)
            sup_id_kits_in_inv = _count_model_in_inventory(ModelID.Superior_Identification_Kit.value)
            salvage_kits_in_inv = _count_model_in_inventory(ModelID.Salvage_Kit.value)

            id_kits_to_buy = max(0, id_kits_target - (id_kits_in_inv + sup_id_kits_in_inv))
            salvage_kits_to_buy = max(0, salvage_kits_target - salvage_kits_in_inv)

            if id_kits_to_buy <= 0 and salvage_kits_to_buy <= 0:
                break

            yield from Routines.Yield.Merchant.BuyIDKits(id_kits_to_buy)
            yield from Routines.Yield.Merchant.BuySalvageKits(salvage_kits_to_buy)
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


def handle_sell_materials(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType
    from Py4GWCoreLib.enums_src.Item_enums import MaterialMap
    from Py4GWCoreLib.enums_src.Model_enums import ModelID

    selector_step = dict(ctx.step)

    name = ctx.step.get("name", "Sell Materials")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    multibox_wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))
    reverse_material_map = {material_name.lower(): int(model_id.value) for model_id, material_name in MaterialMap.items()}

    def _resolve_selected_models_runtime() -> set[int] | None:
        selected_models: set[int] | None = None
        raw_materials = ctx.step.get("materials")
        if raw_materials is None:
            return None

        if not isinstance(raw_materials, (list, tuple, set)):
            raw_materials = [raw_materials]

        selected_models = set()
        for raw_material in raw_materials:
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

    def _sell_local():
        step_selector = dict(selector_step)
        _apply_default_npc_selector(step_selector, "materials")
        selected_models = _resolve_selected_models_runtime()
        log_recipe(ctx, f"sell_materials start: selector={step_selector!r}")
        coords = resolve_agent_xy_from_step(
            step_selector,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            log_recipe(ctx, "sell_materials: failed to resolve Crafting Material Trader coordinates.")
            yield
            return

        x, y = coords
        sent_messages: list[tuple[str, int]] = []
        if multibox:
            sender_email = Player.GetAccountEmail()
            account_emails = _iter_other_account_emails()
            extra_data = ("sell", _encode_material_model_filter(selected_models), "", "")
            for account_email in account_emails:
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (float(x), float(y), 0.0, 0.0),
                    extra_data,
                )
                sent_messages.append((account_email, int(message_index)))
            log_recipe(
                ctx,
                f"sell_materials: dispatched multibox sell command to {len(sent_messages)} account(s) before local execution.",
            )

        log_recipe(ctx, f"sell_materials: resolved trader at ({x}, {y}), executing local merchant routine.")
        sell_metrics = yield from Routines.Yield.Merchant.SellMaterialsAtTrader(
            x,
            y,
            selected_models=selected_models,
        )
        log_recipe(ctx, f"sell_materials metrics: {sell_metrics}")

        if multibox:
            yield from _wait_for_outbound_messages(
                ctx,
                "sell_materials",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )

        log_recipe(ctx, "sell_materials: completed.")
        yield

    ctx.bot.States.AddCustomState(_sell_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_deposit_materials(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Inventory, Player, Routines, SharedCommandType
    from Py4GWCoreLib.enums_src.Item_enums import MaterialMap
    from Py4GWCoreLib.enums_src.Model_enums import ModelID

    name = ctx.step.get("name", "Deposit Materials")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    multibox_wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))
    max_deposit_items_raw = parse_step_int(ctx.step.get("max_deposit_items", 0), 0)
    max_deposit_items = max_deposit_items_raw if max_deposit_items_raw > 0 else None
    exact_quantity_raw = parse_step_int(ctx.step.get("exact_quantity", 250), 250)
    exact_quantity = exact_quantity_raw if exact_quantity_raw > 0 else None
    open_wait_ms = max(0, parse_step_int(ctx.step.get("open_wait_ms", 1000), 1000))
    deposit_wait_ms = max(0, parse_step_int(ctx.step.get("deposit_wait_ms", 250), 250))
    max_passes = max(1, parse_step_int(ctx.step.get("max_passes", 2), 2))
    reverse_material_map = {material_name.lower(): int(model_id.value) for model_id, material_name in MaterialMap.items()}

    selected_models: set[int] | None = None
    raw_materials = ctx.step.get("materials")
    if raw_materials is not None:
        if not isinstance(raw_materials, (list, tuple, set)):
            raw_materials = [raw_materials]

        selected_models = set()
        for raw_material in raw_materials:
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

    def _deposit_local():
        if not Inventory.IsStorageOpen():
            log_recipe(ctx, "deposit_materials: opening Xunlai window.")
        deposit_metrics = yield from Routines.Yield.Merchant.DepositMaterials(
            selected_models=selected_models,
            exact_quantity=exact_quantity,
            max_deposit_items=max_deposit_items,
            open_wait_ms=open_wait_ms,
            deposit_wait_ms=deposit_wait_ms,
            max_passes=max_passes,
        )
        log_recipe(ctx, f"deposit_materials metrics: {deposit_metrics}")

        if multibox:
            sender_email = Player.GetAccountEmail()
            account_emails = _iter_other_account_emails()
            extra_data = ("deposit", _encode_material_model_filter(selected_models), str(max_deposit_items or 0), str(exact_quantity or 0))
            sent_messages: list[tuple[str, int]] = []
            for account_email in account_emails:
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (0.0, 0.0, 0.0, 0.0),
                    extra_data,
                )
                sent_messages.append((account_email, int(message_index)))
            yield from _wait_for_outbound_messages(
                ctx,
                "deposit_materials",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )

        log_recipe(ctx, "deposit_materials: completed.")
        yield

    ctx.bot.States.AddCustomState(_deposit_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_sell_nonsalvageable_golds(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType

    selector_step = dict(ctx.step)
    name = ctx.step.get("name", "Sell Non-Salvageable Golds")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    multibox_wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))

    def _sell_local():
        step_selector = dict(selector_step)
        _apply_default_npc_selector(step_selector, "merchant")
        coords = resolve_agent_xy_from_step(
            step_selector,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            log_recipe(ctx, "sell_nonsalvageable_golds: failed to resolve Merchant coordinates.")
            yield
            return

        x, y = coords
        sent_messages: list[tuple[str, int]] = []
        if multibox:
            sender_email = Player.GetAccountEmail()
            for account_email in _iter_other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (float(x), float(y), 0.0, 0.0),
                    ("sell_nonsalvageable_golds", "", "", ""),
                )
                sent_messages.append((account_email, int(message_index)))

        sell_ids = _get_nonsalvageable_gold_item_ids()
        if sell_ids:
            yield from ctx.bot.Move._coro_xy_and_interact_npc(x, y, name)
            yield from ctx.bot.Wait._coro_for_time(1200)
            yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
            log_recipe(ctx, f"sell_nonsalvageable_golds: sold {len(sell_ids)} item(s).")
        else:
            log_recipe(ctx, "sell_nonsalvageable_golds: no eligible gold items.")

        if multibox:
            yield from _wait_for_outbound_messages(
                ctx,
                "sell_nonsalvageable_golds",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )
        yield

    ctx.bot.States.AddCustomState(_sell_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_sell_leftover_materials(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType

    selector_step = dict(ctx.step)
    name = ctx.step.get("name", "Sell Leftover Materials")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    batch_size = max(1, parse_step_int(ctx.step.get("batch_size", 10), 10))
    multibox_wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))

    def _sell_local():
        step_selector = dict(selector_step)
        _apply_default_npc_selector(step_selector, "merchant")
        coords = resolve_agent_xy_from_step(
            step_selector,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            log_recipe(ctx, "sell_leftover_materials: failed to resolve Merchant coordinates.")
            yield
            return

        x, y = coords
        sent_messages: list[tuple[str, int]] = []
        if multibox:
            sender_email = Player.GetAccountEmail()
            for account_email in _iter_other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (float(x), float(y), 0.0, 0.0),
                    ("sell_merchant_leftovers", "", str(batch_size), ""),
                )
                sent_messages.append((account_email, int(message_index)))

        sell_ids = _get_leftover_material_item_ids(batch_size=batch_size)
        if sell_ids:
            yield from ctx.bot.Move._coro_xy_and_interact_npc(x, y, name)
            yield from ctx.bot.Wait._coro_for_time(1200)
            yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
            log_recipe(ctx, f"sell_leftover_materials: sold {len(sell_ids)} stack(s) with qty < {batch_size}.")
        else:
            log_recipe(ctx, f"sell_leftover_materials: no common material stacks below {batch_size}.")

        if multibox:
            yield from _wait_for_outbound_messages(
                ctx,
                "sell_leftover_materials",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )
        yield

    ctx.bot.States.AddCustomState(_sell_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_sell_scrolls(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType

    selector_step = dict(ctx.step)
    name = ctx.step.get("name", "Sell Scrolls")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    multibox_wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))
    scroll_models = set(int(v) for v in ctx.step.get("scroll_models", [5594, 5595, 5611, 5853, 5975, 5976, 21233]))

    def _sell_local():
        step_selector = dict(selector_step)
        _apply_default_npc_selector(step_selector, "merchant")
        coords = resolve_agent_xy_from_step(
            step_selector,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            log_recipe(ctx, "sell_scrolls: failed to resolve Merchant coordinates.")
            yield
            return

        x, y = coords
        sent_messages: list[tuple[str, int]] = []
        if multibox:
            sender_email = Player.GetAccountEmail()
            filter_raw = ",".join(str(mid) for mid in sorted(scroll_models))
            for account_email in _iter_other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (float(x), float(y), 0.0, 0.0),
                    ("sell_scrolls", filter_raw, "", ""),
                )
                sent_messages.append((account_email, int(message_index)))

        bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
        sell_ids = [int(item_id) for item_id in item_array if int(GLOBAL_CACHE.Item.GetModelID(item_id)) in scroll_models]
        if sell_ids:
            yield from ctx.bot.Move._coro_xy_and_interact_npc(x, y, name)
            yield from ctx.bot.Wait._coro_for_time(1200)
            yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
            log_recipe(ctx, f"sell_scrolls: sold {len(sell_ids)} scroll(s).")
        else:
            log_recipe(ctx, "sell_scrolls: no matching scrolls.")

        if multibox:
            yield from _wait_for_outbound_messages(
                ctx,
                "sell_scrolls",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )
        yield

    ctx.bot.States.AddCustomState(_sell_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_buy_ectoplasm(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType

    selector_step = dict(ctx.step)

    name = ctx.step.get("name", "Buy Ectoplasm")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    multibox_wait_step_ms = max(10, parse_step_int(ctx.step.get("multibox_wait_step_ms", 50), 50))
    multibox_wait_timeout_ms = max(1_000, parse_step_int(ctx.step.get("multibox_wait_timeout_ms", 30_000), 30_000))
    use_storage_gold = str(ctx.step.get("use_storage_gold", True)).strip().lower() in ("1", "true", "yes", "on")
    start_storage_gold_threshold = parse_step_int(ctx.step.get("start_storage_gold_threshold", 900_000), 900_000)
    stop_storage_gold_threshold = parse_step_int(ctx.step.get("stop_storage_gold_threshold", 500_000), 500_000)
    max_ecto_to_buy_raw = parse_step_int(ctx.step.get("max_ecto_to_buy", 0), 0)
    max_ecto_to_buy = max_ecto_to_buy_raw if max_ecto_to_buy_raw > 0 else None
    if stop_storage_gold_threshold < 0:
        stop_storage_gold_threshold = 0
    if start_storage_gold_threshold < stop_storage_gold_threshold:
        start_storage_gold_threshold = stop_storage_gold_threshold

    def _buy_local():
        storage_gold = int(GLOBAL_CACHE.Inventory.GetGoldInStorage())
        character_gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
        if use_storage_gold:
            if storage_gold <= start_storage_gold_threshold:
                log_recipe(
                    ctx,
                    f"buy_ectoplasm: skipped, storage gold {storage_gold} is not above start threshold {start_storage_gold_threshold}.",
                )
                yield
                return
        elif character_gold <= 0:
            log_recipe(ctx, "buy_ectoplasm: skipped, character has no gold and storage mode is disabled.")
            yield
            return

        step_selector = dict(selector_step)
        _apply_default_npc_selector(step_selector, "rare_materials")
        coords = resolve_agent_xy_from_step(
            step_selector,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            log_recipe(ctx, "buy_ectoplasm: failed to resolve Rare Material Trader coordinates.")
            yield
            return

        x, y = coords
        log_recipe(
            ctx,
            f"buy_ectoplasm: use_storage_gold={use_storage_gold}, start storage_gold={storage_gold}, stop_threshold={stop_storage_gold_threshold}, trader=({x}, {y}).",
        )
        ecto_metrics = yield from Routines.Yield.Merchant.BuyEctoplasm(
            x=x,
            y=y,
            use_storage_gold=use_storage_gold,
            start_threshold=start_storage_gold_threshold,
            stop_threshold=stop_storage_gold_threshold,
            max_ecto_to_buy=max_ecto_to_buy,
        )
        log_recipe(ctx, f"buy_ectoplasm metrics: {ecto_metrics}")

        if multibox:
            sender_email = Player.GetAccountEmail()
            account_emails = _iter_other_account_emails()
            extra_data = ("buy_ectoplasm", "1" if use_storage_gold else "0", str(max_ecto_to_buy or 0), "")
            sent_messages: list[tuple[str, int]] = []
            for account_email in account_emails:
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (
                        float(x),
                        float(y),
                        float(start_storage_gold_threshold),
                        float(stop_storage_gold_threshold),
                    ),
                    extra_data,
                )
                sent_messages.append((account_email, int(message_index)))
            yield from _wait_for_outbound_messages(
                ctx,
                "buy_ectoplasm",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=multibox_wait_step_ms,
                timeout_ms=multibox_wait_timeout_ms,
            )

        log_recipe(ctx, f"buy_ectoplasm: completed with storage_gold={int(GLOBAL_CACHE.Inventory.GetGoldInStorage())}.")
        yield

    ctx.bot.States.AddCustomState(_buy_local, f"{name} Execute")
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
    from .action_registry import STEP_HANDLERS

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
        {"type": "resign", "name": "Resign All", "ms": 1000},
        {"type": "leave_party", "name": "Leave Party", "multibox": multibox},
        {"type": "travel_gh", "name": "Travel GH", "multibox": multibox, "ms": 7000},
        {
            "type": "deposit_materials",
            "name": "Store Craft Mats",
            "materials": ["Pile_Of_Glittering_Dust", "Bone", "Iron_Ingot", "Feather", "Plant_Fiber"],
            "exact_quantity": 0,
            "multibox": multibox,
            "ms": 500,
        },
        {"type": "sell_materials", "name": "Sell Trader Mats", "multibox": multibox},
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

        handler = STEP_HANDLERS.get(step_type)
        if handler is None:
            log_recipe(ctx, f"inventory_cleanup: missing handler for sub-step {step_type!r}.")
            continue
        sub_ctx = StepContext(
            bot=ctx.bot,
            step=step,
            step_idx=sub_idx,
            recipe_name=ctx.recipe_name,
            step_type=step_type,
            step_display=str(step.get("name", step_type)),
        )
        handler(sub_ctx)

    wait_after_step(ctx.bot, ctx.step)


def handle_disable_widgets(ctx: StepContext) -> None:
    name = str(ctx.step.get("name", "Disable Widgets") or "Disable Widgets")
    ctx.bot.States.AddCustomState(_yield_toggle_widgets(ctx, enabled=False), name)
    wait_after_step(ctx.bot, ctx.step)


def handle_enable_widgets(ctx: StepContext) -> None:
    name = str(ctx.step.get("name", "Enable Widgets") or "Enable Widgets")
    ctx.bot.States.AddCustomState(_yield_toggle_widgets(ctx, enabled=True), name)
    wait_after_step(ctx.bot, ctx.step)


HANDLERS: dict[str, Callable[[StepContext], None]] = {
    "restock_kits": handle_restock_kits,
    "restock_cons": handle_restock_cons,
    "sell_materials": handle_sell_materials,
    "deposit_materials": handle_deposit_materials,
    "sell_nonsalvageable_golds": handle_sell_nonsalvageable_golds,
    "sell_leftover_materials": handle_sell_leftover_materials,
    "sell_scrolls": handle_sell_scrolls,
    "buy_ectoplasm": handle_buy_ectoplasm,
    "inventory_setup": handle_inventory_setup,
    "inventory_guard": handle_inventory_guard,
    "inventory_cleanup": handle_inventory_cleanup,
    "disable_widgets": handle_disable_widgets,
    "enable_widgets": handle_enable_widgets,
}
