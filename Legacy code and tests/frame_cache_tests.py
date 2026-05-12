import os
from time import time

import Py4GW
from PyItem import PyItem

from Py4GWCoreLib.Item import Bag, Item
from Py4GWCoreLib.ItemArray import ItemArray
from Py4GWCoreLib.enums_src.GameData_enums import Attribute, DyeColor, Profession
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.item_mods_src.upgrades import VampiricStrengthUpgrade
from Py4GWCoreLib.native_src.internals import string_table
from Py4GWCoreLib.ItemMods import *

from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Sources.frenkeyLib.ItemHandling.GlobalConfigs.LootConfig import LootConfig
from Sources.frenkeyLib.ItemHandling.GlobalConfigs.SalvageConfig import SalvageConfig
from Sources.frenkeyLib.ItemHandling.Items.item_snapshot import ItemSnapshot

class StopWatch:
    def __init__(self):
        self.start_time = time()

    def reset(self):
        self.start_time = time()

    def elapsed(self):
        return time() - self.start_time
    
stpwtch1 = StopWatch()
stpwtch2 = StopWatch()
stpwtch3 = StopWatch()

throttle = ThrottledTimer(250)

script_run = False
def main(): 
    global script_run
       
    if script_run:
        return
    
    if not throttle.IsExpired():
        return
    
    throttle.Reset()
    
    
    for l in range(3):
        stpwtch1.reset()
        item_ids = ItemArray.GetItemArray([Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2])
        print(f"[stpwtch1] [Loop {l}] Retrieved {len(item_ids)} item IDs in {stpwtch1.elapsed():.4f} seconds.")
        
        # stpwtch2.reset()
        # for item_id in item_ids:
        #     item = ItemSnapshot(item_id)
        #     # print(f"Item ID: {item_id}, Name: {item.name}, Rarity: {item.rarity.name}, Type: {item.item_type.name}")
            
        # print(f"[stpwtch2] [Loop {l}] Created {len(item_ids)} item snapshots in {stpwtch2.elapsed():.4f} seconds.")
        
        stpwtch2.reset()
        for item_id in item_ids:
            item : ItemSnapshot = ItemSnapshot.from_item_id(item_id)
            # print(f"Item ID: {item_id}, Name: {item.name}, Rarity: {item.rarity.name}, Type: {item.item_type.name}")
            if item.has_upgrades:
                print(f"Item ID: {item_id}, Name: {item.name}, Rarity: {item.rarity.name}, Type: {item.item_type.name}, Has Upgrades: Prefix: {item.prefix.name if item.prefix else None}, Suffix: {item.suffix.name if item.suffix else None}, Inherent: {item.inherent}, Inscription: {item.inscription.name if item.inscription else None}")
                
        print(f"[stpwtch2] [Loop {l}] Created {len(item_ids)} lazy item snapshots using from_item_id in {stpwtch2.elapsed():.4f} seconds.")
            
        stpwtch3.reset()
        for item_id in item_ids:
            item = ItemSnapshot.from_item_id(item_id)
            print(f"Item ID: {item_id}, Name: {item.name}, Rarity: {item.rarity.name}, Type: {item.item_type.name}")
            
        print(f"[stpwtch3] [Loop {l}] Created {len(item_ids)} item snapshots using from_item_id in {stpwtch3.elapsed():.4f} seconds.")

    
    print("Done.")
    script_run = False
    
if __name__ == "__main__":
    main()