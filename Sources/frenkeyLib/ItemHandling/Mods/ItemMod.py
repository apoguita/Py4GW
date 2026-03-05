from PyItem import ItemModifier

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Item import Item
from Sources.frenkeyLib.ItemHandling.Mods.item_modifier_parser import ItemModifierParser
from Sources.frenkeyLib.ItemHandling.Mods.properties import InscriptionProperty, ItemProperty, PrefixProperty, SuffixProperty
from Sources.frenkeyLib.ItemHandling.Mods.types import ItemUpgradeType
from Sources.frenkeyLib.ItemHandling.Mods.upgrades import Upgrade


class ItemMod:
    @staticmethod
    def get_item_upgrades(item_id : int) -> tuple[Upgrade | None, Upgrade | None, Upgrade | None]:
        runtime_modifiers = Item.Customization.Modifiers.GetModifiers(item_id)
        parser = ItemModifierParser(runtime_modifiers)
        properties = parser.get_properties()
        
        prefix = next((p for p in properties if isinstance(p, PrefixProperty) and p.upgrade.mod_type == ItemUpgradeType.Prefix), None)
        suffix = next((s for s in properties if isinstance(s, SuffixProperty) and s.upgrade.mod_type == ItemUpgradeType.Suffix), None)
        inscription = next((i for i in properties if isinstance(i, InscriptionProperty) and i.upgrade.mod_type == ItemUpgradeType.Inscription), None)

        return prefix.upgrade if prefix else None, suffix.upgrade if suffix else None, inscription.upgrade if inscription else None
    
    @staticmethod
    def get_item_upgrades_from_modifiers(runtime_modifiers : list[ItemModifier]) -> tuple[Upgrade | None, Upgrade | None, Upgrade | None]:
        parser = ItemModifierParser(runtime_modifiers)
        properties = parser.get_properties()
        
        prefix = next((p for p in properties if isinstance(p, PrefixProperty) and p.upgrade.mod_type == ItemUpgradeType.Prefix), None)
        suffix = next((s for s in properties if isinstance(s, SuffixProperty) and s.upgrade.mod_type == ItemUpgradeType.Suffix), None)
        inscription = next((i for i in properties if isinstance(i, InscriptionProperty) and i.upgrade.mod_type == ItemUpgradeType.Inscription), None)

        return prefix.upgrade if prefix else None, suffix.upgrade if suffix else None, inscription.upgrade if inscription else None
    
    @staticmethod
    def get_item_upgrades_from_properties(properties : list[ItemProperty]) -> tuple[Upgrade | None, Upgrade | None, Upgrade | None]:
        prefix = next((p for p in properties if isinstance(p, PrefixProperty) and p.upgrade.mod_type == ItemUpgradeType.Prefix), None)
        suffix = next((s for s in properties if isinstance(s, SuffixProperty) and s.upgrade.mod_type == ItemUpgradeType.Suffix), None)
        inscription = next((i for i in properties if isinstance(i, InscriptionProperty) and i.upgrade.mod_type == ItemUpgradeType.Inscription), None)

        return prefix.upgrade if prefix else None, suffix.upgrade if suffix else None, inscription.upgrade if inscription else None
    
    @staticmethod
    def get_item_name_without_upgrades(item_id : int) -> str:
        item_name = GLOBAL_CACHE.Item.GetName(item_id)
        prefix, suffix, _ = ItemMod.get_item_upgrades(item_id)
        item_name = ItemMod.remove_upgrades_from_item_name(item_name, prefix, suffix)
        
        return item_name
    
    @staticmethod
    def get_item_name_with_upgrades(item_id : int) -> str:
        item_name = GLOBAL_CACHE.Item.GetName(item_id)
        prefix, suffix, _ = ItemMod.get_item_upgrades(item_id)
        item_name = ItemMod.apply_upgrades_to_item_name(item_name, prefix, suffix)
        
        return item_name
    
    @staticmethod
    def apply_upgrades_to_item_name(item_name : str, prefix : Upgrade | None, suffix : Upgrade | None) -> str:
        if prefix and hasattr(prefix, "apply_to_item_name"):
            item_name = prefix.apply_to_item_name(item_name) # type: ignore
            
        if suffix and hasattr(suffix, "apply_to_item_name"):
            item_name = suffix.apply_to_item_name(item_name) # type: ignore
            
        return item_name
    
    @staticmethod
    def remove_upgrades_from_item_name(item_name : str, prefix : Upgrade | None, suffix : Upgrade | None) -> str:
        if prefix and hasattr(prefix, "remove_from_item_name"):
            item_name = prefix.remove_from_item_name(item_name) # type: ignore
            
        if suffix and hasattr(suffix, "remove_from_item_name"):
            item_name = suffix.remove_from_item_name(item_name) # type: ignore
            
        return item_name