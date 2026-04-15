import os

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

def filter_dyes_test(item_ids: list[int]):
    for item_id in item_ids:
        if Item.Filter.Dye.IsDyeColor(item_id, DyeColor.Red):
            print(f"Item '{string_table.decode(bytes(PyItem.GetCompleteNameEnc(item_id)))}' ({item_id}) is a red dye.")
            
upgrade = OfDevotionUpgrade(health=45)

def filter_weapon_mods_test(item_ids: list[int]):
    for item_id in item_ids:          
        if Item.Filter.Upgrade.HasUpgradeType(item_id, SunderingUpgrade):
            if (sundering_upgrade := Item.Customization.GetUpgrade(item_id, SunderingUpgrade)) is not None:
                print(f"Item '{string_table.decode(bytes(PyItem.GetCompleteNameEnc(item_id)))}' ({item_id}) has a sundering upgrade ({sundering_upgrade.chance}%).")
                
        if Item.Filter.Upgrade.HasUpgrade(item_id, upgrade):
            if (item_upgrade := Item.Customization.GetUpgrade(item_id, type(upgrade))) is not None:
                print(f"Item '{string_table.decode(bytes(PyItem.GetCompleteNameEnc(item_id)))}' ({item_id}) has an upgrade: {item_upgrade.display_summary}.")
         
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

folder_path = os.path.join(Py4GW.Console.get_projects_path(), "Settings", "item_filters")

LOOT_CONFIG = LootConfig()
SALVAGE_CONFIG = SalvageConfig()

LOOT_CONFIG.Load(os.path.join(folder_path, "loot_config.json"))
SALVAGE_CONFIG.Load(os.path.join(folder_path, "salvage_config.json"))

if len(LOOT_CONFIG) == 0:
    LOOT_CONFIG.AddRarities([Rarity.Gold])
    LOOT_CONFIG.AddItemTypes([item_type for item_type in ItemType if item_type not in [ItemType.Unknown, ItemType.Bundle]])
    LOOT_CONFIG.AddDyeColor(DyeColor.Black)
    LOOT_CONFIG.AddDyeColor(DyeColor.White)    

if True or len(SALVAGE_CONFIG) == 0:
    SALVAGE_CONFIG.AddRarities([Rarity.White, Rarity.Blue, Rarity.Purple])
    SALVAGE_CONFIG.AddItemType(ItemType.Sword)
    SALVAGE_CONFIG.AddItemType(ItemType.Spear)
    SALVAGE_CONFIG.AddItemTypes([ItemType.Staff, ItemType.Wand, ItemType.Offhand])
    SALVAGE_CONFIG.AddUpgrades([
        OfDaggerMasteryUpgrade(chance=20),
        (OfTheProfessionUpgrade(attribute=Attribute.CriticalStrikes), [ItemType.Bow]),
        ])

LOOT_CONFIG.Save(os.path.join(folder_path, "loot_config.json"))
SALVAGE_CONFIG.Save(os.path.join(folder_path, "salvage_config.json"))

fortitude = OfFortitudeUpgrade(health=30)

fortitude2 = OfFortitudeUpgrade()
fortitude2.health = 30


throttle = ThrottledTimer(500)  # 1 second throttle

def loot_config_test(item_ids: list[int]):
    for item_id in item_ids:
        if LOOT_CONFIG.EvaluateItem(item_id):
            print(f"Item '{string_table.decode(bytes(PyItem.GetCompleteNameEnc(item_id)))}' ({item_id}) passed the loot filter.")

def salvage_config_test(item_ids: list[int]):
    for item_id in item_ids:
        if SALVAGE_CONFIG.EvaluateItem(item_id):
            print(f"Item '{string_table.decode(bytes(PyItem.GetCompleteNameEnc(item_id)))}' ({item_id}) passed the salvage filter.")

def main():
    if not throttle.IsExpired():
        return
    
    throttle.Reset()
    
    item_ids = ItemArray.GetItemArray([Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2])
    
    # filter_dyes_test(item_ids)
    # filter_weapon_mods_test(item_ids)
    
    # loot_config_test(item_ids)
    salvage_config_test(item_ids)
    
    
    # print(f"Lootconfig has {len(LootConfig())} rules.")
    # print(f"Salvageconfig has {len(SalvageConfig())} rules.")
    
if __name__ == "__main__":
    main()