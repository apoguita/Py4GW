from __future__ import annotations

from typing import Callable

from .step_context import StepContext
from .step_selectors import resolve_agent_xy_from_step
from .step_utils import log_recipe, parse_step_bool, parse_step_int, wait_after_step


def _command_type_routine_in_message_is_active(account_email: str, shared_command_type: int) -> bool:
    from Py4GWCoreLib import GLOBAL_CACHE

    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
    if index == -1 or message is None:
        return False
    if message.Command != shared_command_type:
        return False
    return True


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


def handle_restock_kits(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, ModelID, Player, Routines, SharedCommandType

    selector_step = dict(ctx.step)
    if (
        "x" not in selector_step
        and "y" not in selector_step
        and "npc" not in selector_step
        and "target" not in selector_step
        and "name_contains" not in selector_step
        and "agent_name" not in selector_step
        and "model_id" not in selector_step
        and "nearest" not in selector_step
    ):
        selector_step["npc"] = "MERCHANT"

    name = ctx.step.get("name", "Restock Kits")
    multibox_raw = ctx.step.get("multibox", False)

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
        coords = resolve_agent_xy_from_step(
            selector_step,
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
            for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                account_email = str(getattr(account, "AccountEmail", "") or "")
                if not account_email or account_email == sender_email:
                    continue
                GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantItems,
                    (x, y, float(id_kits_target), float(salvage_kits_target)),
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
    from Py4GWCoreLib import GLOBAL_CACHE, Inventory, Player, Routines, SharedCommandType
    from Py4GWCoreLib.enums_src.Item_enums import MaterialMap
    from Py4GWCoreLib.enums_src.Model_enums import ModelID

    selector_step = dict(ctx.step)
    if (
        "x" not in selector_step
        and "y" not in selector_step
        and "npc" not in selector_step
        and "target" not in selector_step
        and "name_contains" not in selector_step
        and "agent_name" not in selector_step
        and "model_id" not in selector_step
        and "nearest" not in selector_step
    ):
        selector_step["npc"] = "CRAFTING_MATERIAL_TRADER"

    name = ctx.step.get("name", "Sell Materials")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
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
        post_interact_wait_ms = 500
        trader_inventory_wait_step_ms = 5
        trader_inventory_wait_timeout_ms = 2500
        quote_wait_step_ms = 5
        quote_wait_timeout_ms = 500
        transaction_wait_step_ms = 5
        transaction_wait_timeout_ms = 500
        full_sale_timeout_ms = 250
        deposit_threshold = 80_000
        gold_to_keep = 10_000

        log_recipe(ctx, f"sell_materials start: selector={selector_step!r}")
        coords = resolve_agent_xy_from_step(
            selector_step,
            recipe_name=ctx.recipe_name,
            step_idx=ctx.step_idx,
            agent_kind="npc",
        )
        if coords is None:
            log_recipe(ctx, "sell_materials: failed to resolve Crafting Material Trader coordinates.")
            yield
            return

        x, y = coords
        log_recipe(ctx, f"sell_materials: resolved trader at ({x}, {y}), moving to interact.")
        yield from ctx.bot.Move._coro_xy_and_interact_npc(x, y, name)
        yield from ctx.bot.Wait._coro_for_time(post_interact_wait_ms)
        log_recipe(ctx, "sell_materials: movement/interact coroutine finished, waiting for trader inventory.")

        trader_items = []
        wait_elapsed_ms = 0
        while wait_elapsed_ms < trader_inventory_wait_timeout_ms:
            trader_items = list(GLOBAL_CACHE.Trading.Trader.GetOfferedItems())
            if trader_items:
                break
            wait_elapsed_ms += trader_inventory_wait_step_ms
            yield from Routines.Yield.wait(trader_inventory_wait_step_ms)

        trader_models = [int(GLOBAL_CACHE.Item.GetModelID(item_id)) for item_id in trader_items]
        log_recipe(
            ctx,
            "sell_materials: trader offered item models="
            + (", ".join(str(model_id) for model_id in trader_models) if trader_models else "<none>"),
        )
        if not trader_items:
            log_recipe(ctx, "sell_materials: trader inventory did not populate; aborting sell step.")
            yield
            return

        log_recipe(ctx, "sell_materials: trader inventory ready, scanning inventory.")

        bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
        bag_item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)
        log_recipe(ctx, f"sell_materials: inventory scan found {len(bag_item_array)} items in bags 1-4.")
        material_item_ids_to_sell: list[int] = []
        for item_id in bag_item_array:
            if not GLOBAL_CACHE.Item.Type.IsMaterial(item_id):
                continue
            if GLOBAL_CACHE.Item.Type.IsRareMaterial(item_id):
                continue

            model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
            if selected_models is not None and model_id not in selected_models:
                continue

            material_item_ids_to_sell.append(int(item_id))

        log_recipe(
            ctx,
            "sell_materials: candidate material item ids="
            + (", ".join(str(item_id) for item_id in material_item_ids_to_sell) if material_item_ids_to_sell else "<none>"),
        )
        for item_id in material_item_ids_to_sell:
            model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
            total_quantity = int(GLOBAL_CACHE.Inventory.GetModelCount(model_id))
            sales_remaining = total_quantity // 10
            log_recipe(
                ctx,
                f"sell_materials: item_id={item_id} model_id={model_id} total_quantity={total_quantity} sales_remaining={sales_remaining}.",
            )
            if model_id not in trader_models:
                log_recipe(ctx, f"sell_materials: model_id={model_id} not present in trader inventory; skipping.")
                continue
            while sales_remaining > 0:
                sale_elapsed_ms = 0
                quoted_value = -1
                GLOBAL_CACHE.Trading.Trader.RequestSellQuote(item_id)
                wait_elapsed_ms = 0
                while wait_elapsed_ms < quote_wait_timeout_ms:
                    yield from Routines.Yield.wait(quote_wait_step_ms)
                    quoted_value = int(GLOBAL_CACHE.Trading.Trader.GetQuotedValue())
                    if quoted_value >= 0:
                        break
                    wait_elapsed_ms += quote_wait_step_ms
                    sale_elapsed_ms += quote_wait_step_ms
                    if sale_elapsed_ms >= full_sale_timeout_ms:
                        break

                log_recipe(
                    ctx,
                    f"sell_materials: item_id={item_id} model_id={model_id} quote={quoted_value} remaining before sale={sales_remaining}.",
                )
                if quoted_value <= 0:
                    log_recipe(ctx, f"sell_materials: quote failed for item_id={item_id}; stopping this stack.")
                    break

                GLOBAL_CACHE.Trading.Trader.SellItem(item_id, quoted_value)
                sale_completed = False
                wait_elapsed_ms = 0
                while wait_elapsed_ms < transaction_wait_timeout_ms:
                    yield from Routines.Yield.wait(transaction_wait_step_ms)
                    if GLOBAL_CACHE.Trading.IsTransactionComplete():
                        sale_completed = True
                        break
                    wait_elapsed_ms += transaction_wait_step_ms
                    sale_elapsed_ms += transaction_wait_step_ms
                    if sale_elapsed_ms >= full_sale_timeout_ms:
                        break
                if not sale_completed:
                    log_recipe(
                        ctx,
                        f"sell_materials: timed out waiting for sale completion for item_id={item_id}; stopping this stack.",
                    )
                    break
                sales_remaining -= 1
            if total_quantity > 0 and total_quantity < 10:
                log_recipe(ctx, f"sell_materials: model_id={model_id} skipped, quantity below 10.")

        gold_on_character = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
        if gold_on_character > deposit_threshold:
            log_recipe(
                ctx,
                f"sell_materials: character gold {gold_on_character} exceeds threshold {deposit_threshold}; attempting deposit to {gold_to_keep}.",
            )
            Inventory.OpenXunlaiWindow()
            yield from Routines.Yield.wait(1000)
            yield from Routines.Yield.Items.DepositGold(gold_to_keep, log=False)
            log_recipe(ctx, f"sell_materials: gold after deposit attempt={int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())}.")

        if multibox:
            sender_email = Player.GetAccountEmail()
            account_emails = _iter_other_account_emails()
            extra_data = ("sell", _encode_material_model_filter(selected_models), "", "")
            for account_email in account_emails:
                GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (float(x), float(y), 0.0, 0.0),
                    extra_data,
                )
            for account_email in account_emails:
                while _command_type_routine_in_message_is_active(account_email, SharedCommandType.MerchantMaterials):
                    yield from Routines.Yield.wait(100)

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
        open_wait_ms = 1000
        deposit_wait_ms = 75

        if not Inventory.IsStorageOpen():
            log_recipe(ctx, "deposit_materials: opening Xunlai window.")
            Inventory.OpenXunlaiWindow()
            yield from Routines.Yield.wait(open_wait_ms)

        bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
        bag_item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)

        material_item_ids_to_deposit: list[int] = []
        for item_id in bag_item_array:
            if not GLOBAL_CACHE.Item.Type.IsMaterial(item_id):
                continue
            if GLOBAL_CACHE.Item.Type.IsRareMaterial(item_id):
                continue

            model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
            if selected_models is not None and model_id not in selected_models:
                continue

            quantity = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
            if quantity != 250:
                continue

            material_item_ids_to_deposit.append(int(item_id))

        log_recipe(
            ctx,
            "deposit_materials: full-stack item ids="
            + (", ".join(str(item_id) for item_id in material_item_ids_to_deposit) if material_item_ids_to_deposit else "<none>"),
        )

        for item_id in material_item_ids_to_deposit:
            GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
            yield from Routines.Yield.wait(deposit_wait_ms)

        if multibox:
            sender_email = Player.GetAccountEmail()
            account_emails = _iter_other_account_emails()
            extra_data = ("deposit", _encode_material_model_filter(selected_models), "", "")
            for account_email in account_emails:
                GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.MerchantMaterials,
                    (0.0, 0.0, 0.0, 0.0),
                    extra_data,
                )
            for account_email in account_emails:
                while _command_type_routine_in_message_is_active(account_email, SharedCommandType.MerchantMaterials):
                    yield from Routines.Yield.wait(100)

        log_recipe(ctx, "deposit_materials: completed.")
        yield

    ctx.bot.States.AddCustomState(_deposit_local, f"{name} Execute")
    wait_after_step(ctx.bot, ctx.step)


def handle_buy_ectoplasm(ctx: StepContext) -> None:
    from Py4GWCoreLib import GLOBAL_CACHE, Inventory, Player, Routines, SharedCommandType
    from Py4GWCoreLib.enums_src.Model_enums import ModelID

    selector_step = dict(ctx.step)
    if (
        "x" not in selector_step
        and "y" not in selector_step
        and "npc" not in selector_step
        and "target" not in selector_step
        and "name_contains" not in selector_step
        and "agent_name" not in selector_step
        and "model_id" not in selector_step
        and "nearest" not in selector_step
    ):
        selector_step["npc"] = "RARE_MATERIAL_TRADER"

    name = ctx.step.get("name", "Buy Ectoplasm")
    multibox = parse_step_bool(ctx.step.get("multibox", False), False)
    use_storage_gold = str(ctx.step.get("use_storage_gold", True)).strip().lower() in ("1", "true", "yes", "on")
    start_storage_gold_threshold = parse_step_int(ctx.step.get("start_storage_gold_threshold", 900_000), 900_000)
    stop_storage_gold_threshold = parse_step_int(ctx.step.get("stop_storage_gold_threshold", 500_000), 500_000)
    if stop_storage_gold_threshold < 0:
        stop_storage_gold_threshold = 0
    if start_storage_gold_threshold < stop_storage_gold_threshold:
        start_storage_gold_threshold = stop_storage_gold_threshold

    def _buy_local():
        ecto_model_id = int(ModelID.Glob_Of_Ectoplasm.value)
        open_wait_ms = 500
        withdraw_wait_ms = 350
        post_interact_wait_ms = 500
        trader_inventory_wait_step_ms = 10
        trader_inventory_wait_timeout_ms = 2000
        quote_wait_step_ms = 10
        quote_wait_timeout_ms = 750
        transaction_wait_step_ms = 10
        transaction_wait_timeout_ms = 750
        max_character_gold = 100_000

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

        coords = resolve_agent_xy_from_step(
            selector_step,
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

        while True:
            character_gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
            storage_gold = int(GLOBAL_CACHE.Inventory.GetGoldInStorage())
            if use_storage_gold:
                if storage_gold <= stop_storage_gold_threshold:
                    break

                withdraw_amount = min(max_character_gold - character_gold, storage_gold - stop_storage_gold_threshold)
                if withdraw_amount > 0:
                    if not Inventory.IsStorageOpen():
                        Inventory.OpenXunlaiWindow()
                        yield from Routines.Yield.wait(open_wait_ms)
                    GLOBAL_CACHE.Inventory.WithdrawGold(int(withdraw_amount))
                    yield from Routines.Yield.wait(withdraw_wait_ms)
                    log_recipe(
                        ctx,
                        f"buy_ectoplasm: withdrew {int(withdraw_amount)} gold, char_gold={int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())}, storage_gold={int(GLOBAL_CACHE.Inventory.GetGoldInStorage())}.",
                    )
            elif character_gold <= 0:
                break

            yield from ctx.bot.Move._coro_xy_and_interact_npc(x, y, name)
            yield from ctx.bot.Wait._coro_for_time(post_interact_wait_ms)

            trader_items = []
            wait_elapsed_ms = 0
            while wait_elapsed_ms < trader_inventory_wait_timeout_ms:
                trader_items = list(GLOBAL_CACHE.Trading.Trader.GetOfferedItems())
                if trader_items:
                    break
                wait_elapsed_ms += trader_inventory_wait_step_ms
                yield from Routines.Yield.wait(trader_inventory_wait_step_ms)

            if not trader_items:
                log_recipe(ctx, "buy_ectoplasm: trader inventory did not populate; aborting.")
                break

            trader_item_id = 0
            for candidate in trader_items:
                if int(GLOBAL_CACHE.Item.GetModelID(candidate)) == ecto_model_id:
                    trader_item_id = int(candidate)
                    break

            if trader_item_id <= 0:
                log_recipe(ctx, "buy_ectoplasm: ectoplasm is not present in trader inventory; aborting.")
                break

            while int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter()) > 0:
                quoted_value = -1
                GLOBAL_CACHE.Trading.Trader.RequestQuote(trader_item_id)
                wait_elapsed_ms = 0
                while wait_elapsed_ms < quote_wait_timeout_ms:
                    yield from Routines.Yield.wait(quote_wait_step_ms)
                    quoted_value = int(GLOBAL_CACHE.Trading.Trader.GetQuotedValue())
                    if quoted_value >= 0:
                        break
                    wait_elapsed_ms += quote_wait_step_ms

                character_gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
                log_recipe(
                    ctx,
                    f"buy_ectoplasm: quote={quoted_value}, char_gold={character_gold}, storage_gold={int(GLOBAL_CACHE.Inventory.GetGoldInStorage())}.",
                )
                if quoted_value <= 0 or character_gold < quoted_value:
                    break

                GLOBAL_CACHE.Trading.Trader.BuyItem(trader_item_id, quoted_value)
                wait_elapsed_ms = 0
                while wait_elapsed_ms < transaction_wait_timeout_ms:
                    yield from Routines.Yield.wait(transaction_wait_step_ms)
                    if GLOBAL_CACHE.Trading.IsTransactionComplete():
                        break
                    wait_elapsed_ms += transaction_wait_step_ms

            log_recipe(
                ctx,
                f"buy_ectoplasm: cycle complete, char_gold={int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())}, storage_gold={int(GLOBAL_CACHE.Inventory.GetGoldInStorage())}.",
            )

            if not use_storage_gold:
                break

        if multibox:
            sender_email = Player.GetAccountEmail()
            account_emails = _iter_other_account_emails()
            extra_data = ("buy_ectoplasm", "1" if use_storage_gold else "0", "", "")
            for account_email in account_emails:
                GLOBAL_CACHE.ShMem.SendMessage(
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
            for account_email in account_emails:
                while _command_type_routine_in_message_is_active(account_email, SharedCommandType.MerchantMaterials):
                    yield from Routines.Yield.wait(100)

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
