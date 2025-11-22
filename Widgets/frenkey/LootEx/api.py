import math
from Widgets.frenkey.LootEx import utility
from Py4GWCoreLib import Inventory
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Item import Bag
from Py4GWCoreLib.ItemArray import ItemArray
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog
from Py4GWCoreLib.enums import Bags, Console, ItemType, ModelID


@staticmethod
def DepositMaterials(material_capacity : int = 250) -> None:
    items: list[int] = GLOBAL_CACHE.ItemArray.GetItemArray(
        [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2])

    items: list[int] = ItemArray.Filter.ByCondition(
        items, lambda item_id: GLOBAL_CACHE.Item.GetItemType(item_id)[0] == ItemType.Materials_Zcoins.value)

    material_storage = GLOBAL_CACHE.ItemArray.GetItemArray(
        [Bag.Material_Storage])

    model_ids = [GLOBAL_CACHE.Item.GetModelID(i) for i in items]

    # filter the material_storage items to only include those which share the same model_id as the items in the inventory
    material_storage = ItemArray.Filter.ByCondition(
        material_storage,
        lambda item_id: GLOBAL_CACHE.Item.GetModelID(
            item_id) in model_ids
    )

    for item_id in items:
        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)

        if model_id:
            material_storage_item = next(
                (item_id for item_id in material_storage if GLOBAL_CACHE.Item.GetModelID(item_id) == model_id), None)

            max_move_amount = material_capacity - GLOBAL_CACHE.Item.Properties.GetQuantity(
                material_storage_item) if material_storage_item else material_capacity
            move_amount = min(
                max_move_amount, GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))

            if move_amount <= 0:
                continue

            if material_storage_item:
                ConsoleLog(
                    "LootEx-API", f"Depositing item {move_amount}x {item_id} to material storage.", Console.MessageType.Info)
                Inventory.MoveItem(
                    item_id, Bags.MaterialStorage,GLOBAL_CACHE.Item.GetSlot(material_storage_item), move_amount)
                
@staticmethod
def StashItem(item_id: int) -> bool:
    stash = GLOBAL_CACHE.Inventory.GetZeroFilledStorageArray()
    model_id = GLOBAL_CACHE.Item.GetModelID(item_id)

    if GLOBAL_CACHE.Item.Customization.IsStackable(item_id):
        amount = GLOBAL_CACHE.Item.Properties.GetQuantity(
            item_id)
        color = utility.Util.get_color(item_id)

        sorted_stash = stash.copy()
        sorted_stash.sort(key=lambda x: (
            x == 0, GLOBAL_CACHE.Item.Properties.GetQuantity(x) if x != 0 else 0), reverse=True)

        slot = -1
        for id in sorted_stash:
            slot = stash.index(id)
            storage_index = Bag.Storage_1.value + math.floor(slot / 25)
            storage_slot = slot % 25

            if id == 0:
                continue

            slot_model_id = GLOBAL_CACHE.Item.GetModelID(id)
            if slot_model_id == model_id:
                slot_quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(
                    id)

                if slot_quantity == 250:
                    continue

                if slot_model_id == ModelID.Vial_Of_Dye:
                    if utility.Util.get_color(id) == color:
                        move_amount = min(250 - slot_quantity, amount)
                        ConsoleLog(
                            "LootEx-API", f"Stashing item  {move_amount} '{utility.Util.GetItemDataName(item_id)}' {item_id} to storage {Bag(storage_index)} slot {storage_slot}", Console.MessageType.Info)
                        Inventory.MoveItem(
                            item_id, storage_index, storage_slot, move_amount)
                        amount -= move_amount

                        if amount <= 0:
                            break

                else:
                    name = utility.Util.GetItemDataName(item_id)
                    move_amount = min(250 - slot_quantity, amount)
                    ConsoleLog(
                        "LootEx-API", f"Stashing item {move_amount}'{name}' {item_id} to storage {Bag(storage_index)} slot {storage_slot}", Console.MessageType.Info)
                    Inventory.MoveItem(
                        item_id, storage_index, storage_slot, move_amount)
                    amount -= move_amount

                    if amount <= 0:
                        break

        if amount > 0:
            first_zero_slot = stash.index(0) if 0 in stash else None
            if first_zero_slot is None:
                ConsoleLog(
                    "LootEx-API", "No empty slot found in stash, cannot stash item.", Console.MessageType.Warning)
                return False

            storage_index = Bag.Storage_1.value + \
                math.floor(first_zero_slot / 25)
            storage_slot = first_zero_slot % 25
            move_amount = min(250, amount)
            ConsoleLog(
                "LootEx-API", f"Stashing item {move_amount} '{utility.Util.GetItemDataName(item_id)}' {item_id} to storage {Bag(storage_index)} slot {storage_slot}", Console.MessageType.Info)
            Inventory.MoveItem(item_id, storage_index,
                                storage_slot, move_amount)

        pass

    else:
        # find an empty slot in the stash
        first_zero_slot = stash.index(0) if 0 in stash else None

        if first_zero_slot is None:
            ConsoleLog(
                "LootEx-API", "No empty slot found in stash, cannot stash item.", Console.MessageType.Warning)
            return False

        storage_index = Bag.Storage_1.value + \
            math.floor(first_zero_slot / 25)
        storage_slot = first_zero_slot % 25

        ConsoleLog(
            "LootEx-API", f"Stashing item '{utility.Util.GetItemDataName(item_id)}' {item_id} to storage {Bag(storage_index)} slot {storage_slot}", Console.MessageType.Info)
        Inventory.MoveItem(item_id, storage_index, storage_slot,
                            GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))

    return True