from typing import Optional, Type, TypeVar

from PyItem import ItemModifier

from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.item_mods_src.item_modifier_parser import ItemModifierParser
from Py4GWCoreLib.item_mods_src.properties import InherentProperty, InscriptionProperty, ItemProperty, PrefixProperty, SuffixProperty, TargetItemTypeProperty
from Py4GWCoreLib.item_mods_src.types import ItemUpgradeType
from Py4GWCoreLib.item_mods_src.upgrades import Upgrade

class ItemMod:
    T = TypeVar("T", bound="Upgrade")

    @staticmethod
    def get_upgrade(item_id : int, upgrade_type: Type[T]) -> Optional[T]:
        '''
        Gets the upgrade of the specified type from the item properties. This is a helper method that combines the logic of getting the item modifiers, parsing them into properties, and extracting the relevant upgrade property. It also includes validation for inherent upgrades on green items.
        Recommended usage is with an assignment expression to avoid unnecessary processing if the upgrade is not present or of the wrong type.
        Example usage:
        
        if (upgrade := ItemMod.get_upgrade(item_id, FuriousUpgrade)) is not None and upgrade.chance == 20:
            ...do something with the furious upgrade  
        '''
        
        prefix, suffix, inscription, inherent = ItemMod.get_item_upgrades(item_id)

        if prefix and isinstance(prefix, upgrade_type):
            return prefix

        if suffix and isinstance(suffix, upgrade_type):
            return suffix

        if inscription and isinstance(inscription, upgrade_type):
            return inscription
        
        for inh in inherent or []:
            if inh and isinstance(inh, upgrade_type):
                return inh

        return None
    
    @staticmethod
    def validated_upgrades(rarity : Optional[Rarity | int] = None, prefix: Upgrade | None = None, suffix: Upgrade | None = None, inscription: Upgrade | None = None, inherent: list[Upgrade] | None = None) -> tuple[Upgrade | None, Upgrade | None, Upgrade | None, list[Upgrade] | None]:
        if rarity != Rarity.Green:
            return prefix, suffix, inscription, inherent
        
        if prefix:
            prefix.is_inherent = True
        
        if suffix:
            suffix.is_inherent = True
        
        if inscription:
            inscription.is_inherent = True
        
        return prefix, suffix, inscription, inherent
    
    @staticmethod
    def get_item_upgrades(item_id : int) -> tuple[Upgrade | None, Upgrade | None, Upgrade | None, list[Upgrade] | None]:
        '''
        Gets the item upgrades from the item properties. This method combines the logic of getting the item modifiers, parsing them into properties,
        and extracting the relevant upgrade properties. It also includes validation for inherent upgrades on green items.
        '''
        from Py4GWCoreLib.Item import Item
        
        rarity, _ = Item.Rarity.GetRarity(item_id)
        runtime_modifiers = Item.Customization.Modifiers.GetModifiers(item_id)
        
        return ItemMod.get_item_upgrades_from_modifiers(runtime_modifiers, rarity)
    
    @staticmethod
    def get_item_upgrades_from_modifiers(runtime_modifiers : list[ItemModifier], rarity: Rarity | int = Rarity.Blue) -> tuple[Upgrade | None, Upgrade | None, Upgrade | None, list[Upgrade] | None]:
        parser = ItemModifierParser(runtime_modifiers, rarity)
        properties = parser.get_properties()
        
        return ItemMod.get_item_upgrades_from_properties(properties, rarity)
    
    @staticmethod
    def get_item_upgrades_from_properties(properties : list[ItemProperty], rarity: Rarity | int = Rarity.Blue) -> tuple[Upgrade | None, Upgrade | None, Upgrade | None, list[Upgrade] | None]:
        if not properties:
            return None, None, None, None
        
        prefix_prop = next((p for p in properties if isinstance(p, PrefixProperty) and p.upgrade.mod_type == ItemUpgradeType.Prefix), None)
        suffix_prop = next((s for s in properties if isinstance(s, SuffixProperty) and s.upgrade.mod_type == ItemUpgradeType.Suffix), None)
        inscription_prop = next((i for i in properties if isinstance(i, InscriptionProperty) and i.upgrade.mod_type == ItemUpgradeType.Inscription), None)
        inherent_props = [p for p in properties if isinstance(p, InherentProperty) and p.upgrade.mod_type == ItemUpgradeType.Inherent]
        
        prefix : Upgrade | None = prefix_prop.upgrade if prefix_prop else None
        suffix : Upgrade | None = suffix_prop.upgrade if suffix_prop else None
        inscription : Upgrade | None = inscription_prop.upgrade if inscription_prop else None
        inherent : list[Upgrade] | None = [p.upgrade for p in inherent_props] if inherent_props else None
        
        return ItemMod.validated_upgrades(rarity, prefix, suffix, inscription, inherent)
    
    @staticmethod
    def get_target_item_type(item_id: int) -> Optional[ItemType]:
        '''
        Gets the target item type for an upgrade on the item, which is used for validating item type requirements on upgrades. This method checks all upgrades on the item for a specified target item type, and returns the first one it finds. If no target item type is found on any upgrade, it returns None.
        '''                
        from Py4GWCoreLib.Item import Item
        
        rarity, _ = Item.Rarity.GetRarity(item_id)
        runtime_modifiers = Item.Customization.Modifiers.GetModifiers(item_id)
        
        parser = ItemModifierParser(runtime_modifiers, rarity)
        properties = parser.get_properties()
        target_item_type_prop = next((p for p in properties if isinstance(p, TargetItemTypeProperty)), None)
        
        return target_item_type_prop.item_type if target_item_type_prop else None