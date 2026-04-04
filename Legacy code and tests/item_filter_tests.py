from PyItem import PyItem

from Py4GWCoreLib.Item import Bag, Item
from Py4GWCoreLib.ItemArray import ItemArray
from Py4GWCoreLib.enums_src.GameData_enums import DyeColor
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Py4GWCoreLib.item_mods_src.upgrades import VampiricStrengthUpgrade
from Py4GWCoreLib.native_src.internals import string_table
from Py4GWCoreLib.ItemMods import *

from Sources.frenkeyLib.ItemHandling.GlobalConfigs.LootConfig import LootConfig
from Sources.frenkeyLib.ItemHandling.GlobalConfigs.SalvageConfig import SalvageConfig

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
            
        if (vampiric_strength_upgrade := ItemMod.get_upgrade(item_id, VampiricStrengthUpgrade)) is not None:
            damage = vampiric_strength_upgrade.damage_increase
            degen = vampiric_strength_upgrade.health_regeneration
            is_maxed = vampiric_strength_upgrade.is_maxed
            
            print(f"Item '{string_table.decode(bytes(PyItem.GetCompleteNameEnc(item_id)))}' ({item_id}) has a vampiric strength upgrade (Damage: {damage}%, Health Degeneration: -{degen}).")

LOOT_CONFIG = LootConfig()
SALVAGE_CONFIG = SalvageConfig()

LOOT_CONFIG.AddDyeColor(DyeColor.Black)
LOOT_CONFIG.AddDyeColor(DyeColor.White)
            
SALVAGE_CONFIG.AddItemType(ItemType.Axe)
SALVAGE_CONFIG.AddItemType(ItemType.Sword)
SALVAGE_CONFIG.AddItemType(ItemType.Sword)
SALVAGE_CONFIG.AddItemType(ItemType.Staff)
SALVAGE_CONFIG.AddItemType(ItemType.Scythe)


def main():
    # filter_dyes_test()
    # filter_weapon_mods_test()
    
    print(f"Lootconfig has {len(LootConfig())} rules.")
    print(f"Salvageconfig has {len(SalvageConfig())} rules.")
    
if __name__ == "__main__":
    main()