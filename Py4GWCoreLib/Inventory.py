import PyItem
import PyInventory

from .ItemArray import *


class Inventory:
    @staticmethod
    def inventory_instance():
        return PyInventory.PyInventory()

    @staticmethod
    def GetInventorySpace():
        """
        Purpose: Calculate and return the total number of items and the combined capacity of bags 1, 2, 3, and 4.
        Args: None
        Returns: tuple: (total_items, total_capacity)
            - total_items: The sum of items in the four bags.
            - total_capacity: The combined capacity (size) of the four bags.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)
        total_items = len(item_array)
        total_capacity = sum(PyInventory.Bag(bag_enum.value, bag_enum.name).GetSize() for bag_enum in bags_to_check)

        return total_items, total_capacity

    @staticmethod
    def GetStorageSpace(Anniversary_panel = True, ExtraStoragePanes = 0):
        from .enums import Bags
        """
        Purpose: Calculate and return the total number of items and the combined capacity of bags 8, 9, 10, and 11 (storage bags).
        Args: None
        Returns:
            tuple: (total_items, total_capacity)
                - total_items: The sum of items in the storage bags.
                - total_capacity: The combined capacity (size) of the storage bags.
        """
        # Define the storage bags to check
        if not Anniversary_panel:
            bags_to_check = ItemArray.CreateBagList(Bags.Storage1, Bags.Storage2, Bags.Storage3, Bags.Storage4)
        else:
            bags_to_check = ItemArray.CreateBagList(Bags.Storage1, Bags.Storage2, Bags.Storage3, Bags.Storage4,Bags.Storage5)
    
        # Retrieve the item array for the storage bags
        item_array = ItemArray.GetItemArray(bags_to_check)
    
        # Count the number of items
        total_items = len(item_array)
    
        # Dynamically calculate the total capacity using PyInventory.Bag
        total_capacity = sum(
            PyInventory.Bag(bag_enum.value, bag_enum.name).GetSize() for bag_enum in bags_to_check
        )
    
        return total_items, total_capacity
    
    @staticmethod
    def GetZeroFilledStorageArray(Anniversary_panel = True, ExtraStoragePanes = 0):
        """
        Returns a flat list of item_ids ordered by bag and slot.
        Empty slots are represented as 0.
        """
        from .enums import Bags
        result = []
        
        if not Anniversary_panel:
            bags_to_check = ItemArray.CreateBagList(Bags.Storage1, Bags.Storage2, Bags.Storage3, Bags.Storage4)
        else:
            bags_to_check = ItemArray.CreateBagList(Bags.Storage1, Bags.Storage2, Bags.Storage3, Bags.Storage4,Bags.Storage5)
    

        for bag_enum in bags_to_check:
            bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
            size = bag.GetSize()
            item_slots = [0] * size  # Pre-fill all slots with 0s

            for item in bag.GetItems():
                if 0 <= item.slot < size:
                    item_slots[item.slot] = item.item_id

            result.extend(item_slots)

        return result





    @staticmethod
    def GetFreeSlotCount():
        """
        Purpose: Calculate and return the number of free slots in bags 1, 2, 3, and 4.
        Args: None
        Returns: int: The number of free slots available across the four bags.
        """
        total_items, total_capacity = Inventory.GetInventorySpace()
        free_slots = total_capacity - total_items
        return max(free_slots, 0)

    @staticmethod
    def GetItemCount(item_id):
        """
        Purpose: Count the number of items with the specified item_id in bags 1, 2, 3, and 4.
        Args:
            item_id (int): The ID of the item to count.
        Returns: int: The total number of items matching the item_id in bags 1, 2, 3, and 4.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)

        # Filter to get only the items that match the specified item_id
        matching_items = ItemArray.Filter.ByCondition(item_array, lambda item: item == item_id)

        # Use a lambda to sum the quantity of each matching item using Item.Properties.GetQuantity
        total_quantity = sum(Item.Properties.GetQuantity(item) for item in matching_items)

        return total_quantity

    @staticmethod
    def GetModelCount(model_id):
        """
        Purpose: Count the number of items with the specified model_id in bags 1, 2, 3, and 4.
        Args:
            model_id (int): The model ID of the item to count.
        Returns: int: The total number of items matching the model_id in bags 1, 2, 3, and 4.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)
        
        # Filter items by the specified model_id using Item.GetModelID
        matching_items = ItemArray.Filter.ByCondition(item_array, lambda item_id: Item.GetModelID(item_id) == model_id)
        # Sum the quantity of each matching item using Item.Properties.GetQuantity
        total_quantity = sum(Item.Properties.GetQuantity(item_id) for item_id in matching_items)

        return total_quantity

    @staticmethod
    def GetFirstIDKit():
        """
        Purpose: Find the Identification Kit (ID Kit) with the lowest remaining uses in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the ID Kit with the lowest uses, or 0 if no ID Kit is found.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)
        # Filter to find items that are ID Kits using Item.Usage.IsIDKit
        id_kits = ItemArray.Filter.ByCondition(item_array, Item.Usage.IsIDKit)
        
        if not id_kits:
            return 0  # Return 0 if no ID Kit is found
        # Sort the ID Kits by remaining uses using Item.Usage.GetUses and get the one with the lowest uses
        id_kit_with_lowest_uses = min(id_kits, key=lambda item_id: Item.Usage.GetUses(item_id))

        return id_kit_with_lowest_uses


    @staticmethod
    def GetFirstUnidentifiedItem():
        """
        Purpose: Find the first unidentified item in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the first unidentified item found, or 0 if no unidentified item is found.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)

        unidentified_items = ItemArray.Filter.ByCondition(item_array, lambda item_id: not Item.Usage.IsIdentified(item_id))
        
        return unidentified_items[0] if unidentified_items else 0
        
    @staticmethod
    def GetFirstSalvageKit(use_lesser =True):
        """
        Purpose: Find the salvage kit with the lowest remaining uses in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the salvage kit with the lowest uses, or 0 if no salvage kit is found.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)

        salvage_kits = ItemArray.Filter.ByCondition(item_array, Item.Usage.IsSalvageKit)
        if use_lesser:
            salvage_kits = ItemArray.Filter.ByCondition(salvage_kits, lambda item_id: Item.Usage.IsLesserKit(item_id))
            
        if not salvage_kits:
            return 0  # Return 0 if no salvage kit is found
        salvage_kit_with_lowest_uses = min(salvage_kits, key=lambda item_id: Item.Usage.GetUses(item_id))
        
        return salvage_kit_with_lowest_uses


    
    @staticmethod
    def GetFirstSalvageableItem():
        """
        Purpose: Find the first salvageable item in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the first salvageable item found, or 0 if no salvageable item is found.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)
    
        salvageable_items = ItemArray.Filter.ByCondition(item_array, Item.Usage.IsSalvageable)

        return salvageable_items[0] if salvageable_items else 0


    @staticmethod
    def IdentifyItem (item_id, id_kit_id):
        """
        Purpose: Identify an item using an Identification Kit.
        Args:
            item_id (int): The ID of the item to identify.
            id_kit_id (int): The ID of the Identification Kit to use.
        Returns: None
        """
        inventory = PyInventory.PyInventory()
        inventory.IdentifyItem(id_kit_id, item_id)

    @staticmethod
    def IdentifyFirst():
        """
        Purpose: Identify the first unidentified item found in bags 1, 2, 3, and 4 using the first available ID kit.
                 Items are filtered by the given list of exact rarities (e.g., ["White", "Purple", "Gold"]).
        Args:
            rarities (list of str, optional): The rarity filter for identification.
        Returns:
            bool: True if an item was identified, False if no unidentified item or ID kit was found.
        """
        # Get the first ID Kit
        id_kit_id = Inventory.GetFirstIDKit()
        if id_kit_id == 0:
            Py4GW.Console.Log("IdentifyFirst", "No ID Kit found.")
            return False

        # Find the first unidentified item based on the rarity filter
        unid_item_id = Inventory.GetFirstUnidentifiedItem()
        if unid_item_id == 0:
            Py4GW.Console.Log("IdentifyFirst", "No unidentified item found.")
            return False

        # Use the ID Kit to identify the item
        inventory = PyInventory.PyInventory()
        inventory.IdentifyItem(id_kit_id, unid_item_id)
        Py4GW.Console.Log("IdentifyFirst", f"Identified item with Item ID: {unid_item_id} using ID Kit ID: {id_kit_id}")
        return True

    @staticmethod
    def SalvageItem(item_id,salvage_kit_id):
        """
        Purpose: Salvage an item using a Salvage Kit.
        Args:
            salvage_kit_id (int): The ID of the Salvage Kit to use.
            item_id (int): The ID of the item to salvage.
        Returns: None
        """
        inventory = PyInventory.PyInventory()
        inventory.Salvage(salvage_kit_id, item_id)

    @staticmethod
    def SalvageFirst():
        """
        Purpose: Salvage the first salvageable item found in bags 1, 2, 3, and 4 using the first available salvage kit.
                 Items are filtered by the given list of exact rarities (e.g., ["White", "Purple", "Gold"]).
        Args:
            rarities (list of str, optional): The rarity filter for salvage.
        Returns:
            bool: True if an item was salvaged, False if no salvageable item or salvage kit was found.
        """
        # Get the first available Salvage Kit
        salvage_kit_id = Inventory.GetFirstSalvageKit()
        if salvage_kit_id == 0:
            Py4GW.Console.Log("SalvageFirst", "No salvage kit found.")
            return False

        # Find the first salvageable item based on the rarity filter
        salvage_item_id = Inventory.GetFirstSalvageableItem()
        if salvage_item_id == 0:
            Py4GW.Console.Log("SalvageFirst", "No salvageable item found.")
            return False

        # Use the Salvage Kit to salvage the item
        inventory = PyInventory.PyInventory()
        inventory.Salvage(salvage_kit_id, salvage_item_id)
        Py4GW.Console.Log("SalvageFirst", f"Started salvaging item with Item ID: {salvage_item_id} using Salvage Kit ID: {salvage_kit_id}")

        return False

    
    
    @staticmethod
    def AcceptSalvageMaterialsWindow():
        """
        Checks if the Salvage Materials Dialog frame exists and clicks it if it hasn't already been clicked.
        Returns:
            bool: True if click was performed, False otherwise.
        """
        from .UIManager import UIManager

        parent_hash = 140452905
        yes_button_offsets = [6,100,6]
        
        salvage_material_window = UIManager.GetChildFrameID(parent_hash, yes_button_offsets)
        UIManager.FrameClick(salvage_material_window)
     
        #return Inventory.inventory_instance().AcceptSalvageWindow()

    @staticmethod
    def OpenXunlaiWindow():
        """
        Purpose: Open the Xunlai Storage window.
        Returns: bool: True if the Xunlai Storage window is opened, False if not.
        """
        Inventory.inventory_instance().OpenXunlaiWindow()
        return Inventory.inventory_instance().GetIsStorageOpen()

    @staticmethod
    def IsStorageOpen():
        """
        Purpose: Check if the Xunlai Storage window is open.
        Returns: bool: True if the Xunlai Storage window is open, False if not.
        """
        return Inventory.inventory_instance().GetIsStorageOpen()

    @staticmethod
    def PickUpItem(item_id, call_target=False):
        """
        Purpose: Pick up an item from the ground.
        Args:
            item_id (int): The ID of the item to pick up. (not agent_id)
            call_target (bool, optional): True to call the target, False to pick up the item directly.
        Returns: None
        """
        Inventory.inventory_instance().PickUpItem(item_id, call_target)

    @staticmethod
    def DropItem(item_id, quantity=1):
        """
        Purpose: Drop an item from the inventory.
        Args:
            item_id (int): The ID of the item to drop.
            quantity (int, optional): The quantity of the item to drop.
        Returns: None
        """
        Inventory.inventory_instance().DropItem(item_id, quantity)

    @staticmethod
    def EquipItem(item_id, agent_id):
        """
        Purpose: Equip an item from the inventory.
        Args:
            item_id (int): The ID of the item to equip.
            agent_id (int): The agent ID of the player to equip the item.
        Returns: None
        """
        Inventory.inventory_instance().EquipItem(item_id, agent_id)

    @staticmethod
    def UseItem(item_id):
        """ 
        Purpose: Use an item from the inventory.
        Args:
            item_id (int): The ID of the item to use.
        Returns: None
        """
        Inventory.inventory_instance().UseItem(item_id)

    @staticmethod
    def DestroyItem(item_id):
        """
        Purpose: Destroy an item from the inventory.
        Args:
            item_id (int): The ID of the item to destroy.
        Returns: None
        """
        Inventory.inventory_instance().DestroyItem(item_id)

    @staticmethod
    def GetHoveredItemID():
        """
        Purpose: Get the hovered item ID.
        Args: None
        Returns: int: The hovered item ID.
        """
        return Inventory.inventory_instance().GetHoveredItemID()

    @staticmethod
    def GetGoldOnCharacter():
        """         
        Purpose: Retrieve the amount of gold on the character.
        Args: None
        Returns: int: The amount of gold on the character.
        """
        return Inventory.inventory_instance().GetGoldAmount()

    @staticmethod
    def GetGoldInStorage():
        """
        Purpose: Retrieve the amount of gold in storage.
        Args: None
        Returns: int: The amount of gold in storage.
        """
        return Inventory.inventory_instance().GetGoldAmountInStorage()

    @staticmethod
    def DepositGold(amount):
        """
        Purpose: Deposit gold into storage.
        Args:
            amount (int): The amount of gold to deposit.
        Returns: None
        """
        Inventory.inventory_instance().DepositGold(amount)

    @staticmethod
    def WithdrawGold(amount):
        """
        Purpose: Withdraw gold from storage.
        Args:
            amount (int): The amount of gold to withdraw.
        Returns: None
        """
        Inventory.inventory_instance().WithdrawGold(amount)

    @staticmethod
    def DropGold(amount):
        """
        Purpose: Drop a certain amount of gold.
        Args:
            amount (int): The amount of gold to drop.
        Returns: None
        """
        Inventory.inventory_instance().DropGold(amount)
           
    @staticmethod
    def MoveItem(item_id, bag_id, slot, quantity=1):
        """ 
        Purpose: Move an item within a bag.
        Args:
            item_id (int): The ID of the item to move.
            bag_id (int): The ID of the bag to move the item to.
            slot (int): The slot to move the item to.
            quantity (int, optional): The quantity of the item to move.
        Returns: None
        """
        Inventory.inventory_instance().MoveItem(item_id, bag_id, slot, quantity)

    @staticmethod
    def FindItemBagAndSlot(item_id):
        """
        Locate the bag ID and slot of the given item ID in inventory bags (1, 2, 3, 4).
    
        Args:
            item_id (int): The ID of the item to locate.
    
        Returns:
            tuple: (bag_id, slot) if the item is found, or (None, None) if not found.
        """
        # Convert integers to Bag enum members using CreateBagList
        bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    
        items = ItemArray.GetItemArray(bags_to_check)

        # Locate the item in the retrieved items
        for bag_enum in bags_to_check:
            bag_items = ItemArray.GetItemArray([bag_enum])  # Get items in the specific bag
            for item in bag_items:
                if item == item_id:
                    slot = Item.GetSlot(item)  # Get the item's slot
                    return bag_enum.value, slot  # Return bag ID and slot
        return None, None

    @staticmethod
    def DepositItemToStorage(item_id, Anniversary_panel = True):
        """
        Moves the specified item to storage, filling partial stacks first.
        Args:
            item_id (int): ID of the item to deposit.
            quantity (int): Amount to move. 0 means 'move all available'.
        Returns:
            bool: True if moved at least some of the items, False if failed.
        """
        from .enums import Bags
        
        def GetBags():
            possible_bags = ItemArray.CreateBagList(Bags.Storage1, Bags.Storage2, Bags.Storage3, Bags.Storage4,
                                                    *([Bags.Storage5] if Anniversary_panel else []),
                                                    Bags.Storage6,Bags.Storage7,Bags.Storage8,Bags.Storage9,Bags.Storage10,
                                                    Bags.Storage11,Bags.Storage12,Bags.Storage13,Bags.Storage14)
        
            # Dynamically calculate the total capacity using PyInventory.Bag
            total_capacity = sum(
                PyInventory.Bag(bag_enum.value, bag_enum.name).GetSize() for bag_enum in possible_bags
            )

            bags = total_capacity // 25

            storage_bags = []

            for i in range(1, bags + 1):
                    bag = getattr(Bags, f"Storage{i}")
                    storage_bags.append(bag)

            return storage_bags
    
        MAX_STACK_SIZE = 250

        is_stackable = Item.Customization.IsStackable(item_id)
        quantity = Item.Properties.GetQuantity(item_id)

        if quantity == 0:
            return False  # Nothing to move

        # Gather target bags
        storage_bags = GetBags()
    
        remaining_quantity = quantity
        moved_any = False

        for bag_enum in storage_bags:
            bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
            size = bag.GetSize()
            items = bag.GetItems()

            # Fill existing partial stacks (only if stackable)
            if is_stackable:
                for item in items:
                    if item.model_id == Item.GetModelID(item_id):
                        item_qty = Item.Properties.GetQuantity(item.item_id)
                        if item_qty < MAX_STACK_SIZE:
                            space_left = MAX_STACK_SIZE - item_qty
                            to_move = min(space_left, remaining_quantity)
                            if to_move > 0:
                                Inventory.MoveItem(item_id, bag_enum.value, item.slot, to_move)
                                remaining_quantity -= to_move
                                moved_any = True
                                if remaining_quantity == 0:
                                    return True

            # Fill empty slots
            occupied_slots = {item.slot for item in items}
            for slot in range(size):
                if slot in occupied_slots:
                    continue

                to_move = remaining_quantity if not is_stackable else min(remaining_quantity, MAX_STACK_SIZE)
                Inventory.MoveItem(item_id, bag_enum.value, slot, to_move)
                remaining_quantity -= to_move
                moved_any = True
                if remaining_quantity == 0:
                    return True

        return moved_any

    @staticmethod
    def WithdrawItemFromStorage(item_id):
        """
        Moves the specified item from storage to player inventory, filling partial stacks first.
        Args:
            item_id (int): ID of the item to withdraw.
        Returns:
            bool: True if moved at least some of the items, False otherwise.
        """
        from .enums import Bags
        MAX_STACK_SIZE = 250

        is_stackable = Item.Customization.IsStackable(item_id)
        quantity = Item.Properties.GetQuantity(item_id)

        if quantity == 0:
            return False  # Nothing to move

        # Gather target bags (Backpack, Belt Pouch, Bag1, Bag2)
        inventory_bags = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)

        remaining_quantity = quantity
        moved_any = False

        for bag_enum in inventory_bags:
            bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
            size = bag.GetSize()
            items = bag.GetItems()

            # Fill existing partial stacks
            if is_stackable:
                for item in items:
                    if item.model_id == Item.GetModelID(item_id):
                        item_qty = Item.Properties.GetQuantity(item.item_id)
                        if item_qty < MAX_STACK_SIZE:
                            space_left = MAX_STACK_SIZE - item_qty
                            to_move = min(space_left, remaining_quantity)
                            if to_move > 0:
                                Inventory.MoveItem(item_id, bag_enum.value, item.slot, to_move)
                                remaining_quantity -= to_move
                                moved_any = True
                                if remaining_quantity == 0:
                                    return True

            # Fill empty slots
            occupied_slots = {item.slot for item in items}
            for slot in range(size):
                if slot in occupied_slots:
                    continue

                to_move = remaining_quantity if not is_stackable else min(remaining_quantity, MAX_STACK_SIZE)
                Inventory.MoveItem(item_id, bag_enum.value, slot, to_move)
                remaining_quantity -= to_move
                moved_any = True
                if remaining_quantity == 0:
                    return True

        return moved_any






