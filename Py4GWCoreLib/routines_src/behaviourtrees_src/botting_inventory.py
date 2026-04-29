"""
Reusable inventory and merchant helpers for Botting-style runtimes.
"""
from __future__ import annotations

from time import monotonic
from typing import Callable


CoordResolver = Callable[[], tuple[float, float] | None]
LogFn = Callable[[str], None]

CONS_COMMON_MATERIAL_MODEL_IDS: frozenset[int] = frozenset(
    {
        921,
        922,
        923,
        925,
        929,
        933,
        934,
        940,
        946,
        948,
        953,
        954,
        955,
        956,
    }
)
NON_CONS_COMMON_MATERIAL_MODEL_IDS: frozenset[int] = frozenset(
    {
        924,
        926,
        927,
        928,
        930,
        931,
        932,
        935,
        936,
        937,
        938,
        939,
        941,
        942,
        943,
        944,
        945,
        949,
        950,
        951,
        952,
    }
)

DEFAULT_NPC_SELECTORS: dict[str, str] = {
    "merchant": "MERCHANT",
    "materials": "CRAFTING_MATERIAL_TRADER",
    "rare_materials": "RARE_MATERIAL_TRADER",
}
SUPPORTED_MAP_NPC_SELECTORS: dict[int, dict[str, str]] = {
    642: {"merchant": "MARYANN_MERCHANT", "materials": "IDA_MATERIAL_TRADER", "rare_materials": "ROLAND_RARE_MATERIAL_TRADER"},
    821: {"merchant": "MARYANN_MERCHANT", "materials": "IDA_MATERIAL_TRADER", "rare_materials": "ROLAND_RARE_MATERIAL_TRADER"},
    641: {"merchant": "ADRIANA_MERCHANT", "materials": "ANDERS_MATERIAL_TRADER", "rare_materials": "HELENA_RARE_MATERIAL_TRADER"},
    643: {"merchant": "ABJORN_MERCHANT", "materials": "VATHI_MATERIAL_TRADER", "rare_materials": "BIRNA_RARE_MATERIAL_TRADER"},
    491: {"merchant": "LOKAI_MERCHANT", "materials": "GUUL_MATERIAL_TRADER", "rare_materials": "NEHGOYO_RARE_MATERIAL_TRADER"},
}
SELECTOR_OVERRIDE_KEYS = (
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


def _noop_log(_message: str) -> None:
    return


def iter_other_account_emails() -> list[str]:
    from Py4GWCoreLib import GLOBAL_CACHE, Player

    sender_email = Player.GetAccountEmail()
    account_emails: list[str] = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        account_email = str(getattr(account, "AccountEmail", "") or "")
        if account_email and account_email != sender_email:
            account_emails.append(account_email)
    return account_emails


def parse_widget_names(raw_widgets: object) -> list[str]:
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


def encode_material_model_filter(selected_models: set[int] | None) -> str:
    if not selected_models:
        return ""
    return ",".join(str(model_id) for model_id in sorted(selected_models))


def step_has_explicit_agent_selector(step: dict) -> bool:
    return any(key in step for key in SELECTOR_OVERRIDE_KEYS)


def resolve_default_npc_selector(selector_kind: str) -> str:
    from Py4GWCoreLib import Map

    map_id = int(Map.GetMapID() or 0)
    map_selectors = SUPPORTED_MAP_NPC_SELECTORS.get(map_id)
    if map_selectors is not None:
        selected = map_selectors.get(selector_kind)
        if selected:
            return selected
    return DEFAULT_NPC_SELECTORS[selector_kind]


def apply_default_npc_selector(step: dict, selector_kind: str) -> None:
    if not step_has_explicit_agent_selector(step):
        step["npc"] = resolve_default_npc_selector(selector_kind)


def count_model_stacks_in_inventory(model_id: int) -> int:
    from Py4GWCoreLib import GLOBAL_CACHE

    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    return int(sum(1 for item_id in item_array if int(GLOBAL_CACHE.Item.GetModelID(item_id)) == int(model_id)))


def get_id_kit_count() -> int:
    from Py4GWCoreLib import ModelID

    return count_model_stacks_in_inventory(ModelID.Identification_Kit.value) + count_model_stacks_in_inventory(
        ModelID.Superior_Identification_Kit.value
    )


def get_salvage_kit_count() -> int:
    from Py4GWCoreLib import ModelID

    return count_model_stacks_in_inventory(ModelID.Salvage_Kit.value)


def get_leftover_material_item_ids(batch_size: int = 10) -> list[int]:
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


def get_nonsalvageable_gold_item_ids() -> list[int]:
    from Py4GWCoreLib import GLOBAL_CACHE

    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sell_ids: list[int] = []
    for item_id in item_array:
        _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
        if rarity == "Gold" and GLOBAL_CACHE.Item.Usage.IsIdentified(item_id) and not GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id):
            sell_ids.append(int(item_id))
    return sell_ids


def wait_for_outbound_messages(
    command_name: str,
    message_refs: list[tuple[str, int]],
    shared_command_type: int,
    *,
    wait_step_ms: int = 50,
    timeout_ms: int = 30_000,
    log: LogFn | None = None,
):
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines

    log_fn = log or _noop_log
    if not message_refs:
        return
    pending: dict[tuple[str, int], None] = {}
    sender_email = Player.GetAccountEmail()
    for account_email, message_index in message_refs:
        if message_index < 0:
            log_fn(f"{command_name}: failed to send to {account_email} (no free shared-memory slot).")
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
        log_fn(f"{command_name}: timeout waiting for multibox completion after {timeout_ms} ms. Pending: {pending_accounts}")


def add_toggle_widgets_state(
    bot,
    *,
    enabled: bool,
    names: list[str],
    multibox: bool,
    wait_step_ms: int,
    timeout_ms: int,
    wait_ms: int,
    remember_key: str = "",
    restore_key: str = "",
    name: str = "Toggle Widgets",
    log: LogFn | None = None,
) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

    log_fn = log or _noop_log
    action_name = "enable_widgets" if enabled else "disable_widgets"
    shared_command = SharedCommandType.EnableWidget if enabled else SharedCommandType.DisableWidget

    def _toggle():
        handler = get_widget_handler()
        state_store = getattr(bot.config, "_modular_widget_state_store", None)
        if not isinstance(state_store, dict):
            state_store = {}
            setattr(bot.config, "_modular_widget_state_store", state_store)

        target_names = list(names)
        if enabled and restore_key and restore_key in state_store:
            restored = state_store.get(restore_key, [])
            if isinstance(restored, (list, tuple)):
                target_names = [str(item).strip() for item in restored if str(item).strip()]
        if not enabled and remember_key:
            target_names = [widget_name for widget_name in target_names if handler.is_widget_enabled(widget_name)]
            state_store[remember_key] = list(target_names)
        if not target_names:
            log_fn(f"{action_name}: skipped (no widget names).")
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
            for account_email in iter_other_account_emails():
                for widget_name in target_names:
                    message_index = GLOBAL_CACHE.ShMem.SendMessage(
                        sender_email,
                        account_email,
                        shared_command,
                        (0, 0, 0, 0),
                        (widget_name, "", "", ""),
                    )
                    sent_messages.append((account_email, int(message_index)))
            yield from wait_for_outbound_messages(
                action_name,
                sent_messages,
                shared_command,
                wait_step_ms=wait_step_ms,
                timeout_ms=timeout_ms,
                log=log_fn,
            )
        if wait_ms > 0:
            yield from Routines.Yield.wait(wait_ms)
        log_fn(f"{action_name}: {'enabled' if enabled else 'disabled'} {target_names} (multibox={multibox}).")
        yield

    bot.States.AddCustomState(_toggle, str(name))


def add_restock_kits_state(
    bot,
    *,
    coords_resolver: CoordResolver,
    id_kits_target: int,
    salvage_kits_target: int,
    multibox: bool,
    wait_step_ms: int,
    timeout_ms: int,
    name: str = "Restock Kits",
    log: LogFn | None = None,
) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType

    log_fn = log or _noop_log

    def _restock_local():
        coords = coords_resolver()
        if coords is None:
            yield
            return
        x, y = coords
        yield from bot.Move._coro_xy_and_interact_npc(x, y, name)
        yield from bot.Wait._coro_for_time(1200)

        initial_id_kits = get_id_kit_count()
        initial_salvage_kits = get_salvage_kit_count()
        id_buy_budget = max(0, id_kits_target - initial_id_kits)
        salvage_buy_budget = max(0, salvage_kits_target - initial_salvage_kits)
        id_bought = 0
        salvage_bought = 0
        for _ in range(2):
            id_kits_to_buy = min(max(0, id_kits_target - get_id_kit_count()), max(0, id_buy_budget - id_bought))
            salvage_kits_to_buy = min(
                max(0, salvage_kits_target - get_salvage_kit_count()),
                max(0, salvage_buy_budget - salvage_bought),
            )
            if id_kits_to_buy <= 0 and salvage_kits_to_buy <= 0:
                break
            yield from Routines.Yield.Merchant.BuyIDKits(id_kits_to_buy)
            yield from Routines.Yield.Merchant.BuySalvageKits(salvage_kits_to_buy)
            id_bought += id_kits_to_buy
            salvage_bought += salvage_kits_to_buy
            yield from Routines.Yield.wait(150)

        if multibox:
            sender_email = Player.GetAccountEmail()
            sent_messages: list[tuple[str, int]] = []
            for account_email in iter_other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantItems,
                    (x, y, float(id_kits_target), float(salvage_kits_target)),
                )
                sent_messages.append((account_email, int(message_index)))
            yield from wait_for_outbound_messages(
                "restock_kits",
                sent_messages,
                SharedCommandType.MerchantItems,
                wait_step_ms=wait_step_ms,
                timeout_ms=timeout_ms,
                log=log_fn,
            )
        yield

    bot.States.AddCustomState(_restock_local, f"{name} Execute")


def add_restock_consumables_state(bot, *, name: str = "Restock Consumables", log: LogFn | None = None) -> None:
    from Py4GWCoreLib import Inventory

    log_fn = log or _noop_log
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
    bot.States.AddCustomState(lambda: Inventory.OpenXunlaiWindow() if not Inventory.IsStorageOpen() else None, f"{name} Open Xunlai")
    bot.Wait.ForTime(1000)

    def _enable_restock_properties() -> None:
        for prop_name, _ in restock_specs:
            if bot.Properties.exists(prop_name):
                is_active = bool(bot.Properties.Get(prop_name, "active"))
                qty = int(bot.Properties.Get(prop_name, "restock_quantity") or 0)
                if not is_active and qty > 0:
                    bot.Properties.Enable(prop_name)

    bot.States.AddCustomState(_enable_restock_properties, f"{name} Enable Properties")
    scheduled = 0
    for _, method_name in restock_specs:
        method = getattr(bot.Items.Restock, method_name, None)
        if callable(method):
            method()
            scheduled += 1
    if scheduled == 0:
        bot.States.AddCustomState(lambda: log_fn("restock_cons found no restock methods to execute."), f"{name} Warn: No Restock Methods")


def add_inventory_guard_state(
    bot,
    *,
    id_kits_min: int,
    salvage_kits_min: int,
    setup_factory: Callable[[], object],
    name: str = "Inventory Guard",
    log: LogFn | None = None,
) -> None:
    log_fn = log or _noop_log

    def _guard():
        current_id_kits = get_id_kit_count()
        current_salvage_kits = get_salvage_kit_count()
        if current_id_kits >= id_kits_min and current_salvage_kits >= salvage_kits_min:
            log_fn(
                f"inventory_guard: skipped (id_kits={current_id_kits}, salvage_kits={current_salvage_kits}, "
                f"mins={id_kits_min}/{salvage_kits_min})."
            )
            yield
            return
        log_fn(
            f"inventory_guard: triggering setup (id_kits={current_id_kits}, salvage_kits={current_salvage_kits}, "
            f"mins={id_kits_min}/{salvage_kits_min})."
        )
        yield from setup_factory()

    bot.States.AddCustomState(_guard, str(name))


def add_sell_materials_state(
    bot,
    *,
    coords_resolver: CoordResolver,
    selected_models: set[int] | None,
    multibox: bool,
    wait_step_ms: int,
    timeout_ms: int,
    name: str = "Sell Materials",
    log: LogFn | None = None,
) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType

    log_fn = log or _noop_log

    def _sell_local():
        coords = coords_resolver()
        if coords is None:
            log_fn("sell_materials: failed to resolve Crafting Material Trader coordinates.")
            yield
            return
        x, y = coords
        sent_messages: list[tuple[str, int]] = []
        if multibox:
            sender_email = Player.GetAccountEmail()
            extra_data = ("sell", encode_material_model_filter(selected_models), "", "")
            for account_email in iter_other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (float(x), float(y), 0.0, 0.0),
                    extra_data,
                )
                sent_messages.append((account_email, int(message_index)))
            log_fn(f"sell_materials: dispatched multibox sell command to {len(sent_messages)} account(s) before local execution.")
        log_fn(f"sell_materials: resolved trader at ({x}, {y}), executing local merchant routine.")
        sell_metrics = yield from Routines.Yield.Merchant.SellMaterialsAtTrader(x, y, selected_models=selected_models)
        log_fn(f"sell_materials metrics: {sell_metrics}")
        if multibox:
            yield from wait_for_outbound_messages(
                "sell_materials",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=wait_step_ms,
                timeout_ms=timeout_ms,
                log=log_fn,
            )
        log_fn("sell_materials: completed.")
        yield

    bot.States.AddCustomState(_sell_local, f"{name} Execute")


def add_deposit_materials_state(
    bot,
    *,
    selected_models: set[int] | None,
    max_deposit_items: int | None,
    exact_quantity: int | None,
    open_wait_ms: int,
    deposit_wait_ms: int,
    max_passes: int,
    multibox: bool,
    wait_step_ms: int,
    timeout_ms: int,
    name: str = "Deposit Materials",
    log: LogFn | None = None,
) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Inventory, Player, Routines, SharedCommandType

    log_fn = log or _noop_log

    def _deposit_local():
        if not Inventory.IsStorageOpen():
            log_fn("deposit_materials: opening Xunlai window.")
        deposit_metrics = yield from Routines.Yield.Merchant.DepositMaterials(
            selected_models=selected_models,
            exact_quantity=exact_quantity,
            max_deposit_items=max_deposit_items,
            open_wait_ms=open_wait_ms,
            deposit_wait_ms=deposit_wait_ms,
            max_passes=max_passes,
        )
        log_fn(f"deposit_materials metrics: {deposit_metrics}")
        if multibox:
            sender_email = Player.GetAccountEmail()
            extra_data = ("deposit", encode_material_model_filter(selected_models), str(max_deposit_items or 0), str(exact_quantity or 0))
            sent_messages: list[tuple[str, int]] = []
            for account_email in iter_other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (0.0, 0.0, 0.0, 0.0),
                    extra_data,
                )
                sent_messages.append((account_email, int(message_index)))
            yield from wait_for_outbound_messages(
                "deposit_materials",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=wait_step_ms,
                timeout_ms=timeout_ms,
                log=log_fn,
            )
        log_fn("deposit_materials: completed.")
        yield

    bot.States.AddCustomState(_deposit_local, f"{name} Execute")


def add_sell_item_ids_at_merchant_state(
    bot,
    *,
    coords_resolver: CoordResolver,
    item_ids_factory: Callable[[], list[int]],
    empty_message: str,
    complete_message: Callable[[int], str],
    multibox: bool,
    shared_extra_data: tuple[str, str, str, str],
    wait_step_ms: int,
    timeout_ms: int,
    name: str,
    log: LogFn | None = None,
) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType

    log_fn = log or _noop_log

    def _sell_local():
        coords = coords_resolver()
        if coords is None:
            log_fn(f"{name}: failed to resolve Merchant coordinates.")
            yield
            return
        x, y = coords
        sent_messages: list[tuple[str, int]] = []
        if multibox:
            sender_email = Player.GetAccountEmail()
            for account_email in iter_other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (float(x), float(y), 0.0, 0.0),
                    shared_extra_data,
                )
                sent_messages.append((account_email, int(message_index)))
        sell_ids = item_ids_factory()
        if sell_ids:
            yield from bot.Move._coro_xy_and_interact_npc(x, y, name)
            yield from bot.Wait._coro_for_time(1200)
            yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
            log_fn(complete_message(len(sell_ids)))
        else:
            log_fn(empty_message)
        if multibox:
            yield from wait_for_outbound_messages(
                name,
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=wait_step_ms,
                timeout_ms=timeout_ms,
                log=log_fn,
            )
        yield

    bot.States.AddCustomState(_sell_local, f"{name} Execute")


def add_buy_ectoplasm_state(
    bot,
    *,
    coords_resolver: CoordResolver,
    use_storage_gold: bool,
    start_storage_gold_threshold: int,
    stop_storage_gold_threshold: int,
    max_ecto_to_buy: int | None,
    multibox: bool,
    wait_step_ms: int,
    timeout_ms: int,
    name: str = "Buy Ectoplasm",
    log: LogFn | None = None,
) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType

    log_fn = log or _noop_log

    def _buy_local():
        storage_gold = int(GLOBAL_CACHE.Inventory.GetGoldInStorage())
        character_gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
        if use_storage_gold and storage_gold <= start_storage_gold_threshold:
            log_fn(f"buy_ectoplasm: skipped, storage gold {storage_gold} is not above start threshold {start_storage_gold_threshold}.")
            yield
            return
        if not use_storage_gold and character_gold <= 0:
            log_fn("buy_ectoplasm: skipped, character has no gold and storage mode is disabled.")
            yield
            return
        coords = coords_resolver()
        if coords is None:
            log_fn("buy_ectoplasm: failed to resolve Rare Material Trader coordinates.")
            yield
            return
        x, y = coords
        log_fn(
            f"buy_ectoplasm: use_storage_gold={use_storage_gold}, start storage_gold={storage_gold}, "
            f"stop_threshold={stop_storage_gold_threshold}, trader=({x}, {y})."
        )
        ecto_metrics = yield from Routines.Yield.Merchant.BuyEctoplasm(
            x=x,
            y=y,
            use_storage_gold=use_storage_gold,
            start_threshold=start_storage_gold_threshold,
            stop_threshold=stop_storage_gold_threshold,
            max_ecto_to_buy=max_ecto_to_buy,
        )
        log_fn(f"buy_ectoplasm metrics: {ecto_metrics}")
        if multibox:
            sender_email = Player.GetAccountEmail()
            extra_data = ("buy_ectoplasm", "1" if use_storage_gold else "0", str(max_ecto_to_buy or 0), "")
            sent_messages: list[tuple[str, int]] = []
            for account_email in iter_other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (float(x), float(y), float(start_storage_gold_threshold), float(stop_storage_gold_threshold)),
                    extra_data,
                )
                sent_messages.append((account_email, int(message_index)))
            yield from wait_for_outbound_messages(
                "buy_ectoplasm",
                sent_messages,
                SharedCommandType.MerchantMaterials,
                wait_step_ms=wait_step_ms,
                timeout_ms=timeout_ms,
                log=log_fn,
            )
        log_fn(f"buy_ectoplasm: completed with storage_gold={int(GLOBAL_CACHE.Inventory.GetGoldInStorage())}.")
        yield

    bot.States.AddCustomState(_buy_local, f"{name} Execute")


def add_merchant_rules_execute_state(
    bot,
    *,
    target_emails_factory: Callable[[], list[str]],
    request_id: str,
    include_protected: bool,
    instant_destroy: bool,
    auto_enable_widget: bool,
    widget_names: list[str],
    wait_step_ms: int,
    wait_timeout_ms: int,
    enable_wait_ms: int,
    wait_ms: int,
    name: str = "Merchant Rules Execute",
    log: LogFn | None = None,
) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, SharedCommandType
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

    log_fn = log or _noop_log

    def _execute():
        widget_handler = get_widget_handler()
        sender_email = str(Player.GetAccountEmail() or "").strip()
        if not sender_email:
            log_fn("merchant_rules_execute: sender account email is unavailable.")
            yield
            return
        target_emails = target_emails_factory()
        if auto_enable_widget:
            for widget_name in widget_names:
                widget_handler.enable_widget(widget_name)
            sent_enable_messages: list[tuple[str, int]] = []
            for account_email in target_emails:
                if account_email == sender_email:
                    continue
                for widget_name in widget_names:
                    message_index = GLOBAL_CACHE.ShMem.SendMessage(
                        sender_email,
                        account_email,
                        SharedCommandType.EnableWidget,
                        (0.0, 0.0, 0.0, 0.0),
                        (widget_name, "", "", ""),
                    )
                    sent_enable_messages.append((account_email, int(message_index)))
            yield from wait_for_outbound_messages(
                "merchant_rules_enable_widget",
                sent_enable_messages,
                SharedCommandType.EnableWidget,
                wait_step_ms=wait_step_ms,
                timeout_ms=min(wait_timeout_ms, 30_000),
                log=log_fn,
            )
            if enable_wait_ms > 0:
                yield from Routines.Yield.wait(enable_wait_ms)

        if not target_emails:
            log_fn("merchant_rules_execute: no target accounts selected.")
            yield
            return
        include_protected_flag = "1" if include_protected else "0"
        instant_destroy_flag = "1" if instant_destroy else "0"
        message_refs: list[tuple[str, int]] = []
        for account_email in target_emails:
            message_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                account_email,
                SharedCommandType.MerchantRules,
                (3.0, 0.0, 0.0, 0.0),
                (request_id, "Execute", include_protected_flag, instant_destroy_flag),
            )
            message_refs.append((account_email, int(message_index)))
        yield from wait_for_outbound_messages(
            "merchant_rules_execute",
            message_refs,
            SharedCommandType.MerchantRules,
            wait_step_ms=wait_step_ms,
            timeout_ms=wait_timeout_ms,
            log=log_fn,
        )
        if wait_ms > 0:
            yield from Routines.Yield.wait(wait_ms)
        log_fn(f"merchant_rules_execute: dispatched execute to {len(target_emails)} account(s).")
        yield

    bot.States.AddCustomState(_execute, str(name))
