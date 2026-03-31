from __future__ import annotations

from ...GlobalCache import GLOBAL_CACHE
from ...enums_src.Model_enums import ModelID
from .movement import Movement
from .agents import Agents
from .helpers import wait


class Merchant:
    @staticmethod
    def _get_trader_batch_size(trader_items: list[int] | None = None) -> int:
        offered_items = trader_items if trader_items is not None else list(GLOBAL_CACHE.Trading.Trader.GetOfferedItems())
        offered_models = {int(GLOBAL_CACHE.Item.GetModelID(item_id)) for item_id in offered_items}
        return 10 if int(ModelID.Wood_Plank.value) in offered_models else 1

    @staticmethod
    def _wait_for_trader_inventory(timeout_ms: int = 2500, step_ms: int = 5):
        trader_items = []
        wait_elapsed_ms = 0
        while wait_elapsed_ms < timeout_ms:
            trader_items = list(GLOBAL_CACHE.Trading.Trader.GetOfferedItems())
            if trader_items:
                break
            wait_elapsed_ms += step_ms
            yield from wait(step_ms)
        return trader_items

    @staticmethod
    def _wait_for_quote(request_fn, request_id: int, timeout_ms: int, step_ms: int):
        matched_quote = -1
        request_fn(request_id)
        wait_elapsed_ms = 0
        request_retry_elapsed_ms = 0
        while wait_elapsed_ms < timeout_ms:
            yield from wait(step_ms)
            wait_elapsed_ms += step_ms
            request_retry_elapsed_ms += step_ms

            quoted_item_id = int(GLOBAL_CACHE.Trading.Trader.GetQuotedItemID())
            quoted_value = int(GLOBAL_CACHE.Trading.Trader.GetQuotedValue())
            if quoted_value >= 0 and quoted_item_id == request_id:
                matched_quote = quoted_value
                break
            if request_retry_elapsed_ms >= 150:
                request_fn(request_id)
                request_retry_elapsed_ms = 0
        return matched_quote

    @staticmethod
    def _wait_for_transaction(timeout_ms: int, step_ms: int):
        wait_elapsed_ms = 0
        while wait_elapsed_ms < timeout_ms:
            yield from wait(step_ms)
            if GLOBAL_CACHE.Trading.IsTransactionComplete():
                return True
            wait_elapsed_ms += step_ms
        return False

    @staticmethod
    def _wait_for_stack_quantity_drop(
        item_id: int,
        previous_quantity: int,
        timeout_ms: int,
        step_ms: int,
    ):
        """
        Wait for a sold stack to decrease (or disappear from inventory).
        Material-trader transactions can report completion before inventory state refreshes.
        """
        wait_elapsed_ms = 0
        while wait_elapsed_ms < timeout_ms:
            yield from wait(step_ms)
            current_quantity = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
            if current_quantity < previous_quantity:
                return current_quantity
            wait_elapsed_ms += step_ms

        return int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))

    @staticmethod
    def _scan_material_item_ids(selected_models: set[int] | None = None, exact_quantity: int | None = None) -> list[int]:
        bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
        bag_item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)
        item_ids: list[int] = []
        for item_id in bag_item_array:
            if not GLOBAL_CACHE.Item.Type.IsMaterial(item_id):
                continue
            if GLOBAL_CACHE.Item.Type.IsRareMaterial(item_id):
                continue

            model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
            if selected_models is not None and model_id not in selected_models:
                continue
            if exact_quantity is not None and int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)) != exact_quantity:
                continue

            item_ids.append(int(item_id))
        return item_ids

    @staticmethod
    def _interact_with_trader_xy(x: float, y: float, inventory_timeout_ms: int = 2500, inventory_step_ms: int = 5):
        yield from Movement.FollowPath([(x, y)])
        yield from wait(100)
        yield from Agents.InteractWithAgentXY(x, y)
        yield from wait(500)
        return (
            yield from Merchant._wait_for_trader_inventory(
                timeout_ms=inventory_timeout_ms,
                step_ms=inventory_step_ms,
            )
        )

    @staticmethod
    def SellMaterialsAtTrader(
        x: float,
        y: float,
        selected_models: set[int] | None = None,
        *,
        max_sell_quantity_per_item: int | None = None,
        deposit_threshold: int = 80_000,
        gold_to_keep: int = 10_000,
        inventory_timeout_ms: int = 2500,
        inventory_step_ms: int = 5,
        quote_timeout_ms: int = 250,
        quote_step_ms: int = 5,
        transaction_timeout_ms: int = 250,
        transaction_step_ms: int = 5,
        sale_delay_min_ms: int = 20,
        sale_delay_max_ms: int = 50,
    ):
        from ...Inventory import Inventory
        import random
        metrics = {
            "trader_loaded": 0,
            "batch_size": 10,
            "candidate_items": 0,
            "items_considered": 0,
            "sales_completed": 0,
            "quote_failures": 0,
            "transaction_timeouts": 0,
            "no_progress_breaks": 0,
            "gold_deposit_triggered": 0,
        }

        trader_items = yield from Merchant._interact_with_trader_xy(
            x,
            y,
            inventory_timeout_ms=inventory_timeout_ms,
            inventory_step_ms=inventory_step_ms,
        )
        if not trader_items:
            return metrics
        metrics["trader_loaded"] = 1
        batch_size = Merchant._get_trader_batch_size(trader_items)
        metrics["batch_size"] = int(batch_size)

        trader_models = {int(GLOBAL_CACHE.Item.GetModelID(item_id)) for item_id in trader_items}
        material_item_ids = Merchant._scan_material_item_ids(selected_models)
        metrics["candidate_items"] = int(len(material_item_ids))
        for item_id in material_item_ids:
            model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
            if model_id not in trader_models:
                continue

            metrics["items_considered"] = int(metrics["items_considered"]) + 1
            stack_quantity = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
            quantity_cap = None if max_sell_quantity_per_item is None else max(0, int(max_sell_quantity_per_item))
            sold_quantity = 0
            while stack_quantity >= batch_size:
                if quantity_cap is not None and sold_quantity >= quantity_cap:
                    break
                if quantity_cap is not None and (sold_quantity + batch_size) > quantity_cap:
                    break
                quoted_value = yield from Merchant._wait_for_quote(
                    GLOBAL_CACHE.Trading.Trader.RequestSellQuote,
                    item_id,
                    timeout_ms=quote_timeout_ms,
                    step_ms=quote_step_ms,
                )
                if quoted_value <= 0:
                    metrics["quote_failures"] = int(metrics["quote_failures"]) + 1
                    break

                GLOBAL_CACHE.Trading.Trader.SellItem(item_id, quoted_value)
                updated_quantity = yield from Merchant._wait_for_stack_quantity_drop(
                    item_id,
                    stack_quantity,
                    timeout_ms=transaction_timeout_ms,
                    step_ms=transaction_step_ms,
                )
                if updated_quantity >= stack_quantity:
                    metrics["transaction_timeouts"] = int(metrics["transaction_timeouts"]) + 1
                    metrics["no_progress_breaks"] = int(metrics["no_progress_breaks"]) + 1
                    break
                sold_quantity += (stack_quantity - updated_quantity)
                metrics["sales_completed"] = int(metrics["sales_completed"]) + 1
                stack_quantity = updated_quantity
                low = max(0, int(sale_delay_min_ms))
                high = max(low, int(sale_delay_max_ms))
                if high > 0:
                    yield from wait(random.randint(low, high))

        gold_on_character = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
        if gold_on_character > deposit_threshold:
            from ..Yield import Yield
            metrics["gold_deposit_triggered"] = 1
            Inventory.OpenXunlaiWindow()
            yield from wait(1000)
            yield from Yield.Items.DepositGold(gold_to_keep, log=False)
        return metrics

    @staticmethod
    def DepositMaterials(
        selected_models: set[int] | None = None,
        *,
        exact_quantity: int = 250,
        max_deposit_items: int | None = None,
        open_wait_ms: int = 1000,
        deposit_wait_ms: int = 40,
        max_passes: int = 2,
    ):
        from ...Inventory import Inventory
        metrics = {
            "opened_storage": 0,
            "passes_run": 0,
            "candidates_seen": 0,
            "deposited_items": 0,
        }

        if not Inventory.IsStorageOpen():
            Inventory.OpenXunlaiWindow()
            yield from wait(open_wait_ms)
            metrics["opened_storage"] = 1

        pass_count = max(1, int(max_passes))
        max_items = None if max_deposit_items is None else max(0, int(max_deposit_items))
        deposited = 0
        for _ in range(pass_count):
            metrics["passes_run"] = int(metrics["passes_run"]) + 1
            material_item_ids = Merchant._scan_material_item_ids(
                selected_models,
                exact_quantity=exact_quantity,
            )
            metrics["candidates_seen"] = int(metrics["candidates_seen"]) + int(len(material_item_ids))
            if not material_item_ids:
                break
            for item_id in material_item_ids:
                if max_items is not None and deposited >= max_items:
                    return metrics
                GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                yield from wait(deposit_wait_ms)
                deposited += 1
                metrics["deposited_items"] = int(metrics["deposited_items"]) + 1
        return metrics

    @staticmethod
    def BuyEctoplasm(
        x: float,
        y: float,
        *,
        use_storage_gold: bool = True,
        start_threshold: int = 900_000,
        stop_threshold: int = 500_000,
        open_wait_ms: int = 500,
        withdraw_wait_ms: int = 350,
        inventory_timeout_ms: int = 2000,
        inventory_step_ms: int = 10,
        quote_timeout_ms: int = 750,
        quote_step_ms: int = 10,
        transaction_timeout_ms: int = 750,
        transaction_step_ms: int = 10,
        max_character_gold: int = 100_000,
        max_no_progress_cycles: int = 3,
        max_ecto_to_buy: int | None = None,
    ):
        from ...Inventory import Inventory
        metrics = {
            "trader_loaded_cycles": 0,
            "withdrawals": 0,
            "bought_items": 0,
            "quote_failures": 0,
            "transaction_timeouts": 0,
            "no_progress_breaks": 0,
            "inventory_load_failures": 0,
        }

        if stop_threshold < 0:
            stop_threshold = 0
        if start_threshold < stop_threshold:
            start_threshold = stop_threshold

        ecto_model_id = int(ModelID.Glob_Of_Ectoplasm.value)
        character_gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
        storage_gold = int(GLOBAL_CACHE.Inventory.GetGoldInStorage())

        if use_storage_gold:
            if storage_gold <= start_threshold:
                return metrics
        elif character_gold <= 0:
            return metrics

        max_to_buy = None if max_ecto_to_buy is None else max(0, int(max_ecto_to_buy))
        while True:
            if max_to_buy is not None and int(metrics["bought_items"]) >= max_to_buy:
                break
            character_gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
            storage_gold = int(GLOBAL_CACHE.Inventory.GetGoldInStorage())
            if use_storage_gold:
                if storage_gold <= stop_threshold:
                    break

                withdraw_amount = min(max_character_gold - character_gold, storage_gold - stop_threshold)
                if withdraw_amount > 0:
                    if not Inventory.IsStorageOpen():
                        Inventory.OpenXunlaiWindow()
                        yield from wait(open_wait_ms)
                    GLOBAL_CACHE.Inventory.WithdrawGold(int(withdraw_amount))
                    yield from wait(withdraw_wait_ms)
                    metrics["withdrawals"] = int(metrics["withdrawals"]) + 1
            elif character_gold <= 0:
                break

            trader_items = yield from Merchant._interact_with_trader_xy(
                x,
                y,
                inventory_timeout_ms=inventory_timeout_ms,
                inventory_step_ms=inventory_step_ms,
            )
            if not trader_items:
                metrics["inventory_load_failures"] = int(metrics["inventory_load_failures"]) + 1
                break
            metrics["trader_loaded_cycles"] = int(metrics["trader_loaded_cycles"]) + 1

            trader_item_id = 0
            for candidate in trader_items:
                if int(GLOBAL_CACHE.Item.GetModelID(candidate)) == ecto_model_id:
                    trader_item_id = int(candidate)
                    break
            if trader_item_id <= 0:
                break

            batch_size = Merchant._get_trader_batch_size(trader_items)
            no_progress_cycles = 0
            while int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter()) > 0:
                if max_to_buy is not None and int(metrics["bought_items"]) >= max_to_buy:
                    return metrics
                gold_before = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
                quoted_value = yield from Merchant._wait_for_quote(
                    GLOBAL_CACHE.Trading.Trader.RequestQuote,
                    trader_item_id,
                    timeout_ms=quote_timeout_ms,
                    step_ms=quote_step_ms,
                )
                if quoted_value <= 0 or gold_before < quoted_value:
                    if quoted_value <= 0:
                        metrics["quote_failures"] = int(metrics["quote_failures"]) + 1
                    break

                GLOBAL_CACHE.Trading.Trader.BuyItem(trader_item_id, quoted_value)
                completed = yield from Merchant._wait_for_transaction(
                    timeout_ms=transaction_timeout_ms,
                    step_ms=transaction_step_ms,
                )
                if not completed:
                    metrics["transaction_timeouts"] = int(metrics["transaction_timeouts"]) + 1
                    break

                gold_after = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter())
                if gold_after >= gold_before:
                    no_progress_cycles += 1
                    if no_progress_cycles >= max_no_progress_cycles:
                        metrics["no_progress_breaks"] = int(metrics["no_progress_breaks"]) + 1
                        break
                else:
                    no_progress_cycles = 0
                    metrics["bought_items"] = int(metrics["bought_items"]) + int(batch_size)

            if not use_storage_gold:
                break
        return metrics

    @staticmethod
    def SellItems(item_array: list[int], log=False):
        from ...Py4GWcorelib import ActionQueueManager, ConsoleLog, Console

        if len(item_array) == 0:
            ActionQueueManager().ResetQueue("MERCHANT")
            return

        for item_id in item_array:
            quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
            value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
            cost = quantity * value
            GLOBAL_CACHE.Trading.Merchant.SellItem(item_id, cost)

        while not ActionQueueManager().IsEmpty("MERCHANT"):
            yield from wait(50)

        if log:
            ConsoleLog("SellItems", f"Sold {len(item_array)} items.", Console.MessageType.Info)

    @staticmethod
    def BuyIDKits(kits_to_buy: int, log=False):
        from ...Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
        from ...ItemArray import ItemArray

        if kits_to_buy <= 0:
            ActionQueueManager().ResetQueue("MERCHANT")
            return

        merchant_item_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
        merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: GLOBAL_CACHE.Item.GetModelID(item_id) == 5899)

        if len(merchant_item_list) == 0:
            ActionQueueManager().ResetQueue("MERCHANT")
            return

        for i in range(kits_to_buy):
            item_id = merchant_item_list[0]
            value = GLOBAL_CACHE.Item.Properties.GetValue(item_id) * 2
            GLOBAL_CACHE.Trading.Merchant.BuyItem(item_id, value)

        while not ActionQueueManager().IsEmpty("MERCHANT"):
            yield from wait(50)

        if log:
            ConsoleLog("BuyIDKits", f"Bought {kits_to_buy} ID Kits.", Console.MessageType.Info)

    @staticmethod
    def BuySalvageKits(kits_to_buy: int, log=False):
        from ...ItemArray import ItemArray
        from ...Py4GWcorelib import ActionQueueManager, ConsoleLog, Console

        if kits_to_buy <= 0:
            ActionQueueManager().ResetQueue("MERCHANT")
            return

        merchant_item_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
        merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: GLOBAL_CACHE.Item.GetModelID(item_id) == 2992)

        if len(merchant_item_list) == 0:
            ActionQueueManager().ResetQueue("MERCHANT")
            return

        for i in range(kits_to_buy):
            item_id = merchant_item_list[0]
            value = GLOBAL_CACHE.Item.Properties.GetValue(item_id) * 2
            GLOBAL_CACHE.Trading.Merchant.BuyItem(item_id, value)

        while not ActionQueueManager().IsEmpty("MERCHANT"):
            yield from wait(50)

        if log:
            ConsoleLog("BuySalvageKits", f"Bought {kits_to_buy} Salvage Kits.", Console.MessageType.Info)

    @staticmethod
    def BuyMaterial(model_id: int):
        from ...Py4GWcorelib import ConsoleLog, Console
        MODULE_NAME = "Inventory + Buy Material"

        def _is_material_trader():
            merchant_models = [
                GLOBAL_CACHE.Item.GetModelID(item_id)
                for item_id in GLOBAL_CACHE.Trading.Trader.GetOfferedItems()
            ]
            return ModelID.Wood_Plank.value in merchant_models

        def _get_minimum_quantity():
            return 10 if _is_material_trader() else 1

        required_quantity = _get_minimum_quantity()
        merchant_item_list = GLOBAL_CACHE.Trading.Trader.GetOfferedItems()

        item_id = None
        for candidate in merchant_item_list:
            if GLOBAL_CACHE.Item.GetModelID(candidate) == model_id:
                item_id = candidate
                break

        if item_id is None:
            ConsoleLog(MODULE_NAME, f"Model {model_id} not sold here.", Console.MessageType.Warning)
            return False

        GLOBAL_CACHE.Trading.Trader.RequestQuote(item_id)

        while True:
            yield from wait(50)
            cost = GLOBAL_CACHE.Trading.Trader.GetQuotedValue()
            if cost >= 0:
                break

        if cost == 0:
            ConsoleLog(MODULE_NAME, f"Item {item_id} has no price.", Console.MessageType.Warning)
            return False

        GLOBAL_CACHE.Trading.Trader.BuyItem(item_id, cost)

        while True:
            yield from wait(50)
            if GLOBAL_CACHE.Trading.IsTransactionComplete():
                break

        ConsoleLog(
            MODULE_NAME,
            f"Bought {required_quantity} units of model {model_id} for {cost} gold.",
            Console.MessageType.Success
        )
        return True

    @staticmethod
    def SellMaterial(model_id: int):
        from ...Py4GWcorelib import ConsoleLog, Console
        MODULE_NAME = "Inventory + Sell Material"

        def _is_material_trader():
            merchant_models = [
                GLOBAL_CACHE.Item.GetModelID(item_id)
                for item_id in GLOBAL_CACHE.Trading.Trader.GetOfferedItems()
            ]
            return ModelID.Wood_Plank.value in merchant_models

        def _get_minimum_quantity():
            return 10 if _is_material_trader() else 1

        required_quantity = _get_minimum_quantity()
        merchant_item_list = GLOBAL_CACHE.Trading.Trader.GetOfferedItems()

        item_id = None
        for candidate in merchant_item_list:
            if GLOBAL_CACHE.Item.GetModelID(candidate) == model_id:
                item_id = candidate
                break

        if item_id is None:
            ConsoleLog(MODULE_NAME, f"Model {model_id} not sold here.", Console.MessageType.Warning)
            return False

        GLOBAL_CACHE.Trading.Trader.RequestSellQuote(item_id)
        ConsoleLog(MODULE_NAME, f"Requested Sell Quote for item {item_id}.", Console.MessageType.Warning)

        while True:
            yield from wait(50)
            quoted_id = GLOBAL_CACHE.Trading.Trader.GetQuotedItemID()
            cost = GLOBAL_CACHE.Trading.Trader.GetQuotedValue()
            ConsoleLog(MODULE_NAME, f"Attempted to request sell quote for item {quoted_id}.", Console.MessageType.Warning)
            ConsoleLog(MODULE_NAME, f"Received sell quote for item {item_id} at cost: {cost}", Console.MessageType.Warning)
            if cost >= 0:
                break

        if cost == 0:
            ConsoleLog(MODULE_NAME, f"Item {item_id} has no price.", Console.MessageType.Warning)
            return False

        GLOBAL_CACHE.Trading.Trader.SellItem(item_id, cost)

        while True:
            yield from wait(50)
            if GLOBAL_CACHE.Trading.IsTransactionComplete():
                break

        ConsoleLog(
            MODULE_NAME,
            f"Bought {required_quantity} units of model {model_id} for {cost} gold.",
            Console.MessageType.Success
        )
        return True
