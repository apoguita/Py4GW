from typing import Optional, Type, cast

from PyItem import ItemModifier

from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.item_mods_src.item_modifier_parser import ItemModifierParser
from Py4GWCoreLib.item_mods_src.properties import InherentProperty, InscriptionProperty, ItemProperty, PrefixProperty, SuffixProperty, TargetItemTypeProperty
from Py4GWCoreLib.item_mods_src._typing import TUpgrade
from Py4GWCoreLib.item_mods_src.types import ItemUpgradeType
from Py4GWCoreLib.item_mods_src.upgrades import Upgrade
from Py4GWCoreLib.py4gwcorelib_src.FrameCache import frame_cache

class ItemMod:
    @staticmethod
    def _same_enum_identity(left: object, right: object) -> bool:
        if left is right:
            return True

        left_type = type(left)
        right_type = type(right)
        return (
            left_type.__module__ == right_type.__module__
            and left_type.__qualname__ == right_type.__qualname__
            and getattr(left, 'name', None) == getattr(right, 'name', None)
            and getattr(left, 'value', None) == getattr(right, 'value', None)
        )

    @staticmethod
    def _same_upgrade_type(candidate: Upgrade, expected_type: type[Upgrade]) -> bool:
        candidate_type = type(candidate)
        if candidate_type is expected_type:
            return True

        return (
            candidate_type.__module__ == expected_type.__module__
            and candidate_type.__qualname__ == expected_type.__qualname__
            and ItemMod._same_enum_identity(getattr(candidate_type, 'id', None), getattr(expected_type, 'id', None))
            and ItemMod._same_enum_identity(getattr(candidate_type, 'mod_type', None), getattr(expected_type, 'mod_type', None))
        )

    @staticmethod
    def _same_upgrade_value(left: object, right: object) -> bool:
        left_comparison_data = getattr(left, '_comparison_data', None)
        right_comparison_data = getattr(right, '_comparison_data', None)
        return (
            callable(left_comparison_data)
            and callable(right_comparison_data)
            and left_comparison_data() == right_comparison_data()
        )

    @staticmethod
    def get_upgrade(item_id : int, upgrade: Type[TUpgrade] | TUpgrade | Upgrade) -> Optional[TUpgrade]:
        '''
        Gets the upgrade of the specified type from the item properties. This is a helper method that combines the logic of getting the item modifiers, parsing them into properties, and extracting the relevant upgrade property. It also includes validation for inherent upgrades on green items.
        Recommended usage is with an assignment expression to avoid unnecessary processing if the upgrade is not present or of the wrong type.
        Example usage:
        
        if (upgrade := ItemMod.get_upgrade(item_id, FuriousUpgrade)) is not None and upgrade.chance == 20:
            ...do something with the furious upgrade  
        '''
        
        prefix, suffix, inscription, inherent = ItemMod.get_item_upgrades(item_id)
        desired_upgrade = None if isinstance(upgrade, type) else upgrade
        desired_upgrade_type = upgrade if isinstance(upgrade, type) else type(upgrade)

        def find_match(candidate: Upgrade | None) -> Optional[TUpgrade]:
            if candidate is None:
                return None

            if not ItemMod._same_upgrade_type(candidate, desired_upgrade_type):
                return None

            if desired_upgrade is not None and not ItemMod._same_upgrade_value(candidate, desired_upgrade):
                return None

            return cast(TUpgrade, candidate)

        if (matched_prefix := find_match(prefix)) is not None:
            return matched_prefix

        if (matched_suffix := find_match(suffix)) is not None:
            return matched_suffix

        if (matched_inscription := find_match(inscription)) is not None:
            return matched_inscription

        for inh in inherent or []:
            if (matched_inherent := find_match(inh)) is not None:
                return matched_inherent
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
    @frame_cache(category="ItemMod", source_lib="get_item_upgrades")
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
    @frame_cache(category="ItemMod", source_lib="get_target_item_type")
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
