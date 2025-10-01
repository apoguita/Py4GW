import Py4GW
import PyItem

from typing import Dict

from Py4GWCoreLib import Inventory, UIManager
from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Item
from Py4GWCoreLib import ItemArray
from Py4GWCoreLib import Bags
from Py4GWCoreLib import Trading
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import GLOBAL_CACHE



#region IdentifyCheckedItems         
def IdentifyCheckedItems(id_checkboxes: Dict[int, bool]):
    MODULE_NAME = "Inventory + Identify Items"
    identified_items = 0
    for item_id, checked in list(id_checkboxes.items()):
        if checked:
            first_id_kit = Inventory.GetFirstIDKit()
            if first_id_kit == 0:
                Py4GW.Console.Log(MODULE_NAME, "No ID Kit found in inventory.", Py4GW.Console.MessageType.Warning)
                return
            
            item_instance = PyItem.PyItem(item_id)
            if item_instance.is_identified:
                id_checkboxes[item_id] = False
                continue
            
            ActionQueueManager().AddAction("ACTION", Inventory.IdentifyItem,item_id, first_id_kit)
            identified_items += 1
            while True:
                yield from Routines.Yield.wait(50)
                item_instance.GetContext()
                if item_instance.is_identified:
                    break
            id_checkboxes[item_id] = False
        yield from Routines.Yield.wait(50)
        
    ConsoleLog(MODULE_NAME, f"Identified {identified_items} items.", Py4GW.Console.MessageType.Info)


def get_first_full_material_stack():
    bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = ItemArray.GetItemArray(bags_to_check)

    # Filter items that are materials
    materials = ItemArray.Filter.ByCondition(
        item_array,
        lambda item_id: Item.Type.IsMaterial(item_id)
    )

    # Further filter for materials with quantity == 250
    full_stack_materials = ItemArray.Filter.ByCondition(
        materials,
        lambda item_id: Item.Properties.GetQuantity(item_id) == 250
    )

    if not full_stack_materials:
        return 0  # No full stack material found

    return full_stack_materials[0]  # First one found

def count_stacks_of_model(model_id: int) -> int:
    bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = ItemArray.GetItemArray(bags_to_check)

    # Filter items by the given model_id
    matching_items = ItemArray.Filter.ByCondition(
        item_array,
        lambda item_id: Item.GetModelID(item_id) == model_id
    )

    # Return the number of stacks found (full or partial)
    return len(matching_items)


#region SalvageCheckedItems         
def SalvageCheckedItems(salvage_checkboxes: Dict[int, bool], keep_salvage_kits: int = 0, deposit_materials: bool = False):
    MODULE_NAME = "Inventory + Salvage Items"
    salvaged_items = 0
    items_to_salvage = list(salvage_checkboxes.items())

    for item_id, checked in items_to_salvage:
        while checked:
            first_salv_kit = Inventory.GetFirstSalvageKit(use_lesser=True)
            if first_salv_kit == 0:
                Py4GW.Console.Log(MODULE_NAME, "No Salvage Kit found in inventory.", Py4GW.Console.MessageType.Warning)
                return

            quantity = Item.Properties.GetQuantity(item_id)
            if quantity == 0:
                salvage_checkboxes[item_id] = False
                break

            is_purple = Item.Rarity.IsPurple(item_id)
            is_gold = Item.Rarity.IsGold(item_id)
            require_materials_confirmation = is_purple or is_gold
            wait_for_consumption = quantity == 1

            ActionQueueManager().AddAction("ACTION", Inventory.SalvageItem, item_id, first_salv_kit)

            if require_materials_confirmation:
                yield from Routines.Yield.Items._wait_for_salvage_materials_window()
                ActionQueueManager().AddAction("ACTION", Inventory.AcceptSalvageMaterialsWindow)
                yield from Routines.Yield.wait(50)

            if wait_for_consumption:
                while True:
                    bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
                    item_array = ItemArray.GetItemArray(bag_list)
                    if item_id not in item_array:
                        salvage_checkboxes[item_id] = False
                        salvaged_items += 1
                        break
                    yield from Routines.Yield.wait(50)
            else:
                item_instance = PyItem.PyItem(item_id)
                while True:
                    yield from Routines.Yield.wait(50)
                    item_instance.GetContext()
                    if item_instance.quantity < quantity:
                        salvaged_items += 1
                        break
                    
            #deposit Full Material Stacks
            if deposit_materials:
                first_stack = get_first_full_material_stack()
                if first_stack:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(first_stack)
                    yield from Routines.Yield.wait(75)


            if keep_salvage_kits > 0:
                MERCHANT_FRAME = 3613855137
                merchant_frame_id = UIManager.GetFrameIDByHash(MERCHANT_FRAME)
                merchant_frame_exists = UIManager.FrameExists(merchant_frame_id)
                if not merchant_frame_exists:
                    break
                salvage_kit_model = ModelID.Salvage_Kit.value
                if count_stacks_of_model(salvage_kit_model) < keep_salvage_kits:
                    offered_items = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
                    for item in offered_items:
                        item_model = GLOBAL_CACHE.Item.GetModelID(item)
                        if item_model == salvage_kit_model:
                            GLOBAL_CACHE.Trading.Merchant.BuyItem(item,100)
                            yield from Routines.Yield.wait(75)
                            break

            yield from Routines.Yield.wait(75)
            # Refresh status for the next iteration
            checked = salvage_checkboxes.get(item_id, False)

    ConsoleLog(MODULE_NAME, f"Salvaged {salvaged_items} items.", Py4GW.Console.MessageType.Info)
    
#region MerchantCheckedItems
    
def MerchantCheckedItems(merchant_checkboxes: Dict[int, bool]):
    MODULE_NAME = "Inventory + Merchant Sell Items"
    def _is_merchant():
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        return ModelID.Salvage_Kit.value in merchant_item_models

    def _is_material_trader():
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        return ModelID.Wood_Plank.value in merchant_item_models

    def _get_merchant_minimum_quantity() -> int:
        return 10 if _is_material_trader() else 1

    if _is_merchant():
        ConsoleLog(MODULE_NAME, "Selling to regular merchants is not yet supported.", Py4GW.Console.MessageType.Warning)
        return

    if not merchant_checkboxes:
        ConsoleLog(MODULE_NAME, "No items selected for selling.", Py4GW.Console.MessageType.Warning)
        return

    required_quantity = _get_merchant_minimum_quantity()
    bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
    sold_items = 0
    ammount_sold = 0

    for item_id, checked in list(merchant_checkboxes.items()):
        if not checked:
            continue

        while True:
            item_array = ItemArray.GetItemArray(bag_list)
            if item_id not in item_array:
                #ConsoleLog(MODULE_NAME, f"Item {item_id} no longer in inventory.", Py4GW.Console.MessageType.Info)
                merchant_checkboxes[item_id] = False
                break

            quantity = Item.Properties.GetQuantity(item_id)
            if quantity < required_quantity:
                #ConsoleLog(MODULE_NAME, f"Item {item_id} has quantity {quantity} which is below required {required_quantity}.", Py4GW.Console.MessageType.Info)
                merchant_checkboxes[item_id] = False
                break

            # Request quote
            GLOBAL_CACHE.Trading.Trader.RequestSellQuote(item_id)
            while True:
                yield from Routines.Yield.wait(50)
                quoted_value = Trading.Trader.GetQuotedValue()
                if quoted_value >= 0:
                    break

            if quoted_value == 0:
                ConsoleLog(MODULE_NAME, f"Item {item_id} has no value, skipping.", Py4GW.Console.MessageType.Warning)
                merchant_checkboxes[item_id] = False
                break

            # Proceed with sale
            GLOBAL_CACHE.Trading.Trader.SellItem(item_id, quoted_value)
            #ConsoleLog(MODULE_NAME, f"Sold item {item_id} for {quoted_value}.", Py4GW.Console.MessageType.Success)

            # Wait for confirmation
            while True:
                yield from Routines.Yield.wait(50)
                if Trading.IsTransactionComplete():
                    break

            sold_items += required_quantity  # Assumed fixed chunk sold
            ammount_sold += quoted_value * required_quantity

    ConsoleLog(MODULE_NAME, f"Merchant sold {sold_items} items for a total of {ammount_sold} gold.", Py4GW.Console.MessageType.Info)

#region BuyMerchantItems
def BuyMerchantItems(merchant_item_list, selected_index, quantity):
    MODULE_NAME = "Inventory + Buy Merchant Items"
    def _is_material_trader():
        merchant_models = [
            Item.GetModelID(item_id)
            for item_id in Trading.Trader.GetOfferedItems()
        ]
        return ModelID.Wood_Plank.value in merchant_models

    def _get_minimum_quantity():
        return 10 if _is_material_trader() else 1

    if selected_index < 0 or selected_index >= len(merchant_item_list):
        ConsoleLog(MODULE_NAME, "Invalid merchant selection.", Py4GW.Console.MessageType.Warning)
        return

    item_id = merchant_item_list[selected_index]
    required_quantity = _get_minimum_quantity()

    if quantity < required_quantity:
        ConsoleLog(
            MODULE_NAME,
            f"Minimum quantity required is {required_quantity}.",
            Py4GW.Console.MessageType.Warning
        )
        return

    total_items_bought = 0
    total_gold_spent = 0

    while quantity >= required_quantity:
        GLOBAL_CACHE.Trading.Trader.RequestQuote(item_id)

        while True:
            yield from Routines.Yield.wait(50)
            cost = Trading.Trader.GetQuotedValue()
            if cost >= 0:
                break

        if cost == 0:
            ConsoleLog(MODULE_NAME, f"Item {item_id} has no price, skipping.", Py4GW.Console.MessageType.Warning)
            return

        GLOBAL_CACHE.Trading.Trader.BuyItem(item_id, cost)
        #ConsoleLog(MODULE_NAME,f"Bought {required_quantity} units of item {item_id} for {cost}g.", Py4GW.Console.MessageType.Success)

        while True:
            yield from Routines.Yield.wait(50)
            if Trading.IsTransactionComplete():
                break

        quantity -= required_quantity
        total_items_bought += required_quantity
        total_gold_spent += cost

    ConsoleLog(
        MODULE_NAME,
        f"Purchase complete: {total_items_bought} items bought for a total of {total_gold_spent} gold.",
        Py4GW.Console.MessageType.Info
    )

