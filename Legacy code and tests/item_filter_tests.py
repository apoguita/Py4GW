from PyItem import PyItem

from Py4GWCoreLib.Item import Bag
from Py4GWCoreLib.ItemArray import ItemArray
from Py4GWCoreLib.enums_src.GameData_enums import DyeColor
from Sources.frenkeyLib.ItemHandling.Filters.filter import *
from Py4GWCoreLib.ItemMods import *

def filter_dyes_test():
    item_ids = ItemArray.GetItemArray([Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2])
    
    for item_id in item_ids:
        if Item.Filter.Dye.IsDyeColor(item_id, DyeColor.Red):
            print(f"Item '{string_table.decode(bytes(PyItem.GetCompleteNameEnc(item_id)))}' ({item_id}) is a red dye.")
            

def filter_weapon_mods_test():
    item_ids = ItemArray.GetItemArray([Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2])
    
    for item_id in item_ids:          
        if Item.Filter.Upgrade.HasUpgrade(item_id, SunderingUpgrade):
            if (sundering_upgrade := Item.Customization.GetUpgrade(item_id, SunderingUpgrade)) is not None:
                print(f"Item '{string_table.decode(bytes(PyItem.GetCompleteNameEnc(item_id)))}' ({item_id}) has a sundering upgrade ({sundering_upgrade.chance}%).")
         
        if (sundering_upgrade := ItemMod.get_upgrade(item_id, SunderingUpgrade)) is not None:
            chance = sundering_upgrade.chance
            is_maxed = sundering_upgrade.is_maxed
            armor_pen = sundering_upgrade.armor_penetration
            
        if (fortitude_upgrade := ItemMod.get_upgrade(item_id, OfFortitudeUpgrade)) is not None:
            health = fortitude_upgrade.health
            is_maxed = fortitude_upgrade.is_maxed
            
            
def main():
    filter_dyes_test()
    filter_weapon_mods_test()
    
    
if __name__ == "__main__":
    main()