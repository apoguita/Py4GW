from typing import Generator, Optional

import Py4GW

from Py4GWCoreLib.Item import Bag
from Sources.frenkeyLib.ItemHandling.Items.item_snapshot import ItemSnapshot
from Sources.frenkeyLib.ItemHandling.Rules.profile import RuleProfile
from Sources.frenkeyLib.ItemHandling.Rules.types import ACTION_LIMITS_PER_FRAME, ItemAction
from Sources.frenkeyLib.ItemHandling.utility import GetZeroFilledBags

class InventoryHandler:
    def __init__(self):
        self.enabled: bool = False
        
        self.yield_action : Optional[Generator] = None        
        self.rules : RuleProfile = RuleProfile.load_by_name("Default Inventory Rules")
        
        self.inventory_sorting_config = None  # You would need to define what this is and how it works based on your requirements
    
    def run(self):
        if not self.enabled:
            return
        
        start_bag : Bag = Bag.Backpack
        end_bag : Bag = Bag.Bag_2
        inventory_array, inventory_sizes = GetZeroFilledBags(start_bag, end_bag)
        
        for item_id in inventory_array:
            if item_id == 0:
                continue
            
            action = self.rules.get_action_for_item(item_id)
            item = ItemSnapshot.from_item_id(item_id) if item_id else None  # Ensure the item snapshot is cached for future reference
            
            if item is None:
                continue
            
            if action != ItemAction.NONE:                  
                if action in ACTION_LIMITS_PER_FRAME:
                    # If we don't have an action in progress and the new action is a yield based action, start it                
                    if self.yield_action is None:
                        # Start the action and store the generator
                        generator = self.get_generator_for_action(item_id, action)
                        if generator is not None:
                            self.yield_action = generator
                    
                else:
                    match action:
                        case ItemAction.Destroy:
                            Py4GW.Console.Log("InventoryHandler", f"Destroying item {item_id}", Py4GW.Console.MessageType.Info)        
                            # Inventory.DestroyItem(item_id)
                        
                        case ItemAction.Identify:
                            Py4GW.Console.Log("InventoryHandler", f"Identifying item {item_id}", Py4GW.Console.MessageType.Info)        
                            # Inventory.IdentifyItem(item_id)
                        
                        case ItemAction.Use:
                            Py4GW.Console.Log("InventoryHandler", f"Using item {item_id} {item.quantity} times", Py4GW.Console.MessageType.Info)     
                            for _ in range(item.quantity):   
                                # Inventory.UseItem(item_id)
                                pass
                
                continue
        
        # Compact and Sort inventory whenever .... ??
        
        # Handle all yield based actions (ACTION_LIMITS_PER_FRAME)
        if self.yield_action is not None:
            try:
                yield from self.yield_action
                
            except StopIteration:
                self.yield_action = None
        else:
            yield from self.compact_inventory()
            yield from self.sort_inventory()
            
        
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
    
    def compact_inventory(self):
        # This function should implement the logic to compact the inventory by moving items around to fill empty slots
        # You would need to implement the actual logic for compacting the inventory here
        
        # While there are multiple stacks of the same item, move them into one stack until we reach the max stack size for that item
        yield
    
    def sort_inventory(self):
        # This function should implement the logic to sort the inventory based on certain criteria (e.g., item type, rarity, etc.)
        # You would need to implement the actual logic for sorting the inventory here
        
        # Sort all items in the inventory by the inventory sorting configuration
        yield
    
    def start(self):
        self.enabled = True
    
    def stop(self):
        self.yield_action = None
        self.enabled = False