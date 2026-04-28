from dataclasses import MISSING, dataclass, field, fields, is_dataclass
from enum import Enum
import re
from typing import Any, Callable, ClassVar, Generic, Optional, Protocol, SupportsFloat, SupportsInt, TypeVar, cast

from Py4GWCoreLib.enums_src.GameData_enums import Ailment, Attribute, AttributeNames, DamageType, PROFESSION_ATTRIBUTES, Profession, Reduced_Ailment
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.item_mods_src.decoded_modifier import DecodedModifier
from Py4GWCoreLib.item_mods_src.types import ItemBaneSpecies, ItemUpgrade, ItemUpgradeId, ItemUpgradeType, ModifierIdentifier, ModifierIdentifierSpec, any_of
from Py4GWCoreLib.native_src.internals import string_table
from Py4GWCoreLib.native_src.internals.encoded_strings import GWEncoded, GWStringEncoded

from Py4GWCoreLib.item_mods_src.properties import *

PERSISTENT = True

class NumericValue(SupportsInt, SupportsFloat, Protocol):
    """Protocol for values that behave like orderable numeric types."""

    def __lt__(self, other: Any, /) -> bool: ...
    def __le__(self, other: Any, /) -> bool: ...
    def __gt__(self, other: Any, /) -> bool: ...
    def __ge__(self, other: Any, /) -> bool: ...

NumberT = TypeVar("NumberT", bound=NumericValue)
ValueT = TypeVar("ValueT")
PropertyT = TypeVar("PropertyT", bound=ItemProperty)
UpgradeT = TypeVar("UpgradeT", bound="Upgrade")

class ItemProperties(dict[ModifierIdentifier, ItemProperty]):
    def get(self, key: ModifierIdentifier | type[PropertyT], default: Any = None) -> Any:
        if isinstance(key, type):
            for prop in self.values():
                if isinstance(prop, key):
                    return prop
            return default
        
        return super().get(key, default)

@dataclass(slots=True)
class InstructionResult:
    target: str
    value: Any = None
    applied: bool = False
    reason: Optional[str] = None


class Instruction(Generic[UpgradeT, ValueT]):
    """
    Declarative rule that fills one upgrade field from one or more item properties.

    Each instruction knows:
    - which upgrade attribute it controls
    - how to read a candidate value from ItemProperties
    - how to validate the candidate value
    """

    def __init__(
        self,
        identifier: ModifierIdentifierSpec,
        target: str,
        value_getter: Callable[[ItemProperties, UpgradeT], ValueT | None],
    ) -> None:
        self.identifier = identifier
        self.target = target
        self.value_getter = value_getter

    def get_value(self, properties: ItemProperties, upgrade: UpgradeT) -> ValueT | None:
        return self.value_getter(properties, upgrade)

    def evaluate(self, value: ValueT | None) -> bool:
        return value is not None

    def apply(self, upgrade: UpgradeT, properties: ItemProperties) -> InstructionResult:
        value = self.get_value(properties, upgrade)
        if not self.evaluate(value):
            return InstructionResult(
                target=self.target,
                value=value,
                applied=False,
                reason="candidate value did not satisfy the instruction",
            )

        setattr(upgrade, self.target, value)
        return InstructionResult(target=self.target, value=value, applied=True)

class RangeInstruction(Instruction[UpgradeT, NumberT]):
    def __init__(
        self,
        identifier: ModifierIdentifierSpec,
        target: str,
        min_value: NumberT,
        max_value: NumberT,
        value_getter: Callable[[ItemProperties, UpgradeT], NumberT | None],
    ) -> None:
        super().__init__(identifier, target, value_getter)
        self.min_value = min_value
        self.max_value = max_value

    @property
    def range(self) -> tuple[NumberT, NumberT]:
        return self.min_value, self.max_value

    def evaluate(self, value: NumberT | None) -> bool:
        return value is not None and self.min_value <= value <= self.max_value

class FixedValueInstruction(Instruction[UpgradeT, ValueT]):
    def __init__(
        self,
        identifier: ModifierIdentifierSpec,
        target: str,
        fixed_value: ValueT,
        value_getter: Callable[[ItemProperties, UpgradeT], ValueT | None],
    ) -> None:
        super().__init__(identifier, target, value_getter)
        self.fixed_value = fixed_value

    def evaluate(self, value: ValueT | None) -> bool:
        return value == self.fixed_value

def property_value(
    property_type: type[PropertyT],
    selector: Callable[[PropertyT], ValueT | None],
) -> Callable[[ItemProperties, UpgradeT], ValueT | None]: # type: ignore
    """Create a getter that reads a value from the first matching ItemProperty."""

    def getter(properties: ItemProperties, _: UpgradeT) -> ValueT | None:
        prop = properties.get(property_type)
        if prop is None:
            return None
        return selector(prop)

    return getter

def ranged(
    identifier: ModifierIdentifierSpec,
    target: str,
    min_value: NumberT,
    max_value: NumberT,
    value_getter: Callable[[ItemProperties, UpgradeT], NumberT | None],
) -> RangeInstruction[UpgradeT, NumberT]:
    return RangeInstruction(identifier, target, min_value, max_value, value_getter)

def fixed(
    identifier: ModifierIdentifierSpec,
    target: str,
    fixed_value: ValueT,
    value_getter: Callable[[ItemProperties, UpgradeT], ValueT | None],
) -> FixedValueInstruction[UpgradeT, ValueT]:
    return FixedValueInstruction(identifier, target, fixed_value, value_getter)

def _humanize_identifier(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name).strip()

def _get_property_factory():
    from Py4GWCoreLib.item_mods_src.upgrade_parser import get_property_factory
    return get_property_factory()

@dataclass(eq=False)
class Upgrade:
    """
    Abstract base class for item upgrades. Each specific upgrade type (e.g., Prefix, Suffix, Inscription) should inherit from this class and implement the necessary properties and methods.
    """
    _registry: ClassVar[dict[str, type["Upgrade"]]] = {}
    mod_type: ClassVar[ItemUpgradeType] = ItemUpgradeType.Unknown
    id: ClassVar[ItemUpgrade] = ItemUpgrade.Unknown
    
    properties: ItemProperties = field(default_factory=ItemProperties)
    
    rarity: Rarity = field(init=False, default=Rarity.Blue, repr=False, compare=False)
    upgrade_id: ItemUpgradeId = field(init=False, default=ItemUpgradeId.Unknown, repr=False, compare=False)
    modifier: Optional[DecodedModifier] = field(init=False, default=None, repr=False, compare=False)
    is_inherent: bool = field(init=False, default=False, repr=False, compare=False)
    language: ServerLanguage = field(init=False, repr=False, compare=False)
    
    upgrade_info: ClassVar[tuple[Instruction["Upgrade", Any], ...]] = ()

    __encoded_name: GWStringEncoded = field(init=False, repr=False, compare=False)
    __encoded_description: GWStringEncoded = field(init=False, repr=False, compare=False)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Upgrade._registry[cls.__name__] = cls

    def __post_init__(self):
        object.__setattr__(self, "is_inherent", False)
        object.__setattr__(self, "language", ServerLanguage(string_table._loaded_language) if string_table._loaded_language in ServerLanguage._value2member_map_ else ServerLanguage.English)
        object.__setattr__(self, "rarity", getattr(type(self), "rarity", Rarity.Blue))
        object.__setattr__(self, "upgrade_id", ItemUpgradeId.Unknown)
        object.__setattr__(self, "modifier", None)

        cls = type(self)
        for field_info in fields(self):
            if not field_info.init:
                continue

            field_value = getattr(cls, field_info.name, MISSING)
            if field_value is not MISSING:
                current_value = getattr(self, field_info.name)

                # Allow subclasses to override inherited dataclass defaults via
                # class attributes, but do not clobber explicit constructor args.
                if field_info.default is not MISSING:
                    if current_value == field_info.default:
                        object.__setattr__(self, field_info.name, field_value)
                elif field_info.default_factory is not MISSING:  # type: ignore[attr-defined]
                    default_value = field_info.default_factory()  # type: ignore[misc]
                    if current_value == default_value:
                        object.__setattr__(self, field_info.name, field_value)
        
        self._refresh_encoded_strings()

    def __setattr__(self, name: str, value: Any) -> None:
        upgrade_info_targets = {instruction.target for instruction in self.upgrade_info}
        if name in type(self)._get_serializable_property_names() or name in upgrade_info_targets:
            object.__setattr__(self, name, value)
            self._refresh_encoded_strings()
            return

        object.__setattr__(self, name, value)

    #region Upgrade Composition from Modifiers
    @classmethod
    def _pre_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, all_modifiers: list[DecodedModifier], remaining_modifiers: list[DecodedModifier]) -> None:
        return None

    @classmethod
    def _post_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, all_modifiers: list[DecodedModifier], remaining_modifiers: list[DecodedModifier]) -> None:
        return None

    @classmethod
    def _can_compose(cls, mod: DecodedModifier, all_modifiers: list[DecodedModifier], remaining_modifiers: list[DecodedModifier]) -> bool:
        return True
        
    @classmethod
    def compose_from_modifiers(cls, mod : DecodedModifier, remaining_modifiers: list[DecodedModifier], all_modifiers: list[DecodedModifier], rarity: Rarity = Rarity.Blue) -> Optional["Upgrade"]:        
        if not cls._can_compose(mod, all_modifiers, remaining_modifiers):
            return None

        upgrade = cls()
        upgrade.upgrade_id = mod.upgrade_id
        upgrade.rarity = rarity
        upgrade.modifier = mod

        cls._pre_compose(upgrade, mod, all_modifiers, remaining_modifiers)

        property_factory = _get_property_factory()
        matched_modifiers = cls._match_property_modifiers(remaining_modifiers)
        if not cls.upgrade_info or len(cls.upgrade_info) == 0:
            upgrade._refresh_encoded_strings()
            return upgrade
        
        if matched_modifiers is None:
            return None

        for prop_key, prop_mod in matched_modifiers:
            prop = property_factory.get(prop_mod.identifier, lambda m, _, rarity: ItemProperty(modifier=m, rarity=rarity))(prop_mod, remaining_modifiers, rarity)
            upgrade.properties[prop_key] = prop

            matched_instructions = [instruction for instruction in cls.upgrade_info if cls._get_property_identifier_key(instruction.identifier) == prop_key]
            modifier_applied = False
            for instruction in matched_instructions:
                result = instruction.apply(upgrade, upgrade.properties)
                if not result.applied:
                    return None
                modifier_applied = True

            if modifier_applied and prop_mod in remaining_modifiers:
                remaining_modifiers.remove(prop_mod)

        cls._post_compose(upgrade, mod, all_modifiers, remaining_modifiers)
        upgrade._refresh_encoded_strings()
        return upgrade
   
    @staticmethod
    def _normalize_property_identifier_spec(identifier_spec: ModifierIdentifierSpec) -> tuple[ModifierIdentifier, ...]:
        if isinstance(identifier_spec, tuple):
            return identifier_spec
        return (identifier_spec,)
    
    @classmethod
    def _get_property_identifier_key(cls, identifier_spec: ModifierIdentifierSpec) -> ModifierIdentifier:
        return cls._normalize_property_identifier_spec(identifier_spec)[0]

    @classmethod
    def _match_property_modifiers(cls, modifiers: list[DecodedModifier]) -> Optional[list[tuple[ModifierIdentifier, DecodedModifier]]]:
        used_modifiers: list[DecodedModifier] = []
        matched_by_key: dict[ModifierIdentifier, DecodedModifier] = {}

        if cls.upgrade_info:
            for inst in cls.upgrade_info:
                prop_key = cls._get_property_identifier_key(inst.identifier)
                prop_mod = matched_by_key.get(prop_key)
                if prop_mod is None:
                    identifier_options = cls._normalize_property_identifier_spec(inst.identifier)
                    prop_mod = next((m for m in modifiers if m not in used_modifiers and m.identifier in identifier_options), None)
                    if prop_mod is not None:
                        matched_by_key[prop_key] = prop_mod
                        used_modifiers.append(prop_mod)
                        
                if prop_mod is None:
                    return None

        return list(matched_by_key.items())
    #endregion Upgrade Composition from Modifiers
    
    @classmethod
    def has_id(cls, upgrade_id: ItemUpgradeId) -> bool:
        return cls.id.has_id(upgrade_id)

    @classmethod
    def get_specificity_score(cls) -> tuple[int, int]:
        fixed_instruction_count = sum(
            1
            for instruction in cls.upgrade_info
            if isinstance(instruction, FixedValueInstruction)
        )
        inheritance_depth = len(cls.mro())
        return fixed_instruction_count, inheritance_depth

    #region Equality and Matching
    @classmethod
    def _get_serializable_property_names(cls) -> list[str]:
        blacklisted_fields = {"properties", "modifier", "language"}        
        return [field_info.name for field_info in fields(cls) if field_info.init and field_info.name not in blacklisted_fields]

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        if isinstance(value, Enum):
            return {
                "enum_type": type(value).__name__,
                "value": value.name,
            }

        if isinstance(value, list):
            return [Upgrade._serialize_value(entry) for entry in value]

        if isinstance(value, tuple):
            return [Upgrade._serialize_value(entry) for entry in value]

        if isinstance(value, dict):
            return {str(key): Upgrade._serialize_value(entry) for key, entry in value.items()}

        return value

    @staticmethod
    def _deserialize_value(value: Any) -> Any:
        if isinstance(value, list):
            return [Upgrade._deserialize_value(entry) for entry in value]

        if isinstance(value, dict):
            enum_type = value.get("enum_type")
            enum_value = value.get("value")
            if isinstance(enum_type, str) and isinstance(enum_value, str):
                enum_cls = globals().get(enum_type)
                if isinstance(enum_cls, type) and issubclass(enum_cls, Enum) and enum_value in enum_cls.__members__:
                    return enum_cls[enum_value]

            return {str(key): Upgrade._deserialize_value(entry) for key, entry in value.items()}

        return value

    @staticmethod
    def _normalize_comparison_value(value: Any) -> Any:
        if isinstance(value, Enum):
            return (type(value).__name__, value.name)

        if isinstance(value, list):
            return tuple(Upgrade._normalize_comparison_value(entry) for entry in value)

        if isinstance(value, tuple):
            return tuple(Upgrade._normalize_comparison_value(entry) for entry in value)

        if isinstance(value, dict):
            return tuple(sorted((str(key), Upgrade._normalize_comparison_value(entry)) for key, entry in value.items()))

        return value

    def _comparison_data(self) -> tuple[str, tuple[tuple[str, Any], ...]]:
        comparison_values = {
            property_name: self._normalize_comparison_value(getattr(self, property_name))
            for property_name in self._get_serializable_property_names()
        }
        return type(self).__name__, tuple(sorted(comparison_values.items()))

    def equals(self, other: object) -> bool:
        return isinstance(other, Upgrade) and self._comparison_data() == other._comparison_data()

    def matches(self, other: object) -> bool:
        return self.equals(other)

    def __eq__(self, other: object) -> bool:
        return self.equals(other)
    #endregion Equality and Matching
    
    #region Serialization
    def to_dict(self) -> dict[str, Any]:
        values = {
            property_name: self._serialize_value(getattr(self, property_name))
            for property_name in self._get_serializable_property_names()
        }

        payload: dict[str, Any] = {
            "upgrade_type": type(self).__name__,
            "values": values,
        }

        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Optional["Upgrade"]:
        upgrade_type_name = str(payload.get("upgrade_type", ""))
        upgrade_cls = cls._registry.get(upgrade_type_name)
        if upgrade_cls is None:
            return None

        raw_values = payload.get("values", {})
        if not isinstance(raw_values, dict):
            raw_values = {}

        values = {
            str(key): cls._deserialize_value(value)
            for key, value in raw_values.items()
        }

        upgrade = upgrade_cls()
        valid_property_names = set(upgrade_cls._get_serializable_property_names())
        for key, value in values.items():
            if key in valid_property_names:
                setattr(upgrade, key, value)

        return upgrade
    #endregion Serialization
    
    #region Encoded String Generation
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
            
    def create_upgrade_name(self, item_type: ItemType) -> GWStringEncoded:
        encoded_name = self.create_encoded_name()
        return encoded_name
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"{_humanize_identifier(self.__class__.__name__)} (no encoded name)")

    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)")
    
    def _refresh_encoded_strings(self) -> None:        
        self.__encoded_name = self.create_encoded_name()
        self.__encoded_description = self.create_encoded_description()

    #endregion Encoded String Generation
    
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
    
    @property
    def is_maxed(self) -> bool:
        for instruction in self.upgrade_info:
            if isinstance(instruction, RangeInstruction):
                value = getattr(self, instruction.target)
                if value < instruction.max_value:
                    return False
                
        return True
    
    @classmethod
    def get_static_name(cls, rarity : Rarity = Rarity.Blue) -> str: 
        temp_instance = cls()
        temp_instance.rarity = rarity
        temp_instance.__encoded_name = temp_instance.create_encoded_name()
        
        return temp_instance.name_plain

@dataclass(eq=False)
class UnknownUpgrade(Upgrade):
    mod_type = ItemUpgradeType.Unknown
    id = ItemUpgrade.Unknown
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"{_humanize_identifier(self.modifier.upgrade_id.name) if self.modifier else 'Unknown Upgrade'} (ID: {self.modifier.upgrade_id.value if self.modifier else 'N/A'})")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"{_humanize_identifier(self.modifier.upgrade_id.name) if self.modifier else 'Unknown Upgrade'}")

    
#region Weapon Upgrades
@dataclass(eq=False)
class WeaponUpgrade(Upgrade):
    target_item_type: ItemType = field(init=False, default=ItemType.Unknown, repr=False, compare=False)

    @classmethod
    def _pre_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, all_modifiers: list[DecodedModifier], remaining_modifiers: list[DecodedModifier]) -> None:
        weapon_upgrade = cast(WeaponUpgrade, upgrade)
        weapon_upgrade.target_item_type = cls.id.get_item_type(weapon_upgrade.upgrade_id)      
             
#region Prefixes

@dataclass(eq=False)
class WeaponPrefix(WeaponUpgrade):
    mod_type = ItemUpgradeType.Prefix

    def create_upgrade_name(self, item_type: ItemType) -> GWStringEncoded:
        encoded_upgrade_component = GWEncoded.WEAPON_PREFIXES.get(item_type) or bytes()
        if not encoded_upgrade_component:
            return self.create_encoded_name()

        encoded_name = self.create_encoded_name()
        color_bytes = self.get_text_color(True)
        suffix = encoded_name.encoded[len(color_bytes):] if encoded_name.encoded.startswith(color_bytes) else encoded_name.encoded
        return GWStringEncoded(
            bytes([*color_bytes, *encoded_upgrade_component, *suffix]),
            encoded_name.fallback,
            encoded_name.placeholder_bytes,
            encoded_name.placeholder_replacement,
        )
    
@dataclass(eq=False)
class IncreaseConditionDurationUpgrade(WeaponPrefix):
    condition: Ailment | None = None
    
    def create_encoded_description(self) -> GWStringEncoded:
        if self.condition is None:
            return super().create_encoded_description()
        
        encoded = GWEncoded.CONDITION_INCREASE_BYTES.get(self.condition)
        fallback = f"Lengthens {self.condition.name.replace('_', ' ')} duration on foes by 33%"
        
        if encoded:
            return GWStringEncoded(bytes([*self.get_text_color(), *encoded, *GWEncoded._dull_parenthesized(GWEncoded.STACKING_BYTES, "(Stacking)")]), fallback)
        
        return GWStringEncoded(bytes(), fallback)

@dataclass(eq=False)
class DamageTypeUpgrade(WeaponPrefix):
    damage_type: DamageType | None = None
    
    def create_encoded_description(self) -> GWStringEncoded:
        if self.damage_type is None:
            return super().create_encoded_description()
        
        damage_bytes = GWEncoded.DAMAGE_TYPE_BYTES.get(self.damage_type)
        if damage_bytes:            
            return GWStringEncoded(bytes([*GWEncoded.ITEM_BASIC, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x4C, 0xA, 0x1, 0x0, 0xB, 0x1, *damage_bytes, 0x1, 0x0]), f"{self.damage_type.name} Dmg")
        
        return GWStringEncoded(bytes(), f"{self.damage_type.name} Dmg")

@dataclass
class AdeptUpgrade(WeaponPrefix):
    id: ClassVar[ItemUpgrade] = ItemUpgrade.Adept
    chance: int = 20

    upgrade_info = (
        ranged(
            identifier= ModifierIdentifier.HalvesCastingTimeItemAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
    )
    
    def create_upgrade_name(self, item_type):        
        encoded_upgrade_component = (GWEncoded.WEAPON_PREFIXES.get(item_type) if self.mod_type == ItemUpgradeType.Prefix else GWEncoded.WEAPON_SUFFIXES.get(item_type)) or bytes()
        return GWStringEncoded(bytes([*self.get_text_color(True), *encoded_upgrade_component, 0x1, 0x81, 0x94, 0x5D, 0x1, 0x0]), f"Adept") if encoded_upgrade_component else self.create_encoded_name()
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x1, 0x81, 0x94, 0x5D, 0x1, 0x0]), f"Adept")
    
    def create_encoded_description(self) -> GWStringEncoded:
        parts = [
            GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_CASTING_ITEM_ATTRIBUTE_BYTES]), "Halves casting time on spells of item's attribute"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")
        ]
        
        return GWEncoded.combine_encoded_strings(parts, "no encoded description")

@dataclass(eq=False)
class BarbedUpgrade(IncreaseConditionDurationUpgrade):
    id = ItemUpgrade.Barbed
    condition = Ailment.Bleeding

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.IncreaseConditionDuration,
            target="condition",
            fixed_value=Ailment.Bleeding,
            value_getter=property_value(
                IncreaseConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
    )
    
    def create_upgrade_name(self, item_type):
        encoded_upgrade_component = (GWEncoded.WEAPON_PREFIXES.get(item_type) if self.mod_type == ItemUpgradeType.Prefix else GWEncoded.WEAPON_SUFFIXES.get(item_type)) or bytes()
        return GWStringEncoded(bytes([*self.get_text_color(True), *encoded_upgrade_component, 0x69, 0xA, 0x1, 0x0]), f"Barbed") if encoded_upgrade_component else self.create_encoded_name()
    
    def create_encoded_name(self) -> GWStringEncoded:
         return GWStringEncoded(self.get_text_color(True) + bytes([0x69, 0xA, 0x1, 0x0]), f"Barbed")

@dataclass(eq=False)
class CripplingUpgrade(IncreaseConditionDurationUpgrade):
    id = ItemUpgrade.Crippling
    condition = Ailment.Crippled

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.IncreaseConditionDuration,
            target="condition",
            fixed_value=Ailment.Crippled,
            value_getter=property_value(
                IncreaseConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
    )

    def create_upgrade_name(self, item_type):
        encoded_upgrade_component = (GWEncoded.WEAPON_PREFIXES.get(item_type) if self.mod_type == ItemUpgradeType.Prefix else GWEncoded.WEAPON_SUFFIXES.get(item_type)) or bytes()
        return GWStringEncoded(bytes([*self.get_text_color(True), *encoded_upgrade_component, 0x6A, 0xA, 0x1, 0x0]), f"Crippling") if encoded_upgrade_component else self.create_encoded_name()
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x6A, 0xA, 0x1, 0x0]), f"Crippling")
        
@dataclass(eq=False)
class CruelUpgrade(IncreaseConditionDurationUpgrade):
    id = ItemUpgrade.Cruel
    condition = Ailment.Deep_Wound

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.IncreaseConditionDuration,
            target="condition",
            fixed_value=Ailment.Deep_Wound,
            value_getter=property_value(
                IncreaseConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
    )

    
    def create_upgrade_name(self, item_type):
        encoded_upgrade_component = (GWEncoded.WEAPON_PREFIXES.get(item_type) if self.mod_type == ItemUpgradeType.Prefix else GWEncoded.WEAPON_SUFFIXES.get(item_type)) or bytes()
        return GWStringEncoded(bytes([*self.get_text_color(True), *encoded_upgrade_component, 0x6B, 0xA, 0x1, 0x0]), f"Cruel") if encoded_upgrade_component else self.create_encoded_name()
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x6B, 0xA, 0x1, 0x0]), f"Cruel")

    
@dataclass(eq=False)
class DefensiveUpgrade(WeaponPrefix):
    id = ItemUpgrade.Defensive
    armor: int = 5
    
    upgrade_info = (
        ranged(
            identifier= ModifierIdentifier.ArmorPlus,
            target="armor",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                ArmorPlus,
                lambda prop: prop.armor,
            ),
        ),
    )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x6D, 0xA, 0x1, 0x0]), f"Defensive")
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor")

@dataclass(eq=False)
class EbonUpgrade(DamageTypeUpgrade):
    id = ItemUpgrade.Ebon
    damage_type = DamageType.Earth

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamageTypeProperty,
            target="damage_type",
            fixed_value=DamageType.Earth,
            value_getter=property_value(
                DamageTypeProperty,
                lambda prop: prop.damage_type,
            ),
        ),
    )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0xD5, 0x8, 0x1, 0x0]), "Ebon")

@dataclass(eq=False)
class FieryUpgrade(DamageTypeUpgrade):
    id = ItemUpgrade.Fiery
    damage_type = DamageType.Fire

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamageTypeProperty,
            target="damage_type",
            fixed_value=DamageType.Fire,
            value_getter=property_value(
                DamageTypeProperty,
                lambda prop: prop.damage_type,
            ),
        ),
    )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0xD7, 0x8, 0x1, 0x0]), "Fiery")

@dataclass(eq=False)
class FuriousUpgrade(WeaponPrefix):
    id = ItemUpgrade.Furious
    chance: int = 10

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.Furious,
            target="chance",
            min_value=2,
            max_value=10,
            value_getter=property_value(
                Furious,
                lambda prop: prop.chance,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.DOUBLE_ADRENALINE_BYTES]), "Double Adrenaline on hit"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x6F, 0xA, 0x1, 0x0]), "Furious")

@dataclass(eq=False)
class HaleUpgrade(WeaponPrefix):
    id = ItemUpgrade.Hale
    health: int = 30

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HealthPlus,
            target="health",
            min_value=10,
            max_value=30,
            value_getter=property_value(
                HealthPlus,
                lambda prop: prop.health,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.HEALTH_BYTES, self.health, "Health")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x70, 0xA, 0x1, 0x0]), "Hale")

@dataclass(eq=False)
class HeavyUpgrade(IncreaseConditionDurationUpgrade):
    id = ItemUpgrade.Heavy
    condition = Ailment.Weakness

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.IncreaseConditionDuration,
            target="condition",
            fixed_value=Ailment.Weakness,
            value_getter=property_value(
                IncreaseConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
    )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x72, 0xA, 0x1, 0x0]), "Heavy")

@dataclass(eq=False)
class IcyUpgrade(DamageTypeUpgrade):
    id = ItemUpgrade.Icy
    damage_type = DamageType.Cold

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamageTypeProperty,
            target="damage_type",
            fixed_value=DamageType.Cold,
            value_getter=property_value(
                DamageTypeProperty,
                lambda prop: prop.damage_type,
            ),
        ),
    )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0xD4, 0x8, 0x1, 0x0]), "Icy")

@dataclass(eq=False)
class InsightfulUpgrade(WeaponPrefix):
    id = ItemUpgrade.Insightful
    energy: int = 5

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.EnergyPlus,
            target="energy",
            min_value=1,
            max_value=5,
            value_getter=property_value(
                EnergyPlus,
                lambda prop: prop.energy,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x73, 0xA, 0x1, 0x0]), "Insightful")

@dataclass(eq=False)
class PoisonousUpgrade(IncreaseConditionDurationUpgrade):
    id = ItemUpgrade.Poisonous
    condition = Ailment.Poison

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.IncreaseConditionDuration,
            target="condition",
            fixed_value=Ailment.Poison,
            value_getter=property_value(
                IncreaseConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
    )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x75, 0xA, 0x1, 0x0]), "Poisonous")

@dataclass(eq=False)
class ShockingUpgrade(DamageTypeUpgrade):
    id = ItemUpgrade.Shocking
    damage_type = DamageType.Lightning

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamageTypeProperty,
            target="damage_type",
            fixed_value=DamageType.Lightning,
            value_getter=property_value(
                DamageTypeProperty,
                lambda prop: prop.damage_type,
            ),
        ),
    )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0xD6, 0x8, 0x1, 0x0]), "Shocking")

@dataclass(eq=False)
class SilencingUpgrade(IncreaseConditionDurationUpgrade):
    id = ItemUpgrade.Silencing
    condition = Ailment.Dazed

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.IncreaseConditionDuration,
            target="condition",
            fixed_value=Ailment.Dazed,
            value_getter=property_value(
                IncreaseConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
    )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x6C, 0xA, 0x1, 0x0]), "Silencing")

@dataclass(eq=False)
class SunderingUpgrade(WeaponPrefix):
    id = ItemUpgrade.Sundering
    chance: int = 20
    armor_penetration: int = 20

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPenetration,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                ArmorPenetration,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPenetration,
            target="armor_penetration",
            fixed_value=20,
            value_getter=property_value(
                ArmorPenetration,
                lambda prop: prop.armor_penetration,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        encoded = bytes([
            *self.get_text_color(),
            *GWEncoded.PLUS_PERCENT_TEMPLATE, 0x45, 0xA, 0x1, 0x0, 0x1, 0x1, self.armor_penetration, 0x1, 0x1, 0x0,
            *GWEncoded.ITEM_DULL,
            *GWEncoded.PARENTHESIS_STR1,
            *GWEncoded.CHANCE_TEMPLATE, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0,
            0x1, 0x0
        ])
        return GWStringEncoded(encoded, f"Armor penetration +{self.armor_penetration}% (Chance: {self.chance}%)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x74, 0xA, 0x1, 0x0]), "Sundering")

@dataclass(eq=False)
class SwiftUpgrade(WeaponPrefix):
    id = ItemUpgrade.Swift
    chance: int = 10

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeGeneral,
            target="chance",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                HalvesCastingTimeGeneral,
                lambda prop: prop.chance,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_CASTING_BYTES]), "Halves casting time of spells"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x1, 0x81, 0x95, 0x5D, 0x1, 0x0]), "Swift")

@dataclass(eq=False)
class VampiricMinorUpgrade(WeaponPrefix):
    id = ItemUpgrade.VampiricMinor
    health_regeneration: int = -1
    health_steal: int = 3

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.HealthRegeneneration,
            target="health_regeneration",
            fixed_value=-1,
            value_getter=property_value(
                HealthRegeneneration,
                lambda prop: prop.health_regeneration,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HealthStealOnHit,
            target="health_steal",
            fixed_value=3,
            value_getter=property_value(
                HealthStealOnHit,
                lambda prop: prop.health_steal,
            ),
        ),
    )
    

    def create_encoded_description(self) -> GWStringEncoded:
        parts = [
            GWEncoded._bonus_colon_num(self.get_text_color(), GWEncoded.LIFE_DRAINING_BYTES, self.health_steal, "Life Draining"),
            GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.HEALTH_REGEN_BYTES, abs(self.health_regeneration), "Health regeneration")
        ]
        
        return GWEncoded.combine_encoded_strings(parts, "no encoded description")
    

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x71, 0xA, 0x1, 0x0]), "Vampiric")

@dataclass(eq=False)
class VampiricMajorUpgrade(WeaponPrefix):
    id = ItemUpgrade.VampiricMajor
    health_regeneration: int = -1
    health_steal: int = 5

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.HealthRegeneneration,
            target="health_regeneration",
            fixed_value=-1,
            value_getter=property_value(
                HealthRegeneneration,
                lambda prop: prop.health_regeneration,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HealthStealOnHit,
            target="health_steal",
            fixed_value=5,
            value_getter=property_value(
                HealthStealOnHit,
                lambda prop: prop.health_steal,
            ),
        ),
    )
    

    def create_encoded_description(self) -> GWStringEncoded:
        parts = [
            GWEncoded._bonus_colon_num(self.get_text_color(), GWEncoded.LIFE_DRAINING_BYTES, self.health_steal, "Life Draining"),
            GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.HEALTH_REGEN_BYTES, abs(self.health_regeneration), "Health regeneration")
        ]
        
        return GWEncoded.combine_encoded_strings(parts, "no encoded description")
    

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x71, 0xA, 0x1, 0x0]), "Vampiric")

@dataclass(eq=False)
class ZealousUpgrade(WeaponPrefix):
    id = ItemUpgrade.Zealous
    energy_regeneration: int = -1
    energy_gain: int = 1

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.EnergyGainOnHit,
            target="energy_gain",
            fixed_value=1,
            value_getter=property_value(
                EnergyGainOnHit,
                lambda prop: prop.energy_gain,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.EnergyRegeneration,
            target="energy_regeneration",
            fixed_value=-1,
            value_getter=property_value(
                EnergyRegeneration,
                lambda prop: prop.energy_regeneration,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        parts = [
            GWEncoded._bonus_colon_num(self.get_text_color(), GWEncoded.ENERGY_GAIN_ON_HIT_BYTES, self.energy_gain, "Energy gain on hit"),
            GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.ENERGY_REGEN_BYTES, abs(self.energy_regeneration), "Energy regeneration")
        ]
        
        return GWEncoded.combine_encoded_strings(parts, "no encoded description")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x6E, 0xA, 0x1, 0x0]), "Zealous")
    
#endregion Prefixes

#region Suffixes

@dataclass(eq=False)
class WeaponSuffix(WeaponUpgrade):
    mod_type = ItemUpgradeType.Suffix

    def create_upgrade_name(self, item_type: ItemType) -> GWStringEncoded:
        encoded_upgrade_component = GWEncoded.WEAPON_SUFFIXES.get(item_type) or bytes()
        if not encoded_upgrade_component:
            return self.create_encoded_name()

        encoded_name = self.create_encoded_name()
        color_bytes = self.get_text_color(True)
        suffix_prefix = bytes([*color_bytes, *GWEncoded.STR1_OF_STR2, *GWEncoded.PLACEHOLDER_TO_REMOVE])
        suffix = encoded_name.encoded[len(suffix_prefix):] if encoded_name.encoded.startswith(suffix_prefix) else encoded_name.encoded
        return GWStringEncoded(
            bytes([*color_bytes, *encoded_upgrade_component, *suffix]),
            encoded_name.fallback,
            encoded_name.placeholder_bytes,
            encoded_name.placeholder_replacement,
        )

#region OfAttributeUpgrade
@dataclass(eq=False)
class OfAttributeUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfAttribute
    chance: int = 20
    attribute: Attribute = Attribute.None_
    attribute_level: int = 1
    
    def create_encoded_description(self) -> GWStringEncoded:
        attribute_bytes = GWEncoded._attribute_bytes(self.attribute)
        if attribute_bytes:
            base = GWStringEncoded(bytes([*self.get_text_color(), 0x84, 0xA, 0xA, 0x1, *attribute_bytes, 0x1, 0x0, 0x1, 0x1, 0x1, self.attribute_level]), f"{GWEncoded._attribute_name(self.attribute)} +{self.attribute_level}")
            clause_raw = bytes([0xC1, 0xA, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0])
            
            return GWEncoded._append_line_with_fallback(base, GWEncoded._dull_parenthesized(clause_raw, f"({self.chance}% chance while using skills)"), f"({self.chance}% chance while using skills)")
        return GWStringEncoded(bytes(), f"{GWEncoded._attribute_name(self.attribute)} +1 ({self.chance}% chance while using skills)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0xB, 0x1]) + GWEncoded.ATTRIBUTE_NAMES.get(self.attribute, bytes()) + bytes([0x1, 0x0, 0x1, 0x0]), f"of {AttributeNames.get(self.attribute, self.attribute.name)}", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Attribute"])

    def equals(self, other: object) -> bool:
        return (
            isinstance(other, OfAttributeUpgrade)
            and self.attribute == other.attribute
            and self.attribute_level == other.attribute_level
            and self.chance == other.chance
        )

    def matches(self, other: object) -> bool:
        return self.equals(other)

@dataclass(eq=False)
class OfDivineFavorUpgrade(OfAttributeUpgrade):
    attribute = Attribute.DivineFavor

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.DivineFavor,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfHealingPrayersUpgrade(OfAttributeUpgrade):
    attribute = Attribute.HealingPrayers

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.HealingPrayers,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfSmitingPrayersUpgrade(OfAttributeUpgrade):
    attribute = Attribute.SmitingPrayers

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.SmitingPrayers,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfProtectionPrayersUpgrade(OfAttributeUpgrade):
    attribute = Attribute.ProtectionPrayers

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.ProtectionPrayers,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfBloodMagicUpgrade(OfAttributeUpgrade):
    attribute = Attribute.BloodMagic

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.BloodMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfDeathMagicUpgrade(OfAttributeUpgrade):
    attribute = Attribute.DeathMagic

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.DeathMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfCursesUpgrade(OfAttributeUpgrade):
    attribute = Attribute.Curses

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.Curses,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfIllusionMagicUpgrade(OfAttributeUpgrade):
    attribute = Attribute.IllusionMagic

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.IllusionMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfDominationMagicUpgrade(OfAttributeUpgrade):
    attribute = Attribute.DominationMagic

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.DominationMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfInspirationMagicUpgrade(OfAttributeUpgrade):
    attribute = Attribute.InspirationMagic

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.InspirationMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfAirMagicUpgrade(OfAttributeUpgrade):
    attribute = Attribute.AirMagic

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.AirMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfEarthMagicUpgrade(OfAttributeUpgrade):
    attribute = Attribute.EarthMagic

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.EarthMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfFireMagicUpgrade(OfAttributeUpgrade):
    attribute = Attribute.FireMagic

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.FireMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfWaterMagicUpgrade(OfAttributeUpgrade):
    attribute = Attribute.WaterMagic

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.WaterMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfSpawningPowerUpgrade(OfAttributeUpgrade):
    attribute = Attribute.SpawningPower

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.SpawningPower,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfCommuningUpgrade(OfAttributeUpgrade):
    attribute = Attribute.Communing

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.Communing,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfRestorationMagicUpgrade(OfAttributeUpgrade):
    attribute = Attribute.RestorationMagic

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.RestorationMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfChannelingMagicUpgrade(OfAttributeUpgrade):
    attribute = Attribute.ChannelingMagic

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.ChannelingMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )
#endregion OfAttributeUpgrade

@dataclass(eq=False)
class OfAptitudeUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfAptitude
    chance: int = 20

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeItemAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeItemAttribute,
                lambda prop: prop.chance,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_CASTING_ITEM_ATTRIBUTE_BYTES]), "Halves casting time on spells of item's attribute"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x96, 0x5D, 0x1, 0x0]), "of Aptitude", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Aptitude"])

@dataclass(eq=False)
class OfAxeMasteryUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfAxeMastery
    attribute = Attribute.AxeMastery
    
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.AxeMastery,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfDaggerMasteryUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfDaggerMastery
    attribute = Attribute.DaggerMastery

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.DaggerMastery,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfDefenseUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfDefense
    armor: int = 5

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlus,
            target="armor",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                ArmorPlus,
                lambda prop: prop.armor,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x77, 0xA, 0x1, 0x0]), "of Defense", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Defense"])

@dataclass(eq=False)
class OfDevotionUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfDevotion
    health: int = 45

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HealthPlusEnchanted,
            target="health",
            min_value=30,
            max_value=45,
            value_getter=property_value(
                HealthPlusEnchanted,
                lambda prop: prop.health,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.HEALTH_BYTES, self.health, "Health"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_ENCHANTED_BYTES, "(while Enchanted)"), "(while Enchanted)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x97, 0x5D, 0x1, 0x0]), "of Devotion", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Devotion"])

@dataclass(eq=False)
class OfEnchantingUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfEnchanting
    enchantment_duration: int = 20

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.IncreaseEnchantmentDuration,
            target="enchantment_duration",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                IncreaseEnchantmentDuration,
                lambda prop: prop.enchantment_duration,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes([*self.get_text_color(), 0xA, 0x1, 0xA2, 0xA, 0x1, 0x1, self.enchantment_duration, 0x1, 0x1, 0x0]), f"Enchantments last {self.enchantment_duration}% longer")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x78, 0xA, 0x1, 0x0]), "of Enchanting", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Enchanting"])

@dataclass(eq=False)
class OfEnduranceUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfEndurance
    health: int = 45

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HealthPlusStance,
            target="health",
            min_value=30,
            max_value=45,
            value_getter=property_value(
                HealthPlusStance,
                lambda prop: prop.health,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.HEALTH_BYTES, self.health, "Health"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_IN_A_STANCE_BYTES, "(while in a Stance)"), "(while in a Stance)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x98, 0x5D, 0x1, 0x0]), "of Endurance", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Endurance"])

@dataclass(eq=False)
class OfFortitudeUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfFortitude
    health: int = 30

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HealthPlus,
            target="health",
            min_value=10,
            max_value=30,
            value_getter=property_value(
                HealthPlus,
                lambda prop: prop.health,
            ),
        ),
    )

    
    def create_upgrade_name(self, item_type):
        encoded_upgrade_component = (GWEncoded.WEAPON_PREFIXES.get(item_type) if self.mod_type == ItemUpgradeType.Prefix else GWEncoded.WEAPON_SUFFIXES.get(item_type)) or bytes()
        return GWStringEncoded(bytes([*self.get_text_color(True), *encoded_upgrade_component, 0x79, 0xA, 0x1, 0x0]), f"of Fortitude") if encoded_upgrade_component else self.create_encoded_name()
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.HEALTH_BYTES, self.health, "Health")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x79, 0xA, 0x1, 0x0]), "of Fortitude", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Fortitude"])

@dataclass(eq=False)
class OfHammerMasteryUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfHammerMastery
    attribute = Attribute.HammerMastery
    
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.HammerMastery,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfMarksmanshipUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfMarksmanship
    attribute = Attribute.Marksmanship

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.Marksmanship,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )
@dataclass(eq=False)
class OfMasteryUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfMastery
    chance: int = 20
    attribute_level: int = 1

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOneItem,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOneItem,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOneItem,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOneItem,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.ITEM_ATTRIBUTE_PLUS_ONE_BYTES, self.attribute_level]), "Item's attribute +1"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x99, 0x5D, 0x1, 0x0]), "of Mastery", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Mastery"])

@dataclass(eq=False)
class OfMemoryUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfMemory
    chance: int = 20

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeItemAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeItemAttribute,
                lambda prop: prop.chance,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_RECHARGE_ITEM_ATTRIBUTE_BYTES]), "Halves skill recharge on spells of item's attribute"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x9A, 0x5D, 0x1, 0x0]), "of Memory", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Memory"])

@dataclass(eq=False)
class OfQuickeningUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfQuickening
    chance: int = 10

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeGeneral,
            target="chance",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                HalvesSkillRechargeGeneral,
                lambda prop: prop.chance,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_RECHARGE_BYTES]), "Halves skill recharge of spells"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x9B, 0x5D, 0x1, 0x0]), "of Quickening", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Quickening"])

@dataclass(eq=False)
class OfScytheMasteryUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfScytheMastery
    attribute = Attribute.ScytheMastery
    
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.ScytheMastery,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfShelterUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfShelter
    armor: int = 7

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsPhysical,
            target="armor",
            min_value=4,
            max_value=7,
            value_getter=property_value(
                ArmorPlusVsPhysical,
                lambda prop: prop.armor,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.VS_PHYSICAL_DAMAGE_BYTES, "(vs. physical damage)"), "(vs. physical damage)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x7B, 0xA, 0x1, 0x0]), "of Shelter", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Shelter"])

#region OfSlayingUpgrade

@dataclass(eq=False)
class OfSlayingUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfSlaying
    species: ItemBaneSpecies = ItemBaneSpecies.Unknown
    damage_increase: int = 20

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), bytes([*GWEncoded.DAMAGE_TEXT, 0x1, 0x0]), self.damage_increase, f"Damage +{self.damage_increase}%"), GWEncoded._dull_parenthesized(bytes([*GWEncoded.VS_STR1, *GWEncoded.SPECIES.get(self.species, bytes())]), f"(vs. {self.species.name})"), f"(vs. {self.species.name})")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0xB, 0x1]) + GWEncoded.SLAYING_SUFFIXES.get(self.species, bytes()) + bytes([0x1, 0x0, 0x1, 0x0, 0x0, 0x0]), 
                               f"of {self.species.name}-Slaying", 
                               GWEncoded.PLACEHOLDER_TO_REMOVE, 
                               ["", f"{self.species.name}-Slaying" if self.species != ItemBaneSpecies.Unknown else "Slaying"])

@dataclass(eq=False)
class OfUndeadSlayingUpgrade(OfSlayingUpgrade):
    species = ItemBaneSpecies.Undead

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Undead,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="damage_increase",
            min_value=15,
            max_value=20,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.damage_increase,
            ),
        ),
    )

@dataclass(eq=False)
class OfCharrSlayingUpgrade(OfSlayingUpgrade):
    species = ItemBaneSpecies.Charr

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Charr,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="damage_increase",
            min_value=15,
            max_value=20,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.damage_increase,
            ),
        ),
    )

@dataclass(eq=False)
class OfTrollsSlayingUpgrade(OfSlayingUpgrade):
    species = ItemBaneSpecies.Trolls

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Trolls,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="damage_increase",
            min_value=15,
            max_value=20,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.damage_increase,
            ),
        ),
    )

@dataclass(eq=False)
class OfPlantsSlayingUpgrade(OfSlayingUpgrade):
    species = ItemBaneSpecies.Plants

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Plants,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="damage_increase",
            min_value=15,
            max_value=20,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.damage_increase,
            ),
        ),
    )

@dataclass(eq=False)
class OfSkeletonsSlayingUpgrade(OfSlayingUpgrade):
    species = ItemBaneSpecies.Skeletons

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Skeletons,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="damage_increase",
            min_value=15,
            max_value=20,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.damage_increase,
            ),
        ),
    )

@dataclass(eq=False)
class OfGiantsSlayingUpgrade(OfSlayingUpgrade):
    species = ItemBaneSpecies.Giants

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Giants,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="damage_increase",
            min_value=15,
            max_value=20,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.damage_increase,
            ),
        ),
    )

@dataclass(eq=False)
class OfDwarvesSlayingUpgrade(OfSlayingUpgrade):
    species = ItemBaneSpecies.Dwarves

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Dwarves,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="damage_increase",
            min_value=15,
            max_value=20,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.damage_increase,
            ),
        ),
    )

@dataclass(eq=False)
class OfTengusSlayingUpgrade(OfSlayingUpgrade):
    species = ItemBaneSpecies.Tengus

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Tengus,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="damage_increase",
            min_value=15,
            max_value=20,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.damage_increase,
            ),
        ),
    )

@dataclass(eq=False)
class OfDemonsSlayingUpgrade(OfSlayingUpgrade):
    species = ItemBaneSpecies.Demons

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Demons,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="damage_increase",
            min_value=15,
            max_value=20,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.damage_increase,
            ),
        ),
    )

@dataclass(eq=False)
class OfDragonsSlayingUpgrade(OfSlayingUpgrade):
    species = ItemBaneSpecies.Dragons

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Dragons,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="damage_increase",
            min_value=15,
            max_value=20,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.damage_increase,
            ),
        ),
    )

@dataclass(eq=False)
class OfOgresSlayingUpgrade(OfSlayingUpgrade):
    species = ItemBaneSpecies.Ogres

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Ogres,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.DamagePlusVsSpecies,
            target="damage_increase",
            min_value=15,
            max_value=20,
            value_getter=property_value(
                DamagePlusVsSpecies,
                lambda prop: prop.damage_increase,
            ),
        ),
    )
#endregion OfSlayingUpgrade

@dataclass(eq=False)
class OfSpearMasteryUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfSpearMastery
    attribute = Attribute.SpearMastery

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.SpearMastery,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )

@dataclass(eq=False)
class OfSwiftnessUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfSwiftness
    chance: int = 10

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeGeneral,
            target="chance",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                HalvesCastingTimeGeneral,
                lambda prop: prop.chance,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_CASTING_BYTES]), "Halves casting time of spells"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x7C, 0xA, 0x1, 0x0]), "of Swiftness", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Swiftness"])

@dataclass(eq=False)
class OfSwordsmanshipUpgrade(OfAttributeUpgrade):
    id = ItemUpgrade.OfSwordsmanship
    attribute = Attribute.Swordsmanship

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.Swordsmanship,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
    )
    
#region OfTheProfessionUpgrade
@dataclass(eq=False)
class OfTheProfessionUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfTheProfession
    profession: Profession = Profession._None
    attribute: Attribute = Attribute.None_
    attribute_level: int = 5

    def create_encoded_description(self) -> GWStringEncoded:
        encoded_bytes = bytes([*self.get_text_color(), 0x86, 0xA, 0xA, 0x1, *GWEncoded.ATTRIBUTE_NAMES.get(self.attribute, bytes()), 0x1, 0x0, 0x1, 0x1, self.attribute_level, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x2, 0x81, 0xA8, 0x38, 0x1, 0x0])
        return GWStringEncoded(encoded_bytes, f"{AttributeNames.get(self.attribute)}: {self.attribute_level} (if your rank is lower. No effect in PvP.)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + GWEncoded.THE_PROFESSION.get(self.profession, bytes()), f"of {self.profession.name if self.profession != Profession._None else 'Unknown Profession'}", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", self.profession.name if self.profession != Profession._None else "Profession"])

    def equals(self, other: object) -> bool:
        return (
            isinstance(other, OfTheProfessionUpgrade)
            and self.profession == other.profession
            and self.attribute == other.attribute
            and self.attribute_level == other.attribute_level
        )

    def matches(self, other: object) -> bool:
        return self.equals(other)

@dataclass(eq=False)
class OfTheWarriorUpgrade(OfTheProfessionUpgrade):
    profession = Profession.Warrior
    attribute = Attribute.Strength

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute",
            fixed_value=Attribute.Strength,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute_level",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="profession",
            fixed_value=Profession.Warrior,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.profession,
            ),
        ),
    )

@dataclass(eq=False)
class OfTheRangerUpgrade(OfTheProfessionUpgrade):
    profession = Profession.Ranger
    attribute = Attribute.Expertise

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute",
            fixed_value=Attribute.Expertise,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute_level",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="profession",
            fixed_value=Profession.Ranger,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.profession,
            ),
        ),
    )

@dataclass(eq=False)
class OfTheMonkUpgrade(OfTheProfessionUpgrade):
    profession = Profession.Monk
    attribute = Attribute.DivineFavor

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute",
            fixed_value=Attribute.DivineFavor,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute_level",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="profession",
            fixed_value=Profession.Monk,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.profession,
            ),
        ),
    )

@dataclass(eq=False)
class OfTheNecromancerUpgrade(OfTheProfessionUpgrade):
    profession = Profession.Necromancer
    attribute = Attribute.SoulReaping

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute",
            fixed_value=Attribute.SoulReaping,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute_level",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="profession",
            fixed_value=Profession.Necromancer,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.profession,
            ),
        ),
    )

@dataclass(eq=False)
class OfTheMesmerUpgrade(OfTheProfessionUpgrade):
    profession = Profession.Mesmer
    attribute = Attribute.FastCasting

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute",
            fixed_value=Attribute.FastCasting,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute_level",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="profession",
            fixed_value=Profession.Mesmer,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.profession,
            ),
        ),
    )

@dataclass(eq=False)
class OfTheElementalistUpgrade(OfTheProfessionUpgrade):
    profession = Profession.Elementalist
    attribute = Attribute.EnergyStorage

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute",
            fixed_value=Attribute.EnergyStorage,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute_level",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="profession",
            fixed_value=Profession.Elementalist,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.profession,
            ),
        ),
    )

@dataclass(eq=False)
class OfTheAssassinUpgrade(OfTheProfessionUpgrade):
    profession = Profession.Assassin
    attribute = Attribute.CriticalStrikes

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute",
            fixed_value=Attribute.CriticalStrikes,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute_level",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="profession",
            fixed_value=Profession.Assassin,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.profession,
            ),
        ),
    )

@dataclass(eq=False)
class OfTheRitualistUpgrade(OfTheProfessionUpgrade):
    profession = Profession.Ritualist
    attribute = Attribute.SpawningPower

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute",
            fixed_value=Attribute.SpawningPower,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute_level",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="profession",
            fixed_value=Profession.Ritualist,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.profession,
            ),
        ),
    )

@dataclass(eq=False)
class OfTheParagonUpgrade(OfTheProfessionUpgrade):
    profession = Profession.Paragon
    attribute = Attribute.Leadership

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute",
            fixed_value=Attribute.Leadership,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute_level",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="profession",
            fixed_value=Profession.Paragon,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.profession,
            ),
        ),
    )

@dataclass(eq=False)
class OfTheDervishUpgrade(OfTheProfessionUpgrade):
    profession = Profession.Dervish
    attribute = Attribute.Mysticism

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute",
            fixed_value=Attribute.Mysticism,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.OfTheProfession,
            target="attribute_level",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.OfTheProfession,
            target="profession",
            fixed_value=Profession.Dervish,
            value_getter=property_value(
                OfTheProfession,
                lambda prop: prop.profession,
            ),
        ),
    )
#endregion OfTheProfessionUpgrade

@dataclass(eq=False)
class OfValorUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfValor
    health: int = 60

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HealthPlusHexed,
            target="health",
            min_value=45,
            max_value=60,
            value_getter=property_value(
                HealthPlusHexed,
                lambda prop: prop.health,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.HEALTH_BYTES, self.health, "Health"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEXED_BYTES, "(while Hexed)"), "(while Hexed)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x1, 0x81, 0x9C, 0x5D, 0x1, 0x0]), "of Valor", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Valor"])

@dataclass(eq=False)
class OfWardingUpgrade(WeaponSuffix):
    id = ItemUpgrade.OfWarding
    armor: int = 7

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsElemental,
            target="armor",
            min_value=4,
            max_value=7,
            value_getter=property_value(
                ArmorPlusVsElemental,
                lambda prop: prop.armor,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.VS_ELEMENTAL_DAMAGE_BYTES, "(vs. elemental damage)"), "(vs. elemental damage)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + GWEncoded.STR1_OF_STR2 + GWEncoded.PLACEHOLDER_TO_REMOVE + bytes([0x7D, 0xA, 0x1, 0x0]), "of Warding", GWEncoded.PLACEHOLDER_TO_REMOVE, ["", "Warding"])

#endregion Suffixes

#region Inscriptions    
@dataclass(eq=False)
class Inscription(Upgrade):
    mod_type = ItemUpgradeType.Inscription
    target_item_type: ItemType = field(init=False, default=ItemType.Unknown, repr=False, compare=False)

    @classmethod
    def _pre_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, all_modifiers: list[DecodedModifier], remaining_modifiers: list[DecodedModifier]) -> None:
        inscription = cast(Inscription, upgrade)
        inscription.target_item_type = cls.id.get_item_type(inscription.upgrade_id)   

class OffhandInscription(Inscription):
    target_item_type = ItemType.Offhand
    
class WeaponInscription(Inscription):
    target_item_type = ItemType.Weapon
    
class MartialWeaponInscription(Inscription):
    target_item_type = ItemType.MartialWeapon
    
class OffhandOrShieldInscription(Inscription):
    target_item_type = ItemType.OffhandOrShield
    
class ReduceConditionDurationInscription(OffhandOrShieldInscription):
    condition: Reduced_Ailment | None = None

    def create_encoded_description(self) -> GWStringEncoded:
        if self.condition is not None:
            fallback = f"Reduces {self.condition.name} duration on you by 20% (Stacking)"
            encoded = GWEncoded.REDUCED_CONDITION_BYTES.get(self.condition)
            base = GWStringEncoded(bytes([*self.get_text_color(), *encoded]), fallback) if encoded else GWStringEncoded(bytes(), fallback)
            
            return GWEncoded._append_line_with_fallback(base, GWEncoded._dull_parenthesized(GWEncoded.STACKING_BYTES, "(Stacking)"), fallback)
        
        return super().create_encoded_description()

class ArmorVsDamageTypeInscription(OffhandOrShieldInscription):
    armor: int = 10
    damage_type: DamageType | None = None

    def create_encoded_description(self) -> GWStringEncoded:
        if self.damage_type is None:
            return super().create_encoded_description()
        
        base = GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor")
        clause_bytes = GWEncoded.VS_DAMAGE_BYTES.get(self.damage_type)
        if clause_bytes:
            return GWEncoded._append_line_with_fallback(base, GWEncoded._dull_parenthesized(clause_bytes, f"(vs. {self.damage_type.name} damage)"), f"(vs. {self.damage_type.name} damage)")
        return GWStringEncoded(bytes(), f"{base.fallback} (vs. {self.damage_type.name} damage)")

class EquippableItemInscription(Inscription):
    target_item_type = ItemType.EquippableItem
    
class SpellcastingWeaponInscription(Inscription):
    target_item_type = ItemType.SpellcastingWeapon
    
#region Offhand
@dataclass(eq=False)
class BeJustAndFearNot(OffhandInscription):
    id = ItemUpgrade.BeJustAndFearNot
    armor: int = 10
    target_item_type = ItemType.Offhand

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusHexed,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusHexed,
                lambda prop: prop.armor,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEXED_BYTES, "(while Hexed)"))

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x90, 0x5D, 0x1, 0x0]), f"Be Just And Fear Not")
 
@dataclass(eq=False)
class DownButNotOut(OffhandInscription):
    id = ItemUpgrade.DownButNotOut
    
    armor: int = 10
    health_threshold: int = 50

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusWhileBelow,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusWhileBelow,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusWhileBelow,
            target="health_threshold",
            fixed_value=50,
            value_getter=property_value(
                ArmorPlusWhileBelow,
                lambda prop: prop.health_threshold,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEALTH_BELOW_BYTES, f"(while Health is below {self.health_threshold}%)"), f"(while Health is below {self.health_threshold}%)")

    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x8E, 0x5D, 0x1, 0x0]), f"Down But Not Out")    
    
@dataclass(eq=False)
class FaithIsMyShield(OffhandInscription):
    id = ItemUpgrade.FaithIsMyShield
    armor: int = 5

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusEnchanted,
            target="armor",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                ArmorPlusEnchanted,
                lambda prop: prop.armor,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_ENCHANTED_BYTES, "(while Enchanted)"))

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x8D, 0x5D, 0x1, 0x0]), f"Faith Is My Shield")
    
@dataclass(eq=False)
class ForgetMeNot(OffhandInscription):
    id = ItemUpgrade.ForgetMeNot
    chance: int = 20

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeItemAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeItemAttribute,
                lambda prop: prop.chance,
            ),
        ),
    )
    
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_RECHARGE_ITEM_ATTRIBUTE_BYTES]), "Halves skill recharge on spells of item's attribute"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x93, 0x5D, 0x1, 0x0]), f"Forget Me Not")
    
@dataclass(eq=False)
class HailToTheKing(OffhandInscription):
    id = ItemUpgrade.HailToTheKing
    armor: int = 5
    health_threshold: int = 50

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusAbove,
            target="armor",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                ArmorPlusAbove,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusAbove,
            target="health_threshold",
            fixed_value=50,
            value_getter=property_value(
                ArmorPlusAbove,
                lambda prop: prop.health_threshold,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEALTH_ABOVE_BYTES, "(while health above 50 %)"), "(while health above 50 %)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x8F, 0x5D, 0x1, 0x0]), f"Hail To The King")
    
@dataclass(eq=False)
class IgnoranceIsBliss(OffhandInscription):
    id = ItemUpgrade.IgnoranceIsBliss
    armor: int = 5
    energy: int = 5

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlus,
            target="armor",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                ArmorPlus,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.EnergyMinus,
            target="energy",
            fixed_value=5,
            value_getter=property_value(
                EnergyMinus,
                lambda prop: prop.energy,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        parts = [
            GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, abs(self.armor), "Armor"),
            GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, abs(self.energy), "Energy")
        ]
        
        return GWEncoded.combine_encoded_strings(parts, f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x87, 0x5D, 0x1, 0x0]), f"Ignorance Is Bliss")
    
@dataclass(eq=False)
class KnowingIsHalfTheBattle(OffhandInscription):
    id = ItemUpgrade.KnowingIsHalfTheBattle
    armor: int = 5

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusCasting,
            target="armor",
            fixed_value=5,
            value_getter=property_value(
                ArmorPlusCasting,
                lambda prop: prop.armor,
            ),
        ),
    )
        
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_CASTING_BYTES, "(while casting)"))
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x8C, 0x5D, 0x1, 0x0]), f"Knowing Is Half The Battle")
    
@dataclass(eq=False)
class LifeIsPain(OffhandInscription):
    id = ItemUpgrade.LifeIsPain
    armor: int = 5
    health: int = 20

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlus,
            target="armor",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                ArmorPlus,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HealthMinus,
            target="health",
            fixed_value=20,
            value_getter=property_value(
                HealthMinus,
                lambda prop: prop.health_reduction,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        parts = [
            GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, abs(self.armor), "Armor"),
            GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.HEALTH_BYTES, abs(self.health), "Health")
        ]
        
        return GWEncoded.combine_encoded_strings(parts, f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)")
       
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x88, 0x5D, 0x1, 0x0]), f"Life Is Pain")
    
@dataclass(eq=False)
class LiveForToday(OffhandInscription):
    id = ItemUpgrade.LiveForToday
    energy: int = 15
    energy_regeneration: int = -1
    
    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.EnergyPlus,
            target="energy",
            min_value=10,
            max_value=15,
            value_getter=property_value(
                EnergyPlus,
                lambda prop: prop.energy,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.EnergyRegeneration,
            target="energy_regeneration",
            fixed_value=-1,
            value_getter=property_value(
                EnergyRegeneration,
                lambda prop: prop.energy_regeneration,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        parts = [
            GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy"),
            GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.ENERGY_REGEN_BYTES, abs(self.energy_regeneration), "Energy regeneration")
        ]
        
        return GWEncoded.combine_encoded_strings(parts, f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x91, 0x5D, 0x1, 0x0]), f"Live For Today")
    
@dataclass(eq=False)
class ManForAllSeasons(OffhandInscription):
    id = ItemUpgrade.ManForAllSeasons
    armor: int = 5

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsElemental,
            target="armor",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                ArmorPlusVsElemental,
                lambda prop: prop.armor,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.VS_ELEMENTAL_DAMAGE_BYTES, "(vs. elemental damage)"), "(vs. elemental damage)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x89, 0x5D, 0x1, 0x0]), f"Man For All Seasons")
    
@dataclass(eq=False)
class MightMakesRight(OffhandInscription):
    id = ItemUpgrade.MightMakesRight
    armor: int = 5

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusAttacking,
            target="armor",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                ArmorPlusAttacking,
                lambda prop: prop.armor,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(bytes([0xB4, 0xA, 0x1, 0x0]), "(while attacking)"))

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x8B, 0x5D, 0x1, 0x0]), f"Might Makes Right")
    
@dataclass(eq=False)
class SerenityNow(OffhandInscription):
    id = ItemUpgrade.SerenityNow
    chance: int = 10

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeGeneral,
            target="chance",
            min_value=7,
            max_value=10,
            value_getter=property_value(
                HalvesSkillRechargeGeneral,
                lambda prop: prop.chance,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_RECHARGE_BYTES]), "Halves skill recharge of spells"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x92, 0x5D, 0x1, 0x0]), f"Serenity Now")
    
@dataclass(eq=False)
class SurvivalOfTheFittest(OffhandInscription):
    id = ItemUpgrade.SurvivalOfTheFittest
    armor: int = 5
    
    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsPhysical,
            target="armor",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                ArmorPlusVsPhysical,
                lambda prop: prop.armor,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.VS_PHYSICAL_DAMAGE_BYTES, "(vs. physical damage)"), "(vs. physical damage)")    
   
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x8A, 0x5D, 0x1, 0x0]), f"Survival Of The Fittest")

#endregion Offhand

#region Weapon

@dataclass(eq=False)
class BrawnOverBrains(WeaponInscription):
    id = ItemUpgrade.BrawnOverBrains
    damage_increase: int = 15
    energy: int = 5

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.DamagePlusPercent,
            target="damage_increase",
            min_value=14,
            max_value=15,
            value_getter=property_value(
                DamagePlusPercent,
                lambda prop: prop.damage_increase,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.EnergyMinus,
            target="energy",
            fixed_value=5,
            value_getter=property_value(
                EnergyMinus,
                lambda prop: prop.energy,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        parts = [
            GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"),
            GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, abs(self.energy), "Energy")
        ]
        
        return GWEncoded.combine_encoded_strings(parts, f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)")
    
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xAE, 0x5D, 0x1, 0x0]), f"Brawn Over Brains")
        
@dataclass(eq=False)
class DanceWithDeath(WeaponInscription):
    id = ItemUpgrade.DanceWithDeath
    damage_increase: int = 15

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.DamagePlusStance,
            target="damage_increase",
            min_value=10,
            max_value=15,
            value_getter=property_value(
                DamagePlusStance,
                lambda prop: prop.damage_increase,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_IN_A_STANCE_BYTES, "(while in a Stance)"), "(while in a Stance)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xAD, 0x5D, 0x1, 0x0]), f"Dance With Death")
         
@dataclass(eq=False)
class DontFearTheReaper(WeaponInscription):
    id = ItemUpgrade.DontFearTheReaper
    damage_increase: int = 15

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.DamagePlusHexed,
            target="damage_increase",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                DamagePlusHexed,
                lambda prop: prop.damage_increase,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEXED_BYTES, "(while Hexed)"), "(while Hexed)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xAC, 0x5D, 0x1, 0x0]), f"Dont Fear The Reaper")
    
@dataclass(eq=False)
class DontThinkTwice(WeaponInscription):
    id = ItemUpgrade.DontThinkTwice
    chance: int = 10

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeGeneral,
            target="chance",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                HalvesCastingTimeGeneral,
                lambda prop: prop.chance,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_CASTING_BYTES]), "Halves casting time of spells"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB0, 0x5D, 0x1, 0x0]), f"Dont Think Twice")
    
@dataclass(eq=False)
class GuidedByFate(WeaponInscription):
    id = ItemUpgrade.GuidedByFate
    damage_increase: int = 15

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.DamagePlusEnchanted,
            target="damage_increase",
            min_value=10,
            max_value=15,
            value_getter=property_value(
                DamagePlusEnchanted,
                lambda prop: prop.damage_increase,
            ),
        ),
     )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_ENCHANTED_BYTES, "(while Enchanted)"), "(while Enchanted)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xA9, 0x5D, 0x1, 0x0]), f"Guided By Fate")
    
@dataclass(eq=False)
class StrengthAndHonor(WeaponInscription):
    id = ItemUpgrade.StrengthAndHonor
    damage_increase: int = 15
    health_threshold: int = 50

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.DamagePlusWhileAbove,
            target="damage_increase",
            min_value=10,
            max_value=15,
            value_getter=property_value(
                DamagePlusWhileAbove,
                lambda prop: prop.damage_increase,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.DamagePlusWhileAbove,
            target="health_threshold",
            fixed_value=50,
            value_getter=property_value(
                DamagePlusWhileAbove,
                lambda prop: prop.health_threshold,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEALTH_ABOVE_BYTES, f"(while Health is above {self.health_threshold}%)"), f"(while Health is above {self.health_threshold}%)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xAA, 0x5D, 0x1, 0x0]), f"Strength And Honor")
    
@dataclass(eq=False)
class ToThePain(WeaponInscription):
    id = ItemUpgrade.ToThePain
    damage_increase: int = 15
    armor: int = 10

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.DamagePlusPercent,
            target="damage_increase",
            min_value=14,
            max_value=15,
            value_getter=property_value(
                DamagePlusPercent,
                lambda prop: prop.damage_increase,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorMinusAttacking,
            target="armor",
            fixed_value=10,
            value_getter=property_value(
                ArmorMinusAttacking,
                lambda prop: prop.armor,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        parts = [
            GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"),
            GWEncoded._encoded(
                bytes([*self.get_text_color(), *GWEncoded.MINUS_NUM_TEMPLATE, *GWEncoded.ARMOR_BYTES, 0x1, 0x1, self.armor, 0x1, 0x1, 0x0, *GWEncoded.WHILE_ATTACKING_BYTES]),
                f"Armor -{self.armor} (while attacking)",
            ),
        ]
        
        return GWEncoded.combine_encoded_strings(parts, f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xAF, 0x5D, 0x1, 0x0]), f"To The Pain")
    
@dataclass(eq=False)
class TooMuchInformation(WeaponInscription):
    id = ItemUpgrade.TooMuchInformation
    damage_increase: int = 15

    upgrade_info = (
         ranged(
            identifier=ModifierIdentifier.DamagePlusVsHexed,
            target="damage_increase",
            min_value=10,
            max_value=15,
            value_getter=property_value(
                DamagePlusVsHexed,
                lambda prop: prop.damage_increase,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"), GWEncoded._dull_parenthesized(GWEncoded.VS_HEXED_FOES_BYTES, "(vs. Hexed foes)"), "(vs. Hexed foes)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xA8, 0x5D, 0x1, 0x0]), f"Too Much Information")
    
@dataclass(eq=False)
class VengeanceIsMine(WeaponInscription):
    id = ItemUpgrade.VengeanceIsMine
    damage_increase: int = 20
    health_threshold: int = 50

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.DamagePlusWhileBelow,
            target="damage_increase",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                DamagePlusWhileBelow,
                lambda prop: prop.damage_increase,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.DamagePlusWhileBelow,
            target="health_threshold",
            fixed_value=50,
            value_getter=property_value(
                DamagePlusWhileBelow,
                lambda prop: prop.health_threshold,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEALTH_BELOW_BYTES, f"(while Health is below {self.health_threshold}%)"), f"(while Health is below {self.health_threshold}%)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xAB, 0x5D, 0x1, 0x0]), f"Vengeance Is Mine")

#endregion Weapon

#region MartialWeapon
@dataclass(eq=False)
class IHaveThePower(MartialWeaponInscription):
    id = ItemUpgrade.IHaveThePower
    energy: int = 5

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.EnergyPlus,
            target="energy",
            fixed_value=5,
            value_getter=property_value(
                EnergyPlus,
                lambda prop: prop.energy,
            ),
        ),
    )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x72, 0x5D, 0x1, 0x0]), f"I Have The Power")
    
@dataclass(eq=False)
class LetTheMemoryLiveAgain(MartialWeaponInscription):
    id = ItemUpgrade.LetTheMemoryLiveAgain
    chance: int = 10

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeGeneral,
            target="chance",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                HalvesSkillRechargeGeneral,
                lambda prop: prop.chance,
            ),
        ),
    )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_RECHARGE_BYTES]), "Halves skill recharge of spells"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x73, 0x5D, 0x1, 0x0]), f"Let The Memory Live Again")
    
#endregion MartialWeapon

#region OffhandOrShield
@dataclass(eq=False)
class CastOutTheUnclean(ReduceConditionDurationInscription):
    id = ItemUpgrade.CastOutTheUnclean
    condition = Reduced_Ailment.Disease

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ReduceConditionDuration,
            target="condition",
            fixed_value=Reduced_Ailment.Disease,
            value_getter=property_value(
                ReduceConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
     )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x83, 0x5D, 0x1, 0x0]), f"Cast Out The Unclean")
    
@dataclass(eq=False)
class FearCutsDeeper(ReduceConditionDurationInscription):
    id = ItemUpgrade.FearCutsDeeper
    condition = Reduced_Ailment.Bleeding
    
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ReduceConditionDuration,
            target="condition",
            fixed_value=Reduced_Ailment.Bleeding,
            value_getter=property_value(
                ReduceConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
     )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x7F, 0x5D, 0x1, 0x0]), f"Fear Cuts Deeper")
    
@dataclass(eq=False)
class ICanSeeClearlyNow(ReduceConditionDurationInscription):
    id = ItemUpgrade.ICanSeeClearlyNow
    condition = Reduced_Ailment.Blind
    
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ReduceConditionDuration,
            target="condition",
            fixed_value=Reduced_Ailment.Blind,
            value_getter=property_value(
                ReduceConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
     )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x80, 0x5D, 0x1, 0x0]), f"I Can See Clearly Now")
    
@dataclass(eq=False)
class LeafOnTheWind(ArmorVsDamageTypeInscription):
    id = ItemUpgrade.LeafOnTheWind
    damage_type = DamageType.Cold
    
    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="damage_type",
            fixed_value=DamageType.Cold,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.damage_type,
            ),
        ),
     )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x75, 0x5D, 0x1, 0x0]), f"Leaf On The Wind")
    
@dataclass(eq=False)
class LikeARollingStone(ArmorVsDamageTypeInscription):
    id = ItemUpgrade.LikeARollingStone
    damage_type = DamageType.Earth

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="damage_type",
            fixed_value=DamageType.Earth,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.damage_type,
            ),
        ),
     )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x76, 0x5D, 0x1, 0x0]), f"Like A Rolling Stone")
    
@dataclass(eq=False)
class LuckOfTheDraw(OffhandOrShieldInscription):
    id = ItemUpgrade.LuckOfTheDraw
    damage_reduction: int = 5
    chance: int = 20

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ReceiveLessDamage,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                ReceiveLessDamage,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ReceiveLessDamage,
            target="damage_reduction",
            fixed_value=5,
            value_getter=property_value(
                ReceiveLessDamage,
                lambda prop: prop.damage_reduction,
            ),
        ),
     )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"Received damage -{self.damage_reduction} (Chance: {self.chance}%)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x7B, 0x5D, 0x1, 0x0]), f"Luck Of The Draw")
    
@dataclass(eq=False)
class MasterOfMyDomain(OffhandOrShieldInscription):
    id = ItemUpgrade.MasterOfMyDomain
    chance: int = 20
    attribute_level: int = 1

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOneItem,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOneItem,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOneItem,
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOneItem,
                lambda prop: prop.attribute_level,
            ),
        ),
     )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.ITEM_ATTRIBUTE_PLUS_ONE_BYTES, self.attribute_level]), "Item's attribute +1"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xA7, 0x5D, 0x1, 0x0]), f"Master Of My Domain")
    
@dataclass(eq=False)
class NotTheFace(ArmorVsDamageTypeInscription):
    id = ItemUpgrade.NotTheFace
    damage_type = DamageType.Blunt

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="damage_type",
            fixed_value=DamageType.Blunt,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.damage_type,
            ),
        ),
     )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x74, 0x5D, 0x1, 0x0]), f"Not The Face")
    
@dataclass(eq=False)
class NothingToFear(OffhandOrShieldInscription):
    id = ItemUpgrade.NothingToFear
    damage_reduction: int = 3

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ReceiveLessPhysDamageHexed,
            target="damage_reduction",
            min_value=1,
            max_value=3,
            value_getter=property_value(
                ReceiveLessPhysDamageHexed,
                lambda prop: prop.damage_reduction,
            ),
        ),
     )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_minus_num(self.get_text_color(), bytes([0x1, 0x81, 0x4F, 0x5D, 0x1, 0x0]), self.damage_reduction, "Received physical damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEXED_BYTES, "(while Hexed)"), "(while Hexed)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x7D, 0x5D, 0x1, 0x0]), f"Nothing To Fear")
    
@dataclass(eq=False)
class OnlyTheStrongSurvive(ReduceConditionDurationInscription):
    id = ItemUpgrade.OnlyTheStrongSurvive
    condition = Reduced_Ailment.Weakness

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ReduceConditionDuration,
            target="condition",
            fixed_value=Reduced_Ailment.Weakness,
            value_getter=property_value(
                ReduceConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
     )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x86, 0x5D, 0x1, 0x0]), f"Only The Strong Survive")
    
@dataclass(eq=False)
class PureOfHeart(ReduceConditionDurationInscription):
    id = ItemUpgrade.PureOfHeart
    condition = Reduced_Ailment.Poison

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ReduceConditionDuration,
            target="condition",
            fixed_value=Reduced_Ailment.Poison,
            value_getter=property_value(
                ReduceConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
     )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x84, 0x5D, 0x1, 0x0]), f"Pure Of Heart")
    
@dataclass(eq=False)
class RidersOnTheStorm(ArmorVsDamageTypeInscription):
    id = ItemUpgrade.RidersOnTheStorm
    damage_type = DamageType.Lightning
    
    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="damage_type",
            fixed_value=DamageType.Lightning,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.damage_type,
             ),
        ),
     )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x77, 0x5D, 0x1, 0x0]), f"Riders On The Storm")
    
@dataclass(eq=False)
class RunForYourLife(OffhandOrShieldInscription):
    id = ItemUpgrade.RunForYourLife
    damage_reduction: int = 2

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ReceiveLessPhysDamageStance,
            target="damage_reduction",
            min_value=1,
            max_value=2,
            value_getter=property_value(
                ReceiveLessPhysDamageStance,
                lambda prop: prop.damage_reduction,
            ),
        ),
     )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_minus_num(self.get_text_color(), bytes([0x1, 0x81, 0x4F, 0x5D, 0x1, 0x0]), self.damage_reduction, "Received physical damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_IN_A_STANCE_BYTES, "(while in a Stance)"), "(while in a Stance)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x7E, 0x5D, 0x1, 0x0]), f"Run For Your Life")  
    
@dataclass(eq=False)
class ShelteredByFaith(OffhandOrShieldInscription):
    id = ItemUpgrade.ShelteredByFaith
    damage_reduction: int = 2

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ReceiveLessPhysDamageEnchanted,
            target="damage_reduction",
            min_value=1,
            max_value=2,
            value_getter=property_value(
                ReceiveLessPhysDamageEnchanted,
                lambda prop: prop.damage_reduction,
            ),
        ),
     )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_minus_num(self.get_text_color(), bytes([0x1, 0x81, 0x4F, 0x5D, 0x1, 0x0]), self.damage_reduction, "Received physical damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_ENCHANTED_BYTES, "(while Enchanted)"), "(while Enchanted)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x7C, 0x5D, 0x1, 0x0]), f"Sheltered By Faith")
    
@dataclass(eq=False)
class SleepNowInTheFire(ArmorVsDamageTypeInscription):
    id = ItemUpgrade.SleepNowInTheFire
    damage_type = DamageType.Fire
    
    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="damage_type",
            fixed_value=DamageType.Fire,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.damage_type,
            ),
        ),
     )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x78, 0x5D, 0x1, 0x0]), f"Sleep Now In The Fire")
    
@dataclass(eq=False)
class SoundnessOfMind(ReduceConditionDurationInscription):
    id = ItemUpgrade.SoundnessOfMind
    condition = Reduced_Ailment.Dazed
    
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ReduceConditionDuration,
            target="condition",
            fixed_value=Reduced_Ailment.Dazed,
            value_getter=property_value(
                ReduceConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
     )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x85, 0x5D, 0x1, 0x0]), f"Soundness Of Mind")
    
@dataclass(eq=False)
class StrengthOfBody(ReduceConditionDurationInscription):
    id = ItemUpgrade.StrengthOfBody
    condition = Reduced_Ailment.Deep_Wound
    
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ReduceConditionDuration,
            target="condition",
            fixed_value=Reduced_Ailment.Deep_Wound,
            value_getter=property_value(
                ReduceConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
     )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x82, 0x5D, 0x1, 0x0]), f"Strength Of Body")
    
@dataclass(eq=False)
class SwiftAsTheWind(ReduceConditionDurationInscription):
    id = ItemUpgrade.SwiftAsTheWind
    condition = Reduced_Ailment.Crippled

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ReduceConditionDuration,
            target="condition",
            fixed_value=Reduced_Ailment.Crippled,
            value_getter=property_value(
                ReduceConditionDuration,
                lambda prop: prop.condition,
            ),
        ),
     )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x81, 0x5D, 0x1, 0x0]), f"Swift As The Wind")

@dataclass(eq=False)
class TheRiddleOfSteel(ArmorVsDamageTypeInscription):
    id = ItemUpgrade.TheRiddleOfSteel
    damage_type = DamageType.Slashing
    
    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="damage_type",
            fixed_value=DamageType.Slashing,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.damage_type,
            ),
        ),
     )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x7A, 0x5D, 0x1, 0x0]), f"The Riddle Of Steel")
    
@dataclass(eq=False)
class ThroughThickAndThin(ArmorVsDamageTypeInscription):
    id = ItemUpgrade.ThroughThickAndThin
    damage_type = DamageType.Piercing
    
    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="damage_type",
            fixed_value=DamageType.Piercing,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.damage_type,
            ),
        ),
     )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0x79, 0x5D, 0x1, 0x0]), f"Through Thick And Thin")

#endregion OffhandOrShield

#region EquippableItem
@dataclass(eq=False)
class MeasureForMeasure(EquippableItemInscription):
    id = ItemUpgrade.MeasureForMeasure
    highly_salvageable: bool = True
    
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.HighlySalvageable,
            target="highly_salvageable",
            fixed_value=True,
            value_getter=property_value(
                HighlySalvageable,
                lambda _: True,
            ),
        ),
     )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes([*self.get_text_color(), *GWEncoded.HIGHLY_SALVAGEABLE_BYTES]), "Highly salvageable")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x81, 0x7C, 0x1, 0x0]), f"Measure For Measure")
        
@dataclass(eq=False)
class ShowMeTheMoney(EquippableItemInscription):
    id = ItemUpgrade.ShowMeTheMoney
    improved_sale_value: bool = True

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.IncreasedSaleValue,
            target="improved_sale_value",
            fixed_value=True,
            value_getter=property_value(
                IncreasedSaleValue,
                lambda _: True,
            ),
        ),
     )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes([*self.get_text_color(), *GWEncoded.IMPROVED_SALE_VALUE_BYTES]), "Improved sale value")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x80, 0x7C, 0x1, 0x0]), f"Show Me The Money")

#endregion EquippableItem

#region SpellcastingWeapon
@dataclass(eq=False)
class AptitudeNotAttitude(SpellcastingWeaponInscription):
    id = ItemUpgrade.AptitudeNotAttitude
    chance: int = 20
    
    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeItemAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeItemAttribute,
                lambda prop: prop.chance,
            ),
        ),
     )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_CASTING_ITEM_ATTRIBUTE_BYTES]), "Halves casting time on spells of item's attribute"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB2, 0x5D, 0x1, 0x0]), f"Aptitude Not Attitude")
    
@dataclass(eq=False)
class DontCallItAComeback(SpellcastingWeaponInscription):
    id = ItemUpgrade.DontCallItAComeback
    energy: int = 7
    health_threshold: int = 50

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.EnergyPlusWhileBelow,
            target="energy",
            min_value=5,
            max_value=7,
            value_getter=property_value(
                EnergyPlusWhileBelow,
                lambda prop: prop.energy,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.EnergyPlusWhileBelow,
            target="health_threshold",
            fixed_value=50,
            value_getter=property_value(
                EnergyPlusWhileBelow,
                lambda prop: prop.health_threshold,
            ),
        ),
     )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEALTH_BELOW_BYTES, f"(while Health is below {self.health_threshold}%)"), f"(while Health is below {self.health_threshold}%)")
        
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB6, 0x5D, 0x1, 0x0]), f"Don't Call It A Comeback")
    
@dataclass(eq=False)
class HaleAndHearty(SpellcastingWeaponInscription):
    id = ItemUpgrade.HaleAndHearty
    energy: int = 5
    health_threshold: int = 50
    
    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.EnergyPlusWhileAbove,
            target="energy",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                EnergyPlusWhileAbove,
                lambda prop: prop.energy,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.EnergyPlusWhileAbove,
            target="health_threshold",
            fixed_value=50,
            value_getter=property_value(
                EnergyPlusWhileAbove,
                lambda prop: prop.health_threshold,
            ),
        ),
     )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEALTH_ABOVE_BYTES, f"(while Health is above {self.health_threshold}%)"), f"(while Health is above {self.health_threshold}%)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB5, 0x5D, 0x1, 0x0]), f"Hale And Hearty")
    
@dataclass(eq=False)
class HaveFaith(SpellcastingWeaponInscription):
    id = ItemUpgrade.HaveFaith
    energy: int = 5

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.EnergyPlusEnchanted,
            target="energy",
            min_value=4,
            max_value=5,
            value_getter=property_value(
                EnergyPlusEnchanted,
                lambda prop: prop.energy,
            ),
        ),
     )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_ENCHANTED_BYTES, "(while Enchanted)"), "(while Enchanted)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB4, 0x5D, 0x1, 0x0]), f"Have Faith")
    
@dataclass(eq=False)
class IAmSorrow(SpellcastingWeaponInscription):
    id = ItemUpgrade.IAmSorrow
    energy: int = 7

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.EnergyPlusHexed,
            target="energy",
            min_value=5,
            max_value=7,
            value_getter=property_value(
                EnergyPlusHexed,
                lambda prop: prop.energy,
            ),
        ),
     )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEXED_BYTES, "(while Hexed)"), "(while Hexed)")

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB7, 0x5D, 0x1, 0x0]), f"I Am Sorrow")
    
@dataclass(eq=False)
class SeizeTheDay(SpellcastingWeaponInscription):
    id = ItemUpgrade.SeizeTheDay
    energy: int = 15
    energy_regeneration: int = -1

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.EnergyPlus,
            target="energy",
            min_value=10,
            max_value=15,
            value_getter=property_value(
                EnergyPlus,
                lambda prop: prop.energy,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.EnergyRegeneration,
            target="energy_regeneration",
            fixed_value=-1,
            value_getter=property_value(
                EnergyRegeneration,
                lambda prop: prop.energy_regeneration,
            ),
        ),
     )

    def create_encoded_description(self) -> GWStringEncoded:
        parts = [
            GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy"),
            GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.ENERGY_REGEN_BYTES, abs(self.energy_regeneration), "Energy regeneration")
        ]
        
        return GWEncoded.combine_encoded_strings(parts, f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color() + GWEncoded.INSCRIPTION_STR1 + bytes([0x1, 0x81, 0xB3, 0x5D, 0x1, 0x0]), f"Seize The Day")

#endregion SpellcastingWeapon

#endregion Inscriptions

#region Inherent (Old School)
@dataclass(eq=False)
class Inherent(Upgrade):
    mod_type = ItemUpgradeType.Inherent
    target_item_type: ItemType = ItemType.EquippableItem

    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(self, "is_inherent", True)
    
    @classmethod
    def has_id(cls, upgrade_id: ItemUpgradeId) -> bool:
        return False
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"Inherent: {_humanize_identifier(self.__class__.__name__)}")

#region Weapon
@dataclass(eq=False)
class DamagePlusWhileAboveUpgrade(Inherent, StrengthAndHonor):
    pass


@dataclass(eq=False)
class DamagePlusPercentEnergyMinusUpgrade(Inherent, BrawnOverBrains):
    pass


@dataclass(eq=False)
class DamagePlusStanceUpgrade(Inherent, DanceWithDeath):
    pass


@dataclass(eq=False)
class DamagePlusHexedUpgrade(Inherent, DontFearTheReaper):
    pass


@dataclass(eq=False)
class HalvesCastingTimeGeneralUpgrade(Inherent, DontThinkTwice):
    pass


@dataclass(eq=False)
class DamagePlusEnchantedUpgrade(Inherent, GuidedByFate):
    pass


@dataclass(eq=False)
class DamagePlusPercentArmorMinusAttackingUpgrade(Inherent, ToThePain):
    pass


@dataclass(eq=False)
class DamagePlusVsHexedUpgrade(Inherent, TooMuchInformation):
    pass


@dataclass(eq=False)
class DamagePlusWhileBelowUpgrade(Inherent, VengeanceIsMine):
    pass

@dataclass(eq=False)
class VampiricStrengthUpgrade(Inherent):
    damage_increase: int = 15
    health_regeneration: int = -1
    target_item_type = ItemType.Weapon
        
    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.DamagePlusPercent,
            target="damage_increase",
            min_value=10,
            max_value=15,
            value_getter=property_value(
                DamagePlusPercent,
                lambda prop: prop.damage_increase,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HealthRegeneneration,
            target="health_regeneration",
            fixed_value=-1,
            value_getter=property_value(
                HealthRegeneneration,
                lambda prop: prop.health_regeneration,
            ),
        ),
     )
    
    def create_encoded_description(self) -> GWStringEncoded:
        parts = [
            GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"),
            GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.HEALTH_REGEN_BYTES, abs(self.health_regeneration), "Health regeneration")
        ]
        
        return GWEncoded.combine_encoded_strings(parts, "no encoded description")
    

@dataclass(eq=False)
class ZealousStrengthUpgrade(Inherent):
    damage_increase: int = 15
    energy_regeneration: int = -1
    target_item_type = ItemType.Weapon
    
    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.DamagePlusPercent,
            target="damage_increase",
            min_value=10,
            max_value=15,
            value_getter=property_value(
                DamagePlusPercent,
                lambda prop: prop.damage_increase,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.EnergyRegeneration,
            target="energy_regeneration",
             fixed_value=-1,
            value_getter=property_value(
                EnergyRegeneration,
                lambda prop: prop.energy_regeneration,
            ),
         ),
     )
    
    def create_encoded_description(self) -> GWStringEncoded:
        parts = [
            GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"),
            GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.ENERGY_REGEN_BYTES, abs(self.energy_regeneration), "Energy regeneration")
        ]
        
        return GWEncoded.combine_encoded_strings(parts, "no encoded description")
    
#endregion Weapon

#region Offhand
@dataclass(eq=False)
class ArmorPlusHexedUpgrade(Inherent, BeJustAndFearNot):
    pass


@dataclass(eq=False)
class ArmorPlusWhileBelowUpgrade(Inherent, DownButNotOut):
    pass


@dataclass(eq=False)
class ArmorPlusEnchantedUpgrade(Inherent, FaithIsMyShield):
    pass


@dataclass(eq=False)
class HalvesSkillRechargeItemAttributeUpgrade(Inherent, ForgetMeNot):
    pass

@dataclass(eq=False)
class ArmorPlusAboveUpgrade(Inherent, HailToTheKing):
    pass


@dataclass(eq=False)
class ArmorPlusEnergyMinusUpgrade(Inherent, IgnoranceIsBliss):
    pass


@dataclass(eq=False)
class ArmorPlusCastingUpgrade(Inherent, KnowingIsHalfTheBattle):
    pass


@dataclass(eq=False)
class ArmorPlusHealthMinusUpgrade(Inherent, LifeIsPain):
    pass


@dataclass(eq=False)
class ArmorPlusVsElementalUpgrade(Inherent, ManForAllSeasons):
    pass


@dataclass(eq=False)
class ArmorPlusAttackingUpgrade(Inherent, MightMakesRight):
    pass


@dataclass(eq=False)
class HalvesSkillRechargeGeneralOffhandUpgrade(Inherent, SerenityNow):
    pass


@dataclass(eq=False)
class ArmorPlusVsPhysicalUpgrade(Inherent, SurvivalOfTheFittest):
    pass
#endregion Offhand

#region MartialWeapon
@dataclass(eq=False)
class EnergyPlusUpgrade(Inherent, IHaveThePower):
    pass


@dataclass(eq=False)
class HalvesSkillRechargeGeneralMartialWeaponUpgrade(Inherent, LetTheMemoryLiveAgain):
    pass
#endregion MartialWeapon

#region OffhandOrShield    

@dataclass(eq=False)
class HealthPlusStanceUpgrade(Inherent, OfEnduranceUpgrade):
    target_item_type = ItemType.OffhandOrShield
    pass

@dataclass(eq=False)
class HealthPlusHexedUpgrade(Inherent, OfValorUpgrade):
    target_item_type = ItemType.OffhandOrShield
    pass

@dataclass(eq=False)
class HealthPlusEnchantedUpgrade(Inherent, OfDevotionUpgrade):
    target_item_type = ItemType.OffhandOrShield
    pass

@dataclass(eq=False)
class AttributePlusOneUpgrade(Inherent):
    chance: int = 20
    attribute: Attribute = Attribute.None_
    attribute_level: int = 1
    target_item_type = ItemType.OffhandOrShield    

    def create_encoded_description(self) -> GWStringEncoded:
        attribute_bytes = GWEncoded._attribute_bytes(self.attribute)
        if attribute_bytes:
            base = GWStringEncoded(bytes([*self.get_text_color(), 0x84, 0xA, 0xA, 0x1, *attribute_bytes, 0x1, 0x0, 0x1, 0x1, 0x1, self.attribute_level]), f"{GWEncoded._attribute_name(self.attribute)} +{self.attribute_level}")
            clause_raw = bytes([0xC1, 0xA, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0])
            
            return GWEncoded._append_line_with_fallback(base, GWEncoded._dull_parenthesized(clause_raw, f"({self.chance}% chance while using skills)"), f"({self.chance}% chance while using skills)")
        return GWStringEncoded(bytes(), f"{GWEncoded._attribute_name(self.attribute)} +1 ({self.chance}% chance while using skills)")


@dataclass(eq=False)
class DivineFavorPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.DivineFavor

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.DivineFavor,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HealingPrayersPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.HealingPrayers

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.HealingPrayers,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class SmitingPrayersPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.SmitingPrayers

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.SmitingPrayers,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class ProtectionPrayersPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.ProtectionPrayers

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.ProtectionPrayers,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class SoulReapingPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.SoulReaping

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.SoulReaping,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class BloodMagicPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.BloodMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.BloodMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class DeathMagicPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.DeathMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.DeathMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class CursesPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.Curses

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.Curses,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class FastCastingPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.FastCasting

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.FastCasting,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class IllusionMagicPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.IllusionMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.IllusionMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class DominationMagicPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.DominationMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.DominationMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class InspirationMagicPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.InspirationMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.InspirationMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class EnergyStoragePlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.EnergyStorage

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.EnergyStorage,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class AirMagicPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.AirMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.AirMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class EarthMagicPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.EarthMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.EarthMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class FireMagicPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.FireMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.FireMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class WaterMagicPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.WaterMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.WaterMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class SpawningPowerPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.SpawningPower

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.SpawningPower,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class CommuningPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.Communing

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.Communing,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class RestorationMagicPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.RestorationMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.RestorationMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class ChannelingMagicPlusOneUpgrade(AttributePlusOneUpgrade):
    attribute = Attribute.ChannelingMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="chance",
            min_value=11,
            max_value=20,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne, 
            target="attribute_level",
            fixed_value=1,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute_level,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.AttributePlusOne,
            target="attribute",
            fixed_value=Attribute.ChannelingMagic,
            value_getter=property_value(
                AttributePlusOne,
                lambda prop: prop.attribute,
            ),
        ),
    )        

@dataclass(eq=False)
class ReduceConditionDurationUpgrade(Inherent, CastOutTheUnclean):
    pass


@dataclass(eq=False)
class BluntArmorPlusVsDamageUpgrade(Inherent, NotTheFace):
    pass


@dataclass(eq=False)
class ColdArmorPlusVsDamageUpgrade(Inherent, LeafOnTheWind):
    pass


@dataclass(eq=False)
class EarthArmorPlusVsDamageUpgrade(Inherent, LikeARollingStone):
    pass


@dataclass(eq=False)
class ReceiveLessDamageUpgrade(Inherent, LuckOfTheDraw):
    pass


@dataclass(eq=False)
class AttributePlusOneItemUpgrade(Inherent, MasterOfMyDomain):
    pass


@dataclass(eq=False)
class ReceiveLessPhysDamageHexedUpgrade(Inherent, NothingToFear):
    pass


@dataclass(eq=False)
class LightningArmorPlusVsDamageUpgrade(Inherent, RidersOnTheStorm):
    pass


@dataclass(eq=False)
class ReceiveLessPhysDamageStanceUpgrade(Inherent, RunForYourLife):
    pass


@dataclass(eq=False)
class ReceiveLessPhysDamageEnchantedUpgrade(Inherent, ShelteredByFaith):
    pass


@dataclass(eq=False)
class FireArmorPlusVsDamageUpgrade(Inherent, SleepNowInTheFire):
    pass


@dataclass(eq=False)
class SlashingArmorPlusVsDamageUpgrade(Inherent, TheRiddleOfSteel):
    pass


@dataclass(eq=False)
class PiercingArmorPlusVsDamageUpgrade(Inherent, ThroughThickAndThin):
    pass

@dataclass(eq=False)
class ArmorVsSpeciesUpgrade(Inherent):
    armor: int = 10
    species: ItemBaneSpecies | None = None
    target_item_type = ItemType.Weapon

    def create_encoded_description(self) -> GWStringEncoded:
        if self.species is None:
            return GWStringEncoded(bytes(), f"Armor +{self.armor} vs. ({_humanize_identifier(self.__class__.__name__)})")
        
        encoed_bytes = bytes([*self.get_text_color(), 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, self.armor, 0x1, *GWEncoded.ITEM_DULL, 0xA8, 0xA, 0xA, 0x1, 0xAF, 0xA, 0xA, 0x1, *GWEncoded.SPECIES.get(self.species, bytes()), 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0])
        return GWStringEncoded(encoed_bytes, f"Armor +{self.armor} vs. ({_humanize_identifier(self.__class__.__name__)})")

@dataclass(eq=False)
class ArmorVsUndeadUpgrade(ArmorVsSpeciesUpgrade):
    species = ItemBaneSpecies.Undead

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Undead,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.armor,
            ),
        ),
    )

@dataclass(eq=False)
class ArmorVsCharrUpgrade(ArmorVsSpeciesUpgrade):
    species = ItemBaneSpecies.Charr

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Charr,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.armor,
            ),
        ),
    )

@dataclass(eq=False)
class ArmorVsTrollsUpgrade(ArmorVsSpeciesUpgrade):
    species = ItemBaneSpecies.Trolls

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Trolls,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.armor,
            ),
        ),
    )

@dataclass(eq=False)
class ArmorVsPlantsUpgrade(ArmorVsSpeciesUpgrade):
    species = ItemBaneSpecies.Plants

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Plants,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.armor,
            ),
        ),
    )

@dataclass(eq=False)
class ArmorVsSkeletonsUpgrade(ArmorVsSpeciesUpgrade):
    species = ItemBaneSpecies.Skeletons

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Skeletons,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.armor,
            ),
        ),
    )

@dataclass(eq=False)
class ArmorVsGiantsUpgrade(ArmorVsSpeciesUpgrade):
    species = ItemBaneSpecies.Giants

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Giants,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.armor,
            ),
        ),
    )

@dataclass(eq=False)
class ArmorVsDwarvesUpgrade(ArmorVsSpeciesUpgrade):
    species = ItemBaneSpecies.Dwarves

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Dwarves,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.armor,
            ),
        ),
    )

@dataclass(eq=False)
class ArmorVsTengusUpgrade(ArmorVsSpeciesUpgrade):
    species = ItemBaneSpecies.Tengus

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Tengus,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.armor,
            ),
        ),
    )

@dataclass(eq=False)
class ArmorVsDemonsUpgrade(ArmorVsSpeciesUpgrade):
    species = ItemBaneSpecies.Demons

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Demons,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.armor,
            ),
        ),
    )

@dataclass(eq=False)
class ArmorVsDragonsUpgrade(ArmorVsSpeciesUpgrade):
    species = ItemBaneSpecies.Dragons

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Dragons,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.armor,
            ),
        ),
    )

@dataclass(eq=False)
class ArmorVsOgresUpgrade(ArmorVsSpeciesUpgrade):
    species = ItemBaneSpecies.Ogres

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="species",
            fixed_value=ItemBaneSpecies.Ogres,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.species,
            ),
        ),
        ranged(
            identifier=ModifierIdentifier.ArmorPlusVsSpecies,
            target="armor",
            min_value=5,
            max_value=10,
            value_getter=property_value(
                ArmorPlusVsSpecies,
                lambda prop: prop.armor,
            ),
        ),
    )
        
#endregion OffhandOrShield

#region EquippableItem
@dataclass(eq=False)
class HealthPlusUpgrade(Inherent):
    health: int = 30
    target_item_type = ItemType.EquippableItem

    upgrade_info = (
        ranged(
            identifier=any_of(ModifierIdentifier.HealthPlus, ModifierIdentifier.HealthPlus2),
            target="health",
            min_value=10,
            max_value=30,
            value_getter=property_value(
                HealthPlus,
                lambda prop: prop.health,
            ),
        ),
     )

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.HEALTH_BYTES, self.health, "Health")

@dataclass(eq=False)
class EnergyUpgrade(Inherent):
    target_item_type = ItemType.EquippableItem
    energy: int = 5
    
    upgrade_info = (
        ranged(
            identifier=any_of(ModifierIdentifier.Energy, ModifierIdentifier.Energy2),
            target="energy",
            min_value=0,
            max_value=12,
            value_getter=property_value(
                EnergyProperty,
                lambda prop: prop.energy,
            ),
        ),
     )
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_num(GWEncoded.ITEM_BASIC, GWEncoded.ENERGY_BYTES, self.energy, "Energy")

    
@dataclass(eq=False)
class HighlySalvageableUpgrade(Inherent, MeasureForMeasure):
    pass


@dataclass(eq=False)
class IncreasedSaleValueUpgrade(Inherent, ShowMeTheMoney):
    pass
#endregion EquippableItem

#region SpellcastingWeapon
@dataclass(eq=False)
class HalvesCastingTimeAttributeUpgrade(Inherent):
    chance: int = 20
    attribute: Attribute | None = None
    target_item_type = ItemType.SpellcastingWeapon

    def create_encoded_description(self) -> GWStringEncoded:
        if self.attribute is None:
            return GWStringEncoded(bytes(), f"Halves casting time of spells of item's attribute (Chance: {self.chance}%)")
        
        attribute_bytes = GWEncoded._attribute_bytes(self.attribute)
        if attribute_bytes:
            base = GWEncoded._encoded(bytes([*self.get_text_color(), 0x81, 0xA, 0xA, 0x1, 0x47, 0xA, 0x1, 0x0, 0xB, 0x1, *attribute_bytes, 0x1, 0x0, 0x1, 0x0]), f"Halves casting time of {GWEncoded._attribute_name(self.attribute)} spells")
            return GWEncoded._append_line_with_fallback(base, GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")
        return GWStringEncoded(bytes(), f"Halves casting time of {GWEncoded._attribute_name(self.attribute)} spells (Chance: {self.chance}%)")

@dataclass(eq=False)
class HalvesCastingTimeOfDivineFavorUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.DivineFavor

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.DivineFavor,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfHealingPrayersUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.HealingPrayers

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.HealingPrayers,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfSmitingPrayersUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.SmitingPrayers

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.SmitingPrayers,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfProtectionPrayersUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.ProtectionPrayers

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.ProtectionPrayers,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfSoulReapingUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.SoulReaping

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.SoulReaping,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfBloodMagicUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.BloodMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.BloodMagic,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfDeathMagicUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.DeathMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.DeathMagic,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfCursesUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.Curses

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.Curses,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfFastCastingUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.FastCasting

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.FastCasting,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfIllusionMagicUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.IllusionMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.IllusionMagic,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfDominationMagicUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.DominationMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.DominationMagic,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfInspirationMagicUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.InspirationMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.InspirationMagic,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfEnergyStorageUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.EnergyStorage

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.EnergyStorage,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfAirMagicUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.AirMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.AirMagic,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfEarthMagicUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.EarthMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.EarthMagic,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfFireMagicUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.FireMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.FireMagic,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfWaterMagicUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.WaterMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.WaterMagic,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfSpawningPowerUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.SpawningPower

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.SpawningPower,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfCommuningUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.Communing

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.Communing,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfRestorationMagicUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.RestorationMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.RestorationMagic,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesCastingTimeOfChannelingMagicUpgrade(HalvesCastingTimeAttributeUpgrade):
    attribute = Attribute.ChannelingMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesCastingTimeAttribute,
            target="attribute",
            fixed_value=Attribute.ChannelingMagic,
            value_getter=property_value(
                HalvesCastingTimeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )
    
    
@dataclass(eq=False)
class HalvesRechargeTimeAttributeUpgrade(Inherent):
    chance: int = 20
    attribute: Attribute | None = None
    target_item_type = ItemType.SpellcastingWeapon

    def create_encoded_description(self) -> GWStringEncoded:
        if self.attribute is None:
            return GWStringEncoded(bytes(), f"Halves skill recharge of spells of item's attribute (Chance: {self.chance}%)")
        
        attribute_bytes = GWEncoded._attribute_bytes(self.attribute)
        if attribute_bytes:
            base = GWEncoded._encoded(bytes([*self.get_text_color(), 0x81, 0xA, 0xA, 0x1, 0x58, 0xA, 0x1, 0x0, 0xB, 0x1, *attribute_bytes, 0x1, 0x0, 0x1, 0x0]), f"Halves skill recharge of {GWEncoded._attribute_name(self.attribute)} spells")
            return GWEncoded._append_line_with_fallback(base, GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")
        return GWEncoded._encoded(bytes(), f"Halves skill recharge of {GWEncoded._attribute_name(self.attribute)} spells (Chance: {self.chance}%)")


@dataclass(eq=False)
class HalvesRechargeTimeOfDivineFavorUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.DivineFavor

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.DivineFavor,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfHealingPrayersUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.HealingPrayers

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.HealingPrayers,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfSmitingPrayersUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.SmitingPrayers

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.SmitingPrayers,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfProtectionPrayersUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.ProtectionPrayers

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.ProtectionPrayers,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfSoulReapingUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.SoulReaping

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.SoulReaping,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfBloodMagicUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.BloodMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.BloodMagic,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfDeathMagicUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.DeathMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.DeathMagic,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfCursesUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.Curses

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.Curses,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfFastCastingUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.FastCasting

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.FastCasting,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfIllusionMagicUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.IllusionMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.IllusionMagic,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfDominationMagicUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.DominationMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.DominationMagic,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfInspirationMagicUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.InspirationMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.InspirationMagic,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfEnergyStorageUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.EnergyStorage

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.EnergyStorage,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfAirMagicUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.AirMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.AirMagic,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfEarthMagicUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.EarthMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.EarthMagic,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfFireMagicUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.FireMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.FireMagic,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfWaterMagicUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.WaterMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.WaterMagic,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfSpawningPowerUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.SpawningPower

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.SpawningPower,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfCommuningUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.Communing

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.Communing,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfRestorationMagicUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.RestorationMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.RestorationMagic,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )

@dataclass(eq=False)
class HalvesRechargeTimeOfChannelingMagicUpgrade(HalvesRechargeTimeAttributeUpgrade):
    attribute = Attribute.ChannelingMagic

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="chance",
            min_value=10,
            max_value=20,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.chance,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.HalvesSkillRechargeAttribute,
            target="attribute",
            fixed_value=Attribute.ChannelingMagic,
            value_getter=property_value(
                HalvesSkillRechargeAttribute,
                lambda prop: prop.attribute,
            ),
        ),
    )
    
    
@dataclass(eq=False)
class HalvesCastingTimeItemAttributeUpgrade(Inherent, AptitudeNotAttitude):
    pass


@dataclass(eq=False)
class EnergyPlusWhileBelowUpgrade(Inherent, DontCallItAComeback):
    pass


@dataclass(eq=False)
class EnergyPlusWhileAboveUpgrade(Inherent, HaleAndHearty):
    pass


@dataclass(eq=False)
class EnergyPlusEnchantedUpgrade(Inherent, HaveFaith):
    pass


@dataclass(eq=False)
class EnergyPlusHexedUpgrade(Inherent, IAmSorrow):
    pass


@dataclass(eq=False)
class EnergyPlusEnergyRegenerationMinusUpgrade(Inherent):
    energy: int = 15
    energy_regeneration: int = -1

    upgrade_info = (
        ranged(
            identifier=ModifierIdentifier.EnergyPlus,
            target="energy",
            min_value=10,
            max_value=15,
            value_getter=property_value(
                EnergyPlus,
                lambda prop: prop.energy,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.EnergyRegeneration,
            target="energy_regeneration",
            fixed_value=-1,
            value_getter=property_value(
                EnergyRegeneration,
                lambda prop: prop.energy_regeneration,
            ),
        ),
     )

    def create_encoded_description(self) -> GWStringEncoded:
        parts = [
            GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy"),
            GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.ENERGY_REGEN_BYTES, abs(self.energy_regeneration), "Energy regeneration")
        ]
        
        return GWEncoded.combine_encoded_strings(parts, f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)")
    

    
#endregion SpellcastingWeapon

#endregion Inherent
#endregion Weapon Upgrades

#region Armor Upgrades
@dataclass(eq=False)
class ArmorUpgrade(Upgrade):
    profession: Profession = Profession._None
    rarity = Rarity.Blue
    pass
    
@dataclass(eq=False)
class Insignia(ArmorUpgrade):
    mod_type = ItemUpgradeType.Prefix

    @classmethod
    def _can_compose(cls, mod: DecodedModifier, all_modifiers: list[DecodedModifier], remaining_modifiers: list[DecodedModifier]) -> bool:
        return mod.identifier == ModifierIdentifier.Upgrade
    
@dataclass(eq=False)
class Rune(ArmorUpgrade):    
    mod_type = ItemUpgradeType.Suffix

    @classmethod
    def _can_compose(cls, mod: DecodedModifier, all_modifiers: list[DecodedModifier], remaining_modifiers: list[DecodedModifier]) -> bool:
        return mod.identifier == ModifierIdentifier.Upgrade

@dataclass(eq=False)
class AttributeRune(Rune):
    attribute: Attribute = Attribute.None_
    attribute_level: int = 0
    upgrade_rune_id : ItemUpgradeId = ItemUpgradeId.Unknown
    applies_to_rune_id : ItemUpgradeId = ItemUpgradeId.Unknown

    @classmethod
    def _can_compose(cls, mod: DecodedModifier, all_modifiers: list[DecodedModifier], remaining_modifiers: list[DecodedModifier]) -> bool:
        if mod.identifier != ModifierIdentifier.AttributeRune:
            return False

        modifier_index = all_modifiers.index(mod)
        if modifier_index <= 0:
            return False

        for previous_mod in reversed(all_modifiers[:modifier_index]):
            if previous_mod.identifier == ModifierIdentifier.TooltipDescription:
                continue

            return previous_mod.upgrade_id in (cls.applies_to_rune_id, cls.upgrade_rune_id)

        return False
    
    @classmethod
    def _pre_compose(cls, upgrade: "Upgrade", mod: DecodedModifier, all_modifiers: list[DecodedModifier], remaining_modifiers: list[DecodedModifier]) -> None:
        attribute_rune = cast("AttributeRune", upgrade)
        attribute_rune.attribute = Attribute(mod.arg1)
        attribute_rune.attribute_level = mod.arg2
                
    def create_encoded_description(self) -> GWStringEncoded:
        attribute = GWEncoded.ATTRIBUTE_NAMES.get(self.attribute, bytes())
        fallback = f"{AttributeNames.get(self.attribute)}: {self.attribute_level}" if attribute else ""

        match self.rarity:
            case Rarity.Gold:
                encoded_description = bytes([ 
                                            *self.get_text_color(), *GWEncoded.PLUS_NUM_TEMPLATE, *attribute, 0x1, 0x0, 0x1, 0x1, self.attribute_level, 0x1, 0x1, 0x0, *GWEncoded.ITEM_DULL, *GWEncoded.NOT_STACKING_BYTES, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 
                                            *self.get_text_color(), *GWEncoded.HEALTH_MINUS_NUM, 75, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1])
            case Rarity.Purple:
                encoded_description = bytes([
                                            *self.get_text_color(), *GWEncoded.PLUS_NUM_TEMPLATE, *attribute, 0x1, 0x0, 0x1, 0x1, self.attribute_level, 0x1, 0x1, 0x0, *GWEncoded.ITEM_DULL, *GWEncoded.NOT_STACKING_BYTES, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 
                                            *self.get_text_color(), *GWEncoded.HEALTH_MINUS_NUM, 35, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1])
            case _:
                encoded_description = bytes([
                                            *self.get_text_color(), *GWEncoded.PLUS_NUM_TEMPLATE, *attribute, 0x1, 0x0, 0x1, 0x1, self.attribute_level, 0x1, 0x1, 0x0, *GWEncoded.ITEM_DULL, *GWEncoded.NOT_STACKING_BYTES, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1])

        return GWStringEncoded(encoded_description, fallback)

@dataclass(eq=False)
class MinorAttributeRune(AttributeRune):
    attribute_level = 1
    rarity = Rarity.Blue
    
@dataclass(eq=False)
class MajorAttributeRune(AttributeRune):
    attribute_level = 2
    rarity = Rarity.Purple
    
    health_reduction: int = 35
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.HealthMinus,
            target="health_reduction",
            fixed_value=35,
            value_getter=property_value(
                HealthMinus,
                lambda prop: prop.health_reduction,
            ),
        ),
     )
    
@dataclass(eq=False)
class SuperiorAttributeRune(AttributeRune):
    attribute_level = 3
    rarity = Rarity.Gold
    
    health_reduction: int = 75
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.HealthMinus,
            target="health_reduction",
            fixed_value=75,
            value_getter=property_value(
                HealthMinus,
                lambda prop: prop.health_reduction,
            ),
        ),
     )
    
@dataclass(eq=False)
class AppliesToRune(Upgrade):
    id = ItemUpgrade.AppliesToRune
    mod_type = ItemUpgradeType.AppliesToRune
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"Indicates the very next property specifies a {_humanize_identifier(self.modifier.upgrade_id.name) if self.modifier else 'rune'}.")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"Applies To Rune ({_humanize_identifier(self.modifier.upgrade_id.name) if self.modifier else 'No upgrade present'})")

@dataclass(eq=False)
class UpgradeRune(Upgrade):
    id = ItemUpgrade.UpgradeRune
    mod_type = ItemUpgradeType.UpgradeRune
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"Indicates the very next property specifies a {_humanize_identifier(self.modifier.upgrade_id.name) if self.modifier else 'rune'}.")
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"{_humanize_identifier(self.modifier.upgrade_id.name) if self.modifier else 'Upgrade Rune'}")

#region No Profession

@dataclass(eq=False)
class SurvivorInsignia(Insignia):
    id = ItemUpgrade.SurvivorInsignia
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE3, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x67, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x68, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x69, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class RadiantInsignia(Insignia):
    id = ItemUpgrade.RadiantInsignia
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE4, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x4F, 0xA, 0x1, 0x0, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x67, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x4F, 0xA, 0x1, 0x0, 0x1, 0x1, 0x2, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x68, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x4F, 0xA, 0x1, 0x0, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x69, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class StalwartInsignia(Insignia):
    id = ItemUpgrade.StalwartInsignia
    armor : int = 10

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsPhysical,
            target="armor",
            fixed_value=10,
            value_getter=property_value(
                ArmorPlusVsPhysical,
                lambda prop: prop.armor,
            ),
        ),
     )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE6, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB0, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class BrawlersInsignia(Insignia):
    id = ItemUpgrade.BrawlersInsignia
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE9, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB4, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class BlessedInsignia(Insignia):
    id = ItemUpgrade.BlessedInsignia
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE7, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9C, 0x4D, 0xA, 0x1, 0xB6, 0x4, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)
    
@dataclass(eq=False)
class HeraldsInsignia(Insignia):
    id = ItemUpgrade.HeraldsInsignia
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE8, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB9, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)
    
@dataclass(eq=False)
class SentrysInsignia(Insignia):
    id = ItemUpgrade.SentrysInsignia
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3D, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE5, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xBA, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)
    
@dataclass(eq=False)
class RuneOfMinorVigor(Rune):
    id = ItemUpgrade.RuneOfMinorVigor
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xB0, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB1, 0x64, 0x1, 0x1, 0x1E, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class RuneOfMinorVigor2(Rune):
    id = ItemUpgrade.RuneOfMinorVigor2
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xB0, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB1, 0x64, 0x1, 0x1, 0x1E, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class RuneOfVitae(Rune):
    id = ItemUpgrade.RuneOfVitae
    rarity = Rarity.Blue

    health : int = 10
    
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.HealthPlus,
            target="health",
            fixed_value=10,
            value_getter=property_value(
                HealthPlus,
                lambda prop: prop.health,
            ),
        ),
    )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xE, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class RuneOfAttunement(Rune):
    id = ItemUpgrade.RuneOfAttunement
    rarity = Rarity.Blue

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xD, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x4F, 0xA, 0x1, 0x0, 0x1, 0x1, 0x2, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class RuneOfMajorVigor(Rune):
    id = ItemUpgrade.RuneOfMajorVigor
    rarity = Rarity.Purple

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xB0, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([*self.get_text_color(), 0x8, 0x1, 0xA, 0x1, 0xB1, 0x64, 0x1, 0x1, 0x29, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)
    
@dataclass(eq=False)
class RuneOfRecovery(Rune):
    id = ItemUpgrade.RuneOfRecovery
    rarity = Rarity.Purple
    
    condition_1: Reduced_Ailment = Reduced_Ailment.Dazed
    condition_2: Reduced_Ailment = Reduced_Ailment.Deep_Wound

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ReduceConditionTupleDuration,
            target="condition_1",
            fixed_value=Reduced_Ailment.Dazed,
            value_getter=property_value(
                ReduceConditionTupleDuration,
                lambda prop: prop.condition_1,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ReduceConditionTupleDuration,
            target="condition_2",
            fixed_value=Reduced_Ailment.Deep_Wound,
            value_getter=property_value(
                ReduceConditionTupleDuration,
                lambda prop: prop.condition_2,
            ),
        ),
     )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([*self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x96, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, *self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x90, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class RuneOfRestoration(Rune):
    id = ItemUpgrade.RuneOfRestoration
    rarity = Rarity.Purple
    
    condition_1: Reduced_Ailment = Reduced_Ailment.Bleeding
    condition_2: Reduced_Ailment = Reduced_Ailment.Crippled

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ReduceConditionTupleDuration,
            target="condition_1",
            fixed_value=Reduced_Ailment.Bleeding,
            value_getter=property_value(
                ReduceConditionTupleDuration,
                lambda prop: prop.condition_1,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ReduceConditionTupleDuration,
            target="condition_2",
            fixed_value=Reduced_Ailment.Crippled,
            value_getter=property_value(
                ReduceConditionTupleDuration,
                lambda prop: prop.condition_2,
            ),
        ),
     )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x10, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([*self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x88, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, *self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x8E, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class RuneOfClarity(Rune):
    id = ItemUpgrade.RuneOfClarity
    rarity = Rarity.Purple

    condition_1: Reduced_Ailment = Reduced_Ailment.Blind
    condition_2: Reduced_Ailment = Reduced_Ailment.Weakness

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ReduceConditionTupleDuration,
            target="condition_1",
            fixed_value=Reduced_Ailment.Blind,
            value_getter=property_value(
                ReduceConditionTupleDuration,
                lambda prop: prop.condition_1,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ReduceConditionTupleDuration,
            target="condition_2",
            fixed_value=Reduced_Ailment.Weakness,
            value_getter=property_value(
                ReduceConditionTupleDuration,
                lambda prop: prop.condition_2,
            ),
        ),
     )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x11, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([*self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x8A, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, *self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x98, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class RuneOfPurity(Rune):
    id = ItemUpgrade.RuneOfPurity
    rarity = Rarity.Purple

    condition_1: Reduced_Ailment = Reduced_Ailment.Disease
    condition_2: Reduced_Ailment = Reduced_Ailment.Poison

    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ReduceConditionTupleDuration,
            target="condition_1",
            fixed_value=Reduced_Ailment.Disease,
            value_getter=property_value(
                ReduceConditionTupleDuration,
                lambda prop: prop.condition_1,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ReduceConditionTupleDuration,
            target="condition_2",
            fixed_value=Reduced_Ailment.Poison,
            value_getter=property_value(
                ReduceConditionTupleDuration,
                lambda prop: prop.condition_2,
            ),
        ),
     )

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x12, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([*self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x92, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, *self.get_text_color(), 0xA7, 0xA, 0xA, 0x1, 0x94, 0x62, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class RuneOfSuperiorVigor(Rune):
    id = ItemUpgrade.RuneOfSuperiorVigor
    rarity = Rarity.Gold

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB5, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xB0, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([*self.get_text_color(), 0x8, 0x1, 0xA, 0x1, 0xB1, 0x64, 0x1, 0x1, 0x32, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)


#endregion No Profession

#region Warrior

@dataclass(eq=False)
class KnightsInsignia(Insignia):
    id = ItemUpgrade.KnightsInsignia
    profession = Profession.Warrior
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x41, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x4, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))
    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x7E, 0xA, 0xA, 0x1, 0x1, 0x81, 0x4F, 0x5D, 0x1, 0x0, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class LieutenantsInsignia(Insignia):
    id = ItemUpgrade.LieutenantsInsignia
    profession = Profession.Warrior
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x41, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEE, 0x5C, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0x97, 0x64, 0x1, 0x1, 0x14, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x7E, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x14, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class StonefistInsignia(Insignia):
    id = ItemUpgrade.StonefistInsignia
    profession = Profession.Warrior
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x41, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF0, 0x5C, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0x99, 0x64, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class DreadnoughtInsignia(Insignia):
    id = ItemUpgrade.DreadnoughtInsignia
    profession = Profession.Warrior
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x41, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x3, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class SentinelsInsignia(Insignia):
    id = ItemUpgrade.SentinelsInsignia
    profession = Profession.Warrior
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x41, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x5, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x14, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xA9, 0xA, 0xA, 0x1, 0x40, 0x9, 0x1, 0x0, 0x1, 0x1, 0xD, 0x1, 0x2, 0x0, 0xAB, 0xA, 0x2, 0x0, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)
    
@dataclass(eq=False)
class MinorWarriorRune(MinorAttributeRune):
    profession = Profession.Warrior
    upgrade_rune_id = ItemUpgradeId.MinorWarriorRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMinorWarriorRune

@dataclass(eq=False)
class MajorWarriorRune(MajorAttributeRune):
    profession = Profession.Warrior
    upgrade_rune_id = ItemUpgradeId.MajorWarriorRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMajorWarriorRune

@dataclass(eq=False)
class SuperiorWarriorRune(SuperiorAttributeRune):
    profession = Profession.Warrior
    upgrade_rune_id = ItemUpgradeId.SuperiorWarriorRune
    applies_to_rune_id = ItemUpgradeId.AppliesToSuperiorWarriorRune

@dataclass(eq=False)
class WarriorRuneOfMinorAbsorption(Rune):
    id = ItemUpgrade.WarriorRuneOfMinorAbsorption
    upgrade_rune_id = ItemUpgradeId.MinorWarriorRune
    profession = Profession.Warrior
    rarity = Rarity.Blue    
    
    # upgrade_info = (
    #     fixed(
    #         identifier=ModifierIdentifier.,
    #         target="armor_vs_elemental",
    #         fixed_value=10,
    #         value_getter=property_value(
    #             ArmorPlusVsElemental,
    #             lambda prop: prop.armor,
    #         ),
    #     ),
    # )
    

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xFA, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        encoded_description = bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xFB, 0x64, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1])
        return GWStringEncoded(self.get_text_color() + encoded_description, f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)")

@dataclass(eq=False)
class WarriorRuneOfMinorTactics(MinorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfMinorTactics
    attribute = Attribute.Tactics

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x48, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfMinorStrength(MinorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfMinorStrength
    attribute = Attribute.Strength

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x40, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfMinorAxeMastery(MinorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfMinorAxeMastery
    attribute = Attribute.AxeMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x42, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfMinorHammerMastery(MinorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfMinorHammerMastery
    attribute = Attribute.HammerMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x44, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfMinorSwordsmanship(MinorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfMinorSwordsmanship
    attribute = Attribute.Swordsmanship

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x46, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfMajorAbsorption(Rune):
    id = ItemUpgrade.WarriorRuneOfMajorAbsorption
    profession = Profession.Warrior
    rarity = Rarity.Purple

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xFA, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([*self.get_text_color(), 0x8, 0x1, 0xA, 0x1, 0xFB, 0x64, 0x1, 0x1, 0x2, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

    
@dataclass(eq=False)
class WarriorRuneOfMajorTactics(MajorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfMajorTactics
    attribute = Attribute.Tactics

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x48, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfMajorStrength(MajorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfMajorStrength
    attribute = Attribute.Strength

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x40, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfMajorAxeMastery(MajorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfMajorAxeMastery
    attribute = Attribute.AxeMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x42, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfMajorHammerMastery(MajorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfMajorHammerMastery
    attribute = Attribute.HammerMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x44, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfMajorSwordsmanship(MajorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfMajorSwordsmanship
    attribute = Attribute.Swordsmanship

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x46, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfSuperiorAbsorption(Rune):
    id = ItemUpgrade.WarriorRuneOfSuperiorAbsorption
    upgrade_rune_id = ItemUpgradeId.SuperiorWarriorRune
    profession = Profession.Warrior
    rarity = Rarity.Gold

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0xFA, 0x64, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([*self.get_text_color(), 0x8, 0x1, 0xA, 0x1, 0xFB, 0x64, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)


@dataclass(eq=False)
class WarriorRuneOfSuperiorTactics(SuperiorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorTactics
    attribute = Attribute.Tactics

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x48, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfSuperiorStrength(SuperiorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorStrength
    attribute = Attribute.Strength

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x40, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfSuperiorAxeMastery(SuperiorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorAxeMastery
    attribute = Attribute.AxeMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x42, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfSuperiorHammerMastery(SuperiorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorHammerMastery
    attribute = Attribute.HammerMastery
    attribute = Attribute.HammerMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x44, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class WarriorRuneOfSuperiorSwordsmanship(SuperiorWarriorRune):
    id = ItemUpgrade.WarriorRuneOfSuperiorSwordsmanship
    attribute = Attribute.Swordsmanship

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBA, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x46, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

#endregion Warrior

#region Ranger

@dataclass(eq=False)
class FrostboundInsignia(Insignia):
    id = ItemUpgrade.FrostboundInsignia
    profession = Profession.Ranger
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x42, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xFE, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE1, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class PyreboundInsignia(Insignia):
    id = ItemUpgrade.PyreboundInsignia
    profession = Profession.Ranger
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x42, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xFD, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE4, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class StormboundInsignia(Insignia):
    id = ItemUpgrade.StormboundInsignia
    profession = Profession.Ranger
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x42, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xFF, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE3, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class ScoutsInsignia(Insignia):
    id = ItemUpgrade.ScoutsInsignia
    profession = Profession.Ranger
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x42, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x1, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xBF, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class EarthboundInsignia(Insignia):
    id = ItemUpgrade.EarthboundInsignia
    profession = Profession.Ranger
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x42, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x0, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE2, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class BeastmastersInsignia(Insignia):
    id = ItemUpgrade.BeastmastersInsignia
    profession = Profession.Ranger
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x42, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x2, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5E, 0x4D, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class MinorRangerRune(MinorAttributeRune):
    profession = Profession.Ranger
    upgrade_rune_id = ItemUpgradeId.MinorRangerRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMinorRangerRune

@dataclass(eq=False)
class MajorRangerRune(MajorAttributeRune):
    profession = Profession.Ranger
    upgrade_rune_id = ItemUpgradeId.MajorRangerRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMajorRangerRune

@dataclass(eq=False)
class SuperiorRangerRune(SuperiorAttributeRune):
    profession = Profession.Ranger
    upgrade_rune_id = ItemUpgradeId.SuperiorRangerRune
    applies_to_rune_id = ItemUpgradeId.AppliesToSuperiorRangerRune

@dataclass(eq=False)
class RangerRuneOfMinorWildernessSurvival(MinorRangerRune):
    id = ItemUpgrade.RangerRuneOfMinorWildernessSurvival
    attribute = Attribute.WildernessSurvival

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x54, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RangerRuneOfMinorExpertise(MinorRangerRune):
    id = ItemUpgrade.RangerRuneOfMinorExpertise
    attribute = Attribute.Expertise

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x52, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RangerRuneOfMinorBeastMastery(MinorRangerRune):
    id = ItemUpgrade.RangerRuneOfMinorBeastMastery
    attribute = Attribute.BeastMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x50, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RangerRuneOfMinorMarksmanship(MinorRangerRune):
    id = ItemUpgrade.RangerRuneOfMinorMarksmanship
    attribute = Attribute.Marksmanship

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x56, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RangerRuneOfMajorWildernessSurvival(MajorRangerRune):
    id = ItemUpgrade.RangerRuneOfMajorWildernessSurvival
    attribute = Attribute.WildernessSurvival

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x54, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RangerRuneOfMajorExpertise(MajorRangerRune):
    id = ItemUpgrade.RangerRuneOfMajorExpertise
    attribute = Attribute.Expertise

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x52, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RangerRuneOfMajorBeastMastery(MajorRangerRune):
    id = ItemUpgrade.RangerRuneOfMajorBeastMastery
    attribute = Attribute.BeastMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x50, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RangerRuneOfMajorMarksmanship(MajorRangerRune):
    id = ItemUpgrade.RangerRuneOfMajorMarksmanship
    attribute = Attribute.Marksmanship

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x56, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RangerRuneOfSuperiorWildernessSurvival(SuperiorRangerRune):
    id = ItemUpgrade.RangerRuneOfSuperiorWildernessSurvival
    attribute = Attribute.WildernessSurvival

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x54, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RangerRuneOfSuperiorExpertise(SuperiorRangerRune):
    id = ItemUpgrade.RangerRuneOfSuperiorExpertise
    attribute = Attribute.Expertise

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x52, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RangerRuneOfSuperiorBeastMastery(SuperiorRangerRune):
    id = ItemUpgrade.RangerRuneOfSuperiorBeastMastery
    attribute = Attribute.BeastMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x50, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RangerRuneOfSuperiorMarksmanship(SuperiorRangerRune):
    id = ItemUpgrade.RangerRuneOfSuperiorMarksmanship
    attribute = Attribute.Marksmanship

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBB, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x56, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

#endregion Ranger

#region Monk

@dataclass(eq=False)
class WanderersInsignia(Insignia):
    id = ItemUpgrade.WanderersInsignia
    profession = Profession.Monk
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x40, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF6, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class DisciplesInsignia(Insignia):
    id = ItemUpgrade.DisciplesInsignia
    profession = Profession.Monk
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x40, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF7, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9C, 0x4D, 0xA, 0x1, 0xAC, 0x4, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class AnchoritesInsignia(Insignia):
    id = ItemUpgrade.AnchoritesInsignia
    profession = Profession.Monk
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x40, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF5, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5F, 0x4D, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5F, 0x4D, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5F, 0x4D, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class MinorMonkRune(MinorAttributeRune):
    profession = Profession.Monk
    upgrade_rune_id = ItemUpgradeId.MinorMonkRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMinorMonkRune

@dataclass(eq=False)
class MajorMonkRune(MajorAttributeRune):
    profession = Profession.Monk
    upgrade_rune_id = ItemUpgradeId.MajorMonkRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMajorMonkRune

@dataclass(eq=False)
class SuperiorMonkRune(SuperiorAttributeRune):
    profession = Profession.Monk
    upgrade_rune_id = ItemUpgradeId.SuperiorMonkRune
    applies_to_rune_id = ItemUpgradeId.AppliesToSuperiorMonkRune


@dataclass(eq=False)
class MonkRuneOfMinorHealingPrayers(MinorMonkRune):
    id = ItemUpgrade.MonkRuneOfMinorHealingPrayers
    attribute = Attribute.HealingPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MonkRuneOfMinorSmitingPrayers(MinorMonkRune):
    id = ItemUpgrade.MonkRuneOfMinorSmitingPrayers
    attribute = Attribute.SmitingPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MonkRuneOfMinorProtectionPrayers(MinorMonkRune):
    id = ItemUpgrade.MonkRuneOfMinorProtectionPrayers
    attribute = Attribute.ProtectionPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MonkRuneOfMinorDivineFavor(MinorMonkRune):
    id = ItemUpgrade.MonkRuneOfMinorDivineFavor
    attribute = Attribute.DivineFavor

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x38, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MonkRuneOfMajorHealingPrayers(MajorMonkRune):
    id = ItemUpgrade.MonkRuneOfMajorHealingPrayers
    attribute = Attribute.HealingPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MonkRuneOfMajorSmitingPrayers(MajorMonkRune):
    id = ItemUpgrade.MonkRuneOfMajorSmitingPrayers
    attribute = Attribute.SmitingPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MonkRuneOfMajorProtectionPrayers(MajorMonkRune):
    id = ItemUpgrade.MonkRuneOfMajorProtectionPrayers
    attribute = Attribute.ProtectionPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MonkRuneOfMajorDivineFavor(MajorMonkRune):
    id = ItemUpgrade.MonkRuneOfMajorDivineFavor
    attribute = Attribute.DivineFavor

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x38, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MonkRuneOfSuperiorHealingPrayers(SuperiorMonkRune):
    id = ItemUpgrade.MonkRuneOfSuperiorHealingPrayers
    attribute = Attribute.HealingPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MonkRuneOfSuperiorSmitingPrayers(SuperiorMonkRune):
    id = ItemUpgrade.MonkRuneOfSuperiorSmitingPrayers
    attribute = Attribute.SmitingPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MonkRuneOfSuperiorProtectionPrayers(SuperiorMonkRune):
    id = ItemUpgrade.MonkRuneOfSuperiorProtectionPrayers
    attribute = Attribute.ProtectionPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x3C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MonkRuneOfSuperiorDivineFavor(SuperiorMonkRune):
    id = ItemUpgrade.MonkRuneOfSuperiorDivineFavor
    attribute = Attribute.DivineFavor

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB9, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x38, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

#endregion Monk

#region Necromancer

@dataclass(eq=False)
class BloodstainedInsignia(Insignia):
    id = ItemUpgrade.BloodstainedInsignia
    profession = Profession.Necromancer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0xB8, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEF, 0x5C, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0x7F, 0x64, 0x1, 0x1, 0x0, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x8, 0x1, 0xA, 0x1, 0xB2, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class TormentorsInsignia(Insignia):
    id = ItemUpgrade.TormentorsInsignia
    profession = Profession.Necromancer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0xB8, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xFA, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x1, 0x81, 0xE1, 0x53, 0xA, 0x1, 0xE7, 0x8, 0x1, 0x0, 0x1, 0x1, 0x6, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x67, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x1, 0x81, 0xE1, 0x53, 0xA, 0x1, 0xE7, 0x8, 0x1, 0x0, 0x1, 0x1, 0x4, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x68, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x1, 0x81, 0xE1, 0x53, 0xA, 0x1, 0xE7, 0x8, 0x1, 0x0, 0x1, 0x1, 0x2, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x69, 0x4C, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)


@dataclass(eq=False)
class BonelaceInsignia(Insignia):
    id = ItemUpgrade.BonelaceInsignia
    profession = Profession.Necromancer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0xB8, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xFC, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xDF, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class MinionMastersInsignia(Insignia):
    id = ItemUpgrade.MinionMastersInsignia
    profession = Profession.Necromancer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0xB8, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF9, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x4E, 0x6D, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x4E, 0x6D, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x4E, 0x6D, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)


@dataclass(eq=False)
class BlightersInsignia(Insignia):
    id = ItemUpgrade.BlightersInsignia
    profession = Profession.Necromancer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0xB8, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xFB, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x14, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9C, 0x4D, 0xA, 0x1, 0xB4, 0x4, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class UndertakersInsignia(Insignia):
    id = ItemUpgrade.UndertakersInsignia
    profession = Profession.Necromancer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0xB8, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF8, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xBB, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0x50, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xBB, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0x3C, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xBB, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0x28, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xBB, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, 0x14, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class MinorNecromancerRune(MinorAttributeRune):
    profession = Profession.Necromancer
    upgrade_rune_id = ItemUpgradeId.MinorNecromancerRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMinorNecromancerRune

@dataclass(eq=False)
class MajorNecromancerRune(MajorAttributeRune):
    profession = Profession.Necromancer
    upgrade_rune_id = ItemUpgradeId.MajorNecromancerRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMajorNecromancerRune

@dataclass(eq=False)
class SuperiorNecromancerRune(SuperiorAttributeRune):
    profession = Profession.Necromancer
    upgrade_rune_id = ItemUpgradeId.SuperiorNecromancerRune
    applies_to_rune_id = ItemUpgradeId.AppliesToSuperiorNecromancerRune
    
@dataclass(eq=False)
class NecromancerRuneOfMinorBloodMagic(MinorNecromancerRune):
    id = ItemUpgrade.NecromancerRuneOfMinorBloodMagic
    attribute = Attribute.BloodMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x26, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class NecromancerRuneOfMinorDeathMagic(MinorNecromancerRune):
    id = ItemUpgrade.NecromancerRuneOfMinorDeathMagic
    attribute = Attribute.DeathMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class NecromancerRuneOfMinorCurses(MinorNecromancerRune):
    id = ItemUpgrade.NecromancerRuneOfMinorCurses
    attribute = Attribute.Curses

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x28, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class NecromancerRuneOfMinorSoulReaping(MinorNecromancerRune):
    id = ItemUpgrade.NecromancerRuneOfMinorSoulReaping
    attribute = Attribute.SoulReaping

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class NecromancerRuneOfMajorBloodMagic(MajorNecromancerRune):
    id = ItemUpgrade.NecromancerRuneOfMajorBloodMagic
    attribute = Attribute.BloodMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x26, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class NecromancerRuneOfMajorDeathMagic(MajorNecromancerRune):
    id = ItemUpgrade.NecromancerRuneOfMajorDeathMagic
    attribute = Attribute.DeathMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class NecromancerRuneOfMajorCurses(MajorNecromancerRune):
    id = ItemUpgrade.NecromancerRuneOfMajorCurses
    attribute = Attribute.Curses

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x28, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class NecromancerRuneOfMajorSoulReaping(MajorNecromancerRune):
    id = ItemUpgrade.NecromancerRuneOfMajorSoulReaping
    attribute = Attribute.SoulReaping

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class NecromancerRuneOfSuperiorBloodMagic(SuperiorNecromancerRune):
    id = ItemUpgrade.NecromancerRuneOfSuperiorBloodMagic
    attribute = Attribute.BloodMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x26, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class NecromancerRuneOfSuperiorDeathMagic(SuperiorNecromancerRune):
    id = ItemUpgrade.NecromancerRuneOfSuperiorDeathMagic
    attribute = Attribute.DeathMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class NecromancerRuneOfSuperiorCurses(SuperiorNecromancerRune):
    id = ItemUpgrade.NecromancerRuneOfSuperiorCurses
    attribute = Attribute.Curses

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x28, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class NecromancerRuneOfSuperiorSoulReaping(SuperiorNecromancerRune):
    id = ItemUpgrade.NecromancerRuneOfSuperiorSoulReaping
    attribute = Attribute.SoulReaping

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB7, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

#endregion Necromancer

#region Mesmer

@dataclass(eq=False)
class VirtuososInsignia(Insignia):
    id = ItemUpgrade.VirtuososInsignia
    profession = Profession.Mesmer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3C, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF4, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xC0, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class ArtificersInsignia(Insignia):
    id = ItemUpgrade.ArtificersInsignia
    profession = Profession.Mesmer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3C, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF3, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0xE2, 0x53, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class ProdigysInsignia(Insignia):
    id = ItemUpgrade.ProdigysInsignia
    profession = Profession.Mesmer
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3C, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF2, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5F, 0x4D, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5F, 0x4D, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x5F, 0x4D, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class MinorMesmerRune(MinorAttributeRune):
    profession = Profession.Mesmer
    upgrade_rune_id = ItemUpgradeId.MinorMesmerRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMinorMesmerRune

@dataclass(eq=False)
class MajorMesmerRune(MajorAttributeRune):
    profession = Profession.Mesmer
    upgrade_rune_id = ItemUpgradeId.MajorMesmerRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMajorMesmerRune

@dataclass(eq=False)
class SuperiorMesmerRune(SuperiorAttributeRune):
    profession = Profession.Mesmer
    upgrade_rune_id = ItemUpgradeId.SuperiorMesmerRune
    applies_to_rune_id = ItemUpgradeId.AppliesToSuperiorMesmerRune

@dataclass(eq=False)
class MesmerRuneOfMinorFastCasting(MinorMesmerRune):
    id = ItemUpgrade.MesmerRuneOfMinorFastCasting
    attribute = Attribute.FastCasting

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MesmerRuneOfMinorDominationMagic(MinorMesmerRune):
    id = ItemUpgrade.MesmerRuneOfMinorDominationMagic
    attribute = Attribute.DominationMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x22, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MesmerRuneOfMinorIllusionMagic(MinorMesmerRune):
    id = ItemUpgrade.MesmerRuneOfMinorIllusionMagic    
    attribute = Attribute.IllusionMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x20, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MesmerRuneOfMinorInspirationMagic(MinorMesmerRune):
    id = ItemUpgrade.MesmerRuneOfMinorInspirationMagic
    attribute = Attribute.InspirationMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x24, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MesmerRuneOfMajorFastCasting(MajorMesmerRune):
    id = ItemUpgrade.MesmerRuneOfMajorFastCasting
    attribute = Attribute.FastCasting

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MesmerRuneOfMajorDominationMagic(MajorMesmerRune):
    id = ItemUpgrade.MesmerRuneOfMajorDominationMagic
    attribute = Attribute.DominationMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x22, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MesmerRuneOfMajorIllusionMagic(MajorMesmerRune):
    id = ItemUpgrade.MesmerRuneOfMajorIllusionMagic
    attribute = Attribute.IllusionMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x20, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MesmerRuneOfMajorInspirationMagic(MajorMesmerRune):
    id = ItemUpgrade.MesmerRuneOfMajorInspirationMagic
    attribute = Attribute.InspirationMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x24, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MesmerRuneOfSuperiorFastCasting(SuperiorMesmerRune):
    id = ItemUpgrade.MesmerRuneOfSuperiorFastCasting
    attribute = Attribute.FastCasting

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MesmerRuneOfSuperiorDominationMagic(SuperiorMesmerRune):
    id = ItemUpgrade.MesmerRuneOfSuperiorDominationMagic
    attribute = Attribute.DominationMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x22, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MesmerRuneOfSuperiorIllusionMagic(SuperiorMesmerRune):
    id = ItemUpgrade.MesmerRuneOfSuperiorIllusionMagic
    attribute = Attribute.IllusionMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x20, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class MesmerRuneOfSuperiorInspirationMagic(SuperiorMesmerRune):
    id = ItemUpgrade.MesmerRuneOfSuperiorInspirationMagic
    attribute = Attribute.InspirationMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB6, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x24, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

#endregion Mesmer

#region Elementalist

@dataclass(eq=False)
class HydromancerInsignia(Insignia):
    id = ItemUpgrade.HydromancerInsignia
    profession = Profession.Elementalist
    
    damage_type : DamageType = DamageType.Cold
    armor_vs_elemental : int = 10
    armor_vs_damage : int = 10
    
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsElemental,
            target="armor_vs_elemental",
            fixed_value=10,
            value_getter=property_value(
                ArmorPlusVsElemental,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="armor_vs_damage",
            fixed_value=10,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="damage_type",
            fixed_value=DamageType.Cold,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.damage_type,
            ),
        )
    )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3F, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF1, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))
    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE1, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class GeomancerInsignia(Insignia):
    id = ItemUpgrade.GeomancerInsignia
    profession = Profession.Elementalist    
    
    damage_type : DamageType = DamageType.Earth
    armor_vs_elemental : int = 10
    armor_vs_damage : int = 10
    
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsElemental,
            target="armor_vs_elemental",
            fixed_value=10,
            value_getter=property_value(
                ArmorPlusVsElemental,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="armor_vs_damage",
            fixed_value=10,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="damage_type",
            fixed_value=DamageType.Earth,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.damage_type,
            ),
        )
    )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3F, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEF, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))
    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE2, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class PyromancerInsignia(Insignia):
    id = ItemUpgrade.PyromancerInsignia
    profession = Profession.Elementalist
    
    damage_type : DamageType = DamageType.Fire
    armor_vs_elemental : int = 10
    armor_vs_damage : int = 10
    
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsElemental,
            target="armor_vs_elemental",
            fixed_value=10,
            value_getter=property_value(
                ArmorPlusVsElemental,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="armor_vs_damage",
            fixed_value=10,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="damage_type",
            fixed_value=DamageType.Fire,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.damage_type,
            ),
        )
    )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3F, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xF0, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))
    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE4, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class AeromancerInsignia(Insignia):
    id = ItemUpgrade.AeromancerInsignia
    profession = Profession.Elementalist
        
    damage_type : DamageType = DamageType.Lightning
    armor_vs_elemental : int = 10
    armor_vs_damage : int = 10
    
    upgrade_info = (
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsElemental,
            target="armor_vs_elemental",
            fixed_value=10,
            value_getter=property_value(
                ArmorPlusVsElemental,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="armor_vs_damage",
            fixed_value=10,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.armor,
            ),
        ),
        fixed(
            identifier=ModifierIdentifier.ArmorPlusVsDamage,
            target="damage_type",
            fixed_value=DamageType.Lightning,
            value_getter=property_value(
                ArmorPlusVsDamage,
                lambda prop: prop.damage_type,
            ),
        )
    )
    
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3F, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEE, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAD, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE3, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class PrismaticInsignia(Insignia):
    id = ItemUpgrade.PrismaticInsignia
    profession = Profession.Elementalist
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3F, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xED, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xA9, 0xA, 0xA, 0x1, 0x2E, 0x9, 0x1, 0x0, 0x1, 0x1, 0x9, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xA9, 0xA, 0xA, 0x1, 0x30, 0x9, 0x1, 0x0, 0x1, 0x1, 0x9, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xA9, 0xA, 0xA, 0x1, 0x34, 0x9, 0x1, 0x0, 0x1, 0x1, 0x9, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xA9, 0xA, 0xA, 0x1, 0x36, 0x9, 0x1, 0x0, 0x1, 0x1, 0x9, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class MinorElementalistRune(MinorAttributeRune):
    profession = Profession.Elementalist
    upgrade_rune_id = ItemUpgradeId.MinorElementalistRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMinorElementalistRune

@dataclass(eq=False)
class MajorElementalistRune(MajorAttributeRune):
    profession = Profession.Elementalist
    upgrade_rune_id = ItemUpgradeId.MajorElementalistRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMajorElementalistRune

@dataclass(eq=False)
class SuperiorElementalistRune(SuperiorAttributeRune):
    profession = Profession.Elementalist
    upgrade_rune_id = ItemUpgradeId.SuperiorElementalistRune
    applies_to_rune_id = ItemUpgradeId.AppliesToSuperiorElementalistRune

@dataclass(eq=False)
class ElementalistRuneOfMinorEnergyStorage(MinorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfMinorEnergyStorage
    attribute = Attribute.EnergyStorage

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x32, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

@dataclass(eq=False)
class ElementalistRuneOfMinorFireMagic(MinorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfMinorFireMagic
    attribute = Attribute.FireMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x34, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ElementalistRuneOfMinorAirMagic(MinorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfMinorAirMagic
    attribute = Attribute.AirMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ElementalistRuneOfMinorEarthMagic(MinorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfMinorEarthMagic
    attribute = Attribute.EarthMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x30, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ElementalistRuneOfMinorWaterMagic(MinorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfMinorWaterMagic
    attribute = Attribute.WaterMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x36, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ElementalistRuneOfMajorEnergyStorage(MajorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfMajorEnergyStorage
    attribute = Attribute.EnergyStorage

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x32, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ElementalistRuneOfMajorFireMagic(MajorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfMajorFireMagic
    attribute = Attribute.FireMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x34, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ElementalistRuneOfMajorAirMagic(MajorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfMajorAirMagic
    attribute = Attribute.AirMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ElementalistRuneOfMajorEarthMagic(MajorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfMajorEarthMagic
    attribute = Attribute.EarthMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x30, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ElementalistRuneOfMajorWaterMagic(MajorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfMajorWaterMagic
    attribute = Attribute.WaterMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x36, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ElementalistRuneOfSuperiorEnergyStorage(SuperiorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorEnergyStorage
    attribute = Attribute.EnergyStorage

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x32, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ElementalistRuneOfSuperiorFireMagic(SuperiorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorFireMagic
    attribute = Attribute.FireMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x34, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ElementalistRuneOfSuperiorAirMagic(SuperiorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorAirMagic
    attribute = Attribute.AirMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x2E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ElementalistRuneOfSuperiorEarthMagic(SuperiorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorEarthMagic
    attribute = Attribute.EarthMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x30, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ElementalistRuneOfSuperiorWaterMagic(SuperiorElementalistRune):
    id = ItemUpgrade.ElementalistRuneOfSuperiorWaterMagic
    attribute = Attribute.WaterMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xB8, 0x22, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x36, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

#endregion Elementalist

#region Assassin

@dataclass(eq=False)
class VanguardsInsignia(Insignia):
    id = ItemUpgrade.VanguardsInsignia
    profession = Profession.Assassin
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3B, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xB, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB0, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xDE, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class InfiltratorsInsignia(Insignia):
    id = ItemUpgrade.InfiltratorsInsignia
    profession = Profession.Assassin
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3B, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x9, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB0, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xDF, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class SaboteursInsignia(Insignia):
    id = ItemUpgrade.SaboteursInsignia
    profession = Profession.Assassin
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3B, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xA, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB0, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xAC, 0xA, 0xA, 0x1, 0xE0, 0x8, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class NightstalkersInsignia(Insignia):
    id = ItemUpgrade.NightstalkersInsignia
    profession = Profession.Assassin
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x3B, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xC, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xB4, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class MinorAssassinRune(MinorAttributeRune):
    profession = Profession.Assassin
    upgrade_rune_id = ItemUpgradeId.MinorAssassinRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMinorAssassinRune

@dataclass(eq=False)
class MajorAssassinRune(MajorAttributeRune):
    profession = Profession.Assassin
    upgrade_rune_id = ItemUpgradeId.MajorAssassinRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMajorAssassinRune

@dataclass(eq=False)
class SuperiorAssassinRune(SuperiorAttributeRune):
    profession = Profession.Assassin
    upgrade_rune_id = ItemUpgradeId.SuperiorAssassinRune
    applies_to_rune_id = ItemUpgradeId.AppliesToSuperiorAssassinRune


@dataclass(eq=False)
class AssassinRuneOfMinorCriticalStrikes(MinorAssassinRune):
    id = ItemUpgrade.AssassinRuneOfMinorCriticalStrikes
    attribute = Attribute.CriticalStrikes

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x58, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class AssassinRuneOfMinorDaggerMastery(MinorAssassinRune):
    id = ItemUpgrade.AssassinRuneOfMinorDaggerMastery
    attribute = Attribute.DaggerMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class AssassinRuneOfMinorDeadlyArts(MinorAssassinRune):
    id = ItemUpgrade.AssassinRuneOfMinorDeadlyArts
    attribute = Attribute.DeadlyArts

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class AssassinRuneOfMinorShadowArts(MinorAssassinRune):
    id = ItemUpgrade.AssassinRuneOfMinorShadowArts
    attribute = Attribute.ShadowArts

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class AssassinRuneOfMajorCriticalStrikes(MajorAssassinRune):
    id = ItemUpgrade.AssassinRuneOfMajorCriticalStrikes
    attribute = Attribute.CriticalStrikes

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x58, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class AssassinRuneOfMajorDaggerMastery(MajorAssassinRune):
    id = ItemUpgrade.AssassinRuneOfMajorDaggerMastery
    attribute = Attribute.DaggerMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class AssassinRuneOfMajorDeadlyArts(MajorAssassinRune):
    id = ItemUpgrade.AssassinRuneOfMajorDeadlyArts
    attribute = Attribute.DeadlyArts

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class AssassinRuneOfMajorShadowArts(MajorAssassinRune):
    id = ItemUpgrade.AssassinRuneOfMajorShadowArts
    attribute = Attribute.ShadowArts

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class AssassinRuneOfSuperiorCriticalStrikes(SuperiorAssassinRune):
    id = ItemUpgrade.AssassinRuneOfSuperiorCriticalStrikes
    attribute = Attribute.CriticalStrikes

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x58, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class AssassinRuneOfSuperiorDaggerMastery(SuperiorAssassinRune):
    id = ItemUpgrade.AssassinRuneOfSuperiorDaggerMastery
    attribute = Attribute.DaggerMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5A, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class AssassinRuneOfSuperiorDeadlyArts(SuperiorAssassinRune):
    id = ItemUpgrade.AssassinRuneOfSuperiorDeadlyArts
    attribute = Attribute.DeadlyArts

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5C, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class AssassinRuneOfSuperiorShadowArts(SuperiorAssassinRune):
    id = ItemUpgrade.AssassinRuneOfSuperiorShadowArts
    attribute = Attribute.ShadowArts

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xBF, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x5E, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

#endregion Assassin

#region Ritualist

@dataclass(eq=False)
class ShamansInsignia(Insignia):
    id = ItemUpgrade.ShamansInsignia
    profession = Profession.Ritualist
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x44, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x6, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x82, 0x7D, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x82, 0x7D, 0x1, 0x1, 0x2, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x82, 0x7D, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class GhostForgeInsignia(Insignia):
    id = ItemUpgrade.GhostForgeInsignia
    profession = Profession.Ritualist
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x44, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x8, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9C, 0x4D, 0xA, 0x1, 0xBA, 0x4, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class MysticsInsignia(Insignia):
    id = ItemUpgrade.MysticsInsignia
    profession = Profession.Ritualist
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x44, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0x7, 0x59, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))
    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xF, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0xC0, 0xA, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class MinorRitualistRune(MinorAttributeRune):
    profession = Profession.Ritualist
    upgrade_rune_id = ItemUpgradeId.MinorRitualistRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMinorRitualistRune

@dataclass(eq=False)
class MajorRitualistRune(MajorAttributeRune):
    profession = Profession.Ritualist
    upgrade_rune_id = ItemUpgradeId.MajorRitualistRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMajorRitualistRune

@dataclass(eq=False)
class SuperiorRitualistRune(SuperiorAttributeRune):
    profession = Profession.Ritualist
    upgrade_rune_id = ItemUpgradeId.SuperiorRitualistRune
    applies_to_rune_id = ItemUpgradeId.AppliesToSuperiorRitualistRune
    
@dataclass(eq=False)
class RitualistRuneOfMinorChannelingMagic(MinorRitualistRune):
    id = ItemUpgrade.RitualistRuneOfMinorChannelingMagic
    attribute = Attribute.ChannelingMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x66, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RitualistRuneOfMinorRestorationMagic(MinorRitualistRune):
    id = ItemUpgrade.RitualistRuneOfMinorRestorationMagic
    attribute = Attribute.RestorationMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x64, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RitualistRuneOfMinorCommuning(MinorRitualistRune):
    id = ItemUpgrade.RitualistRuneOfMinorCommuning
    attribute = Attribute.Communing

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x60, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RitualistRuneOfMinorSpawningPower(MinorRitualistRune):
    id = ItemUpgrade.RitualistRuneOfMinorSpawningPower
    attribute = Attribute.SpawningPower

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x62, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RitualistRuneOfMajorChannelingMagic(MajorRitualistRune):
    id = ItemUpgrade.RitualistRuneOfMajorChannelingMagic
    attribute = Attribute.ChannelingMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x66, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RitualistRuneOfMajorRestorationMagic(MajorRitualistRune):
    id = ItemUpgrade.RitualistRuneOfMajorRestorationMagic
    attribute = Attribute.RestorationMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x64, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RitualistRuneOfMajorCommuning(MajorRitualistRune):
    id = ItemUpgrade.RitualistRuneOfMajorCommuning
    attribute = Attribute.Communing

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x60, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RitualistRuneOfMajorSpawningPower(MajorRitualistRune):
    id = ItemUpgrade.RitualistRuneOfMajorSpawningPower
    attribute = Attribute.SpawningPower

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x62, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RitualistRuneOfSuperiorChannelingMagic(SuperiorRitualistRune):
    id = ItemUpgrade.RitualistRuneOfSuperiorChannelingMagic
    attribute = Attribute.ChannelingMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x66, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RitualistRuneOfSuperiorRestorationMagic(SuperiorRitualistRune):
    id = ItemUpgrade.RitualistRuneOfSuperiorRestorationMagic
    attribute = Attribute.RestorationMagic

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x64, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RitualistRuneOfSuperiorCommuning(SuperiorRitualistRune):
    id = ItemUpgrade.RitualistRuneOfSuperiorCommuning
    attribute = Attribute.Communing

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x60, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class RitualistRuneOfSuperiorSpawningPower(SuperiorRitualistRune):
    id = ItemUpgrade.RitualistRuneOfSuperiorSpawningPower
    attribute = Attribute.SpawningPower

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0xC0, 0x55, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x62, 0x9, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

#endregion Ritualist

#region Dervish

@dataclass(eq=False)
class WindwalkerInsignia(Insignia):
    id = ItemUpgrade.WindwalkerInsignia
    profession = Profession.Dervish
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x43, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEC, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9E, 0x4D, 0xA, 0x1, 0xB6, 0x4, 0x1, 0x0, 0x1, 0x1, 0x1, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9E, 0x4D, 0xA, 0x1, 0xB6, 0x4, 0x1, 0x0, 0x1, 0x1, 0x2, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9E, 0x4D, 0xA, 0x1, 0xB6, 0x4, 0x1, 0x0, 0x1, 0x1, 0x3, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1, 0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9E, 0x4D, 0xA, 0x1, 0xB6, 0x4, 0x1, 0x0, 0x1, 0x1, 0x4, 0x1, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class ForsakenInsignia(Insignia):
    id = ItemUpgrade.ForsakenInsignia
    profession = Profession.Dervish
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x43, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEB, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))
    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x9D, 0x4D, 0xA, 0x1, 0xB6, 0x4, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class MinorDervishRune(MinorAttributeRune):
    profession = Profession.Dervish
    upgrade_rune_id = ItemUpgradeId.MinorDervishRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMinorDervishRune

@dataclass(eq=False)
class MajorDervishRune(MajorAttributeRune):
    profession = Profession.Dervish
    upgrade_rune_id = ItemUpgradeId.MajorDervishRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMajorDervishRune

@dataclass(eq=False)
class SuperiorDervishRune(SuperiorAttributeRune):
    profession = Profession.Dervish
    upgrade_rune_id = ItemUpgradeId.SuperiorDervishRune
    applies_to_rune_id = ItemUpgradeId.AppliesToSuperiorDervishRune
    
@dataclass(eq=False)
class DervishRuneOfMinorMysticism(MinorDervishRune):
    id = ItemUpgrade.DervishRuneOfMinorMysticism
    attribute = Attribute.Mysticism

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x39, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class DervishRuneOfMinorEarthPrayers(MinorDervishRune):
    id = ItemUpgrade.DervishRuneOfMinorEarthPrayers
    attribute = Attribute.EarthPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x37, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class DervishRuneOfMinorScytheMastery(MinorDervishRune):
    id = ItemUpgrade.DervishRuneOfMinorScytheMastery
    attribute = Attribute.ScytheMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x22, 0x11, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class DervishRuneOfMinorWindPrayers(MinorDervishRune):
    id = ItemUpgrade.DervishRuneOfMinorWindPrayers
    attribute = Attribute.WindPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x35, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class DervishRuneOfMajorMysticism(MajorDervishRune):
    id = ItemUpgrade.DervishRuneOfMajorMysticism
    attribute = Attribute.Mysticism

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x39, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class DervishRuneOfMajorEarthPrayers(MajorDervishRune):
    id = ItemUpgrade.DervishRuneOfMajorEarthPrayers
    attribute = Attribute.EarthPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x37, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class DervishRuneOfMajorScytheMastery(MajorDervishRune):
    id = ItemUpgrade.DervishRuneOfMajorScytheMastery
    attribute = Attribute.ScytheMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x22, 0x11, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class DervishRuneOfMajorWindPrayers(MajorDervishRune):
    id = ItemUpgrade.DervishRuneOfMajorWindPrayers
    attribute = Attribute.WindPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x35, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class DervishRuneOfSuperiorMysticism(SuperiorDervishRune):
    id = ItemUpgrade.DervishRuneOfSuperiorMysticism
    attribute = Attribute.Mysticism

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x39, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class DervishRuneOfSuperiorEarthPrayers(SuperiorDervishRune):
    id = ItemUpgrade.DervishRuneOfSuperiorEarthPrayers
    attribute = Attribute.EarthPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x37, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class DervishRuneOfSuperiorScytheMastery(SuperiorDervishRune):
    id = ItemUpgrade.DervishRuneOfSuperiorScytheMastery
    attribute = Attribute.ScytheMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x22, 0x11, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class DervishRuneOfSuperiorWindPrayers(SuperiorDervishRune):
    id = ItemUpgrade.DervishRuneOfSuperiorWindPrayers
    attribute = Attribute.WindPrayers

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x71, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x35, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

#endregion Dervish

#region Paragon

@dataclass(eq=False)
class CenturionsInsignia(Insignia):
    id = ItemUpgrade.CenturionsInsignia
    profession = Profession.Paragon
    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x30, 0xA, 0xA, 0x1, 0x1, 0x81, 0x45, 0x59, 0x1, 0x0, 0xB, 0x1, 0x1, 0x81, 0xEA, 0x58, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))

    
    def create_encoded_description(self) -> GWStringEncoded:
        fallback = f"{_humanize_identifier(self.__class__.__name__)} (no encoded description)"
        return GWStringEncoded(bytes([0x2, 0x0, 0x3C, 0xA, 0xA, 0x1, 0x84, 0xA, 0xA, 0x1, 0x44, 0xA, 0x1, 0x0, 0x1, 0x1, 0xA, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x1, 0x81, 0x60, 0x4D, 0x1, 0x0, 0x1, 0x0, 0x2, 0x0, 0x2, 0x1]), fallback)

@dataclass(eq=False)
class MinorParagonRune(MinorAttributeRune):
    profession = Profession.Paragon
    upgrade_rune_id = ItemUpgradeId.MinorParagonRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMinorParagonRune

@dataclass(eq=False)
class MajorParagonRune(MajorAttributeRune):
    profession = Profession.Paragon
    upgrade_rune_id = ItemUpgradeId.MajorParagonRune
    applies_to_rune_id = ItemUpgradeId.AppliesToMajorParagonRune

@dataclass(eq=False)
class SuperiorParagonRune(SuperiorAttributeRune):
    profession = Profession.Paragon
    upgrade_rune_id = ItemUpgradeId.SuperiorParagonRune
    applies_to_rune_id = ItemUpgradeId.AppliesToSuperiorParagonRune
    
@dataclass(eq=False)
class ParagonRuneOfMinorLeadership(MinorParagonRune):
    id = ItemUpgrade.ParagonRuneOfMinorLeadership
    attribute = Attribute.Leadership

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x33, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ParagonRuneOfMinorMotivation(MinorParagonRune):
    id = ItemUpgrade.ParagonRuneOfMinorMotivation
    attribute = Attribute.Motivation

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x1A, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ParagonRuneOfMinorCommand(MinorParagonRune):
    id = ItemUpgrade.ParagonRuneOfMinorCommand
    attribute = Attribute.Command

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0xD5, 0x6, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ParagonRuneOfMinorSpearMastery(MinorParagonRune):
    id = ItemUpgrade.ParagonRuneOfMinorSpearMastery
    attribute = Attribute.SpearMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x20, 0x11, 0x1, 0x0, 0xB, 0x1, 0x5A, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ParagonRuneOfMajorLeadership(MajorParagonRune):
    id = ItemUpgrade.ParagonRuneOfMajorLeadership
    attribute = Attribute.Leadership

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x33, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ParagonRuneOfMajorMotivation(MajorParagonRune):
    id = ItemUpgrade.ParagonRuneOfMajorMotivation
    attribute = Attribute.Motivation

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x1A, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ParagonRuneOfMajorCommand(MajorParagonRune):
    id = ItemUpgrade.ParagonRuneOfMajorCommand
    attribute = Attribute.Command

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0xD5, 0x6, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ParagonRuneOfMajorSpearMastery(MajorParagonRune):
    id = ItemUpgrade.ParagonRuneOfMajorSpearMastery
    attribute = Attribute.SpearMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x20, 0x11, 0x1, 0x0, 0xB, 0x1, 0x5B, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ParagonRuneOfSuperiorLeadership(SuperiorParagonRune):
    id = ItemUpgrade.ParagonRuneOfSuperiorLeadership
    attribute = Attribute.Leadership

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x33, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ParagonRuneOfSuperiorMotivation(SuperiorParagonRune):
    id = ItemUpgrade.ParagonRuneOfSuperiorMotivation
    attribute = Attribute.Motivation

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x1A, 0x12, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ParagonRuneOfSuperiorCommand(SuperiorParagonRune):
    id = ItemUpgrade.ParagonRuneOfSuperiorCommand
    attribute = Attribute.Command

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0xD5, 0x6, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))


@dataclass(eq=False)
class ParagonRuneOfSuperiorSpearMastery(SuperiorParagonRune):
    id = ItemUpgrade.ParagonRuneOfSuperiorSpearMastery
    attribute = Attribute.SpearMastery

    def create_encoded_name(self) -> GWStringEncoded:
        return GWStringEncoded(self.get_text_color(True) + bytes([0x33, 0xA, 0xA, 0x1, 0x1, 0x81, 0x72, 0x1C, 0x1, 0x0, 0xB, 0x1, 0x8, 0x1, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x1, 0x81, 0x20, 0x11, 0x1, 0x0, 0xB, 0x1, 0x5C, 0xA, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0]), _humanize_identifier(self.__class__.__name__))
    
#endregion Paragon

#endregion Armor Upgrades

def _get_concrete_upgrade_types(
    base_type: type[Upgrade],
    excluded_types: tuple[type[Upgrade], ...] = (),
    class_filter: Callable[[type[Upgrade]], bool] | None = None,
) -> list[type[Upgrade]]:
    classes = tuple(
        cls
        for cls in globals().values()
        if isinstance(cls, type)
        and issubclass(cls, base_type)
        and cls not in (Upgrade, Inherent, *excluded_types)
        and cls.__module__ == __name__
        and (class_filter is None or class_filter(cls))
    )
    base_classes = set(classes)

    return [
        cls
        for cls in classes
        if not any(
            subclass is not cls
            and subclass in base_classes
            and issubclass(subclass, cls)
            for subclass in classes
        )
    ]


_UPGRADES: list[type[Upgrade]] = [
    cls
    for cls in _get_concrete_upgrade_types(
        Upgrade,
        excluded_types=(
            Inherent,
            Inscription,
            OffhandInscription,
            WeaponInscription,
            MartialWeaponInscription,
            OffhandOrShieldInscription,
            ReduceConditionDurationInscription,
            ArmorVsDamageTypeInscription,
            EquippableItemInscription,
            SpellcastingWeaponInscription,
        ),
        class_filter=lambda cls: not issubclass(cls, Inherent),
    )
]

_INHERENT_UPGRADES: list[type[Upgrade]] = _get_concrete_upgrade_types(
    Inherent,
    excluded_types=(
        ArmorVsSpeciesUpgrade,
        AttributePlusOneUpgrade,
        HalvesCastingTimeAttributeUpgrade,
        HalvesRechargeTimeAttributeUpgrade,
    ),
)
