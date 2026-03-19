from typing import Optional

import Py4GW
import PyInventory
from PyItem import PyItem

from Py4GWCoreLib.Item import Bag
from Sources.frenkeyLib.ItemHandling.Items.item_snapshot import ItemSnapshot

class ItemCache:
    def __init__(self):
        self.items : dict[int, ItemSnapshot] = {}
        self.inventory : dict[Bag, dict[int, Optional[ItemSnapshot]]] = {}
    
    def reset(self):
        self.items = {}
        self.inventory = {}
    
    def get_item_snapshot(self, item_id: int, item_instance: Optional[PyItem] = None) -> Optional[ItemSnapshot]:
        if item_id <= 0:
            return None
        
        if item_id not in self.items:
            snapshot = ItemSnapshot.create(item_id, item_instance)
            
            if not snapshot or not snapshot.is_valid:
                return None
            
            self.items[item_id] = snapshot
        # else:
        #     self.items[item_id].update()
            
        return self.items[item_id]
    
    def get_bag_snapshot(self, bag: Bag) -> dict[int, Optional[ItemSnapshot]]:
        if bag not in self.inventory:                
            inventory_bag = PyInventory.Bag(bag.value, bag.name)
            bag_snapshot: dict[int, Optional[ItemSnapshot]] = {}

            bag_size = inventory_bag.GetSize()

            for slot in range(bag_size):
                bag_snapshot[slot] = None

            for item in inventory_bag.GetItems():
                slot = item.slot  # real slot of the item
                bag_snapshot[slot] = self.get_item_snapshot(
                    item.item_id,
                    item
                )

            self.inventory[bag] = bag_snapshot
        
        return self.inventory[bag]
    
    def get_inventory_snapshot(self, start_bag: Bag, end_bag: Bag) -> dict[Bag, dict[int, Optional[ItemSnapshot]]]:
        bags = [Bag(bag_id) for bag_id in range(start_bag.value, end_bag.value + 1)]
        return self.get_bags_snapshot(bags)
    
    def get_bags_snapshot(self, bags: list[Bag]) -> dict[Bag, dict[int, Optional[ItemSnapshot]]]:
        snapshot = {}

        for bag in bags:
            snapshot[bag] = self.get_bag_snapshot(bag)

        return snapshot

ITEM_CACHE = ItemCache()