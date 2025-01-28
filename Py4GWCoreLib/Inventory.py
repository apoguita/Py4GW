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
    def GetStorageSpace():
        """
        Purpose: Calculate and return the total number of items and the combined capacity of bags 8, 9, 10, and 11 (storage bags).
        Args: None
        Returns:
            tuple: (total_items, total_capacity)
                - total_items: The sum of items in the storage bags.
                - total_capacity: The combined capacity (size) of the storage bags.
        """
        # Define the storage bags to check
        bags_to_check = ItemArray.CreateBagList(8, 9, 10, 11)
    
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
    def GetFirstSalvageKit():
        """
        Purpose: Find the salvage kit with the lowest remaining uses in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the salvage kit with the lowest uses, or 0 if no salvage kit is found.
        """
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        item_array = ItemArray.GetItemArray(bags_to_check)

        salvage_kits = ItemArray.Filter.ByCondition(item_array, Item.Usage.IsSalvageKit)
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
        if not inventory.IsSalvaging():
            inventory.StartSalvage(salvage_kit_id, item_id)

        #you add the dialgos HERE!!!!!

        if inventory.IsSalvaging() and inventory.IsSalvageTransactionDone():
            inventory.FinishSalvage()

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
        inventory.StartSalvage(salvage_kit_id, salvage_item_id)
        Py4GW.Console.Log("SalvageFirst", f"Started salvaging item with Item ID: {salvage_item_id} using Salvage Kit ID: {salvage_kit_id}")
        
        if inventory.IsSalvaging() and inventory.IsSalvageTransactionDone():
            inventory.FinishSalvage()
            Py4GW.Console.Log("SalvageFirst", f"Finished salvaging item with Item ID: {salvage_item_id}.")
            return True

        return False

    @staticmethod
    def IsInSalvageSession():
        """
        Purpose: Check if the player is currently salvaging.
        Returns: bool: True if the player is salvaging, False if not.
        """
        return Inventory.inventory_instance().IsSalvaging()

    @staticmethod
    def IsSalvageSessionDone():
        """
        Purpose: Check if the salvage transaction is completed.
        Returns: bool: True if the salvage transaction is done, False if not.
        """
        return Inventory.inventory_instance().IsSalvageTransactionDone()

    @staticmethod
    def FinishSalvage():
        """
        Purpose: Finish the salvage process.
        Returns: bool: True if the salvage process is finished, False if not.
        """
        if Inventory.inventory_instance().IsSalvaging() and Inventory.inventory_instance().IsSalvageTransactionDone():
            Inventory.inventory_instance().FinishSalvage()
            Py4GW.Console.Log("FinishSalvage", "Finished the salvage process.")
            return True

        return False

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
                    slot = Item.Properties.GetSlot(item)  # Get the item's slot
                    return bag_enum.value, slot  # Return bag ID and slot
        return None, None


    @staticmethod
    def DepositItemToStorage(item_id, quantity=0):
        """
        Moves the specified item (item_id) from its current location to the first available slot
        in storage bags (8, 9, 10, 11).

        Args:
            item_id (int): The ID of the item to be moved.

        Returns:
            bool: True if the item was successfully moved, False otherwise.
        """
        # Create a list of storage bags as Bag enums
        storage_bags = ItemArray.CreateBagList(8, 9, 10, 11)

        for storage_bag in storage_bags:
            try:
                # Initialize the SafeBag instance for this storage bag
                bag_instance = PyInventory.Bag(storage_bag.value, storage_bag.name)
            
                # Retrieve occupied slots using Item.GetSlot
                items_in_bag = bag_instance.GetItems()
                occupied_slots = {Item.GetSlot(item.item_id) for item in items_in_bag}
            
                # Determine the bag's capacity
                total_slots = bag_instance.GetSize()

                # Find the first free slot by checking from 0 to total_slots - 1
                for slot in range(total_slots):
                    if slot not in occupied_slots:
                        # Move the item to the first available slot in this storage bag
                        if quantity == 0:
                            quantity = Item.Properties.GetQuantity(item_id)

                        Inventory.MoveItem(item_id, storage_bag.value, slot,quantity)
                        #Py4GW.Console.Log("DepositItemToStorage", f"Moved item with ID {item_id} to storage bag {storage_bag.value}, slot {slot}." )
                        return True  # Successfully moved

            except Exception as e:
                Py4GW.Console.Log(
                    "DepositSpecificItemToStorage",
                    f"Error processing storage bag {storage_bag.name}: {str(e)}",
                    Py4GW.Console.MessageType.Error
                )

        # No available slots found
        Py4GW.Console.Log(
            "DepositSpecificItemToStorage",
            f"No free slots available for item ID {item_id} in storage bags."
        )
        return False  # No slots available





