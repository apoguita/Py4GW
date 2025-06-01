import PyInventory
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib import Bags
from .ItemCache import RawItemCache, Bag_enum, ItemCache

class InventoryCache:
    def __init__(self, action_queue_manager, raw_item_cache, item_cache):
        self._raw_item_cache:RawItemCache = raw_item_cache
        self.item_cache:ItemCache = item_cache
        self._inventory_instance = PyInventory.PyInventory()
        self._action_queue_manager:ActionQueueManager = action_queue_manager


    def GetInventorySpace(self):
        bags_to_check = [
            Bag_enum.Backpack.value,
            Bag_enum.Belt_Pouch.value,
            Bag_enum.Bag_1.value,
            Bag_enum.Bag_2.value
        ]
        bag_array = self._raw_item_cache.get_bags(bags_to_check)
        
        total_items = 0
        bag_size = 0
        for bag in bag_array:
            total_items += bag.GetItemCount()
            bag_size += bag.GetSize()
            
        return total_items, bag_size
    
    def GetStorageSpace(self, Anniversary_panel=True):
        start = Bag_enum.Storage_1.value
        end = Bag_enum.Storage_13.value

        bags_to_check = list(range(start, end + 1))  # Storage_1 to Storage_13

        if Anniversary_panel:
            bags_to_check.append(Bag_enum.Storage_14.value)  # Add Storage_14 if available

        bag_array = self._raw_item_cache.get_bags(bags_to_check)

        total_items = 0
        bag_size = 0
        for bag in bag_array:
            total_items += bag.GetItemCount()
            bag_size += bag.GetSize()

        return total_items, bag_size
    
    def GetZeroFilledStorageArray(self, Anniversary_panel=True, ExtraStoragePanes=0):
        """
        Returns a flat list of item_ids ordered by bag and slot.
        Empty slots are represented as 0.
        """
        result = []

        # Base: Storage_1 to Storage_13
        start = Bag_enum.Storage_1.value
        end = Bag_enum.Storage_13.value

        if Anniversary_panel:
            end = Bag_enum.Storage_14.value

        end += ExtraStoragePanes  # Add any extra panes

        bags_to_check = list(range(start, min(end + 1, Bag_enum.Max.value)))

        bag_array = self._raw_item_cache.get_bags(bags_to_check)

        for bag in bag_array:
            size = bag.GetSize()
            item_slots = [0] * size  # Fill with 0s

            for item in bag.GetItems():
                if 0 <= item.slot < size:
                    item_slots[item.slot] = item.item_id

            result.extend(item_slots)

        return result

    def GetFreeSlotCount(self):
        """
        Purpose: Calculate and return the number of free slots in inventory bags (1 to 4).
        Returns: int: The number of free slots available.
        """
        total_items, total_capacity = self.GetInventorySpace()
        return max(total_capacity - total_items, 0)

    def GetItemCount(self, item_id: int) -> int:
        """
        Purpose: Count the total quantity of items with the specified item_id 
        in bags Backpack, Belt Pouch, Bag 1, and Bag 2.
        Returns: int: Total quantity across all matching items.
        """
        bags_to_check = [
            Bag_enum.Backpack.value,
            Bag_enum.Belt_Pouch.value,
            Bag_enum.Bag_1.value,
            Bag_enum.Bag_2.value
        ]

        bags = self._raw_item_cache.get_bags(bags_to_check)
        total_quantity = 0

        for bag in bags:
            for item in bag.GetItems():
                if item.model_id == item_id:
                    total_quantity += item.quantity

        return total_quantity

    def GetModelCount(self, model_id: int) -> int:
        """
        Purpose: Count the number of items with the specified model_id 
        in inventory bags 1, 2, 3, and 4.
        Args:
            model_id (int): The model ID of the item to count.
        Returns:
            int: Total quantity of matching items.
        """
        
        if model_id <= 0:
            return 0
        
        bags_to_check = [
            Bag_enum.Backpack.value,
            Bag_enum.Belt_Pouch.value,
            Bag_enum.Bag_1.value,
            Bag_enum.Bag_2.value
        ]

        bags = self._raw_item_cache.get_bags(bags_to_check)
        total_quantity = 0

        for bag in bags:
            for item in bag.GetItems():
                if item.model_id == model_id:
                    total_quantity += item.quantity

        return total_quantity

    def GetFirstIDKit(self) -> int:
        """
        Purpose: Find the Identification Kit (ID Kit) with the lowest remaining uses
        in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the ID Kit with the lowest uses, or 0 if no ID Kit is found.
        """
        bags_to_check = [
            Bag_enum.Backpack.value,
            Bag_enum.Belt_Pouch.value,
            Bag_enum.Bag_1.value,
            Bag_enum.Bag_2.value
        ]

        bags = self._raw_item_cache.get_bags(bags_to_check)
        id_kits = []

        for bag in bags:
            for item in bag.GetItems():
                if self.item_cache.Usage.IsIDKit(item.item_id):
                    id_kits.append(item)

        if not id_kits:
            return 0

        id_kit_with_lowest_uses = min(id_kits, key=lambda item: self.item_cache.Usage.GetUses(item.item_id))
        return id_kit_with_lowest_uses.item_id
    

    def GetFirstUnidentifiedItem(self) -> int:
        """
        Purpose: Find the first unidentified item in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the first unidentified item found, or 0 if none found.
        """
        bags_to_check = [
            Bag_enum.Backpack.value,
            Bag_enum.Belt_Pouch.value,
            Bag_enum.Bag_1.value,
            Bag_enum.Bag_2.value
        ]

        bags = self._raw_item_cache.get_bags(bags_to_check)

        for bag in bags:
            for item in bag.GetItems():
                if not self.item_cache.Usage.IsIdentified(item.item_id):
                    return item.item_id

        return 0

    def GetFirstSalvageKit(self, use_lesser=True) -> int:
        """
        Purpose: Find the salvage kit with the lowest remaining uses 
        in bags 1, 2, 3, and 4. Optionally filters to only lesser kits.
        
        Args:
            use_lesser (bool): If True, only consider lesser salvage kits.

        Returns:
            int: The item_id of the salvage kit with the fewest uses, or 0 if none found.
        """
        bags_to_check = [
            Bag_enum.Backpack.value,
            Bag_enum.Belt_Pouch.value,
            Bag_enum.Bag_1.value,
            Bag_enum.Bag_2.value
        ]

        bags = self._raw_item_cache.get_bags(bags_to_check)
        kits = []

        for bag in bags:
            for item in bag.GetItems():
                if not self.item_cache.Usage.IsSalvageKit(item.item_id):
                    continue
                if use_lesser and not self.item_cache.Usage.IsLesserKit(item.item_id):
                    continue
                kits.append(item)

        if not kits:
            return 0

        best_kit = min(kits, key=lambda item: self.item_cache.Usage.GetUses(item.item_id))
        return best_kit.item_id

    def GetFirstSalvageableItem(self) -> int:
        """
        Purpose: Find the first salvageable item in bags 1, 2, 3, and 4.
        Returns:
            int: The Item ID of the first salvageable item found, or 0 if none found.
        """
        bags_to_check = [
            Bag_enum.Backpack.value,
            Bag_enum.Belt_Pouch.value,
            Bag_enum.Bag_1.value,
            Bag_enum.Bag_2.value
        ]

        bags = self._raw_item_cache.get_bags(bags_to_check)

        for bag in bags:
            for item in bag.GetItems():
                if self.item_cache.Usage.IsSalvageable(item.item_id):
                    return item.item_id

        return 0

    def IdentifyItem (self, item_id, id_kit_id):
        """
        Purpose: Identify an item using an Identification Kit.
        """
        self._action_queue_manager.AddAction("IDENTIFY", self._inventory_instance.IdentifyItem,id_kit_id, item_id)

    def IdentifyFirst(self) -> bool:
        """
        Purpose: Identify the first unidentified item found in bags 1, 2, 3, and 4 using the first available ID kit.
        Returns:
            bool: True if an item was queued for identification, False otherwise.
        """
        id_kit_id = self.GetFirstIDKit()
        if id_kit_id == 0:
            ConsoleLog("IdentifyFirst", "No ID Kit found.")
            return False

        unid_item_id = self.GetFirstUnidentifiedItem()
        if unid_item_id == 0:
            ConsoleLog("IdentifyFirst", "No unidentified item found.")
            return False

        self._action_queue_manager.AddAction("IDENTIFY", self._inventory_instance.IdentifyItem, id_kit_id, unid_item_id)
        ConsoleLog("IdentifyFirst", f"Queued identification for item ID: {unid_item_id} using ID Kit ID: {id_kit_id}")
        return True

    def SalvageItem(self, item_id: int, salvage_kit_id: int):
        """
        Purpose: Identify an item using an Identification Kit.
        """
        self._action_queue_manager.AddAction("SALVAGE", self._inventory_instance.Salvage, salvage_kit_id, item_id)

    def SalvageFirst(self) -> bool:
        """
        Purpose: Queue the action to salvage the first salvageable item using the first available salvage kit.
        Returns:
            bool: True if a salvage action was queued, False if no valid kit or item was found.
        """
        salvage_kit_id = self.GetFirstSalvageKit()
        if salvage_kit_id == 0:
            ConsoleLog("SalvageFirst", "No salvage kit found.")
            return False

        salvage_item_id = self.GetFirstSalvageableItem()
        if salvage_item_id == 0:
            ConsoleLog("SalvageFirst", "No salvageable item found.")
            return False

        self._action_queue_manager.AddAction(
            "SALVAGE",
            self._inventory_instance.Salvage,
            salvage_kit_id,
            salvage_item_id
        )
        ConsoleLog("SalvageFirst", f"Queued salvage for item ID {salvage_item_id} with kit ID {salvage_kit_id}")
        return True

    def AcceptSalvageMaterialsWindow(self):

        parent_hash = 140452905
        yes_button_offsets = [6,98,6]
        
        salvage_material_window = UIManager.GetChildFrameID(parent_hash, yes_button_offsets)
        UIManager.FrameClick(salvage_material_window)

    def IsStorageOpen(self):

        return self._inventory_instance.GetIsStorageOpen()
    
    def OpenXunlaiWindow(self) -> bool:

        if self._inventory_instance.GetIsStorageOpen():
            return True  # Already open

        self._action_queue_manager.AddAction("ACTION",self._inventory_instance.OpenXunlaiWindow)
        return False  # Queued but not yet open

    def PickUpItem(self, item_id: int, call_target: bool = False) -> None:
        """
        Purpose: Queue an action to pick up an item from the ground.
        """
        self._action_queue_manager.AddAction("ACTION", self._inventory_instance.PickUpItem, item_id, call_target)

    def DropItem(self, item_id: int, quantity: int = 1) -> None:
        """
        Purpose: Queue an action to drop an item from the inventory.
        """
        self._action_queue_manager.AddAction("ACTION", self._inventory_instance.DropItem,item_id, quantity)
        
    def EquipItem(self, item_id: int, agent_id: int) -> None:
        """
        Purpose: Queue an action to equip an item from the inventory.
        """
        self._action_queue_manager.AddAction("ACTION",self._inventory_instance.EquipItem, item_id,agent_id)

    def UseItem(self, item_id: int) -> None:
        """
        Purpose: Queue an action to use an item from the inventory.
        """
        self._action_queue_manager.AddAction("ACTION",self._inventory_instance.UseItem,item_id)

    def DestroyItem(self, item_id: int):
        self._action_queue_manager.AddAction("ACTION",self._inventory_instance.DestroyItem,item_id)

    def GetHoveredItemID(self) -> int:
        return self._inventory_instance.GetHoveredItemID()

    def GetGoldOnCharacter(self) -> int:
        return self._inventory_instance.GetGoldAmount()

    def GetGoldInStorage(self) -> int:
        return self._inventory_instance.GetGoldAmountInStorage()

    def DepositGold(self, amount: int):
        self._action_queue_manager.AddAction( "ACTION",self._inventory_instance.DepositGold,amount )

    def WithdrawGold(self, amount: int):
        self._action_queue_manager.AddAction( "ACTION", self._inventory_instance.WithdrawGold,amount)

    def DropGold(self, amount: int):
        self._action_queue_manager.AddAction("ACTION",self._inventory_instance.DropGold,amount)

    def MoveItem(self, item_id: int, bag_id: int, slot: int, quantity: int = 1):
        self._action_queue_manager.AddAction( "ACTION",self._inventory_instance.MoveItem, item_id, bag_id,slot,quantity)

    def FindItemBagAndSlot(self, item_id: int) -> tuple[int | None, int | None]:
        """
        Locate the bag ID and slot of the given item ID in inventory bags (1, 2, 3, 4).
        """
        bags_to_check = [1, 2, 3, 4]
        bags = self._raw_item_cache.get_bags(bags_to_check)

        for bag in bags:
            for item in bag.GetItems():
                if item.item_id == item_id:
                    return bag.id, item.slot

        return None, None

    def DepositItemToStorage(self, item_id: int, Anniversary_panel: bool = True) -> bool:
        """
        Purpose: Moves the specified item to storage, filling partial stacks first.
        Args:
            item_id (int): ID of the item to deposit.
            Anniversary_panel (bool): Whether the Anniversary Panel (Storage14) is enabled.
        Returns:
            bool: True if moved at least some of the items, False if failed.
        """
        MAX_STACK_SIZE = 250
        quantity = self.item_cache.Properties.GetQuantity(item_id)
        is_stackable = self.item_cache.Customization.IsStackable(item_id)

        if quantity == 0:
            return False  # Nothing to move

        def GetStorageBags():
            bag_list = [
                Bags.Storage1, Bags.Storage2, Bags.Storage3, Bags.Storage4,
                *( [Bags.Storage5] if Anniversary_panel else [] ),
                Bags.Storage6, Bags.Storage7, Bags.Storage8, Bags.Storage9, Bags.Storage10,
                Bags.Storage11, Bags.Storage12, Bags.Storage13, Bags.Storage14
            ]
            # Only include bags that exist (have size > 0)
            valid_bags = []
            for bag_enum in bag_list:
                try:
                    bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
                    if bag.GetSize() > 0:
                        valid_bags.append((bag_enum, bag))
                except Exception:
                    continue
            return valid_bags

        storage_bags = GetStorageBags()
        remaining_quantity = quantity
        moved_any = False
        model_id = self.item_cache.GetModelID(item_id)

        for bag_enum, bag in storage_bags:
            items = bag.GetItems()

            # === Fill partial stacks ===
            if is_stackable:
                for item in items:
                    if item.model_id == model_id:
                        current_qty = self.item_cache.Properties.GetQuantity(item.item_id)
                        if current_qty < MAX_STACK_SIZE:
                            space_left = MAX_STACK_SIZE - current_qty
                            to_move = min(space_left, remaining_quantity)
                            if to_move > 0:
                                self.MoveItem(item_id, bag_enum.value, item.slot, to_move)
                                remaining_quantity -= to_move
                                moved_any = True
                                if remaining_quantity == 0:
                                    return True

            # === Fill empty slots ===
            occupied_slots = {item.slot for item in items}
            for slot in range(bag.GetSize()):
                if slot in occupied_slots:
                    continue
                to_move = remaining_quantity if not is_stackable else min(remaining_quantity, MAX_STACK_SIZE)
                self.MoveItem(item_id, bag_enum.value, slot, to_move)
                remaining_quantity -= to_move
                moved_any = True
                if remaining_quantity == 0:
                    return True

        return moved_any
    
    def WithdrawItemFromStorage(self, item_id: int) -> bool:
        """
        Moves the specified item from storage to player inventory, filling partial stacks first.
        Args:
            item_id (int): ID of the item to withdraw.
        Returns:
            bool: True if moved at least some of the items, False otherwise.
        """
        MAX_STACK_SIZE = 250
        quantity = self.item_cache.Properties.GetQuantity(item_id)
        is_stackable = self.item_cache.Customization.IsStackable(item_id)

        if quantity == 0:
            return False  # Nothing to move

        inventory_bags = [
            Bags.Backpack,
            Bags.BeltPouch,
            Bags.Bag1,
            Bags.Bag2
        ]

        remaining_quantity = quantity
        moved_any = False
        model_id = self.item_cache.GetModelID(item_id)

        for bag_enum in inventory_bags:
            try:
                bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
                size = bag.GetSize()
                items = bag.GetItems()
            except Exception:
                continue

            # Fill existing partial stacks
            if is_stackable:
                for item in items:
                    if item.model_id == model_id:
                        item_qty = self.item_cache.Properties.GetQuantity(item.item_id)
                        if item_qty < MAX_STACK_SIZE:
                            space_left = MAX_STACK_SIZE - item_qty
                            to_move = min(space_left, remaining_quantity)
                            if to_move > 0:
                                self.MoveItem(item_id, bag_enum.value, item.slot, to_move)
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
                self.MoveItem(item_id, bag_enum.value, slot, to_move)
                remaining_quantity -= to_move
                moved_any = True
                if remaining_quantity == 0:
                    return True

        return moved_any

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
