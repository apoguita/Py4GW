from Py4GWCoreLib.Item import Item
from Py4GWCoreLib.enums_src.GameData_enums import DyeColor
from Py4GWCoreLib.item_mods_src.item_mod import ItemMod
from Py4GWCoreLib.item_mods_src.upgrades import *

class DyeFilter:
    @staticmethod     
    def is_dye(item_id: int, color: DyeColor) -> bool:
        item_color = Item.GetDyeColor(item_id)
        item_type, _ = Item.GetItemType(item_id)
        
        return item_type == ItemType.Dye and item_color == color

class WeaponModFilter:
    @staticmethod
    def is_weapon_mod(item_id: int, mod_type : type, max : bool = False) -> bool:
        prefix, suffix, inscription = ItemMod.get_item_upgrades(item_id)
        
        
        return isinstance(prefix, mod_type) or isinstance(suffix, mod_type) or isinstance(inscription, mod_type)
