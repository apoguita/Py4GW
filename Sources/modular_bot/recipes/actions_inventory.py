from __future__ import annotations

from time import monotonic
from typing import Callable

from .step_context import StepContext
from .step_selectors import resolve_agent_xy_from_step
from .step_utils import log_recipe, parse_step_bool, parse_step_int, wait_after_step

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

        id_kits_in_inv = int(GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit.value))
        sup_id_kits_in_inv = int(GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value))
        salvage_kits_in_inv = int(GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value))

        id_kits_to_buy = max(0, id_kits_target - (id_kits_in_inv + sup_id_kits_in_inv))
        salvage_kits_to_buy = max(0, salvage_kits_target - salvage_kits_in_inv)

        yield from Routines.Yield.Merchant.BuyIDKits(id_kits_to_buy)
        yield from Routines.Yield.Merchant.BuySalvageKits(salvage_kits_to_buy)

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
    from Py4GWCoreLib import ConsoleLog, Inventory

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
            lambda: ConsoleLog(
                f"Recipe:{ctx.recipe_name}",
                "restock_cons found no restock methods to execute.",
            ),
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
    max_sell_quantity_per_item_raw = parse_step_int(ctx.step.get("max_sell_quantity_per_item", 0), 0)
    max_sell_quantity_per_item = max_sell_quantity_per_item_raw if max_sell_quantity_per_item_raw > 0 else None
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

    def _sell_local():
        step_selector = dict(selector_step)
        _apply_default_npc_selector(step_selector, "materials")
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
        log_recipe(ctx, f"sell_materials: resolved trader at ({x}, {y}), executing merchant routine.")
        sell_metrics = yield from Routines.Yield.Merchant.SellMaterialsAtTrader(
            x,
            y,
            selected_models=selected_models,
            max_sell_quantity_per_item=max_sell_quantity_per_item,
        )
        log_recipe(ctx, f"sell_materials metrics: {sell_metrics}")

        if multibox:
            sender_email = Player.GetAccountEmail()
            account_emails = _iter_other_account_emails()
            extra_data = ("sell", _encode_material_model_filter(selected_models), str(max_sell_quantity_per_item or 0), "")
            sent_messages: list[tuple[str, int]] = []
            for account_email in account_emails:
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (float(x), float(y), 0.0, 0.0),
                    extra_data,
                )
                sent_messages.append((account_email, int(message_index)))
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
            max_deposit_items=max_deposit_items,
        )
        log_recipe(ctx, f"deposit_materials metrics: {deposit_metrics}")

        if multibox:
            sender_email = Player.GetAccountEmail()
            account_emails = _iter_other_account_emails()
            extra_data = ("deposit", _encode_material_model_filter(selected_models), str(max_deposit_items or 0), "")
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


HANDLERS: dict[str, Callable[[StepContext], None]] = {
    "restock_kits": handle_restock_kits,
    "restock_cons": handle_restock_cons,
    "sell_materials": handle_sell_materials,
    "deposit_materials": handle_deposit_materials,
    "buy_ectoplasm": handle_buy_ectoplasm,
}
