from typing import Optional

import Py4GW
from PyItem import ItemModifier

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.enums_src.Item_enums import Rarity
from Sources.frenkeyLib.ItemHandling.Mods.item_modifier_parser import ItemModifierParser
from Sources.frenkeyLib.ItemHandling.Mods.properties import InscriptionProperty, ItemProperty, PrefixProperty, SuffixProperty
from Sources.frenkeyLib.ItemHandling.Mods.types import ItemUpgradeType
from Sources.frenkeyLib.ItemHandling.Mods.upgrades import Upgrade


class ItemMod:
    @staticmethod
    def validated_upgrades(rarity : Optional[Rarity] = None, prefix: Upgrade | None = None, suffix: Upgrade | None = None, inscription: Upgrade | None = None) -> tuple[Upgrade | None, Upgrade | None, Upgrade | None]:
        if rarity != Rarity.Green:
            return prefix, suffix, inscription
        
        if prefix:
            prefix.is_inherent = True
        
        if suffix:
            suffix.is_inherent = True
        
        if inscription:
            inscription.is_inherent = True
        
        return prefix, suffix, inscription
    
    @staticmethod
    def get_item_upgrades(item_id : int) -> tuple[Upgrade | None, Upgrade | None, Upgrade | None]:
        from Sources.frenkeyLib.ItemHandling.Items.ItemCache import ITEM_CACHE
        
        item = ITEM_CACHE.get_item_snapshot(item_id)
        rarity = item.rarity if item else Rarity.Blue
        runtime_modifiers = item.modifiers if item else []
        
        return ItemMod.get_item_upgrades_from_modifiers(runtime_modifiers, rarity)
    
    @staticmethod
    def get_item_upgrades_from_modifiers(runtime_modifiers : list[ItemModifier], rarity: Rarity = Rarity.Blue) -> tuple[Upgrade | None, Upgrade | None, Upgrade | None]:
        parser = ItemModifierParser(runtime_modifiers, rarity)
        properties = parser.get_properties()
        
        return ItemMod.get_item_upgrades_from_properties(properties, rarity)
    
    @staticmethod
    def get_item_upgrades_from_properties(properties : list[ItemProperty], rarity: Rarity = Rarity.Blue) -> tuple[Upgrade | None, Upgrade | None, Upgrade | None]:
        if not properties:
            return None, None, None
        
        prefix_prop = next((p for p in properties if isinstance(p, PrefixProperty) and p.upgrade.mod_type == ItemUpgradeType.Prefix), None)
        suffix_prop = next((s for s in properties if isinstance(s, SuffixProperty) and s.upgrade.mod_type == ItemUpgradeType.Suffix), None)
        inscription_prop = next((i for i in properties if isinstance(i, InscriptionProperty) and i.upgrade.mod_type == ItemUpgradeType.Inscription), None)
        
        prefix : Upgrade | None = prefix_prop.upgrade if prefix_prop else None
        suffix : Upgrade | None = suffix_prop.upgrade if suffix_prop else None
        inscription : Upgrade | None = inscription_prop.upgrade if inscription_prop else None
        
        return ItemMod.validated_upgrades(rarity, prefix, suffix, inscription)
        
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