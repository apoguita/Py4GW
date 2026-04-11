from __future__ import annotations

from typing import Optional, Callable, Generator, Any

from ...Agent import Agent
from ...Player import Player
from ...GlobalCache import GLOBAL_CACHE
from ...Py4GWcorelib import ConsoleLog, Console, ActionQueueManager
from ...enums import SharedCommandType
from ..BehaviourTrees import BT
from .helpers import _run_bt_tree, wait
from .movement import Movement
from .player import Player as YieldPlayer


class Items:
    @staticmethod
    def _finish_active_pick_up_loot_message() -> bool:
        account_email = Player.GetAccountEmail()
        if not account_email:
            return False

        index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
        if index == -1 or message is None or message.Command != SharedCommandType.PickUpLoot:
            return False

        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(account_email, index)
        return True

    @staticmethod
    def GetItemNameByItemID(item_id):
        tree = BT.Items.GetItemNameByItemID(item_id)
        yield from _run_bt_tree(tree, throttle_ms=100)
        item_name = tree.blackboard.get("result", '')
        return item_name

    @staticmethod
    def _wait_for_salvage_materials_window(timeout_ms: int = 1200, poll_ms: int = 50, initial_wait_ms: int = 150):
        from ...UIManager import UIManager
        yield from wait(max(0, initial_wait_ms))

        parent_hash = 140452905
        yes_button_offsets = [6, 110, 6]
        waited_ms = 0

        while waited_ms < max(0, timeout_ms):
            salvage_materials_frame = UIManager.GetChildFrameID(parent_hash, yes_button_offsets)
            if salvage_materials_frame and UIManager.FrameExists(salvage_materials_frame):
                yield from wait(max(0, poll_ms))
                return True

            yield from wait(max(1, poll_ms))
            waited_ms += max(1, poll_ms)

        yield from wait(max(0, poll_ms))
        return False

    @staticmethod
    def _wait_for_empty_queue(queue_name: str, timeout_ms: Optional[int] = None, poll_ms: int = 50):
        from ...Py4GWcorelib import ActionQueueManager
        poll_ms = max(1, poll_ms)
        waited_ms = 0
        while not ActionQueueManager().IsEmpty(queue_name):
            if timeout_ms is not None and waited_ms >= max(0, timeout_ms):
                ConsoleLog(
                    "Yield.Items",
                    f"Timed out waiting for queue '{queue_name}' to empty.",
                    Console.MessageType.Warning
                )
                return False
            yield from wait(poll_ms)
            waited_ms += poll_ms
        return True

    @staticmethod
    def _salvage_item(item_id):
        from ...Inventory import Inventory

        salvage_kit = GLOBAL_CACHE.Inventory.GetFirstSalvageKit()
        if salvage_kit == 0:
            ConsoleLog("SalvageItems", "No salvage kits found.", Console.MessageType.Warning)
            return
        Inventory.SalvageItem(item_id, salvage_kit)

    @staticmethod
    def _identify_item(item_id):
        from ...Inventory import Inventory

        id_kit = GLOBAL_CACHE.Inventory.GetFirstIDKit()
        if id_kit == 0:
            ConsoleLog("IdentifyItems", "No ID kits found.", Console.MessageType.Warning)
            return
        Inventory.IdentifyItem(item_id, id_kit)

    @staticmethod
    def SalvageItems(item_array: list[int], log=False):
        from ...Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
        from ...Inventory import Inventory
        queue_wait_timeout_ms = 5000

        if len(item_array) == 0:
            ActionQueueManager().ResetQueue("SALVAGE")
            return

        for item_id in item_array:
            _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            is_purple = rarity == "Purple"
            is_gold = rarity == "Gold"
            ActionQueueManager().AddAction("SALVAGE", Items._salvage_item, item_id)
            queue_drained = yield from Items._wait_for_empty_queue("SALVAGE", timeout_ms=queue_wait_timeout_ms)
            if not queue_drained:
                ConsoleLog("SalvageItems", f"Timed out waiting for salvage queue after starting salvage (item_id={item_id}).", Console.MessageType.Warning)
                continue

            if (is_purple or is_gold):
                found_confirm_window = yield from Items._wait_for_salvage_materials_window()
                if not found_confirm_window:
                    ConsoleLog("SalvageItems", f"Timed out waiting for salvage confirmation window (item_id={item_id}).", Console.MessageType.Warning)
                    continue
                ActionQueueManager().AddAction("SALVAGE", Inventory.AcceptSalvageMaterialsWindow)
                queue_drained = yield from Items._wait_for_empty_queue("SALVAGE", timeout_ms=queue_wait_timeout_ms)
                if not queue_drained:
                    ConsoleLog("SalvageItems", f"Timed out waiting for salvage queue after confirmation (item_id={item_id}).", Console.MessageType.Warning)
                    continue

            yield from wait(100)

        if log and len(item_array) > 0:
            ConsoleLog("SalvageItems", f"Salvaged {len(item_array)} items.", Console.MessageType.Info)

    @staticmethod
    def IdentifyItems(item_array: list[int], log=False):
        from ...Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
        if len(item_array) == 0:
            ActionQueueManager().ResetQueue("IDENTIFY")
            return

        for item_id in item_array:
            ActionQueueManager().AddAction("IDENTIFY", Items._identify_item, item_id)

        while not ActionQueueManager().IsEmpty("IDENTIFY"):
            yield from wait(350)

        if log and len(item_array) > 0:
            ConsoleLog("IdentifyItems", f"Identified {len(item_array)} items.", Console.MessageType.Info)

    @staticmethod
    def DepositItems(item_array: list[int], log=False):
        from ...Py4GWcorelib import ActionQueueManager, ConsoleLog, Console

        if len(item_array) == 0:
            ActionQueueManager().ResetQueue("ACTION")
            return

        total_items, total_capacity = GLOBAL_CACHE.Inventory.GetStorageSpace()
        free_slots = total_capacity - total_items

        if free_slots <= 0:
            return

        for item_id in item_array:
            GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)

        while not ActionQueueManager().IsEmpty("ACTION"):
            yield from wait(350)

        if log and len(item_array) > 0:
            ConsoleLog("DepositItems", f"Deposited {len(item_array)} items.", Console.MessageType.Info)

    @staticmethod
    def DepositGold(gold_amount_to_leave_on_character: int, log=False):
        gold_amount_on_character = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
        gold_amount_on_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()

        max_allowed_gold = 1_000_000
        available_space = max_allowed_gold - gold_amount_on_storage

        if gold_amount_on_character > gold_amount_to_leave_on_character:
            gold_to_deposit = gold_amount_on_character - gold_amount_to_leave_on_character
            gold_to_deposit = min(gold_to_deposit, available_space)

            if gold_to_deposit > 0:
                GLOBAL_CACHE.Inventory.DepositGold(gold_to_deposit)
                yield from wait(350)
                if log:
                    ConsoleLog("DepositGold", f"Deposited {gold_to_deposit} gold.", Console.MessageType.Success)
                return True

            if log:
                ConsoleLog("DepositGold", "No gold deposited, storage full.", Console.MessageType.Warning)
            return False

        elif gold_amount_on_character < gold_amount_to_leave_on_character:
            gold_needed = gold_amount_to_leave_on_character - gold_amount_on_character
            gold_to_withdraw = min(gold_needed, gold_amount_on_storage)

            if gold_to_withdraw > 0:
                GLOBAL_CACHE.Inventory.WithdrawGold(gold_to_withdraw)
                yield from wait(350)
                if log:
                    ConsoleLog("DepositGold", f"Withdrew {gold_to_withdraw} gold.", Console.MessageType.Success)
                return True

            if log:
                ConsoleLog("DepositGold", "No gold withdrawn, storage empty.", Console.MessageType.Warning)
            return False

        if log:
            ConsoleLog("DepositGold", f"Gold already balanced at {gold_amount_to_leave_on_character}.", Console.MessageType.Info)
        return True

    @staticmethod
    def WithdrawGold(target_gold: int, deposit_all: bool = True, log: bool = False):
        gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

        if deposit_all and gold_on_char > target_gold:
            to_deposit = gold_on_char - target_gold
            gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
            available_space = 1_000_000 - gold_in_storage
            to_deposit = min(to_deposit, available_space)
            if to_deposit > 0:
                GLOBAL_CACHE.Inventory.DepositGold(to_deposit)
                yield from wait(350)
                if log:
                    ConsoleLog("WithdrawGold", f"Deposited {to_deposit} gold (excess).", Console.MessageType.Info)
                gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

        if gold_on_char < target_gold:
            to_withdraw = target_gold - gold_on_char
            gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
            to_withdraw = min(to_withdraw, gold_in_storage)
            if to_withdraw > 0:
                GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
                yield from wait(350)
                if log:
                    ConsoleLog("WithdrawGold", f"Withdrew {to_withdraw} gold.", Console.MessageType.Info)
            elif log:
                ConsoleLog("WithdrawGold", "Not enough gold in storage to reach target.", Console.MessageType.Warning)

    @staticmethod
    def LootItems(item_array:list[int], log=False, progress_callback: Optional[Callable[[float], None]] = None, pickup_timeout:int=5000):
        from ...AgentArray import AgentArray
        from ..Checks import Checks

        if len(item_array) == 0:
            Items._finish_active_pick_up_loot_message()
            return True

        yield from wait(1000)
        if not Checks.Map.MapValid():
            item_array.clear()
            ActionQueueManager().ResetAllQueues()
            Items._finish_active_pick_up_loot_message()
            return False

        total_items = len(item_array)
        while len(item_array) > 0:
            item_id = item_array.pop(0)
            if item_id == 0:
                continue

            free_slots_in_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
            if free_slots_in_inventory <= 0:
                item_array.clear()
                ActionQueueManager().ResetAllQueues()
                Items._finish_active_pick_up_loot_message()
                return False

            if not Checks.Map.MapValid():
                item_array.clear()
                ActionQueueManager().ResetAllQueues()
                Items._finish_active_pick_up_loot_message()
                return False

            if not Agent.IsValid(item_id):
                continue

            item_x, item_y = Agent.GetXY(item_id)
            item_reached = yield from Movement.FollowPath([(item_x, item_y)], timeout=pickup_timeout)
            if not item_reached:
                item_array.clear()
                ActionQueueManager().ResetAllQueues()
                Items._finish_active_pick_up_loot_message()
                return False

            if not Checks.Map.MapValid():
                item_array.clear()
                ActionQueueManager().ResetAllQueues()
                Items._finish_active_pick_up_loot_message()
                return False
            if Agent.IsValid(item_id):
                yield from YieldPlayer.InteractAgent(item_id)
                while True:
                    yield from wait(50)
                    live_items = AgentArray.GetItemArray()
                    if item_id not in live_items:
                        break

            if progress_callback and total_items > 0:
                progress_callback(1 - len(item_array) / total_items)

        Items._finish_active_pick_up_loot_message()
        return True

    @staticmethod
    def LootItemsWithMaxAttempts(
        item_array: list[int],
        log: bool = False,
        progress_callback: Optional[Callable[[float], None]] = None,
        pickup_timeout: int = 5000,
        max_attempts: int = 5,
        attempts_timeout_seconds: int = 3,
    ):
        from ...AgentArray import AgentArray
        from ..Checks import Checks

        if len(item_array) == 0:
            Items._finish_active_pick_up_loot_message()
            return []

        failed_items: list[int] = []
        total_items = len(item_array)

        while len(item_array) > 0:
            item_id = item_array.pop(0)
            if item_id == 0:
                continue

            free_slots_in_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
            if free_slots_in_inventory <= 0:
                ConsoleLog("LootItems", "No free slots in inventory, stopping loot.", Console.MessageType.Warning)
                ActionQueueManager().ResetAllQueues()
                Items._finish_active_pick_up_loot_message()
                return failed_items + item_array

            if not Checks.Map.MapValid():
                ActionQueueManager().ResetAllQueues()
                Items._finish_active_pick_up_loot_message()
                return failed_items + item_array

            if not Agent.IsValid(item_id):
                continue

            item_x, item_y = Agent.GetXY(item_id)
            item_reached = yield from Movement.FollowPath([(item_x, item_y)], timeout=pickup_timeout)
            if not item_reached:
                ConsoleLog("LootItems", f"Failed to reach item {item_id}, skipping.", Console.MessageType.Warning)
                failed_items.append(item_id)
                continue

            if Agent.IsValid(item_id):
                attempts = 0
                picked_up = False

                while attempts < max_attempts and not picked_up:
                    if Agent.IsValid(item_id):
                        yield from YieldPlayer.InteractAgent(item_id)

                    for _ in range(attempts_timeout_seconds * 10):
                        yield from wait(100)
                        live_items = AgentArray.GetItemArray()
                        if item_id not in live_items:
                            picked_up = True
                            break

                    if not picked_up:
                        attempts += 1

                if not picked_up:
                    ConsoleLog("Loot", f"Failed to pick up item {item_id} after {max_attempts} attempts.")
                    failed_items.append(item_id)

            if progress_callback and total_items > 0:
                progress_callback(1 - len(item_array) / total_items)

        if log:
            ConsoleLog(
                "LootItems",
                f"Looted {total_items - len(failed_items)} items. Failed: {len(failed_items)}",
                Console.MessageType.Info,
            )

        Items._finish_active_pick_up_loot_message()
        return failed_items

    @staticmethod
    def WithdrawItems(model_id:int, quantity:int) -> Generator[Any, Any, bool]:
        item_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
        if item_in_storage < quantity:
            return False

        items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, quantity)
        yield from wait(500)
        if not items_withdrawn:
            return False

        return True

    @staticmethod
    def WithdrawUpTo(model_id: int, max_quantity: int) -> Generator[Any, Any, None]:
        available = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
        to_withdraw = min(available, max_quantity)
        if to_withdraw > 0:
            GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, to_withdraw)
            yield from wait(500)

    @staticmethod
    def WithdrawFirstAvailable(model_ids: list, max_quantity: int) -> Generator[Any, Any, None]:
        for model_id in model_ids:
            available = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
            if available > 0:
                to_withdraw = min(available, max_quantity)
                GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, to_withdraw)
                yield from wait(500)
                return

    @staticmethod
    def DepositAllInventory() -> Generator[Any, Any, None]:
        item_ids = GLOBAL_CACHE.Inventory.GetAllInventoryItemIds()
        for item_id in item_ids:
            GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
            yield from wait(350)

    @staticmethod
    def RestockItems(model_id: int, desired_quantity: int) -> Generator[Any, Any, bool]:
        in_bags = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
        if in_bags >= desired_quantity:
            return True

        need = desired_quantity - in_bags
        in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)

        if need <= 0 or in_storage <= 0:
            return False

        ok = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, need)
        yield from wait(250)

        if not ok:
            fallback_amount = min(need, in_storage)
            if fallback_amount > 0:
                ok = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, fallback_amount)
                yield from wait(250)

        final_bags = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
        return final_bags >= desired_quantity

    @staticmethod
    def CraftItem(output_model_id: int, cost: int, trade_model_ids: list[int], quantity_list: list[int]) -> Generator[Any, Any, bool]:
        k = min(len(trade_model_ids), len(quantity_list))
        if k == 0:
            return False
        trade_model_ids = trade_model_ids[:k]
        quantity_list = quantity_list[:k]

        trade_item_ids: list[int] = []
        for m in trade_model_ids:
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(m)
            trade_item_ids.append(item_id or 0)

        if any(i == 0 for i in trade_item_ids):
            return False

        target_item_id = 0
        for offered_item_id in GLOBAL_CACHE.Trading.Merchant.GetOfferedItems():
            if GLOBAL_CACHE.Item.GetModelID(offered_item_id) == output_model_id:
                target_item_id = offered_item_id
                break
        if target_item_id == 0:
            return False

        GLOBAL_CACHE.Trading.Crafter.CraftItem(target_item_id, cost, trade_item_ids, quantity_list)
        yield from wait(500)
        return True

    @staticmethod
    def EquipItem(model_id: int) -> Generator[Any, Any, bool]:
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        if item_id:
            GLOBAL_CACHE.Inventory.EquipItem(item_id, Player.GetAgentID())
            yield from wait(750)
        else:
            return False
        return True

    @staticmethod
    def DestroyItem(model_id: int) -> Generator[Any, Any, bool]:
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        if item_id:
            GLOBAL_CACHE.Inventory.DestroyItem(item_id)
            yield from wait(600)
        else:
            return False
        return True

    @staticmethod
    def UseItem(model_id: int) -> Generator[Any, Any, bool]:
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        if item_id:
            GLOBAL_CACHE.Inventory.UseItem(item_id)
            yield from wait(600)
        else:
            return False
        return True

    @staticmethod
    def SpawnBonusItems():
        Player.SendChatCommand("bonus")
        yield from wait(250)
