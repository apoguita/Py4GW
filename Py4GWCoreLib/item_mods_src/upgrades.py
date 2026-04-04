from enum import IntEnum
import re
from typing import Optional, TypeAlias, cast

import Py4GW
from PyItem import ItemModifier

from Py4GWCoreLib.enums_src.GameData_enums import Attribute, AttributeNames, Profession
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.native_src.internals import string_table
from Py4GWCoreLib.item_mods_src.decoded_modifier import DecodedModifier
from Py4GWCoreLib.item_mods_src.properties import ItemProperty
from Py4GWCoreLib.item_mods_src.types import ItemBaneSpecies, ItemModifierParam, ItemUpgrade, ItemUpgradeId, ItemUpgradeType, ModifierIdentifier
from Py4GWCoreLib.native_src.internals.encoded_strings import GWStringEncoded, GWEncoded
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils

ModifierIdentifierSpec: TypeAlias = ModifierIdentifier | tuple[ModifierIdentifier, ...]

def any_of(*identifiers: ModifierIdentifier) -> ModifierIdentifierSpec:
    if not identifiers:
        raise ValueError("any_of requires at least one ModifierIdentifier")
    return identifiers

def _get_property_factory():
    from Py4GWCoreLib.item_mods_src.upgrade_parser import get_property_factory
    return get_property_factory()


def _humanize_identifier(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name).strip()

PERSISTENT = True

class ModifierType(IntEnum):
    None_ = 0
    Arg1 = 1
    Arg2 = 2
    Fixed = 3
    
class ModifierRange:
    def __init__(self, modifier_identifier : ModifierIdentifier, modifier_type : ModifierType, min_value: int, max_value: int):
        self.modifierIdentifier = modifier_identifier
        self.min_value = min_value
        self.max_value = max_value
        self.modifier_type = modifier_type
        
class Upgrade:
    """
    Abstract base class for item upgrades. Each specific upgrade type (e.g., Prefix, Suffix, Inscription) should inherit from this class and implement the necessary properties and methods.
    """
    mod_type : ItemUpgradeType
    rarity : Rarity = Rarity.Blue
    id: ItemUpgrade = ItemUpgrade.Unknown
    upgrade_id: ItemUpgradeId = ItemUpgradeId.Unknown
    property_identifiers: list[ModifierIdentifierSpec] = []
    properties: dict[ModifierIdentifier, ItemProperty] = {}
    max_modifier_values: dict[ModifierIdentifier, tuple[int, int]] = {}    
    
    encoded_name : bytes = bytes()
    encoded_description : bytes = bytes()    
    descriptions: dict[ServerLanguage, str] = {}
    
    modifier : Optional[DecodedModifier] = None
    __encoded_name: GWStringEncoded
    __encoded_description: GWStringEncoded
    
    def __init__(self):
        self.is_inherent = False
        self.language = ServerLanguage(string_table._loaded_language) if string_table._loaded_language in ServerLanguage._value2member_map_ else ServerLanguage.English
        
    @classmethod
    def _pre_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, all_modifiers: list[DecodedModifier], remaining_modifiers: list[DecodedModifier]) -> None:
        return None

    @classmethod
    def _post_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, all_modifiers: list[DecodedModifier], remaining_modifiers: list[DecodedModifier]) -> None:
        return None

    @staticmethod
    def _normalize_property_identifier_spec(identifier_spec: ModifierIdentifierSpec) -> tuple[ModifierIdentifier, ...]:
        if isinstance(identifier_spec, tuple):
            return identifier_spec
        return (identifier_spec,)

    @classmethod
    def _get_property_identifier_key(cls, identifier_spec: ModifierIdentifierSpec) -> ModifierIdentifier:
        return cls._normalize_property_identifier_spec(identifier_spec)[0]

    @classmethod
    def _format_property_identifier_spec(cls, identifier_spec: ModifierIdentifierSpec) -> str:
        identifiers = cls._normalize_property_identifier_spec(identifier_spec)
        return " OR ".join(identifier.name for identifier in identifiers)

    @classmethod
    def _match_property_modifiers(cls, modifiers: list[DecodedModifier]) -> Optional[list[tuple[ModifierIdentifier, DecodedModifier]]]:
        matched_modifiers: list[tuple[ModifierIdentifier, DecodedModifier]] = []
        used_modifiers: list[DecodedModifier] = []

        for identifier_spec in cls.property_identifiers:
            identifier_options = cls._normalize_property_identifier_spec(identifier_spec)
            prop_mod = next((m for m in modifiers if m not in used_modifiers and m.identifier in identifier_options), None)
            if prop_mod is None:
                return None

            matched_modifiers.append((cls._get_property_identifier_key(identifier_spec), prop_mod))
            used_modifiers.append(prop_mod)

        return matched_modifiers

    def _get_property_by_spec(self, identifier_spec: ModifierIdentifierSpec) -> Optional[ItemProperty]:
        for identifier in self._normalize_property_identifier_spec(identifier_spec):
            prop = self.properties.get(identifier)
            if prop is not None:
                return prop
        return None
    
    @classmethod
    def compose_from_modifiers(cls, mod : DecodedModifier, remaining_modifiers: list[DecodedModifier], all_modifiers: list[DecodedModifier], rarity: Rarity = Rarity.Blue) -> Optional["Upgrade"]:        
        upgrade = cls()
        upgrade.properties = {}
        upgrade.upgrade_id = mod.upgrade_id
        upgrade.rarity = rarity
        upgrade.modifier = mod

        cls._pre_compose(upgrade, mod, all_modifiers, remaining_modifiers)

        property_factory = _get_property_factory()
        matched_modifiers = cls._match_property_modifiers(remaining_modifiers)
        if matched_modifiers is None:
            for identifier_spec in upgrade.property_identifiers:
                identifier_options = cls._normalize_property_identifier_spec(identifier_spec)
                if not any(m.identifier in identifier_options for m in remaining_modifiers):
                    Py4GW.Console.Log("ItemHandling", f"Missing modifier for property {cls._format_property_identifier_spec(identifier_spec)} in upgrade {upgrade.__class__.__name__}. Upgrade composition failed.")
                    return None
            return None

        for prop_key, prop_mod in matched_modifiers:
            prop = property_factory.get(prop_mod.identifier, lambda m, _, rarity: ItemProperty(modifier=m, rarity=rarity))(prop_mod, remaining_modifiers, rarity)
            upgrade.properties[prop_key] = prop

        cls._post_compose(upgrade, mod, all_modifiers, remaining_modifiers)
        upgrade.__encoded_name = upgrade.create_encoded_name()
        upgrade.__encoded_description = upgrade.create_encoded_description()
        return upgrade

    @classmethod
    def has_id(cls, upgrade_id: ItemUpgradeId) -> bool:
        return cls.id.has_id(upgrade_id)

    @classmethod
    def _get_max_modifier_args(cls, identifier: ModifierIdentifier) -> Optional[tuple[int, int]]:
        args = cls.max_modifier_values.get(identifier)
        if args is not None:
            return args

        modifier_range_prop = getattr(cls, "modifier_range", None)
        modifier_range = cast(Optional[ModifierRange], modifier_range_prop) if isinstance(modifier_range_prop, ModifierRange) else None
        if modifier_range and modifier_range.modifierIdentifier == identifier:
            arg1 = 0
            arg2 = 0

            match modifier_range.modifier_type:
                case ModifierType.Arg1:
                    arg1 = modifier_range.max_value
                case ModifierType.Arg2 | ModifierType.Fixed:
                    arg2 = modifier_range.max_value
                case ModifierType.None_:
                    return None

            return arg1, arg2

        return None

    @classmethod
    def _create_synthetic_modifier(cls, identifier: ModifierIdentifier, arg1: int, arg2: int) -> DecodedModifier:
        return DecodedModifier(
            modifier=cast(ItemModifier, None),
            raw_identifier=0,
            identifier=identifier,
            param=cast(ItemModifierParam, 0),
            arg1=arg1,
            arg2=arg2,
            arg=(arg1 << 8) | arg2,
            raw_bits=0,
            upgrade_id=ItemUpgradeId.Unknown,
            flags=0,
        )

    @classmethod
    def _create_max_properties(cls, rarity: Rarity = Rarity.Blue) -> Optional[dict[ModifierIdentifier, ItemProperty]]:
        if not cls.property_identifiers:
            return {}
        modifiers: list[DecodedModifier] = []
        created_modifier_ids: set[ModifierIdentifier] = set()
        property_identifier_options = {
            identifier
            for identifier_spec in cls.property_identifiers
            for identifier in cls._normalize_property_identifier_spec(identifier_spec)
        }

        for identifier_spec in cls.property_identifiers:
            resolved_identifier: Optional[ModifierIdentifier] = None
            resolved_args: Optional[tuple[int, int]] = None

            for identifier in cls._normalize_property_identifier_spec(identifier_spec):
                args = cls._get_max_modifier_args(identifier)
                if args is not None:
                    resolved_identifier = identifier
                    resolved_args = args
                    break

            if resolved_identifier is None or resolved_args is None:
                return None

            if resolved_identifier not in created_modifier_ids:
                modifiers.append(cls._create_synthetic_modifier(resolved_identifier, resolved_args[0], resolved_args[1]))
                created_modifier_ids.add(resolved_identifier)

        for identifier, args in cls.max_modifier_values.items():
            if identifier in created_modifier_ids or identifier in property_identifier_options:
                continue

            modifiers.append(cls._create_synthetic_modifier(identifier, args[0], args[1]))
            created_modifier_ids.add(identifier)

        property_factory = _get_property_factory()
        properties: dict[ModifierIdentifier, ItemProperty] = {}

        for identifier_spec in cls.property_identifiers:
            prop_key = cls._get_property_identifier_key(identifier_spec)
            identifier_options = cls._normalize_property_identifier_spec(identifier_spec)
            prop_mod = next((m for m in modifiers if m.identifier in identifier_options), None)
            if prop_mod is None:
                return None

            prop = property_factory.get(prop_mod.identifier, lambda m, _, rarity: ItemProperty(modifier=m, rarity=rarity))(prop_mod, modifiers, rarity)
            properties[prop_key] = prop

        return properties

    @classmethod
    def get_max_description_encoded(cls, rarity: Rarity = Rarity.Blue) -> Optional[GWStringEncoded]:
        properties = cls._create_max_properties(rarity)
        if properties is None:
            return None

        if not properties:
            fallback = cls.descriptions.get(ServerLanguage.English)
            if fallback:
                return GWStringEncoded(bytes(), fallback)
            return None

        parts = [prop.encoded_description for prop in properties.values() if prop.encoded_description]
        return GWEncoded.combine_encoded_strings(parts, f"no max description ({cls.__name__})")

    @classmethod
    def get_max_description_plain(cls, rarity: Rarity = Rarity.Blue) -> Optional[str]:
        encoded = cls.get_max_description_encoded(rarity)
        if encoded is None:
            return None

        return encoded.bonuses_only or encoded.plain or encoded.full or None
    
    def get_text_color(self, name : bool = False) -> bytes:
        match self.rarity:
            case Rarity.Blue | Rarity.White:
                return GWEncoded.ITEM_ENHANCE if name else GWEncoded.ITEM_BONUS
            
            case Rarity.Purple:
                return GWEncoded.ITEM_UNCOMMON
            
            case Rarity.Gold:
                return GWEncoded.ITEM_RARE
            
            case Rarity.Green:
                return GWEncoded.ITEM_UNIQUE
            
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.encoded_name, f"no encoded name ({self.__class__.__name__})")
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(self.encoded_description, f"no encoded description ({self.__class__.__name__})")
    
    @property
    def name(self) -> str:
        return self.__encoded_name.full
    
    @property
    def name_plain(self) -> str:
        return self.__encoded_name.plain    
    
    @property
    def description_plain(self) -> str:
        return self.__encoded_description.bonuses_only or self.__encoded_description.plain or "no encoded description (short)"
    
    @property
    def description(self) -> str:
        return self.__encoded_description.full
        
    @property
    def display_summary(self) -> str:
        name = self.name_plain
        description = self.description_plain
        
        return f"{name}\n{description}" if description else name
    
    @property
    def item_type(self) -> Optional[ItemType]:
        if isinstance(self, WeaponUpgrade):
            return self.target_item_type
        
        elif isinstance(self, Inscription):
            return self.target_item_type
        
        return None
    
    @classmethod
    def get_static_name(cls, rarity : Rarity = Rarity.Blue) -> str: 
        temp_instance = cls()
        temp_instance.rarity = rarity
        temp_instance.__encoded_name = temp_instance.create_encoded_name()
        
        return temp_instance.name_plain           
    
    @property
    def is_maxed(self) -> bool:
        return True
    
class UnknownUpgrade(Upgrade):
    mod_type = ItemUpgradeType.Unknown
    id = ItemUpgrade.Unknown
    property_identifiers = []
    
#region Weapon Upgrades
class WeaponUpgrade(Upgrade):
    target_item_type : ItemType
    modifier_range: Optional[ModifierRange] = None

    @classmethod
    def _pre_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, all_modifiers: list[DecodedModifier], remaining_modifiers: list[DecodedModifier]) -> None:
        weapon_upgrade = cast("WeaponUpgrade", upgrade)
        weapon_upgrade.target_item_type = cls.id.get_item_type(weapon_upgrade.upgrade_id)

    def create_encoded_description(self) -> GWStringEncoded:
        if not self.properties:
            return super().create_encoded_description()
        parts = [prop.encoded_description for prop in self.properties.values() if prop.encoded_description]
        return GWEncoded.combine_encoded_strings(parts, "no encoded description")

    def _get_upgrade_property(self, identifier: ModifierIdentifierSpec) -> Optional[ItemProperty]:
        return self._get_property_by_spec(identifier)

    def _get_property_value(self, identifier: ModifierIdentifierSpec, attr_name: str, default):
        prop = self._get_upgrade_property(identifier)
        return getattr(prop, attr_name, default) if prop else default
    
    @property
    def is_maxed(self) -> bool:
        if not self.properties or not self.modifier_range:
            return True
        
        prop = self._get_upgrade_property(self.modifier_range.modifierIdentifier)
    
        if not prop:
            return False
        
        value = prop.modifier.arg1 if self.modifier_range.modifier_type == ModifierType.Arg1 else prop.modifier.arg2
        if value < self.modifier_range.min_value or value > self.modifier_range.max_value:
            return False
    
        return True
        
#region Prefixes

class WeaponPrefix(WeaponUpgrade):
    mod_type = ItemUpgradeType.Prefix
    
class AdeptUpgrade(WeaponPrefix):
    id = ItemUpgrade.Adept
    property_identifiers = [
        ModifierIdentifier.HalvesCastingTimeItemAttribute,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HalvesCastingTimeItemAttribute, ModifierType.Arg1, 10, 20)
    
    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.HalvesCastingTimeItemAttribute, "chance", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x1, 0x81, 0x94, 0x5D, 0x1, 0x0]), f"Adept")
    
class BarbedUpgrade(WeaponPrefix):
    id = ItemUpgrade.Barbed
    property_identifiers = [
        ModifierIdentifier.IncreaseConditionDuration,
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.IncreaseConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
         return GWStringEncoded(self.get_text_color(True) + bytes([0x69, 0xA, 0x1, 0x0]), f"Barbed")
    
class CripplingUpgrade(WeaponPrefix):
    id = ItemUpgrade.Crippling
    property_identifiers = [
        ModifierIdentifier.IncreaseConditionDuration,
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.IncreaseConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x6A, 0xA, 0x1, 0x0]), f"Crippling")
        
class CruelUpgrade(WeaponPrefix):
    id = ItemUpgrade.Cruel
    property_identifiers = [
        ModifierIdentifier.IncreaseConditionDuration,
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.IncreaseConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x6B, 0xA, 0x1, 0x0]), f"Cruel")

class DefensiveUpgrade(WeaponPrefix):
    id = ItemUpgrade.Defensive
    property_identifiers = [
        ModifierIdentifier.ArmorPlus,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlus, ModifierType.Arg2, 1, 5)

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlus, "armor", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x6D, 0xA, 0x1, 0x0]), f"Defensive")
    
class EbonUpgrade(WeaponPrefix):
    id = ItemUpgrade.Ebon
    property_identifiers = [
        ModifierIdentifier.DamageTypeProperty,
    ]

    @property
    def damage_type(self):
        return self._get_property_value(ModifierIdentifier.DamageTypeProperty, "damage_type", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0xD5, 0x8, 0x1, 0x0]), f"Ebon")
    
class FieryUpgrade(WeaponPrefix):
    id = ItemUpgrade.Fiery
    property_identifiers = [
        ModifierIdentifier.DamageTypeProperty,
    ]

    @property
    def damage_type(self):
        return self._get_property_value(ModifierIdentifier.DamageTypeProperty, "damage_type", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0xD7, 0x8, 0x1, 0x0]), f"Fiery")
    
class FuriousUpgrade(WeaponPrefix):
    id = ItemUpgrade.Furious
    property_identifiers = [
        ModifierIdentifier.Furious,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.Furious, ModifierType.Arg2, 2, 10)
    
    @property
    def chance(self) -> int:
        prop = self.properties.get(ModifierIdentifier.Furious)
        return prop.modifier.arg2 if prop else 0
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x6F, 0xA, 0x1, 0x0]), f"Furious")
    
class HaleUpgrade(WeaponPrefix):
    id = ItemUpgrade.Hale
    property_identifiers = [
        ModifierIdentifier.HealthPlus,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HealthPlus, ModifierType.Arg1, 1, 30)

    @property
    def health(self) -> int:
        return self._get_property_value(ModifierIdentifier.HealthPlus, "health", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x70, 0xA, 0x1, 0x0]), f"Hale")
    
class HeavyUpgrade(WeaponPrefix):
    id = ItemUpgrade.Heavy
    property_identifiers = [
        ModifierIdentifier.IncreaseConditionDuration,
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.IncreaseConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x72, 0xA, 0x1, 0x0]), f"Heavy")
    
class IcyUpgrade(WeaponPrefix):
    id = ItemUpgrade.Icy
    property_identifiers = [
        ModifierIdentifier.DamageTypeProperty,
    ]

    @property
    def damage_type(self):
        return self._get_property_value(ModifierIdentifier.DamageTypeProperty, "damage_type", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0xD4, 0x8, 0x1, 0x0]), f"Icy")
    
class InsightfulUpgrade(WeaponPrefix):
    id = ItemUpgrade.Insightful
    property_identifiers = [
        ModifierIdentifier.EnergyPlus,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.EnergyPlus, ModifierType.Arg2, 1, 5)

    @property
    def energy(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyPlus, "energy", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x73, 0xA, 0x1, 0x0]), f"Insightful")
    
class PoisonousUpgrade(WeaponPrefix):
    id = ItemUpgrade.Poisonous
    property_identifiers = [
        ModifierIdentifier.IncreaseConditionDuration,
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.IncreaseConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x75, 0xA, 0x1, 0x0]), f"Poisonous")
    
class ShockingUpgrade(WeaponPrefix):
    id = ItemUpgrade.Shocking
    property_identifiers = [
        ModifierIdentifier.DamageTypeProperty,
    ]

    @property
    def damage_type(self):
        return self._get_property_value(ModifierIdentifier.DamageTypeProperty, "damage_type", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0xD6, 0x8, 0x1, 0x0]), f"Shocking")
    
class SilencingUpgrade(WeaponPrefix):
    id = ItemUpgrade.Silencing
    property_identifiers = [
        ModifierIdentifier.IncreaseConditionDuration,
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.IncreaseConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x6C, 0xA, 0x1, 0x0]), f"Silencing")
    
class SunderingUpgrade(WeaponPrefix):
    id = ItemUpgrade.Sundering
    property_identifiers = [
        ModifierIdentifier.ArmorPenetration,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPenetration, ModifierType.Arg1, 10, 20)
    max_modifier_values = {
        ModifierIdentifier.ArmorPenetration: (20, 20),
    }

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPenetration, "chance", 0)

    @property
    def armor_penetration(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPenetration, "armor_pen", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x74, 0xA, 0x1, 0x0]), f"Sundering")
    
class SwiftUpgrade(WeaponPrefix):
    id = ItemUpgrade.Swift
    property_identifiers = [
        ModifierIdentifier.HalvesCastingTimeGeneral,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HalvesCastingTimeGeneral, ModifierType.Arg1, 5, 10)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.HalvesCastingTimeGeneral, "chance", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x1, 0x81, 0x95, 0x5D, 0x1, 0x0]), f"Swift")
    
class VampiricUpgrade(WeaponPrefix):
    id = ItemUpgrade.Vampiric
    property_identifiers = [
        ModifierIdentifier.HealthDegen,
        ModifierIdentifier.HealthStealOnHit,
    ]
    # modifier_range = ModifierRange(ModifierIdentifier.HealthStealOnHit, ModifierType.Arg1, 1, 5)

    @property
    def health_degen(self) -> int:
        return self._get_property_value(ModifierIdentifier.HealthDegen, "health_degen", 0)

    @property
    def health_steal(self) -> int:
        return self._get_property_value(ModifierIdentifier.HealthStealOnHit, "health_steal", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x71, 0xA, 0x1, 0x0]), f"Vampiric")
    
class ZealousUpgrade(WeaponPrefix):
    id = ItemUpgrade.Zealous
    property_identifiers = [
        ModifierIdentifier.EnergyDegen,
        ModifierIdentifier.EnergyGainOnHit,
    ]

    @property
    def energy_degen(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyDegen, "energy_degen", 0)

    @property
    def energy_gain(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyGainOnHit, "energy_gain", 0)

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x6E, 0xA, 0x1, 0x0]), f"Zealous")

#endregion Prefixes
  
#region Suffixes
class WeaponSuffix(WeaponUpgrade):
    mod_type = ItemUpgradeType.Suffix
    
class OfAttributeUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfAttribute
    property_identifiers = [
        ModifierIdentifier.AttributePlusOne,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.AttributePlusOne, ModifierType.Arg2, 10, 20)
        
    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.AttributePlusOne, "chance", 0)

    @property
    def attribute(self) -> Attribute:
        return self._get_property_value(ModifierIdentifier.AttributePlusOne, "attribute", Attribute.None_)

    @property
    def attribute_level(self) -> int:
        return self._get_property_value(ModifierIdentifier.AttributePlusOne, "attribute_level", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0xB, 0x1]) + GWEncoded.ATTRIBUTE_NAMES.get(self.attribute, bytes()) + bytes([0x1, 0x0, 0x1, 0x0]), f"of {AttributeNames.get(self.attribute, self.attribute.name)}", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Attribute"])
        
    
class OfAptitudeUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfAptitude
    property_identifiers = [
        ModifierIdentifier.HalvesCastingTimeItemAttribute,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HalvesCastingTimeItemAttribute, ModifierType.Arg1, 10, 20)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.HalvesCastingTimeItemAttribute, "chance", 0)
    
    def create_encoded_name(self):
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x95, 0x5D, 0x1, 0x0]), f"of Aptitude", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Aptitude"])
    
class OfAxeMasteryUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfAxeMastery
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0xB, 0x1]) + GWEncoded.ATTRIBUTE_NAMES.get(self.attribute, bytes()) + bytes([0x1, 0x0, 0x1, 0x0]), f"of {AttributeNames.get(self.attribute, self.attribute.name)}", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Axe Mastery"])
        
    
class OfDaggerMasteryUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfDaggerMastery
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0xB, 0x1]) + GWEncoded.ATTRIBUTE_NAMES.get(self.attribute, bytes()) + bytes([0x1, 0x0, 0x1, 0x0]), f"of {AttributeNames.get(self.attribute, self.attribute.name)}", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Dagger Mastery"])
    
class OfDefenseUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfDefense
    property_identifiers = [
        ModifierIdentifier.ArmorPlus,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlus, ModifierType.Arg2, 4, 5)

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlus, "armor", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x77, 0xA, 0x1, 0x0]), f"of Defense", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Defense"])
    
class OfDevotionUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfDevotion
    property_identifiers = [
        ModifierIdentifier.HealthPlusEnchanted,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HealthPlusEnchanted, ModifierType.Arg1, 30, 45)

    @property
    def health(self) -> int:
        return self._get_property_value(ModifierIdentifier.HealthPlusEnchanted, "health", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x97, 0x5D, 0x1, 0x0]), f"of Devotion", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Devotion"])
    
class OfEnchantingUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfEnchanting
    property_identifiers = [
        ModifierIdentifier.IncreaseEnchantmentDuration,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.IncreaseEnchantmentDuration, ModifierType.Arg2, 10, 20)

    @property
    def enchantment_duration(self) -> int:
        return self._get_property_value(ModifierIdentifier.IncreaseEnchantmentDuration, "enchantment_duration", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x78, 0xA, 0x1, 0x0]), f"of Enchanting", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Enchanting"])
    
class OfEnduranceUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfEndurance
    property_identifiers = [
        ModifierIdentifier.HealthPlusStance,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HealthPlusStance, ModifierType.Arg1, 30, 45)

    @property
    def health(self) -> int:
        return self._get_property_value(ModifierIdentifier.HealthPlusStance, "health", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x98, 0x5D, 0x1, 0x0]), f"of Endurance", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Endurance"])
    
class OfFortitudeUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfFortitude
    property_identifiers = [
        ModifierIdentifier.HealthPlus,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HealthPlus, ModifierType.Arg1, 10, 30)

    @property
    def health(self) -> int:
        return self._get_property_value(ModifierIdentifier.HealthPlus, "health", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x79, 0xA, 0x1, 0x0]), f"of Fortitude", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Fortitude"])
    
class OfHammerMasteryUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfHammerMastery
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0xB, 0x1]) + GWEncoded.ATTRIBUTE_NAMES.get(self.attribute, bytes()) + bytes([0x1, 0x0, 0x1, 0x0]), f"of {AttributeNames.get(self.attribute, self.attribute.name)}", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Hammer Mastery"])
    
class OfMarksmanshipUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfMarksmanship
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0xB, 0x1]) + GWEncoded.ATTRIBUTE_NAMES.get(self.attribute, bytes()) + bytes([0x1, 0x0, 0x1, 0x0]), f"of {AttributeNames.get(self.attribute, self.attribute.name)}", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Marksmanship"])
    
class OfMasteryUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfMastery
    property_identifiers = [
        ModifierIdentifier.AttributePlusOneItem,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.AttributePlusOneItem, ModifierType.Arg1, 10, 20)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.AttributePlusOneItem, "chance", 0)

    @property
    def attribute_level(self) -> int:
        return self._get_property_value(ModifierIdentifier.AttributePlusOneItem, "attribute_level", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x99, 0x5D, 0x1, 0x0]), f"of Mastery", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Mastery"])
    
class OfMemoryUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfMemory
    property_identifiers = [
        ModifierIdentifier.HalvesSkillRechargeItemAttribute,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HalvesSkillRechargeItemAttribute, ModifierType.Arg1, 10, 20)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.HalvesSkillRechargeItemAttribute, "chance", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x9A, 0x5D, 0x1, 0x0]), f"of Memory", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Memory"])

class OfQuickeningUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfQuickening
    property_identifiers = [
        ModifierIdentifier.HalvesSkillRechargeGeneral,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HalvesSkillRechargeGeneral, ModifierType.Arg1, 5, 10)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.HalvesSkillRechargeGeneral, "chance", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x9B, 0x5D, 0x1, 0x0]), f"of Quickening", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Quickening"])

class OfScytheMasteryUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfScytheMastery
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0xB, 0x1]) + GWEncoded.ATTRIBUTE_NAMES.get(self.attribute, bytes()) + bytes([0x1, 0x0, 0x1, 0x0]), f"of {AttributeNames.get(self.attribute, self.attribute.name)}", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Scythe Mastery"])
    
class OfShelterUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfShelter
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsPhysical,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusVsPhysical, ModifierType.Arg2, 4, 7)

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsPhysical, "armor", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x7B, 0xA, 0x1, 0x0]), f"of Shelter", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Shelter"])
    
class OfSlayingUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfSlaying
    modifier_range = ModifierRange(ModifierIdentifier.DamagePlusVsSpecies, ModifierType.Arg1, 10, 20)
    
    property_identifiers = [
        ModifierIdentifier.DamagePlusVsSpecies,
        # ModifierIdentifier.BaneSpecies,
    ]
    
    def __init__(self):
        super().__init__()
    
    @property
    def species(self) -> ItemBaneSpecies:
        return self._get_property_value(ModifierIdentifier.DamagePlusVsSpecies, "species", ItemBaneSpecies.Unknown)
    
    @property
    def damage_increase(self) -> int:
        return self._get_property_value(ModifierIdentifier.DamagePlusVsSpecies, "damage_increase", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + GWEncoded.SLAYING_SUFFIXES.get(self.species, bytes()), f"of {self.species.name}-Slaying", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", f"{self.species.name}-Slaying" if self.species != ItemBaneSpecies.Unknown else "Slaying"])

class OfSpearMasteryUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfSpearMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0xB, 0x1]) + GWEncoded.ATTRIBUTE_NAMES.get(self.attribute, bytes()) + bytes([0x1, 0x0, 0x1, 0x0]), f"of {AttributeNames.get(self.attribute, self.attribute.name)}", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Spear Mastery"])

class OfSwiftnessUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfSwiftness
    property_identifiers = [
        ModifierIdentifier.HalvesCastingTimeGeneral,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HalvesCastingTimeGeneral, ModifierType.Arg1, 5, 10)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.HalvesCastingTimeGeneral, "chance", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x7C, 0xA, 0x1, 0x0]), f"of Swiftness", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Swiftness"])
    
class OfSwordsmanshipUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfSwordsmanship
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0xB, 0x1]) + GWEncoded.ATTRIBUTE_NAMES.get(self.attribute, bytes()) + bytes([0x1, 0x0, 0x1, 0x0]), f"of {AttributeNames.get(self.attribute, self.attribute.name)}", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Swordsmanship"])
    
class OfTheProfessionUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfTheProfession
    modifier_range = ModifierRange(ModifierIdentifier.OfTheProfession, ModifierType.Arg2, 4, 5)
    
    property_identifiers = [
        ModifierIdentifier.OfTheProfession,
    ]

    @property
    def profession(self) -> Profession:
        return self._get_property_value(ModifierIdentifier.OfTheProfession, "profession", Profession._None)

    @property
    def attribute(self) -> Attribute:
        return self._get_property_value(ModifierIdentifier.OfTheProfession, "attribute", Attribute.None_)

    @property
    def attribute_level(self) -> int:
        return self._get_property_value(ModifierIdentifier.OfTheProfession, "attribute_level", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + GWEncoded.THE_PROFESSION.get(self.profession, bytes()), f"of {self.profession.name if self.profession != Profession._None else 'Unknown Profession'}", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", self.profession.name if self.profession != Profession._None else "Profession"])
        
    
class OfValorUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfValor
    property_identifiers = [
        ModifierIdentifier.HealthPlusHexed,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HealthPlusHexed, ModifierType.Arg1, 45, 60)

    @property
    def health(self) -> int:
        return self._get_property_value(ModifierIdentifier.HealthPlusHexed, "health", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True)+ GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x9C, 0x5D, 0x1, 0x0]), f"of Valor", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Valor"])
    
class OfWardingUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfWarding
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsElemental,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusVsElemental, ModifierType.Arg2, 4, 7)

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsElemental, "armor", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x7D, 0xA, 0x1, 0x0]), f"of Warding", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Warding"])

#endregion Suffixes

#region Inscriptions
class Inscription(Upgrade):
    mod_type = ItemUpgradeType.Inscription
    inventory_icon : str
    id : ItemUpgrade
    target_item_type : ItemType
    modifier_range: Optional[ModifierRange] = None

    def create_encoded_description(self) -> GWStringEncoded:
        if not self.properties:
            return super().create_encoded_description()
        parts = [prop.encoded_description for prop in self.properties.values() if prop.encoded_description]
        return GWEncoded.combine_encoded_strings(parts, "no encoded description")

    def _get_upgrade_property(self, identifier: ModifierIdentifierSpec) -> Optional[ItemProperty]:
        return self._get_property_by_spec(identifier)

    def _get_property_value(self, identifier: ModifierIdentifierSpec, attr_name: str, default):
        prop = self._get_upgrade_property(identifier)
        return getattr(prop, attr_name, default) if prop else default

    def _get_modifier_arg(self, identifier: ModifierIdentifierSpec, arg_index: int, default: int = 0) -> int:
        prop = self._get_upgrade_property(identifier)
        if not prop:
            return default
        return prop.modifier.arg1 if arg_index == 1 else prop.modifier.arg2

    @property
    def is_maxed(self) -> bool:
        if not self.properties or not self.modifier_range:
            return True

        prop = self._get_upgrade_property(self.modifier_range.modifierIdentifier)
        if not prop:
            return False

        value = prop.modifier.arg1 if self.modifier_range.modifier_type == ModifierType.Arg1 else prop.modifier.arg2
        return self.modifier_range.min_value <= value <= self.modifier_range.max_value
    
#region Offhand
class BeJustAndFearNot(Inscription):
    id = ItemUpgrade.BeJustAndFearNot
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusHexed,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusHexed, ModifierType.Arg2, 5, 10)
    
    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusHexed, "armor", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x90, 0x5D, 0x1, 0x0]), f"Be Just And Fear Not")
        
class DownButNotOut(Inscription):
    id = ItemUpgrade.DownButNotOut
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusWhileBelow
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusWhileBelow, ModifierType.Arg2, 5, 10)
    max_modifier_values = {
        ModifierIdentifier.ArmorPlusWhileBelow: (50, 10),
    }

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusWhileBelow, "armor", 0)

    @property
    def health_threshold(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusWhileBelow, "health_threshold", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x86, 0x5D, 0x1, 0x0]), f"Down But Not Out")    
    
class FaithIsMyShield(Inscription):
    id = ItemUpgrade.FaithIsMyShield
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusEnchanted,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusEnchanted, ModifierType.Arg2, 4, 5)
    
    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusEnchanted, "armor", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x8D, 0x5D, 0x1, 0x0]), f"Faith Is My Shield")
    
class ForgetMeNot(Inscription):
    id = ItemUpgrade.ForgetMeNot
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.HalvesSkillRechargeItemAttribute,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HalvesSkillRechargeItemAttribute, ModifierType.Arg1, 15, 20)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.HalvesSkillRechargeItemAttribute, "chance", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x93, 0x5D, 0x1, 0x0]), f"Forget Me Not")
    
class HailToTheKing(Inscription):
    id = ItemUpgrade.HailToTheKing
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusAbove,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusAbove, ModifierType.Arg2, 4, 5)
    max_modifier_values = {
        ModifierIdentifier.ArmorPlusAbove: (50, 5),
    }

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusAbove, "armor", 0)

    @property
    def health_threshold(self) -> int:
        return self._get_modifier_arg(ModifierIdentifier.ArmorPlusAbove, 1, 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x8E, 0x5D, 0x1, 0x0]), f"Hail To The King")
    
class IgnoranceIsBliss(Inscription):
    id = ItemUpgrade.IgnoranceIsBliss
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlus,
        ModifierIdentifier.EnergyMinus,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlus, ModifierType.Arg2, 4, 5)

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlus, "armor", 0)

    @property
    def energy(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyMinus, "energy", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x87, 0x5D, 0x1, 0x0]), f"Ignorance Is Bliss")
    
class KnowingIsHalfTheBattle(Inscription):
    id = ItemUpgrade.KnowingIsHalfTheBattle
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusCasting,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusCasting, ModifierType.Arg2, 5, 5)
    
    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusCasting, "armor", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x8C, 0x5D, 0x1, 0x0]), f"Knowing Is Half The Battle")
    
class LifeIsPain(Inscription):
    id = ItemUpgrade.LifeIsPain
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlus,
        ModifierIdentifier.HealthMinus,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlus, ModifierType.Arg2, 4, 5)

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlus, "armor", 0)

    @property
    def health(self) -> int:
        return self._get_property_value(ModifierIdentifier.HealthMinus, "health", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x88, 0x5D, 0x1, 0x0]), f"Life Is Pain")
    
class LiveForToday(Inscription):
    id = ItemUpgrade.LiveForToday
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.EnergyPlus,
        ModifierIdentifier.EnergyDegen,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.EnergyPlus, ModifierType.Arg2, 10, 15)

    @property
    def energy(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyPlus, "energy", 0)

    @property
    def energy_regen(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyDegen, "energy_regen", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x91, 0x5D, 0x1, 0x0]), f"Live For Today")
    
class ManForAllSeasons(Inscription):
    id = ItemUpgrade.ManForAllSeasons
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsElemental,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusVsElemental, ModifierType.Arg2, 4, 5)

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsElemental, "armor", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x89, 0x5D, 0x1, 0x0]), f"Man For All Seasons")
    
class MightMakesRight(Inscription):
    id = ItemUpgrade.MightMakesRight
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusAttacking,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusAttacking, ModifierType.Arg2, 4, 5)

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusAttacking, "armor", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x8B, 0x5D, 0x1, 0x0]), f"Might Makes Right")
    
class SerenityNow(Inscription):
    id = ItemUpgrade.SerenityNow
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.HalvesSkillRechargeGeneral,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HalvesSkillRechargeGeneral, ModifierType.Arg1, 7, 10)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.HalvesSkillRechargeGeneral, "chance", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x92, 0x5D, 0x1, 0x0]), f"Serenity Now")
    
class SurvivalOfTheFittest(Inscription):
    id = ItemUpgrade.SurvivalOfTheFittest
    target_item_type = ItemType.Offhand
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsPhysical,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusVsPhysical, ModifierType.Arg2, 4, 5)

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsPhysical, "armor", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x8A, 0x5D, 0x1, 0x0]), f"Survival Of The Fittest")

#endregion Offhand

#region Weapon

class BrawnOverBrains(Inscription):
    id = ItemUpgrade.BrawnOverBrains
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusPercent,
        ModifierIdentifier.EnergyMinus,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.DamagePlusPercent, ModifierType.Arg2, 14, 15)

    @property
    def damage_increase(self) -> int:
        return self._get_property_value(ModifierIdentifier.DamagePlusPercent, "damage_increase", 0)

    @property
    def energy(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyMinus, "energy", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xAE, 0x5D, 0x1, 0x0]), f"Brawn Over Brains")
        
class DanceWithDeath(Inscription):
    id = ItemUpgrade.DanceWithDeath
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusStance,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.DamagePlusStance, ModifierType.Arg2, 10, 15)

    @property
    def damage_increase(self) -> int:
        return self._get_property_value(ModifierIdentifier.DamagePlusStance, "damage_increase", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xAD, 0x5D, 0x1, 0x0]), f"Dance With Death")
         
class DontFearTheReaper(Inscription):
    id = ItemUpgrade.DontFearTheReaper
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusHexed,
    ]    
    modifier_range = ModifierRange(ModifierIdentifier.DamagePlusHexed, ModifierType.Arg2, 10, 20)

    @property
    def damage_increase(self) -> int:
        return self._get_property_value(ModifierIdentifier.DamagePlusHexed, "damage_increase", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xAC, 0x5D, 0x1, 0x0]), f"Dont Fear The Reaper")
    
class DontThinkTwice(Inscription):
    id = ItemUpgrade.DontThinkTwice
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.HalvesCastingTimeGeneral,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HalvesCastingTimeGeneral, ModifierType.Arg1, 5, 10)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.HalvesCastingTimeGeneral, "chance", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB0, 0x5D, 0x1, 0x0]), f"Dont Think Twice")
    
class GuidedByFate(Inscription):
    id = ItemUpgrade.GuidedByFate
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusEnchanted,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.DamagePlusEnchanted, ModifierType.Arg2, 10, 15)

    @property
    def damage_increase(self) -> int:
        return self._get_property_value(ModifierIdentifier.DamagePlusEnchanted, "damage_increase", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xA9, 0x5D, 0x1, 0x0]), f"Guided By Fate")
    
class StrengthAndHonor(Inscription):
    id = ItemUpgrade.StrengthAndHonor
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusWhileAbove,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.DamagePlusWhileAbove, ModifierType.Arg2, 10, 15)
    max_modifier_values = {
        ModifierIdentifier.DamagePlusWhileAbove: (50, 15),
    }

    @property
    def damage_increase(self) -> int:
        return self._get_property_value(ModifierIdentifier.DamagePlusWhileAbove, "damage_increase", 0)

    @property
    def health_threshold(self) -> int:
        return self._get_property_value(ModifierIdentifier.DamagePlusWhileAbove, "health_threshold", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xAA, 0x5D, 0x1, 0x0]), f"Strength And Honor")
    
class ToThePain(Inscription):
    id = ItemUpgrade.ToThePain
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusPercent,
        ModifierIdentifier.ArmorMinusAttacking
    ]
    modifier_range = ModifierRange(ModifierIdentifier.DamagePlusPercent, ModifierType.Arg2, 14, 15)

    @property
    def damage_increase(self) -> int:
        return self._get_property_value(ModifierIdentifier.DamagePlusPercent, "damage_increase", 0)

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorMinusAttacking, "armor", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xAF, 0x5D, 0x1, 0x0]), f"To The Pain")
    
class TooMuchInformation(Inscription):
    id = ItemUpgrade.TooMuchInformation
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusVsHexed,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.DamagePlusVsHexed, ModifierType.Arg2, 10, 15)

    @property
    def damage_increase(self) -> int:
        return self._get_property_value(ModifierIdentifier.DamagePlusVsHexed, "damage_increase", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xA8, 0x5D, 0x1, 0x0]), f"Too Much Information")
    
class VengeanceIsMine(Inscription):
    id = ItemUpgrade.VengeanceIsMine
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusWhileBelow,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.DamagePlusWhileBelow, ModifierType.Arg2, 10, 20)
    max_modifier_values = {
        ModifierIdentifier.DamagePlusWhileBelow: (50, 20),
    }

    @property
    def damage_increase(self) -> int:
        return self._get_property_value(ModifierIdentifier.DamagePlusWhileBelow, "damage_increase", 0)

    @property
    def health_threshold(self) -> int:
        return self._get_property_value(ModifierIdentifier.DamagePlusWhileBelow, "health_threshold", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xAB, 0x5D, 0x1, 0x0]), f"Vengeance Is Mine")

#endregion Weapon

#region MartialWeapon
class IHaveThePower(Inscription):
    id = ItemUpgrade.IHaveThePower
    target_item_type = ItemType.MartialWeapon
    property_identifiers = [
        ModifierIdentifier.EnergyPlus,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.EnergyPlus, ModifierType.Arg2, 5, 5)

    @property
    def energy(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyPlus, "energy", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x72, 0x5D, 0x1, 0x0]), f"I Have The Power")
    
class LetTheMemoryLiveAgain(Inscription):
    id = ItemUpgrade.LetTheMemoryLiveAgain
    target_item_type = ItemType.MartialWeapon
    property_identifiers = [
        ModifierIdentifier.HalvesSkillRechargeGeneral,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HalvesSkillRechargeGeneral, ModifierType.Arg1, 5, 10)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.HalvesSkillRechargeGeneral, "chance", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x73, 0x5D, 0x1, 0x0]), f"Let The Memory Live Again")
    
#endregion MartialWeapon

#region OffhandOrShield
class CastOutTheUnclean(Inscription):
    id = ItemUpgrade.CastOutTheUnclean
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.ReduceConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x83, 0x5D, 0x1, 0x0]), f"Cast Out The Unclean")
    
class FearCutsDeeper(Inscription):
    id = ItemUpgrade.FearCutsDeeper
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.ReduceConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x7F, 0x5D, 0x1, 0x0]), f"Fear Cuts Deeper")
    
class ICanSeeClearlyNow(Inscription):
    id = ItemUpgrade.ICanSeeClearlyNow
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,   
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.ReduceConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x80, 0x5D, 0x1, 0x0]), f"I Can See Clearly Now")
    
class LeafOnTheWind(Inscription):
    id = ItemUpgrade.LeafOnTheWind
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusVsDamage, ModifierType.Arg2, 5, 10)
    max_modifier_values = {
        ModifierIdentifier.ArmorPlusVsDamage: (3, 10),
    }

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "armor", 0)

    @property
    def damage_type(self):
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "damage_type", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x75, 0x5D, 0x1, 0x0]), f"Leaf On The Wind")
    
class LikeARollingStone(Inscription):
    id = ItemUpgrade.LikeARollingStone
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusVsDamage, ModifierType.Arg2, 5, 10)
    max_modifier_values = {
        ModifierIdentifier.ArmorPlusVsDamage: (11, 10),
    }

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "armor", 0)

    @property
    def damage_type(self):
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "damage_type", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x76, 0x5D, 0x1, 0x0]), f"Like A Rolling Stone")
    
class LuckOfTheDraw(Inscription):
    id = ItemUpgrade.LuckOfTheDraw
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReceiveLessDamage,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ReceiveLessDamage, ModifierType.Arg1, 11, 20)
    max_modifier_values = {
        ModifierIdentifier.ReceiveLessDamage: (20, 5),
    }

    @property
    def damage_reduction(self) -> int:
        return self._get_property_value(ModifierIdentifier.ReceiveLessDamage, "damage_reduction", 0)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.ReceiveLessDamage, "chance", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x7B, 0x5D, 0x1, 0x0]), f"Luck Of The Draw")
    
class MasterOfMyDomain(Inscription):
    id = ItemUpgrade.MasterOfMyDomain
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.AttributePlusOneItem,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.AttributePlusOneItem, ModifierType.Arg1, 11, 20)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.AttributePlusOneItem, "chance", 0)

    @property
    def attribute_level(self) -> int:
        return self._get_property_value(ModifierIdentifier.AttributePlusOneItem, "attribute_level", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xA7, 0x5D, 0x1, 0x0]), f"Master Of My Domain")
    
class NotTheFace(Inscription):
    id = ItemUpgrade.NotTheFace
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusVsDamage, ModifierType.Arg2, 5, 10)
    max_modifier_values = {
        ModifierIdentifier.ArmorPlusVsDamage: (0, 10),
    }

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "armor", 0)

    @property
    def damage_type(self):
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "damage_type", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x74, 0x5D, 0x1, 0x0]), f"Not The Face")
    
class NothingToFear(Inscription):
    id = ItemUpgrade.NothingToFear
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReceiveLessPhysDamageHexed,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ReceiveLessPhysDamageHexed, ModifierType.Arg2, 1, 3)

    @property
    def damage_reduction(self) -> int:
        return self._get_property_value(ModifierIdentifier.ReceiveLessPhysDamageHexed, "damage_reduction", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x7D, 0x5D, 0x1, 0x0]), f"Nothing To Fear")
    
class OnlyTheStrongSurvive(Inscription):
    id = ItemUpgrade.OnlyTheStrongSurvive
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.ReduceConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x86, 0x5D, 0x1, 0x0]), f"Only The Strong Survive")
    
class PureOfHeart(Inscription):
    id = ItemUpgrade.PureOfHeart
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.ReduceConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x84, 0x5D, 0x1, 0x0]), f"Pure Of Heart")
    
class RidersOnTheStorm(Inscription):
    id = ItemUpgrade.RidersOnTheStorm
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusVsDamage, ModifierType.Arg2, 5, 10)
    max_modifier_values = {
        ModifierIdentifier.ArmorPlusVsDamage: (4, 10),
    }

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "armor", 0)

    @property
    def damage_type(self):
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "damage_type", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x77, 0x5D, 0x1, 0x0]), f"Riders On The Storm")
    
class RunForYourLife(Inscription):
    id = ItemUpgrade.RunForYourLife
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReceiveLessPhysDamageStance,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ReceiveLessPhysDamageStance, ModifierType.Arg2, 1, 2)

    @property
    def damage_reduction(self) -> int:
        return self._get_property_value(ModifierIdentifier.ReceiveLessPhysDamageStance, "damage_reduction", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x7E, 0x5D, 0x1, 0x0]), f"Run For Your Life")  
    
class ShelteredByFaith(Inscription):
    id = ItemUpgrade.ShelteredByFaith
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReceiveLessPhysDamageEnchanted,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ReceiveLessPhysDamageEnchanted, ModifierType.Arg2, 1, 2)

    @property
    def damage_reduction(self) -> int:
        return self._get_property_value(ModifierIdentifier.ReceiveLessPhysDamageEnchanted, "damage_reduction", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x7C, 0x5D, 0x1, 0x0]), f"Sheltered By Faith")
    
class SleepNowInTheFire(Inscription):
    id = ItemUpgrade.SleepNowInTheFire
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusVsDamage, ModifierType.Arg2, 5, 10)
    max_modifier_values = {
        ModifierIdentifier.ArmorPlusVsDamage: (5, 10),
    }

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "armor", 0)

    @property
    def damage_type(self):
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "damage_type", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x78, 0x5D, 0x1, 0x0]), f"Sleep Now In The Fire")
    
class SoundnessOfMind(Inscription):
    id = ItemUpgrade.SoundnessOfMind
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.ReduceConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x85, 0x5D, 0x1, 0x0]), f"Soundness Of Mind")
    
class StrengthOfBody(Inscription):
    id = ItemUpgrade.StrengthOfBody
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.ReduceConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x82, 0x5D, 0x1, 0x0]), f"Strength Of Body")
    
class SwiftAsTheWind(Inscription):
    id = ItemUpgrade.SwiftAsTheWind
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ReduceConditionDuration,
    ]

    @property
    def condition(self):
        return self._get_property_value(ModifierIdentifier.ReduceConditionDuration, "condition", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x81, 0x5D, 0x1, 0x0]), f"Swift As The Wind")

class TheRiddleOfSteel(Inscription):
    id = ItemUpgrade.TheRiddleOfSteel
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusVsDamage, ModifierType.Arg2, 5, 10)
    max_modifier_values = {
        ModifierIdentifier.ArmorPlusVsDamage: (2, 10),
    }

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "armor", 0)

    @property
    def damage_type(self):
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "damage_type", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x7A, 0x5D, 0x1, 0x0]), f"The Riddle Of Steel")
    
class ThroughThickAndThin(Inscription):
    id = ItemUpgrade.ThroughThickAndThin
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsDamage,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusVsDamage, ModifierType.Arg2, 5, 10)
    max_modifier_values = {
        ModifierIdentifier.ArmorPlusVsDamage: (1, 10),
    }

    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "armor", 0)

    @property
    def damage_type(self):
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsDamage, "damage_type", None)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x79, 0x5D, 0x1, 0x0]), f"Through Thick And Thin")

#endregion OffhandOrShield

#region EquippableItem
class MeasureForMeasure(Inscription):
    id = ItemUpgrade.MeasureForMeasure
    target_item_type = ItemType.EquippableItem
    property_identifiers = [
        ModifierIdentifier.HighlySalvageable,
    ]

    @property
    def highly_salvageable(self) -> bool:
        return self._get_upgrade_property(ModifierIdentifier.HighlySalvageable) is not None
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x81, 0x7C, 0x1, 0x0]), f"Measure For Measure")
        
class ShowMeTheMoney(Inscription):
    id = ItemUpgrade.ShowMeTheMoney
    target_item_type = ItemType.EquippableItem
    property_identifiers = [
        ModifierIdentifier.IncreasedSaleValue,
    ]    

    @property
    def improved_sale_value(self) -> bool:
        return self._get_upgrade_property(ModifierIdentifier.IncreasedSaleValue) is not None
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x80, 0x7C, 0x1, 0x0]), f"Show Me The Money")

#endregion EquippableItem

#region SpellcastingWeapon
class AptitudeNotAttitude(Inscription):
    id = ItemUpgrade.AptitudeNotAttitude
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.HalvesCastingTimeItemAttribute,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HalvesCastingTimeItemAttribute, ModifierType.Arg1, 10, 20)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.HalvesCastingTimeItemAttribute, "chance", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB1, 0x5D, 0x1, 0x0]), f"Aptitude Not Attitude")
    
class DontCallItAComeback(Inscription):
    id = ItemUpgrade.DontCallItAComeback
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.EnergyPlusWhileBelow,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.EnergyPlusWhileBelow, ModifierType.Arg2, 5, 7)
    max_modifier_values = {
        ModifierIdentifier.EnergyPlusWhileBelow: (50, 7),
    }

    @property
    def energy(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyPlusWhileBelow, "energy", 0)

    @property
    def health_threshold(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyPlusWhileBelow, "health_threshold", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB2, 0x5D, 0x1, 0x0]), f"Don't Call It A Comeback")
    
class HaleAndHearty(Inscription):
    id = ItemUpgrade.HaleAndHearty
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.EnergyPlusWhileAbove,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.EnergyPlusWhileAbove, ModifierType.Arg2, 4, 5)
    max_modifier_values = {
        ModifierIdentifier.EnergyPlusWhileAbove: (50, 5),
    }

    @property
    def energy(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyPlusWhileAbove, "energy", 0)

    @property
    def health_threshold(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyPlusWhileAbove, "health_threshold", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB5, 0x5D, 0x1, 0x0]), f"Hale And Hearty")
    
class HaveFaith(Inscription):
    id = ItemUpgrade.HaveFaith
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.EnergyPlusEnchanted,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.EnergyPlusEnchanted, ModifierType.Arg2, 4, 5)

    @property
    def energy(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyPlusEnchanted, "energy", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB4, 0x5D, 0x1, 0x0]), f"Have Faith")
    
class IAmSorrow(Inscription):
    id = ItemUpgrade.IAmSorrow
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.EnergyPlusHexed,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.EnergyPlusHexed, ModifierType.Arg2, 5, 7)

    @property
    def energy(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyPlusHexed, "energy", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB7, 0x5D, 0x1, 0x0]), f"I Am Sorrow")
    
class SeizeTheDay(Inscription):
    id = ItemUpgrade.SeizeTheDay
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.EnergyPlus,
        ModifierIdentifier.EnergyDegen,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.EnergyPlus, ModifierType.Arg2, 10, 15)

    @property
    def energy(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyPlus, "energy", 0)

    @property
    def energy_regen(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyDegen, "energy_regen", 0)
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(GWEncoded.ITEM_BASIC + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB3, 0x5D, 0x1, 0x0]), f"Seize The Day")

#endregion SpellcastingWeapon
#endregion Inscriptions

#region Inherent (Old School)
class Inherent(Upgrade):
    mod_type = ItemUpgradeType.Inherent
    id : ItemUpgrade = ItemUpgrade.Inherent
    
    target_item_type : ItemType
    modifier_range: Optional[ModifierRange] = None
    
    def __init__(self):
        super().__init__()
        self.is_inherent = True
    
    def create_encoded_description(self) -> GWStringEncoded:
        if not self.properties:
            return GWStringEncoded(self.encoded_description, f"NO PROPERTIES! Thus no encoded description ({self.__class__.__name__})")
        
        parts = [prop.encoded_description for prop in self.properties.values() if prop.encoded_description]
        return GWEncoded.combine_encoded_strings(parts, "no encoded description")

    def _get_upgrade_property(self, identifier: ModifierIdentifierSpec) -> Optional[ItemProperty]:
        return self._get_property_by_spec(identifier)

    def _get_property_value(self, identifier: ModifierIdentifierSpec, attr_name: str, default):
        prop = self._get_upgrade_property(identifier)
        return getattr(prop, attr_name, default) if prop else default

    def _get_modifier_arg(self, identifier: ModifierIdentifierSpec, arg_index: int, default: int = 0) -> int:
        prop = self._get_upgrade_property(identifier)
        if not prop:
            return default
        return prop.modifier.arg1 if arg_index == 1 else prop.modifier.arg2
    
    @classmethod
    def has_id(cls, upgrade_id: ItemUpgradeId) -> bool:
        return False

    @property
    def is_maxed(self) -> bool:
        if not self.properties or not self.modifier_range:
            return True

        prop = self._get_upgrade_property(self.modifier_range.modifierIdentifier)
        if not prop:
            return False

        value = prop.modifier.arg1 if self.modifier_range.modifier_type == ModifierType.Arg1 else prop.modifier.arg2
        return self.modifier_range.min_value <= value <= self.modifier_range.max_value
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"Inherent: {Utils.humanize_string(self.__class__.__name__)}")
    
#region Weapon
class DamagePlusWhileAboveUpgrade(Inherent, StrengthAndHonor):
    pass


class DamagePlusPercentEnergyMinusUpgrade(Inherent, BrawnOverBrains):
    pass


class DamagePlusStanceUpgrade(Inherent, DanceWithDeath):
    pass


class DamagePlusHexedUpgrade(Inherent, DontFearTheReaper):
    pass


class HalvesCastingTimeGeneralUpgrade(Inherent, DontThinkTwice):
    pass


class DamagePlusEnchantedUpgrade(Inherent, GuidedByFate):
    pass


class DamagePlusPercentArmorMinusAttackingUpgrade(Inherent, ToThePain):
    pass


class DamagePlusVsHexedUpgrade(Inherent, TooMuchInformation):
    pass


class DamagePlusWhileBelowUpgrade(Inherent, VengeanceIsMine):
    pass

class VampiricStrengthUpgrade(Inherent):
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusPercent,
        ModifierIdentifier.HealthDegen,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.DamagePlusPercent, ModifierType.Arg2, 10, 15)
    
    @property
    def damage_increase(self) -> int:
        return self._get_property_value(ModifierIdentifier.DamagePlusPercent, "damage_increase", 0)
    
    @property
    def health_degen(self) -> int:
        return self._get_property_value(ModifierIdentifier.HealthDegen, "health_degen", 0)

class ZealousStrengthUpgrade(Inherent):
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.DamagePlusPercent,
        ModifierIdentifier.EnergyDegen,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.DamagePlusPercent, ModifierType.Arg2, 10, 15)
    
    @property
    def damage_increase(self) -> int:
        return self._get_property_value(ModifierIdentifier.DamagePlusPercent, "damage_increase", 0)
    
    @property
    def energy_degen(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyDegen, "energy_degen", 0)
    
#endregion Weapon

#region Offhand
class ArmorPlusHexedUpgrade(Inherent, BeJustAndFearNot):
    pass


class ArmorPlusWhileBelowUpgrade(Inherent, DownButNotOut):
    pass


class ArmorPlusEnchantedUpgrade(Inherent, FaithIsMyShield):
    pass


class HalvesSkillRechargeItemAttributeUpgrade(Inherent, ForgetMeNot):
    pass


class ArmorPlusAboveUpgrade(Inherent, HailToTheKing):
    pass


class ArmorPlusEnergyMinusUpgrade(Inherent, IgnoranceIsBliss):
    pass


class ArmorPlusCastingUpgrade(Inherent, KnowingIsHalfTheBattle):
    pass


class ArmorPlusHealthMinusUpgrade(Inherent, LifeIsPain):
    pass


class ArmorPlusVsElementalUpgrade(Inherent, ManForAllSeasons):
    pass


class ArmorPlusAttackingUpgrade(Inherent, MightMakesRight):
    pass


class HalvesSkillRechargeGeneralOffhandUpgrade(Inherent, SerenityNow):
    pass


class ArmorPlusVsPhysicalUpgrade(Inherent, SurvivalOfTheFittest):
    pass
#endregion Offhand

#region MartialWeapon
class EnergyPlusUpgrade(Inherent, IHaveThePower):
    pass


class HalvesSkillRechargeGeneralMartialWeaponUpgrade(Inherent, LetTheMemoryLiveAgain):
    pass
#endregion MartialWeapon

#region OffhandOrShield    

class HealthPlusStanceUpgrade(Inherent, OfEnduranceUpgrade):
    target_item_type = ItemType.OffhandOrShield
    pass

class HealthPlusHexedUpgrade(Inherent, OfValorUpgrade):
    target_item_type = ItemType.OffhandOrShield
    pass

class HealthPlusEnchantedUpgrade(Inherent, OfDevotionUpgrade):
    target_item_type = ItemType.OffhandOrShield
    pass

class AttributePlusOneUpgrade(Inherent):
    target_item_type = ItemType.OffhandOrShield
    property_identifiers = [
        ModifierIdentifier.AttributePlusOne,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.AttributePlusOne, ModifierType.Arg1, 11, 20)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.AttributePlusOne, "chance", 0)
    
    @property
    def attribute(self) -> Attribute:
        return self._get_property_value(ModifierIdentifier.AttributePlusOne, "attribute", Attribute.None_)

    @property
    def attribute_level(self) -> int:
        return self._get_property_value(ModifierIdentifier.AttributePlusOne, "attribute_level", 0)
        

class ReduceConditionDurationUpgrade(Inherent, CastOutTheUnclean):
    pass


class BluntArmorPlusVsDamageUpgrade(Inherent, NotTheFace):
    pass


class ColdArmorPlusVsDamageUpgrade(Inherent, LeafOnTheWind):
    pass


class EarthArmorPlusVsDamageUpgrade(Inherent, LikeARollingStone):
    pass


class ReceiveLessDamageUpgrade(Inherent, LuckOfTheDraw):
    pass


class AttributePlusOneItemUpgrade(Inherent, MasterOfMyDomain):
    pass


class ReceiveLessPhysDamageHexedUpgrade(Inherent, NothingToFear):
    pass


class LightningArmorPlusVsDamageUpgrade(Inherent, RidersOnTheStorm):
    pass


class ReceiveLessPhysDamageStanceUpgrade(Inherent, RunForYourLife):
    pass


class ReceiveLessPhysDamageEnchantedUpgrade(Inherent, ShelteredByFaith):
    pass


class FireArmorPlusVsDamageUpgrade(Inherent, SleepNowInTheFire):
    pass


class SlashingArmorPlusVsDamageUpgrade(Inherent, TheRiddleOfSteel):
    pass


class PiercingArmorPlusVsDamageUpgrade(Inherent, ThroughThickAndThin):
    pass

class ArmorVsSpeciesUpgrade(Inherent):
    target_item_type = ItemType.Weapon
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsSpecies,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.ArmorPlusVsSpecies, ModifierType.Arg2, 5, 10)
    
    @property
    def armor(self) -> int:
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsSpecies, "armor", 0)
    
    @property
    def species(self):
        return self._get_property_value(ModifierIdentifier.ArmorPlusVsSpecies, "species", None)

#endregion OffhandOrShield

#region EquippableItem
class HealthPlusUpgrade(Inherent):
    target_item_type = ItemType.EquippableItem
    property_identifiers = [
        any_of(ModifierIdentifier.HealthPlus2, ModifierIdentifier.HealthPlus),
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HealthPlus2, ModifierType.Arg1, 10, 30)

    @property
    def health(self) -> int:
        return self._get_property_value(ModifierIdentifier.HealthPlus2, "health", 0)
    
class HighlySalvageableUpgrade(Inherent, MeasureForMeasure):
    pass


class IncreasedSaleValueUpgrade(Inherent, ShowMeTheMoney):
    pass
#endregion EquippableItem

#region SpellcastingWeapon
class HalvesCastingTimeAttributeUpgrade(Inherent):
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.HalvesCastingTimeAttribute,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HalvesCastingTimeAttribute, ModifierType.Arg1, 10, 20)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.HalvesCastingTimeAttribute, "chance", 0)
    
    @property
    def attribute(self):
        return self._get_property_value(ModifierIdentifier.HalvesCastingTimeAttribute, "attribute", None)
    
class HalvesRechargeTimeAttributeUpgrade(Inherent):
    target_item_type = ItemType.SpellcastingWeapon
    property_identifiers = [
        ModifierIdentifier.HalvesSkillRechargeAttribute,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.HalvesSkillRechargeAttribute, ModifierType.Arg1, 10, 20)

    @property
    def chance(self) -> int:
        return self._get_property_value(ModifierIdentifier.HalvesSkillRechargeAttribute, "chance", 0)
    
    @property
    def attribute(self):
        return self._get_property_value(ModifierIdentifier.HalvesSkillRechargeAttribute, "attribute", None)
    
    
class HalvesCastingTimeItemAttributeUpgrade(Inherent, AptitudeNotAttitude):
    pass


class EnergyPlusWhileBelowUpgrade(Inherent, DontCallItAComeback):
    pass


class EnergyPlusWhileAboveUpgrade(Inherent, HaleAndHearty):
    pass


class EnergyPlusEnchantedUpgrade(Inherent, HaveFaith):
    pass


class EnergyPlusHexedUpgrade(Inherent, IAmSorrow):
    pass


class EnergyPlusEnergyDegenUpgrade(Inherent):
    property_identifiers = [
        ModifierIdentifier.EnergyPlus,
        ModifierIdentifier.EnergyDegen,
    ]
    modifier_range = ModifierRange(ModifierIdentifier.EnergyPlus, ModifierType.Arg2, 10, 15)

    @property
    def energy(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyPlus, "energy", 0)

    @property
    def energy_regen(self) -> int:
        return self._get_property_value(ModifierIdentifier.EnergyDegen, "energy_regen", 0)
    
#endregion SpellcastingWeapon

#endregion Inherent

#endregion Weapon Upgrades

#region Armor Upgrades
class Insignia(Upgrade):
    mod_type = ItemUpgradeType.Prefix

    id : ItemUpgrade
    inventory_icon : str
    rarity : Rarity = Rarity.Blue
    profession : Profession = Profession._None

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), _humanize_identifier(self.__class__.__name__))
    
class Rune(Upgrade):
    RUNE_PATTERNS = {
        ServerLanguage.English: r"^.*?\bRune\b\s*",
        ServerLanguage.German: r"^.*?Rune\b\s*",
        ServerLanguage.French: r"^Rune(?:\s+de\s+\S+)?\s*",
        ServerLanguage.Italian: r"^Runa(?:\s+del\s+\S+)?\s*",
        ServerLanguage.Spanish: r"^Runa(?:\s+de\s+\S+)?\s*",
        ServerLanguage.Korean: r"^.*?룬",
        ServerLanguage.Japanese: r"^.*?ルーン",
        ServerLanguage.TraditionalChinese: r"^.*?符文",
        ServerLanguage.Polish: r"^Runa(?:\s+\S+)?\s*",
        ServerLanguage.Russian: r"^.*?\bRune\b\s*",
    }
    
    mod_type = ItemUpgradeType.Suffix

    id : ItemUpgrade
    inventory_icon : str
    rarity : Rarity = Rarity.Blue
    profession : Profession = Profession._None

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), _humanize_identifier(self.__class__.__name__))

class AttributeRune(Rune):
    attribute : Attribute
    attribute_level : int

    @classmethod
    def _pre_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, all_modifiers: list[DecodedModifier], remaining_modifiers: list[DecodedModifier]) -> None:
        attribute_rune = cast("AttributeRune", upgrade)
        attribute_rune.attribute = Attribute(mod.arg1)
        attribute_rune.attribute_level = mod.arg2

    def create_encoded_description(self) -> GWStringEncoded:
        attribute = GWEncoded.ATTRIBUTE_NAMES.get(self.attribute, bytes())
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")

        match self.attribute_level:
            case 3:
                gold_value = 100
                encoded_description = bytes([ 
                                            *self.get_text_color(), *GWEncoded.PLUS_NUM_TEMPLATE, *attribute, 0x1, 0x0, 0x1, 0x1, self.attribute_level, 0x1, 0x1, 0x0, *GWEncoded.ITEM_DULL, *GWEncoded.NOT_STACKING_BYTES, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 
                                            *self.get_text_color(), *GWEncoded.HEALTH_MINUS_NUM, 75, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1])
            case 2:
                encoded_description = bytes([
                                            *self.get_text_color(), *GWEncoded.PLUS_NUM_TEMPLATE, *attribute, 0x1, 0x0, 0x1, 0x1, self.attribute_level, 0x1, 0x1, 0x0, *GWEncoded.ITEM_DULL, *GWEncoded.NOT_STACKING_BYTES, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 
                                            *self.get_text_color(), *GWEncoded.HEALTH_MINUS_NUM, 35, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1])
            case _:
                encoded_description = bytes([
                                            *self.get_text_color(), *GWEncoded.PLUS_NUM_TEMPLATE, *attribute, 0x1, 0x0, 0x1, 0x1, self.attribute_level, 0x1, 0x1, 0x0, *GWEncoded.ITEM_DULL, *GWEncoded.NOT_STACKING_BYTES, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1])

        return GWStringEncoded(encoded_description, fallback)

class AppliesToRune(Upgrade):
    pass

class UpgradeRune(Upgrade):
    pass

#region No Profession

class SurvivorInsignia(Insignia):
    id = ItemUpgrade.SurvivorInsignia
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE3, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x67, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x68, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x69, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

class RadiantInsignia(Insignia):
    id = ItemUpgrade.RadiantInsignia
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE4, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x4F, 0xA, 0x1, 0x0, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x67, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x4F, 0xA, 0x1, 0x0, 0x1, 0x1, 0x2, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x68, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x4F, 0xA, 0x1, 0x0, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x69, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

class StalwartInsignia(Insignia):
    id = ItemUpgrade.StalwartInsignia
    property_identifiers = [
        ModifierIdentifier.ArmorPlusVsPhysical,
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE6, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB0, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

class BrawlersInsignia(Insignia):
    id = ItemUpgrade.BrawlersInsignia
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE9, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB4, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

class BlessedInsignia(Insignia):
    id = ItemUpgrade.BlessedInsignia
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE7, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9C, 0x4D, 0xA, 0x1, 0xB6, 0x4, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)
    
class HeraldsInsignia(Insignia):
    id = ItemUpgrade.HeraldsInsignia
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE8, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB9, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)
    
class SentrysInsignia(Insignia):
    id = ItemUpgrade.SentrysInsignia
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE5, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xBA, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)
    
class RuneOfMinorVigor(Rune):
    id = ItemUpgrade.RuneOfMinorVigor
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xB0, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB1, 0x64, 0x1, 0x1, 0x1E, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

class RuneOfMinorVigor2(Rune):
    id = ItemUpgrade.RuneOfMinorVigor2
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xB0, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB1, 0x64, 0x1, 0x1, 0x1E, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

class RuneOfVitae(Rune):
    id = ItemUpgrade.RuneOfVitae
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

class RuneOfAttunement(Rune):
    id = ItemUpgrade.RuneOfAttunement
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xD, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x4F, 0xA, 0x1, 0x0, 0x1, 0x1, 0x2, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

class RuneOfMajorVigor(Rune):
    id = ItemUpgrade.RuneOfMajorVigor
    rarity = Rarity.Purple

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xB0, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([*self.get_text_color(), 0x8, 0x1, 0xA, 0x1, 0xB1, 0x64, 0x1, 0x1, 0x29, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)
    
class RuneOfRecovery(Rune):
    id = ItemUpgrade.RuneOfRecovery
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.ReduceConditionTupleDuration,
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([*self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x96, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, *self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x90, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

class RuneOfRestoration(Rune):
    id = ItemUpgrade.RuneOfRestoration
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.ReduceConditionTupleDuration,
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x10, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([*self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x88, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, *self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x8E, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

class RuneOfClarity(Rune):
    id = ItemUpgrade.RuneOfClarity
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.ReduceConditionTupleDuration,
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x11, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([*self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x8A, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, *self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x98, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

class RuneOfPurity(Rune):
    id = ItemUpgrade.RuneOfPurity
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.ReduceConditionTupleDuration,
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x12, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([*self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x92, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, *self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x94, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

class RuneOfSuperiorVigor(Rune):
    id = ItemUpgrade.RuneOfSuperiorVigor
    rarity = Rarity.Gold

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xB0, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([*self.get_text_color(), 0x8, 0x1, 0xA, 0x1, 0xB1, 0x64, 0x1, 0x1, 0x32, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)


#endregion No Profession

#region Warrior

class KnightsInsignia(Insignia):
    id = ItemUpgrade.KnightsInsignia
    profession = Profession.Warrior
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x41, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x4, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))
    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x7E, 0xA, 0xA, 0x1, 0x1, 0x81, 0x4F, 0x5D, 0x1, 0x0, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: "Received physical damage -3"
    }

class LieutenantsInsignia(Insignia):
    id = ItemUpgrade.LieutenantsInsignia
    profession = Profession.Warrior
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x41, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEE, 0x5C, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0x97, 0x64, 0x1, 0x1, 0x14, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x7E, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x14, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Reduces Hex durations on you by 20% and damage dealt by you by 5% (Non-stacking)\nArmor -20"
    }

class StonefistInsignia(Insignia):
    id = ItemUpgrade.StonefistInsignia
    profession = Profession.Warrior
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x41, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF0, 0x5C, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0x99, 0x64, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Increases knockdown time on foes by 1 second.\n(Maximum: 3 seconds)"
    }

class DreadnoughtInsignia(Insignia):
    id = ItemUpgrade.DreadnoughtInsignia
    profession = Profession.Warrior
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x41, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x3, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. elemental damage)"
    }

class SentinelsInsignia(Insignia):
    id = ItemUpgrade.SentinelsInsignia
    profession = Profession.Warrior
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x41, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x5, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x14, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xA9, 0xA, 0xA, 0x1, 0x40, 0x9, 0x1, 0x0, 0x1, 0x1, 0xD, 0x1, 0x2, 0x0, 0xAB, 0xA, 0x2, 0x0, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +20 (Requires 13 Strength, vs. elemental damage)"
    }

class WarriorRuneOfMinorAbsorption(Rune):
    id = ItemUpgrade.WarriorRuneOfMinorAbsorption
    profession = Profession.Warrior
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xFA, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    encoded_description = bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xFB, 0x64, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1])
    

class WarriorRuneOfMinorTactics(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMinorTactics
    profession = Profession.Warrior
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x48, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfMinorStrength(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMinorStrength
    profession = Profession.Warrior
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x40, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfMinorAxeMastery(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMinorAxeMastery
    profession = Profession.Warrior
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x42, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfMinorHammerMastery(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMinorHammerMastery
    profession = Profession.Warrior
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x44, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfMinorSwordsmanship(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMinorSwordsmanship
    profession = Profession.Warrior
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x46, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfMajorAbsorption(Rune):
    id = ItemUpgrade.WarriorRuneOfMajorAbsorption
    profession = Profession.Warrior
    rarity = Rarity.Purple

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xFA, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([*self.get_text_color(), 0x8, 0x1, 0xA, 0x1, 0xFB, 0x64, 0x1, 0x1, 0x2, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    
class WarriorRuneOfMajorTactics(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMajorTactics
    profession = Profession.Warrior
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x48, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfMajorStrength(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMajorStrength
    profession = Profession.Warrior
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x40, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfMajorAxeMastery(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMajorAxeMastery
    profession = Profession.Warrior
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x42, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfMajorHammerMastery(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMajorHammerMastery
    profession = Profession.Warrior
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x44, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfMajorSwordsmanship(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfMajorSwordsmanship
    profession = Profession.Warrior
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x46, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfSuperiorAbsorption(Rune):
    id = ItemUpgrade.WarriorRuneOfSuperiorAbsorption
    profession = Profession.Warrior
    rarity = Rarity.Gold

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xFA, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([*self.get_text_color(), 0x8, 0x1, 0xA, 0x1, 0xFB, 0x64, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)


class WarriorRuneOfSuperiorTactics(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorTactics
    profession = Profession.Warrior
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x48, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfSuperiorStrength(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorStrength
    profession = Profession.Warrior
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x40, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfSuperiorAxeMastery(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorAxeMastery
    profession = Profession.Warrior
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x42, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfSuperiorHammerMastery(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorHammerMastery
    profession = Profession.Warrior
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x44, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class WarriorRuneOfSuperiorSwordsmanship(AttributeRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorSwordsmanship
    profession = Profession.Warrior
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x46, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class UpgradeMinorRuneWarrior(UpgradeRune):
    id = ItemUpgrade.UpgradeMinorRuneWarrior
    profession = Profession.Warrior
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneWarrior(UpgradeRune):
    id = ItemUpgrade.UpgradeMajorRuneWarrior
    profession = Profession.Warrior
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneWarrior(UpgradeRune):
    id = ItemUpgrade.UpgradeSuperiorRuneWarrior
    profession = Profession.Warrior
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneWarrior(AppliesToRune):
    id = ItemUpgrade.AppliesToMinorRuneWarrior
    profession = Profession.Warrior
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneWarrior(AppliesToRune):
    id = ItemUpgrade.AppliesToMajorRuneWarrior
    profession = Profession.Warrior
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneWarrior(AppliesToRune):
    id = ItemUpgrade.AppliesToSuperiorRuneWarrior
    profession = Profession.Warrior
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Warrior

#region Ranger

class FrostboundInsignia(Insignia):
    id = ItemUpgrade.FrostboundInsignia
    profession = Profession.Ranger
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x42, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xFE, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE1, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +15 (vs. Cold damage)"
    }

class PyreboundInsignia(Insignia):
    id = ItemUpgrade.PyreboundInsignia
    profession = Profession.Ranger
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x42, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xFD, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE4, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +15 (vs. Fire damage)"
    }

class StormboundInsignia(Insignia):
    id = ItemUpgrade.StormboundInsignia
    profession = Profession.Ranger
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x42, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xFF, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE3, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +15 (vs. Lightning damage)"
    }

class ScoutsInsignia(Insignia):
    id = ItemUpgrade.ScoutsInsignia
    profession = Profession.Ranger
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x42, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x1, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xBF, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +10 (while using a Preparation)"
    }

class EarthboundInsignia(Insignia):
    id = ItemUpgrade.EarthboundInsignia
    profession = Profession.Ranger
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x42, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x0, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE2, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +15 (vs. Earth damage)"
    }

class BeastmastersInsignia(Insignia):
    id = ItemUpgrade.BeastmastersInsignia
    profession = Profession.Ranger
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x42, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x2, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5E, 0x4D, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +10 (while your pet is alive)"
    }

class RangerRuneOfMinorWildernessSurvival(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMinorWildernessSurvival
    profession = Profession.Ranger
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x54, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RangerRuneOfMinorExpertise(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMinorExpertise
    profession = Profession.Ranger
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x52, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RangerRuneOfMinorBeastMastery(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMinorBeastMastery
    profession = Profession.Ranger
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x50, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RangerRuneOfMinorMarksmanship(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMinorMarksmanship
    profession = Profession.Ranger
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x56, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RangerRuneOfMajorWildernessSurvival(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMajorWildernessSurvival
    profession = Profession.Ranger
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x54, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RangerRuneOfMajorExpertise(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMajorExpertise
    profession = Profession.Ranger
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x52, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RangerRuneOfMajorBeastMastery(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMajorBeastMastery
    profession = Profession.Ranger
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x50, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RangerRuneOfMajorMarksmanship(AttributeRune):
    id = ItemUpgrade.RangerRuneOfMajorMarksmanship
    profession = Profession.Ranger
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x56, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RangerRuneOfSuperiorWildernessSurvival(AttributeRune):
    id = ItemUpgrade.RangerRuneOfSuperiorWildernessSurvival
    profession = Profession.Ranger
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x54, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RangerRuneOfSuperiorExpertise(AttributeRune):
    id = ItemUpgrade.RangerRuneOfSuperiorExpertise
    profession = Profession.Ranger
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x52, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RangerRuneOfSuperiorBeastMastery(AttributeRune):
    id = ItemUpgrade.RangerRuneOfSuperiorBeastMastery
    profession = Profession.Ranger
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x50, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RangerRuneOfSuperiorMarksmanship(AttributeRune):
    id = ItemUpgrade.RangerRuneOfSuperiorMarksmanship
    profession = Profession.Ranger
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x56, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class UpgradeMinorRuneRanger(UpgradeRune):
    id = ItemUpgrade.UpgradeMinorRuneRanger
    profession = Profession.Ranger
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneRanger(UpgradeRune):
    id = ItemUpgrade.UpgradeMajorRuneRanger
    profession = Profession.Ranger
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneRanger(UpgradeRune):
    id = ItemUpgrade.UpgradeSuperiorRuneRanger
    profession = Profession.Ranger
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneRanger(AppliesToRune):
    id = ItemUpgrade.AppliesToMinorRuneRanger
    profession = Profession.Ranger
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneRanger(AppliesToRune):
    id = ItemUpgrade.AppliesToMajorRuneRanger
    profession = Profession.Ranger
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneRanger(AppliesToRune):
    id = ItemUpgrade.AppliesToSuperiorRuneRanger
    profession = Profession.Ranger
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Ranger

#region Monk

class WanderersInsignia(Insignia):
    id = ItemUpgrade.WanderersInsignia
    profession = Profession.Monk
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x40, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF6, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. elemental damage)"
    }

class DisciplesInsignia(Insignia):
    id = ItemUpgrade.DisciplesInsignia
    profession = Profession.Monk
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x40, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF7, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9C, 0x4D, 0xA, 0x1, 0xAC, 0x4, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +15 (while affected by a Condition)"
    }

class AnchoritesInsignia(Insignia):
    id = ItemUpgrade.AnchoritesInsignia
    profession = Profession.Monk
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x40, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF5, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5F, 0x4D, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5F, 0x4D, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5F, 0x4D, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +5 (while recharging 1 or more skills)\nArmor +5 (while recharging 3 or more skills)\nArmor +5 (while recharging 5 or more skills)"

    }

class MonkRuneOfMinorHealingPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMinorHealingPrayers
    profession = Profession.Monk
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MonkRuneOfMinorSmitingPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMinorSmitingPrayers
    profession = Profession.Monk
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MonkRuneOfMinorProtectionPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMinorProtectionPrayers
    profession = Profession.Monk
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MonkRuneOfMinorDivineFavor(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMinorDivineFavor
    profession = Profession.Monk
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x38, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MonkRuneOfMajorHealingPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMajorHealingPrayers
    profession = Profession.Monk
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MonkRuneOfMajorSmitingPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMajorSmitingPrayers
    profession = Profession.Monk
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MonkRuneOfMajorProtectionPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMajorProtectionPrayers
    profession = Profession.Monk
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MonkRuneOfMajorDivineFavor(AttributeRune):
    id = ItemUpgrade.MonkRuneOfMajorDivineFavor
    profession = Profession.Monk
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x38, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MonkRuneOfSuperiorHealingPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfSuperiorHealingPrayers
    profession = Profession.Monk
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MonkRuneOfSuperiorSmitingPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfSuperiorSmitingPrayers
    profession = Profession.Monk
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MonkRuneOfSuperiorProtectionPrayers(AttributeRune):
    id = ItemUpgrade.MonkRuneOfSuperiorProtectionPrayers
    profession = Profession.Monk
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MonkRuneOfSuperiorDivineFavor(AttributeRune):
    id = ItemUpgrade.MonkRuneOfSuperiorDivineFavor
    profession = Profession.Monk
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x38, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class UpgradeMinorRuneMonk(UpgradeRune):
    id = ItemUpgrade.UpgradeMinorRuneMonk
    profession = Profession.Monk
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneMonk(UpgradeRune):
    id = ItemUpgrade.UpgradeMajorRuneMonk
    profession = Profession.Monk
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneMonk(UpgradeRune):
    id = ItemUpgrade.UpgradeSuperiorRuneMonk
    profession = Profession.Monk
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneMonk(AppliesToRune):
    id = ItemUpgrade.AppliesToMinorRuneMonk
    profession = Profession.Monk
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneMonk(AppliesToRune):
    id = ItemUpgrade.AppliesToMajorRuneMonk
    profession = Profession.Monk
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneMonk(AppliesToRune):
    id = ItemUpgrade.AppliesToSuperiorRuneMonk
    profession = Profession.Monk
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Monk

#region Necromancer

class BloodstainedInsignia(Insignia):
    id = ItemUpgrade.BloodstainedInsignia
    profession = Profession.Necromancer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0xB8, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEF, 0x5C, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0x7F, 0x64, 0x1, 0x1, 0x0, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Reduces casting time of spells that exploit corpses by 25% (Non-stacking)"
    }

class TormentorsInsignia(Insignia):
    id = ItemUpgrade.TormentorsInsignia
    profession = Profession.Necromancer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0xB8, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xFA, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x1, 0x81, 0xE1, 0x53, 0xA, 0x1, 0xE7, 0x8, 0x1, 0x0, 0x1, 0x1, 0x6, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x67, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x1, 0x81, 0xE1, 0x53, 0xA, 0x1, 0xE7, 0x8, 0x1, 0x0, 0x1, 0x1, 0x4, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x68, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x1, 0x81, 0xE1, 0x53, 0xA, 0x1, 0xE7, 0x8, 0x1, 0x0, 0x1, 0x1, 0x2, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x69, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Holy damage you receive increased by 6 (on chest armor)\nHoly damage you receive increased by 4 (on leg armor)\nHoly damage you receive increased by 2 (on other armor)\nArmor +10"

    }

class BonelaceInsignia(Insignia):
    id = ItemUpgrade.BonelaceInsignia
    profession = Profession.Necromancer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0xB8, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xFC, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xDF, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +15 (vs. Piercing damage)"
    }

class MinionMastersInsignia(Insignia):
    id = ItemUpgrade.MinionMastersInsignia
    profession = Profession.Necromancer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0xB8, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF9, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x4E, 0x6D, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x4E, 0x6D, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x4E, 0x6D, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +5 (while you control 1 or more minions)\nArmor +5 (while you control 3 or more minions)\nArmor +5 (while you control 5 or more minions)"

    }

class BlightersInsignia(Insignia):
    id = ItemUpgrade.BlightersInsignia
    profession = Profession.Necromancer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0xB8, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xFB, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x14, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9C, 0x4D, 0xA, 0x1, 0xB4, 0x4, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +20 (while affected by a Hex Spell)"
    }

class UndertakersInsignia(Insignia):
    id = ItemUpgrade.UndertakersInsignia
    profession = Profession.Necromancer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0xB8, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF8, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xBB, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0x50, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xBB, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0x3C, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xBB, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0x28, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xBB, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0x14, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +5 (while health is below 80%)\nArmor +5 (while health is below 60%)\nArmor +5 (while health is below 40%)\nArmor +5 (while health is below 20%)"

    }

class NecromancerRuneOfMinorBloodMagic(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMinorBloodMagic
    profession = Profession.Necromancer
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x26, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class NecromancerRuneOfMinorDeathMagic(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMinorDeathMagic
    profession = Profession.Necromancer
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class NecromancerRuneOfMinorCurses(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMinorCurses
    profession = Profession.Necromancer
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x28, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class NecromancerRuneOfMinorSoulReaping(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMinorSoulReaping
    profession = Profession.Necromancer
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class NecromancerRuneOfMajorBloodMagic(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMajorBloodMagic
    profession = Profession.Necromancer
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x26, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class NecromancerRuneOfMajorDeathMagic(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMajorDeathMagic
    profession = Profession.Necromancer
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class NecromancerRuneOfMajorCurses(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMajorCurses
    profession = Profession.Necromancer
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x28, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class NecromancerRuneOfMajorSoulReaping(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfMajorSoulReaping
    profession = Profession.Necromancer
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class NecromancerRuneOfSuperiorBloodMagic(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfSuperiorBloodMagic
    profession = Profession.Necromancer
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x26, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class NecromancerRuneOfSuperiorDeathMagic(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfSuperiorDeathMagic
    profession = Profession.Necromancer
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class NecromancerRuneOfSuperiorCurses(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfSuperiorCurses
    profession = Profession.Necromancer
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x28, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class NecromancerRuneOfSuperiorSoulReaping(AttributeRune):
    id = ItemUpgrade.NecromancerRuneOfSuperiorSoulReaping
    profession = Profession.Necromancer
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class UpgradeMinorRuneNecromancer(UpgradeRune):
    id = ItemUpgrade.UpgradeMinorRuneNecromancer
    profession = Profession.Necromancer
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneNecromancer(UpgradeRune):
    id = ItemUpgrade.UpgradeMajorRuneNecromancer
    profession = Profession.Necromancer
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneNecromancer(UpgradeRune):
    id = ItemUpgrade.UpgradeSuperiorRuneNecromancer
    profession = Profession.Necromancer
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneNecromancer(AppliesToRune):
    id = ItemUpgrade.AppliesToMinorRuneNecromancer
    profession = Profession.Necromancer
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneNecromancer(AppliesToRune):
    id = ItemUpgrade.AppliesToMajorRuneNecromancer
    profession = Profession.Necromancer
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneNecromancer(AppliesToRune):
    id = ItemUpgrade.AppliesToSuperiorRuneNecromancer
    profession = Profession.Necromancer
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Necromancer

#region Mesmer

class VirtuososInsignia(Insignia):
    id = ItemUpgrade.VirtuososInsignia
    profession = Profession.Mesmer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3C, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF4, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xC0, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +15 (while activating skills)"
    }

class ArtificersInsignia(Insignia):
    id = ItemUpgrade.ArtificersInsignia
    profession = Profession.Mesmer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3C, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF3, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0xE2, 0x53, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +3 (for each equipped Signet)"
    }

class ProdigysInsignia(Insignia):
    id = ItemUpgrade.ProdigysInsignia
    profession = Profession.Mesmer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3C, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF2, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5F, 0x4D, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5F, 0x4D, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5F, 0x4D, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +5 (while recharging 1 or more skills)\nArmor +5 (while recharging 3 or more skills)\nArmor +5 (while recharging 5 or more skills)"
    }

class MesmerRuneOfMinorFastCasting(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMinorFastCasting
    profession = Profession.Mesmer
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MesmerRuneOfMinorDominationMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMinorDominationMagic
    profession = Profession.Mesmer
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x22, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MesmerRuneOfMinorIllusionMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMinorIllusionMagic
    profession = Profession.Mesmer
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x20, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MesmerRuneOfMinorInspirationMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMinorInspirationMagic
    profession = Profession.Mesmer
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x24, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MesmerRuneOfMajorFastCasting(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMajorFastCasting
    profession = Profession.Mesmer
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MesmerRuneOfMajorDominationMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMajorDominationMagic
    profession = Profession.Mesmer
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x22, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MesmerRuneOfMajorIllusionMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMajorIllusionMagic
    profession = Profession.Mesmer
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x20, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MesmerRuneOfMajorInspirationMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfMajorInspirationMagic
    profession = Profession.Mesmer
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x24, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MesmerRuneOfSuperiorFastCasting(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfSuperiorFastCasting
    profession = Profession.Mesmer
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MesmerRuneOfSuperiorDominationMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfSuperiorDominationMagic
    profession = Profession.Mesmer
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x22, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MesmerRuneOfSuperiorIllusionMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfSuperiorIllusionMagic
    profession = Profession.Mesmer
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x20, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class MesmerRuneOfSuperiorInspirationMagic(AttributeRune):
    id = ItemUpgrade.MesmerRuneOfSuperiorInspirationMagic
    profession = Profession.Mesmer
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x24, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class UpgradeMinorRuneMesmer(UpgradeRune):
    id = ItemUpgrade.UpgradeMinorRuneMesmer
    profession = Profession.Mesmer
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneMesmer(UpgradeRune):
    id = ItemUpgrade.UpgradeMajorRuneMesmer
    profession = Profession.Mesmer
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneMesmer(UpgradeRune):
    id = ItemUpgrade.UpgradeSuperiorRuneMesmer
    profession = Profession.Mesmer
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneMesmer(AppliesToRune):
    id = ItemUpgrade.AppliesToMinorRuneMesmer
    profession = Profession.Mesmer
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneMesmer(AppliesToRune):
    id = ItemUpgrade.AppliesToMajorRuneMesmer
    profession = Profession.Mesmer
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneMesmer(AppliesToRune):
    id = ItemUpgrade.AppliesToSuperiorRuneMesmer
    profession = Profession.Mesmer
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Mesmer

#region Elementalist

class HydromancerInsignia(Insignia):
    id = ItemUpgrade.HydromancerInsignia
    profession = Profession.Elementalist
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3F, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF1, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE1, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. elemental damage)\nArmor +10 (vs. Cold damage)"
    }

class GeomancerInsignia(Insignia):
    id = ItemUpgrade.GeomancerInsignia
    profession = Profession.Elementalist
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3F, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEF, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE2, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. elemental damage)\nArmor +10 (vs. Earth damage)"
    }

class PyromancerInsignia(Insignia):
    id = ItemUpgrade.PyromancerInsignia
    profession = Profession.Elementalist
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3F, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF0, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE4, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. elemental damage)\nArmor +10 (vs. Fire damage)"
    }

class AeromancerInsignia(Insignia):
    id = ItemUpgrade.AeromancerInsignia
    profession = Profession.Elementalist
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3F, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEE, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE3, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. elemental damage)\nArmor +10 (vs. Lightning damage)"
    }

class PrismaticInsignia(Insignia):
    id = ItemUpgrade.PrismaticInsignia
    profession = Profession.Elementalist
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3F, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xED, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xA9, 0xA, 0xA, 0x1, 0x2E, 0x9, 0x1, 0x0, 0x1, 0x1, 0x9, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xA9, 0xA, 0xA, 0x1, 0x30, 0x9, 0x1, 0x0, 0x1, 0x1, 0x9, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xA9, 0xA, 0xA, 0x1, 0x34, 0x9, 0x1, 0x0, 0x1, 0x1, 0x9, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xA9, 0xA, 0xA, 0x1, 0x36, 0x9, 0x1, 0x0, 0x1, 0x1, 0x9, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +5 (requires 9 Air Magic)\nArmor +5 (requires 9 Earth Magic)\nArmor +5 (requires 9 Fire Magic)\nArmor +5 (requires 9 Water Magic)"

    }

class ElementalistRuneOfMinorEnergyStorage(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMinorEnergyStorage
    profession = Profession.Elementalist
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x32, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfMinorFireMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMinorFireMagic
    profession = Profession.Elementalist
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x34, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfMinorAirMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMinorAirMagic
    profession = Profession.Elementalist
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfMinorEarthMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMinorEarthMagic
    profession = Profession.Elementalist
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x30, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfMinorWaterMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMinorWaterMagic
    profession = Profession.Elementalist
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x36, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfMajorEnergyStorage(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMajorEnergyStorage
    profession = Profession.Elementalist
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x32, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfMajorFireMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMajorFireMagic
    profession = Profession.Elementalist
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x34, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfMajorAirMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMajorAirMagic
    profession = Profession.Elementalist
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfMajorEarthMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMajorEarthMagic
    profession = Profession.Elementalist
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x30, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfMajorWaterMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfMajorWaterMagic
    profession = Profession.Elementalist
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x36, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfSuperiorEnergyStorage(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorEnergyStorage
    profession = Profession.Elementalist
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x32, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfSuperiorFireMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorFireMagic
    profession = Profession.Elementalist
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x34, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfSuperiorAirMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorAirMagic
    profession = Profession.Elementalist
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfSuperiorEarthMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorEarthMagic
    profession = Profession.Elementalist
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x30, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ElementalistRuneOfSuperiorWaterMagic(AttributeRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorWaterMagic
    profession = Profession.Elementalist
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x36, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class UpgradeMinorRuneElementalist(UpgradeRune):
    id = ItemUpgrade.UpgradeMinorRuneElementalist
    profession = Profession.Elementalist
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneElementalist(UpgradeRune):
    id = ItemUpgrade.UpgradeMajorRuneElementalist
    profession = Profession.Elementalist
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneElementalist(UpgradeRune):
    id = ItemUpgrade.UpgradeSuperiorRuneElementalist
    profession = Profession.Elementalist
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneElementalist(AppliesToRune):
    id = ItemUpgrade.AppliesToMinorRuneElementalist
    profession = Profession.Elementalist
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneElementalist(AppliesToRune):
    id = ItemUpgrade.AppliesToMajorRuneElementalist
    profession = Profession.Elementalist
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneElementalist(AppliesToRune):
    id = ItemUpgrade.AppliesToSuperiorRuneElementalist
    profession = Profession.Elementalist
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Elementalist

#region Assassin

class VanguardsInsignia(Insignia):
    id = ItemUpgrade.VanguardsInsignia
    profession = Profession.Assassin
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3B, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xB, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB0, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xDE, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. physical damage)\nArmor +10 (vs. Blunt damage)"
    }

class InfiltratorsInsignia(Insignia):
    id = ItemUpgrade.InfiltratorsInsignia
    profession = Profession.Assassin
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3B, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x9, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB0, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xDF, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. physical damage)\nArmor +10 (vs. Piercing damage)"
    }

class SaboteursInsignia(Insignia):
    id = ItemUpgrade.SaboteursInsignia
    profession = Profession.Assassin
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3B, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xA, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB0, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE0, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +10 (vs. physical damage)\nArmor +10 (vs. Slashing damage)"
    }

class NightstalkersInsignia(Insignia):
    id = ItemUpgrade.NightstalkersInsignia
    profession = Profession.Assassin
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3B, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xC, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB4, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +15 (while attacking)"
    }

class AssassinRuneOfMinorCriticalStrikes(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMinorCriticalStrikes
    profession = Profession.Assassin
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x58, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class AssassinRuneOfMinorDaggerMastery(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMinorDaggerMastery
    profession = Profession.Assassin
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class AssassinRuneOfMinorDeadlyArts(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMinorDeadlyArts
    profession = Profession.Assassin
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class AssassinRuneOfMinorShadowArts(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMinorShadowArts
    profession = Profession.Assassin
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class AssassinRuneOfMajorCriticalStrikes(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMajorCriticalStrikes
    profession = Profession.Assassin
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x58, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class AssassinRuneOfMajorDaggerMastery(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMajorDaggerMastery
    profession = Profession.Assassin
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class AssassinRuneOfMajorDeadlyArts(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMajorDeadlyArts
    profession = Profession.Assassin
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class AssassinRuneOfMajorShadowArts(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfMajorShadowArts
    profession = Profession.Assassin
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class AssassinRuneOfSuperiorCriticalStrikes(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfSuperiorCriticalStrikes
    profession = Profession.Assassin
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x58, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class AssassinRuneOfSuperiorDaggerMastery(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfSuperiorDaggerMastery
    profession = Profession.Assassin
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class AssassinRuneOfSuperiorDeadlyArts(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfSuperiorDeadlyArts
    profession = Profession.Assassin
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class AssassinRuneOfSuperiorShadowArts(AttributeRune):
    id = ItemUpgrade.AssassinRuneOfSuperiorShadowArts
    profession = Profession.Assassin
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class UpgradeMinorRuneAssassin(UpgradeRune):
    id = ItemUpgrade.UpgradeMinorRuneAssassin
    profession = Profession.Assassin
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneAssassin(UpgradeRune):
    id = ItemUpgrade.UpgradeMajorRuneAssassin
    profession = Profession.Assassin
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneAssassin(UpgradeRune):
    id = ItemUpgrade.UpgradeSuperiorRuneAssassin
    profession = Profession.Assassin
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneAssassin(AppliesToRune):
    id = ItemUpgrade.AppliesToMinorRuneAssassin
    profession = Profession.Assassin
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneAssassin(AppliesToRune):
    id = ItemUpgrade.AppliesToMajorRuneAssassin
    profession = Profession.Assassin
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneAssassin(AppliesToRune):
    id = ItemUpgrade.AppliesToSuperiorRuneAssassin
    profession = Profession.Assassin
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Assassin

#region Ritualist

class ShamansInsignia(Insignia):
    id = ItemUpgrade.ShamansInsignia
    profession = Profession.Ritualist
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x44, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x6, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x82, 0x7D, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x82, 0x7D, 0x1, 0x1, 0x2, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x82, 0x7D, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +5 (while you control 1 or more Spirits)\nArmor +5 (while you control 2 or more Spirits)\nArmor +5 (while you control 3 or more Spirits)"

    }

class GhostForgeInsignia(Insignia):
    id = ItemUpgrade.GhostForgeInsignia
    profession = Profession.Ritualist
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x44, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x8, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9C, 0x4D, 0xA, 0x1, 0xBA, 0x4, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +15 (while affected by a Weapon Spell)"

    }

class MysticsInsignia(Insignia):
    id = ItemUpgrade.MysticsInsignia
    profession = Profession.Ritualist
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x44, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x7, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xC0, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +15 (while activating skills)"
    }

class RitualistRuneOfMinorChannelingMagic(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMinorChannelingMagic
    profession = Profession.Ritualist
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x66, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RitualistRuneOfMinorRestorationMagic(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMinorRestorationMagic
    profession = Profession.Ritualist
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x64, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RitualistRuneOfMinorCommuning(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMinorCommuning
    profession = Profession.Ritualist
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x60, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RitualistRuneOfMinorSpawningPower(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMinorSpawningPower
    profession = Profession.Ritualist
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x62, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RitualistRuneOfMajorChannelingMagic(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMajorChannelingMagic
    profession = Profession.Ritualist
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x66, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RitualistRuneOfMajorRestorationMagic(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMajorRestorationMagic
    profession = Profession.Ritualist
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x64, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RitualistRuneOfMajorCommuning(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMajorCommuning
    profession = Profession.Ritualist
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x60, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RitualistRuneOfMajorSpawningPower(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfMajorSpawningPower
    profession = Profession.Ritualist
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x62, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RitualistRuneOfSuperiorChannelingMagic(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfSuperiorChannelingMagic
    profession = Profession.Ritualist
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x66, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RitualistRuneOfSuperiorRestorationMagic(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfSuperiorRestorationMagic
    profession = Profession.Ritualist
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x64, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RitualistRuneOfSuperiorCommuning(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfSuperiorCommuning
    profession = Profession.Ritualist
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x60, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class RitualistRuneOfSuperiorSpawningPower(AttributeRune):
    id = ItemUpgrade.RitualistRuneOfSuperiorSpawningPower
    profession = Profession.Ritualist
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x62, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class UpgradeMinorRuneRitualist(UpgradeRune):
    id = ItemUpgrade.UpgradeMinorRuneRitualist
    profession = Profession.Ritualist
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneRitualist(UpgradeRune):
    id = ItemUpgrade.UpgradeMajorRuneRitualist
    profession = Profession.Ritualist
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneRitualist(UpgradeRune):
    id = ItemUpgrade.UpgradeSuperiorRuneRitualist
    profession = Profession.Ritualist
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneRitualist(AppliesToRune):
    id = ItemUpgrade.AppliesToMinorRuneRitualist
    profession = Profession.Ritualist
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneRitualist(AppliesToRune):
    id = ItemUpgrade.AppliesToMajorRuneRitualist
    profession = Profession.Ritualist
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneRitualist(AppliesToRune):
    id = ItemUpgrade.AppliesToSuperiorRuneRitualist
    profession = Profession.Ritualist
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Ritualist

#region Dervish

class WindwalkerInsignia(Insignia):
    id = ItemUpgrade.WindwalkerInsignia
    profession = Profession.Dervish
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x43, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEC, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9E, 0x4D, 0xA, 0x1, 0xB6, 0x4, 0x1, 0x0, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9E, 0x4D, 0xA, 0x1, 0xB6, 0x4, 0x1, 0x0, 0x1, 0x1, 0x2, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9E, 0x4D, 0xA, 0x1, 0xB6, 0x4, 0x1, 0x0, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9E, 0x4D, 0xA, 0x1, 0xB6, 0x4, 0x1, 0x0, 0x1, 0x1, 0x4, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +5 (while affected by 1 or more Enchantment Spells)\nArmor +5 (while affected by 2 or more Enchantment Spells)\nArmor +5 (while affected by 3 or more Enchantment Spells)\nArmor +5 (while affected by 4 or more Enchantment Spells)"

    }

class ForsakenInsignia(Insignia):
    id = ItemUpgrade.ForsakenInsignia
    profession = Profession.Dervish
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x43, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEB, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9D, 0x4D, 0xA, 0x1, 0xB6, 0x4, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +10 (while not affected by an Enchantment Spell)"
    }

class DervishRuneOfMinorMysticism(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMinorMysticism
    profession = Profession.Dervish
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x39, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class DervishRuneOfMinorEarthPrayers(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMinorEarthPrayers
    profession = Profession.Dervish
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x37, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class DervishRuneOfMinorScytheMastery(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMinorScytheMastery
    profession = Profession.Dervish
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x22, 0x11, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class DervishRuneOfMinorWindPrayers(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMinorWindPrayers
    profession = Profession.Dervish
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x35, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class DervishRuneOfMajorMysticism(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMajorMysticism
    profession = Profession.Dervish
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x39, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class DervishRuneOfMajorEarthPrayers(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMajorEarthPrayers
    profession = Profession.Dervish
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x37, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class DervishRuneOfMajorScytheMastery(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMajorScytheMastery
    profession = Profession.Dervish
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x22, 0x11, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class DervishRuneOfMajorWindPrayers(AttributeRune):
    id = ItemUpgrade.DervishRuneOfMajorWindPrayers
    profession = Profession.Dervish
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x35, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class DervishRuneOfSuperiorMysticism(AttributeRune):
    id = ItemUpgrade.DervishRuneOfSuperiorMysticism
    profession = Profession.Dervish
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x39, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class DervishRuneOfSuperiorEarthPrayers(AttributeRune):
    id = ItemUpgrade.DervishRuneOfSuperiorEarthPrayers
    profession = Profession.Dervish
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x37, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class DervishRuneOfSuperiorScytheMastery(AttributeRune):
    id = ItemUpgrade.DervishRuneOfSuperiorScytheMastery
    profession = Profession.Dervish
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x22, 0x11, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class DervishRuneOfSuperiorWindPrayers(AttributeRune):
    id = ItemUpgrade.DervishRuneOfSuperiorWindPrayers
    profession = Profession.Dervish
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x35, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class UpgradeMinorRuneDervish(UpgradeRune):
    id = ItemUpgrade.UpgradeMinorRuneDervish
    profession = Profession.Dervish
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneDervish(UpgradeRune):
    id = ItemUpgrade.UpgradeMajorRuneDervish
    profession = Profession.Dervish
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneDervish(UpgradeRune):
    id = ItemUpgrade.UpgradeSuperiorRuneDervish
    profession = Profession.Dervish
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneDervish(AppliesToRune):
    id = ItemUpgrade.AppliesToMinorRuneDervish
    profession = Profession.Dervish
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneDervish(AppliesToRune):
    id = ItemUpgrade.AppliesToMajorRuneDervish
    profession = Profession.Dervish
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneDervish(AppliesToRune):
    id = ItemUpgrade.AppliesToSuperiorRuneDervish
    profession = Profession.Dervish
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Dervish

#region Paragon

class CenturionsInsignia(Insignia):
    id = ItemUpgrade.CenturionsInsignia
    profession = Profession.Paragon
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x45, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEA, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = self.descriptions.get(ServerLanguage.English, f"no encoded description ({self.__class__.__name__})")
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x60, 0x4D, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    descriptions = {
        ServerLanguage.English: f"Armor +10 (while affected by a Shout, Echo, or Chant)"
    }

class ParagonRuneOfMinorLeadership(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMinorLeadership
    profession = Profession.Paragon
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x33, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ParagonRuneOfMinorMotivation(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMinorMotivation
    profession = Profession.Paragon
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x1A, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ParagonRuneOfMinorCommand(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMinorCommand
    profession = Profession.Paragon
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0xD5, 0x6, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ParagonRuneOfMinorSpearMastery(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMinorSpearMastery
    profession = Profession.Paragon
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x20, 0x11, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ParagonRuneOfMajorLeadership(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMajorLeadership
    profession = Profession.Paragon
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x33, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ParagonRuneOfMajorMotivation(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMajorMotivation
    profession = Profession.Paragon
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x1A, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ParagonRuneOfMajorCommand(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMajorCommand
    profession = Profession.Paragon
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0xD5, 0x6, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ParagonRuneOfMajorSpearMastery(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfMajorSpearMastery
    profession = Profession.Paragon
    rarity = Rarity.Purple

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x20, 0x11, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ParagonRuneOfSuperiorLeadership(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfSuperiorLeadership
    profession = Profession.Paragon
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x33, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ParagonRuneOfSuperiorMotivation(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfSuperiorMotivation
    profession = Profession.Paragon
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x1A, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ParagonRuneOfSuperiorCommand(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfSuperiorCommand
    profession = Profession.Paragon
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0xD5, 0x6, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class ParagonRuneOfSuperiorSpearMastery(AttributeRune):
    id = ItemUpgrade.ParagonRuneOfSuperiorSpearMastery
    profession = Profession.Paragon
    rarity = Rarity.Gold

    property_identifiers = [
        ModifierIdentifier.HealthMinus
    ]

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x20, 0x11, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


class UpgradeMinorRuneParagon(UpgradeRune):
    id = ItemUpgrade.UpgradeMinorRuneParagon
    profession = Profession.Paragon
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeMajorRuneParagon(UpgradeRune):
    id = ItemUpgrade.UpgradeMajorRuneParagon
    profession = Profession.Paragon
    mod_type = ItemUpgradeType.UpgradeRune

class UpgradeSuperiorRuneParagon(UpgradeRune):
    id = ItemUpgrade.UpgradeSuperiorRuneParagon
    profession = Profession.Paragon
    mod_type = ItemUpgradeType.UpgradeRune

class AppliesToMinorRuneParagon(AppliesToRune):
    id = ItemUpgrade.AppliesToMinorRuneParagon
    profession = Profession.Paragon
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToMajorRuneParagon(AppliesToRune):
    id = ItemUpgrade.AppliesToMajorRuneParagon
    profession = Profession.Paragon
    mod_type = ItemUpgradeType.AppliesToRune

class AppliesToSuperiorRuneParagon(AppliesToRune):
    id = ItemUpgrade.AppliesToSuperiorRuneParagon
    profession = Profession.Paragon
    mod_type = ItemUpgradeType.AppliesToRune

#endregion Paragon

#endregion Armor Upgrades

_UPGRADES: list[type[Upgrade]] = [
    IcyUpgrade,
    EbonUpgrade,
    ShockingUpgrade,
    FieryUpgrade,
    BarbedUpgrade,
    CripplingUpgrade,
    CruelUpgrade,
    PoisonousUpgrade,
    SilencingUpgrade,
    FuriousUpgrade,
    HeavyUpgrade,
    ZealousUpgrade,
    VampiricUpgrade,
    SunderingUpgrade,
    DefensiveUpgrade,
    InsightfulUpgrade,
    HaleUpgrade,
    OfDefenseUpgrade,
    OfWardingUpgrade,
    OfShelterUpgrade,
    OfSlayingUpgrade,
    OfFortitudeUpgrade,
    OfEnchantingUpgrade,
    OfTheProfessionUpgrade,
    OfAxeMasteryUpgrade,
    OfMarksmanshipUpgrade,
    OfDaggerMasteryUpgrade,
    OfHammerMasteryUpgrade,
    OfScytheMasteryUpgrade,
    OfSpearMasteryUpgrade,
    OfSwordsmanshipUpgrade,
    OfAttributeUpgrade,
    OfMasteryUpgrade,
    SwiftUpgrade,
    AdeptUpgrade,
    OfMemoryUpgrade,
    OfQuickeningUpgrade,
    OfAptitudeUpgrade,
    OfDevotionUpgrade,
    OfValorUpgrade,
    OfEnduranceUpgrade,
    OfSwiftnessUpgrade,
    
    BeJustAndFearNot,
    DownButNotOut,
    FaithIsMyShield,
    ForgetMeNot,
    HailToTheKing,
    IgnoranceIsBliss,
    KnowingIsHalfTheBattle,
    LifeIsPain,
    LiveForToday,
    ManForAllSeasons,
    MightMakesRight,
    SerenityNow,
    SurvivalOfTheFittest,
    BrawnOverBrains,
    DanceWithDeath,
    DontFearTheReaper,
    DontThinkTwice,
    GuidedByFate,
    StrengthAndHonor,
    ToThePain,
    TooMuchInformation,
    VengeanceIsMine,
    IHaveThePower,
    LetTheMemoryLiveAgain,
    CastOutTheUnclean,
    FearCutsDeeper,
    ICanSeeClearlyNow,
    LeafOnTheWind,
    LikeARollingStone,
    LuckOfTheDraw,
    MasterOfMyDomain,
    NotTheFace,
    NothingToFear,
    OnlyTheStrongSurvive,
    PureOfHeart,
    RidersOnTheStorm,
    RunForYourLife,
    ShelteredByFaith,
    SleepNowInTheFire,
    SoundnessOfMind,
    StrengthOfBody,
    SwiftAsTheWind,
    TheRiddleOfSteel,
    ThroughThickAndThin,
    MeasureForMeasure,
    ShowMeTheMoney,
    AptitudeNotAttitude,
    DontCallItAComeback,
    HaleAndHearty,
    HaveFaith,
    IAmSorrow,
    SeizeTheDay,
        
    # No Profession
    SurvivorInsignia,
    RadiantInsignia,
    StalwartInsignia,
    BrawlersInsignia,
    BlessedInsignia,
    HeraldsInsignia,
    SentrysInsignia,
    
    # Warrior
    KnightsInsignia,
    LieutenantsInsignia,
    StonefistInsignia,
    DreadnoughtInsignia,
    SentinelsInsignia,
    
    # Ranger
    FrostboundInsignia,
    PyreboundInsignia,
    StormboundInsignia,
    ScoutsInsignia,
    EarthboundInsignia,
    BeastmastersInsignia,
    
    # Monk
    WanderersInsignia,
    DisciplesInsignia,
    AnchoritesInsignia,
    
    # Necromancer
    BloodstainedInsignia,
    TormentorsInsignia,
    BonelaceInsignia,
    MinionMastersInsignia,
    BlightersInsignia,
    UndertakersInsignia,
    
    # Mesmer 
    VirtuososInsignia,
    ArtificersInsignia,
    ProdigysInsignia,
    
    # Elementalist
    HydromancerInsignia,
    GeomancerInsignia,
    PyromancerInsignia,
    AeromancerInsignia,
    PrismaticInsignia,
    
    # Assassin
    VanguardsInsignia,
    InfiltratorsInsignia,
    SaboteursInsignia,
    NightstalkersInsignia,
    
    # Ritualist
    ShamansInsignia,
    GhostForgeInsignia,
    MysticsInsignia,
    
    # Dervish
    WindwalkerInsignia,
    ForsakenInsignia,
    
    # Paragon
    CenturionsInsignia,    
    
    #No Profession
    RuneOfMinorVigor,
    RuneOfMinorVigor2,
    RuneOfVitae,
    RuneOfAttunement,
    RuneOfMajorVigor,
    RuneOfRecovery,
    RuneOfRestoration,
    RuneOfClarity,
    RuneOfPurity,
    RuneOfSuperiorVigor,
    
    # Warrior    
    WarriorRuneOfMinorAbsorption,
    WarriorRuneOfMinorTactics,
    WarriorRuneOfMinorStrength,
    WarriorRuneOfMinorAxeMastery,
    WarriorRuneOfMinorHammerMastery,
    WarriorRuneOfMinorSwordsmanship,
    WarriorRuneOfMajorAbsorption,
    WarriorRuneOfMajorTactics,
    WarriorRuneOfMajorStrength,
    WarriorRuneOfMajorAxeMastery,
    WarriorRuneOfMajorHammerMastery,
    WarriorRuneOfMajorSwordsmanship,
    WarriorRuneOfSuperiorAbsorption,
    WarriorRuneOfSuperiorTactics,
    WarriorRuneOfSuperiorStrength,
    WarriorRuneOfSuperiorAxeMastery,
    WarriorRuneOfSuperiorHammerMastery,
    WarriorRuneOfSuperiorSwordsmanship,
    
    UpgradeMinorRuneWarrior,
    UpgradeMajorRuneWarrior,
    UpgradeSuperiorRuneWarrior,
    AppliesToMinorRuneWarrior,
    AppliesToMajorRuneWarrior,
    AppliesToSuperiorRuneWarrior,
    
    # Ranger        
    RangerRuneOfMinorWildernessSurvival,
    RangerRuneOfMinorExpertise,
    RangerRuneOfMinorBeastMastery,
    RangerRuneOfMinorMarksmanship,
    RangerRuneOfMajorWildernessSurvival,
    RangerRuneOfMajorExpertise,
    RangerRuneOfMajorBeastMastery,
    RangerRuneOfMajorMarksmanship,
    RangerRuneOfSuperiorWildernessSurvival,
    RangerRuneOfSuperiorExpertise,
    RangerRuneOfSuperiorBeastMastery,
    RangerRuneOfSuperiorMarksmanship,
    
    UpgradeMinorRuneRanger,
    UpgradeMajorRuneRanger,
    UpgradeSuperiorRuneRanger,
    AppliesToMinorRuneRanger,
    AppliesToMajorRuneRanger,
    AppliesToSuperiorRuneRanger,
    
    # Monk    
    MonkRuneOfMinorHealingPrayers,
    MonkRuneOfMinorSmitingPrayers,
    MonkRuneOfMinorProtectionPrayers,
    MonkRuneOfMinorDivineFavor,
    MonkRuneOfMajorHealingPrayers,
    MonkRuneOfMajorSmitingPrayers,
    MonkRuneOfMajorProtectionPrayers,
    MonkRuneOfMajorDivineFavor,
    MonkRuneOfSuperiorHealingPrayers,
    MonkRuneOfSuperiorSmitingPrayers,
    MonkRuneOfSuperiorProtectionPrayers,
    MonkRuneOfSuperiorDivineFavor,
    
    UpgradeMinorRuneMonk,
    UpgradeMajorRuneMonk,
    UpgradeSuperiorRuneMonk,
    AppliesToMinorRuneMonk,
    AppliesToMajorRuneMonk,
    AppliesToSuperiorRuneMonk,
    
    # Necromancer
    NecromancerRuneOfMinorBloodMagic,
    NecromancerRuneOfMinorDeathMagic,
    NecromancerRuneOfMinorCurses,
    NecromancerRuneOfMinorSoulReaping,
    NecromancerRuneOfMajorBloodMagic,
    NecromancerRuneOfMajorDeathMagic,
    NecromancerRuneOfMajorCurses,
    NecromancerRuneOfMajorSoulReaping,
    NecromancerRuneOfSuperiorBloodMagic,
    NecromancerRuneOfSuperiorDeathMagic,
    NecromancerRuneOfSuperiorCurses,
    NecromancerRuneOfSuperiorSoulReaping,
    
    UpgradeMinorRuneNecromancer,
    UpgradeMajorRuneNecromancer,
    UpgradeSuperiorRuneNecromancer,
    AppliesToMinorRuneNecromancer,
    AppliesToMajorRuneNecromancer,
    AppliesToSuperiorRuneNecromancer,
    
    # Mesmer 
    MesmerRuneOfMinorFastCasting,
    MesmerRuneOfMinorDominationMagic,
    MesmerRuneOfMinorIllusionMagic,
    MesmerRuneOfMinorInspirationMagic,
    MesmerRuneOfMajorFastCasting,
    MesmerRuneOfMajorDominationMagic,
    MesmerRuneOfMajorIllusionMagic,
    MesmerRuneOfMajorInspirationMagic,
    MesmerRuneOfSuperiorFastCasting,
    MesmerRuneOfSuperiorDominationMagic,
    MesmerRuneOfSuperiorIllusionMagic,
    MesmerRuneOfSuperiorInspirationMagic,
    
    UpgradeMinorRuneMesmer,
    UpgradeMajorRuneMesmer,
    UpgradeSuperiorRuneMesmer,
    AppliesToMinorRuneMesmer,
    AppliesToMajorRuneMesmer,
    AppliesToSuperiorRuneMesmer,
    
    # Elementalist
    ElementalistRuneOfMinorEnergyStorage,
    ElementalistRuneOfMinorFireMagic,
    ElementalistRuneOfMinorAirMagic,
    ElementalistRuneOfMinorEarthMagic,
    ElementalistRuneOfMinorWaterMagic,
    ElementalistRuneOfMajorEnergyStorage,
    ElementalistRuneOfMajorFireMagic,
    ElementalistRuneOfMajorAirMagic,
    ElementalistRuneOfMajorEarthMagic,
    ElementalistRuneOfMajorWaterMagic,
    ElementalistRuneOfSuperiorEnergyStorage,
    ElementalistRuneOfSuperiorFireMagic,
    ElementalistRuneOfSuperiorAirMagic,
    ElementalistRuneOfSuperiorEarthMagic,
    ElementalistRuneOfSuperiorWaterMagic,
    
    UpgradeMinorRuneElementalist,
    UpgradeMajorRuneElementalist,
    UpgradeSuperiorRuneElementalist,
    AppliesToMinorRuneElementalist,
    AppliesToMajorRuneElementalist,
    AppliesToSuperiorRuneElementalist,
    
    # Assassin
    AssassinRuneOfMinorCriticalStrikes,
    AssassinRuneOfMinorDaggerMastery,
    AssassinRuneOfMinorDeadlyArts,
    AssassinRuneOfMinorShadowArts,
    AssassinRuneOfMajorCriticalStrikes,
    AssassinRuneOfMajorDaggerMastery,
    AssassinRuneOfMajorDeadlyArts,
    AssassinRuneOfMajorShadowArts,
    AssassinRuneOfSuperiorCriticalStrikes,
    AssassinRuneOfSuperiorDaggerMastery,
    AssassinRuneOfSuperiorDeadlyArts,
    AssassinRuneOfSuperiorShadowArts,
    
    UpgradeMinorRuneAssassin,
    UpgradeMajorRuneAssassin,
    UpgradeSuperiorRuneAssassin,
    AppliesToMinorRuneAssassin,
    AppliesToMajorRuneAssassin,
    AppliesToSuperiorRuneAssassin,
    
    # Ritualist
    RitualistRuneOfMinorChannelingMagic,
    RitualistRuneOfMinorRestorationMagic,
    RitualistRuneOfMinorCommuning,
    RitualistRuneOfMinorSpawningPower,
    RitualistRuneOfMajorChannelingMagic,
    RitualistRuneOfMajorRestorationMagic,
    RitualistRuneOfMajorCommuning,
    RitualistRuneOfMajorSpawningPower,
    RitualistRuneOfSuperiorChannelingMagic,
    RitualistRuneOfSuperiorRestorationMagic,
    RitualistRuneOfSuperiorCommuning,
    RitualistRuneOfSuperiorSpawningPower,
    
    UpgradeMinorRuneRitualist,
    UpgradeMajorRuneRitualist,
    UpgradeSuperiorRuneRitualist,
    AppliesToMinorRuneRitualist,
    AppliesToMajorRuneRitualist,
    AppliesToSuperiorRuneRitualist,
    
    # Dervish
    DervishRuneOfMinorMysticism,
    DervishRuneOfMinorEarthPrayers,
    DervishRuneOfMinorScytheMastery,
    DervishRuneOfMinorWindPrayers,
    DervishRuneOfMajorMysticism,
    DervishRuneOfMajorEarthPrayers,
    DervishRuneOfMajorScytheMastery,
    DervishRuneOfMajorWindPrayers,
    DervishRuneOfSuperiorMysticism,
    DervishRuneOfSuperiorEarthPrayers,
    DervishRuneOfSuperiorScytheMastery,
    DervishRuneOfSuperiorWindPrayers,
    
    UpgradeMinorRuneDervish,
    UpgradeMajorRuneDervish,
    UpgradeSuperiorRuneDervish,
    AppliesToMinorRuneDervish,
    AppliesToMajorRuneDervish,
    AppliesToSuperiorRuneDervish,
    
    # Paragon    
    ParagonRuneOfMinorLeadership,
    ParagonRuneOfMinorMotivation,
    ParagonRuneOfMinorCommand,
    ParagonRuneOfMinorSpearMastery,
    ParagonRuneOfMajorLeadership,
    ParagonRuneOfMajorMotivation,
    ParagonRuneOfMajorCommand,
    ParagonRuneOfMajorSpearMastery,
    ParagonRuneOfSuperiorLeadership,
    ParagonRuneOfSuperiorMotivation,
    ParagonRuneOfSuperiorCommand,
    ParagonRuneOfSuperiorSpearMastery,   
    
    UpgradeMinorRuneParagon,
    UpgradeMajorRuneParagon,
    UpgradeSuperiorRuneParagon,
    AppliesToMinorRuneParagon,
    AppliesToMajorRuneParagon,
    AppliesToSuperiorRuneParagon, 
]

_INHERENT_UPGRADES: list[type[Inherent]] = [
    cls
    for cls in globals().values()
    if isinstance(cls, type)
    and issubclass(cls, Inherent)
    and cls is not Inherent
    and cls.__module__ == __name__
]
