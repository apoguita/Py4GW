from typing import Generator, Optional

import Py4GW

from Py4GWCoreLib.Item import Bag
from Sources.frenkeyLib.ItemHandling.Items.ItemCache import ITEM_CACHE
from Sources.frenkeyLib.ItemHandling.Rules.profile import RuleProfile
from Sources.frenkeyLib.ItemHandling.Rules.types import ACTION_LIMITS_PER_FRAME, ItemAction
from Sources.frenkeyLib.ItemHandling.utility import GetZeroFilledBags

class InventoryHandler:
    def __init__(self):
        self.enabled: bool = False
        
        self.yield_action : Optional[Generator] = None        
        self.rules : RuleProfile = RuleProfile.load_by_name("Default Xunlai Rules")
        
        self.xunlai_sorting_config = None  # You would need to define what this is and how it works based on your requirements
        self.anniversary_tab: bool = False  # You would need to define how this is set
        
    def run(self):
        if not self.enabled:
            return       
               
        # Handle all yield based actions (ACTION_LIMITS_PER_FRAME)    
        yield from self.compact_xunlai_storage()
        yield from self.sort_xunlai_storage()
            
        
        pass
    
    def get_generator_for_action(self, item_id: int, action: ItemAction) -> Optional[Generator]:
        # This function should return a generator for the given action
        # For example, if the action is Salvage, it would return a generator that performs the salvage action on the item
        # You would need to implement the actual logic for each action type here
        
        match action:
            case ItemAction.Salvage_Mods:
                yield
                
            case ItemAction.Salvage_Common_Materials:
                yield
                
            case ItemAction.Salvage_Rare_Materials:
                yield
                
            case _:
                return None
    
    def get_items(self):
        start_bag : Bag = Bag.Storage_1
        end_bag : Bag = Bag.Storage_13 if not self.anniversary_tab else Bag.Storage_14
        inventory_array, inventory_sizes = GetZeroFilledBags(start_bag, end_bag)
        
        items = []
        for item_id in inventory_array:
            if item_id != 0:
                items.append(ITEM_CACHE.get_item_snapshot(item_id))
        
        return items
    
    def get_materialstorage_items(self):
        start_bag : Bag = Bag.Material_Storage
        end_bag : Bag = Bag.Material_Storage
        inventory_array, inventory_sizes = GetZeroFilledBags(start_bag, end_bag)
        
        items = []
        for item_id in inventory_array:
            if item_id != 0:
                items.append(ITEM_CACHE.get_item_snapshot(item_id))
        
        return items
    
    def compact_xunlai_storage(self):
        # This function should implement the logic to compact the inventory by moving items around to fill empty slots
        # You would need to implement the actual logic for compacting the inventory here
        
        # While there are multiple stacks of the same item, move them into one stack until we reach the max stack size for that item
        items = self.get_items()
        material_storage_items = self.get_materialstorage_items()
        
        # Move items from storage to material storage if they are materials and we have space in material storage
        
        yield
    
    def sort_xunlai_storage(self):
        # This function should implement the logic to sort the inventory based on certain criteria (e.g., item type, rarity, etc.)
        # You would need to implement the actual logic for sorting the inventory here
        
        # Sort all items in the inventory by the inventory sorting configuration
        items = self.get_items()
        
        yield
    
    def start(self):
        self.enabled = True
    
    def stop(self):
        self.yield_action = None
        self.enabled = False