from typing import TYPE_CHECKING
from dataclasses import dataclass, field
from Py4GWCoreLib.enums_src.GameData_enums import Ailment, Attribute, AttributeNames, DamageType, Profession, Reduced_Ailment
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Sources.frenkeyLib.ItemHandling.Mods.decoded_modifier import DecodedModifier
from Sources.frenkeyLib.ItemHandling.Mods.types import ItemBaneSpecies, ItemUpgradeId
from Sources.frenkeyLib.ItemHandling.encoded_strings import GWStringEncoded, GWEncoded

PERSISTENT = True

if TYPE_CHECKING:
    from Sources.frenkeyLib.ItemHandling.Mods.upgrades import Upgrade

@dataclass
class ItemProperty:
    modifier: DecodedModifier
    rarity: Rarity
    
    def __post_init__(self):
        self.__encoded_description = self.create_encoded_description()
        
    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"No description available... ({self.__class__.__name__})")
    
    def get_text_color(self) -> bytes:
        match self.rarity:
            case Rarity.Blue | Rarity.White:
                return GWEncoded.ITEM_BONUS
            
            case Rarity.Purple:
                return GWEncoded.ITEM_UNCOMMON
            
            case Rarity.Gold:
                return GWEncoded.ITEM_RARE
            
            case Rarity.Green:
                return GWEncoded.ITEM_UNIQUE
    
    def is_valid(self) -> bool:
        return True

    @property
    def encoded_description(self) -> GWStringEncoded:
        return self.__encoded_description
        
    @property
    def description(self) -> str:
        return self.__encoded_description.full
    
    @property
    def plain_description(self) -> str:        
        return self.__encoded_description.plain
    
@dataclass
class ArmorProperty(ItemProperty):
    armor: int
    
    def create_encoded_description(self) -> GWStringEncoded:
        encoded_bytes = bytes([*GWEncoded.ITEM_BASIC, 0x86, 0xA, 0xA, 0x1, *GWEncoded.ARMOR_BYTES, 0x1, 0x1, self.armor, 0x1, 0x1, 0x0])
        return GWStringEncoded(encoded_bytes, f"Armor: {self.armor}")
    
@dataclass
class ArmorEnergyRegen(ItemProperty):
    energy_regen: int

    def create_encoded_description(self) -> GWStringEncoded:
        encoded_bytes = bytes([*self.get_text_color(), *GWEncoded.PLUS_NUM_TEMPLATE, *GWEncoded.ENERGY_RECOVERY_BYTES, 0x1, 0x1, self.energy_regen, 0x1, 0x1, 0x0])
        return GWStringEncoded(encoded_bytes, f"Energy recovery: +{self.energy_regen}")

@dataclass
class ArmorMinusAttacking(ItemProperty):
    armor: int
    
    def create_encoded_description(self) -> GWStringEncoded:
        encoded_bytes = bytes([*self.get_text_color(), *GWEncoded.MINUS_NUM_TEMPLATE, *GWEncoded.ARMOR_BYTES, 0x1, 0x1, self.armor, 0x1, 0x1, 0x0, *GWEncoded.WHILE_ATTACKING_BYTES])
        return GWStringEncoded(encoded_bytes, f"Armor: -{self.armor} (while attacking)")
    
@dataclass
class ArmorPenetration(ItemProperty):
    armor_pen: int
    chance: int

    def create_encoded_description(self) -> GWStringEncoded:
        encoded = bytes([
            *self.get_text_color(),
            *GWEncoded.PLUS_PERCENT_TEMPLATE, 0x45, 0xA, 0x1, 0x0, 0x1, 0x1, self.armor_pen, 0x1, 0x1, 0x0,
            *GWEncoded.ITEM_DULL,
            *GWEncoded.PARENTHESIS_STR1,
            *GWEncoded.CHANCE_TEMPLATE, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0,
            0x1, 0x0
        ])
        return GWStringEncoded(encoded, f"Armor penetration +{self.armor_pen}% (Chance: {self.chance}%)")
    
@dataclass
class ArmorPlus(ItemProperty):
    armor: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor")

@dataclass
class ArmorPlusAttacking(ItemProperty):
    armor: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(bytes([0xB4, 0xA, 0x1, 0x0]), "(while attacking)"))

@dataclass
class ArmorPlusCasting(ItemProperty):
    armor: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_CASTING_BYTES, "(while casting)"))

@dataclass
class ArmorPlusEnchanted(ItemProperty):
    armor: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_ENCHANTED_BYTES, "(while Enchanted)"))

@dataclass
class ArmorPlusHexed(ItemProperty):
    armor: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEXED_BYTES, "(while Hexed)"))

@dataclass
class ArmorPlusAbove(ItemProperty):
    armor: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEXED_BYTES, "(while Hexed)"), "(while Hexed)")

@dataclass
class ArmorPlusVsDamage(ItemProperty):
    armor: int
    damage_type: DamageType

    def create_encoded_description(self) -> GWStringEncoded:
        base = GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor")
        clause_bytes = GWEncoded.VS_DAMAGE_BYTES.get(self.damage_type)
        if clause_bytes:
            return GWEncoded._append_line_with_fallback(base, GWEncoded._dull_parenthesized(clause_bytes, f"(vs. {self.damage_type.name} damage)"), f"(vs. {self.damage_type.name} damage)")
        return GWStringEncoded(base.encoded, f"{base.fallback} (vs. {self.damage_type.name} damage)")

@dataclass
class ArmorPlusVsElemental(ItemProperty):
    armor: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.VS_ELEMENTAL_DAMAGE_BYTES, "(vs. elemental damage)"), "(vs. elemental damage)")

@dataclass
class ArmorPlusVsPhysical(ItemProperty):
    armor: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(GWEncoded.VS_PHYSICAL_DAMAGE_BYTES, "(vs. physical damage)"), "(vs. physical damage)")

@dataclass
class ArmorPlusVsSpecies(ItemProperty):
    armor: int
    species: ItemBaneSpecies

    def create_encoded_description(self) -> GWStringEncoded:
        species = self.species.name if self.species != ItemBaneSpecies.Unknown else f"ID {self.modifier.arg1}"
        return GWStringEncoded(bytes(), f"Armor +{self.armor}\n(vs. {species})")

@dataclass
class ArmorPlusWhileDown(ItemProperty):
    armor: int
    health_threshold: int

    def create_encoded_description(self) -> GWStringEncoded:
        clause_raw = bytes([0xBB, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, self.health_threshold, 0x1, 0x1, 0x0, 0x1, 0x0])
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ARMOR_BYTES, self.armor, "Armor"), GWEncoded._dull_parenthesized(clause_raw, f"(while Health is below {self.health_threshold}%)"), f"(while Health is below {self.health_threshold}%)")

@dataclass
class AttributePlusOne(ItemProperty):
    attribute: Attribute
    chance: int
    attribute_level: int = 1

    def create_encoded_description(self) -> GWStringEncoded:
        attribute_bytes = GWEncoded._attribute_bytes(self.attribute)
        if attribute_bytes:
            base = GWStringEncoded(bytes([*self.get_text_color(), 0x84, 0xA, 0xA, 0x1, 0x64, 0x9, 0x1, 0x0, 0x1, 0x1, 0x1, self.attribute_level]), f"{GWEncoded._attribute_name(self.attribute)} +{self.attribute_level}")
            clause_raw = bytes([0xC1, 0xA, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0])
            
            return GWEncoded._append_line_with_fallback(base, GWEncoded._dull_parenthesized(clause_raw, f"({self.chance}% chance while using skills)"), f"({self.chance}% chance while using skills)")
        return GWStringEncoded(bytes(), f"{GWEncoded._attribute_name(self.attribute)} +1 ({self.chance}% chance while using skills)")

@dataclass
class AttributePlusOneItem(ItemProperty):
    chance: int
    attribute_level: int = 1

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.ITEM_ATTRIBUTE_PLUS_ONE_BYTES, self.attribute_level]), "Item's attribute +1"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

@dataclass
class DamageCustomized(ItemProperty):
    damage_increase: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_percent(GWEncoded.ITEM_BASIC, GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage")

@dataclass
class DamagePlusEnchanted(ItemProperty):
    damage_increase: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_ENCHANTED_BYTES, "(while Enchanted)"), "(while Enchanted)")

@dataclass
class DamagePlusHexed(ItemProperty):
    damage_increase: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEXED_BYTES, "(while Hexed)"), "(while Hexed)")

@dataclass
class DamagePlusPercent(ItemProperty):
    damage_increase: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage")

@dataclass
class DamagePlusStance(ItemProperty):
    damage_increase: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_IN_A_STANCE_BYTES, "(while in a Stance)"), "(while in a Stance)")

@dataclass
class DamagePlusVsHexed(ItemProperty):
    damage_increase: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"), GWEncoded._dull_parenthesized(GWEncoded.VS_HEXED_FOES_BYTES, "(vs. Hexed foes)"), "(vs. Hexed foes)")

@dataclass
class DamagePlusVsSpecies(ItemProperty):
    damage_increase: int
    species: ItemBaneSpecies

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), bytes([*GWEncoded.DAMAGE_TEXT, 0x1, 0x0]), self.damage_increase, f"Damage +{self.damage_increase}%"), GWEncoded._dull_parenthesized(bytes([*GWEncoded.VS_STR1, *GWEncoded.SLAYING_BANE.get(self.species, bytes())]), f"(vs. {self.species.name})"), f"(vs. {self.species.name})")

@dataclass
class DamagePlusWhileDown(ItemProperty):
    damage_increase: int
    health_threshold: int

    def create_encoded_description(self) -> GWStringEncoded:
        clause_raw = bytes([0xBB, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, self.health_threshold, 0x1, 0x1, 0x0, 0x1, 0x0])
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"), GWEncoded._dull_parenthesized(clause_raw, f"(while Health is below {self.health_threshold}%)"), f"(while Health is below {self.health_threshold}%)")

@dataclass
class DamagePlusWhileUp(ItemProperty):
    damage_increase: int
    health_threshold: int

    def create_encoded_description(self) -> GWStringEncoded:
        clause_raw = bytes([0xBC, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, self.health_threshold, 0x1, 0x1, 0x0, 0x1, 0x0])
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_percent(self.get_text_color(), GWEncoded.DAMAGE_BYTES, self.damage_increase, "Damage"), GWEncoded._dull_parenthesized(clause_raw, f"(while Health is above {self.health_threshold}%)"), f"(while Health is above {self.health_threshold}%)")

@dataclass
class DamageTypeProperty(ItemProperty):
    damage_type: DamageType

    def create_encoded_description(self) -> GWStringEncoded:
        damage_bytes = GWEncoded.DAMAGE_TYPE_BYTES.get(self.damage_type)
        if damage_bytes:
            
            # return EncodedString(bytes([*EncodedStrings.ITEM_BASIC, 0xB, 0x1, *damage_bytes, 0x1, 0x0]), f"{self.damage_type.name} Dmg")
            return GWStringEncoded(bytes([*GWEncoded.ITEM_BASIC, 0xA, 0x1, 0x8B, 0xA, 0xA, 0x1, 0x4C, 0xA, 0x1, 0x0, 0xB, 0x1, *damage_bytes, 0x1, 0x0]), f"{self.damage_type.name} Dmg")
        return GWStringEncoded(bytes(), f"{self.damage_type.name} Dmg")

@dataclass
class EnergyProperty(ItemProperty):
    energy: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_num(GWEncoded.ITEM_BASIC, GWEncoded.ENERGY_BYTES, self.energy, "Energy")

@dataclass
class Energy2(ItemProperty):
    energy: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_num(GWEncoded.ITEM_BASIC, GWEncoded.ENERGY_BYTES, self.energy, "Energy")

@dataclass
class EnergyDegen(ItemProperty):
    energy_regen: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.ENERGY_REGEN_BYTES, self.energy_regen, "Energy regeneration")

@dataclass
class EnergyGainOnHit(ItemProperty):
    energy_gain: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_colon_num(self.get_text_color(), GWEncoded.ENERGY_GAIN_ON_HIT_BYTES, self.energy_gain, "Energy gain on hit")

@dataclass
class EnergyMinus(ItemProperty):
    energy: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy")

@dataclass
class EnergyPlus(ItemProperty):
    energy: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy")

@dataclass
class EnergyPlusEnchanted(ItemProperty):
    energy: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_ENCHANTED_BYTES, "(while Enchanted)"), "(while Enchanted)")

@dataclass
class EnergyPlusHexed(ItemProperty):
    energy: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEXED_BYTES, "(while Hexed)"), "(while Hexed)")

@dataclass
class EnergyPlusWhileBelow(ItemProperty):
    energy: int
    health_threshold: int

    def create_encoded_description(self) -> GWStringEncoded:
        clause_raw = bytes([0xBB, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, self.health_threshold, 0x1, 0x1, 0x0, 0x1, 0x0])
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy"), GWEncoded._dull_parenthesized(clause_raw, f"(while Health is below {self.health_threshold}%)"), f"(while Health is below {self.health_threshold}%)")

@dataclass
class Furious(ItemProperty):
    chance: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.DOUBLE_ADRENALINE_BYTES]), "Double Adrenaline on hit"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

@dataclass
class HalvesCastingTimeAttribute(ItemProperty):
    chance: int
    attribute: Attribute

    def create_encoded_description(self) -> GWStringEncoded:
        attribute_bytes = GWEncoded._attribute_bytes(self.attribute)
        if attribute_bytes:
            base = GWEncoded._encoded(bytes([*self.get_text_color(), 0x81, 0xA, 0xA, 0x1, 0x47, 0xA, 0x1, 0x0, 0xB, 0x1, *attribute_bytes, 0x1, 0x0, 0x1, 0x0]), f"Halves casting time of {GWEncoded._attribute_name(self.attribute)} spells")
            return GWEncoded._append_line_with_fallback(base, GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")
        return GWStringEncoded(bytes(), f"Halves casting time of {GWEncoded._attribute_name(self.attribute)} spells (Chance: {self.chance}%)")

@dataclass
class HalvesCastingTimeGeneral(ItemProperty):
    chance: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_CASTING_BYTES]), "Halves casting time of spells"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

@dataclass
class HalvesCastingTimeItemAttribute(ItemProperty):
    chance: int
    attribute : Attribute = field(default=Attribute.None_)

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_CASTING_ITEM_ATTRIBUTE_BYTES]), "Halves casting time on spells of item's attribute"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

@dataclass
class HalvesSkillRechargeAttribute(ItemProperty):
    chance: int
    attribute: Attribute

    def create_encoded_description(self) -> GWStringEncoded:
        attribute_bytes = GWEncoded._attribute_bytes(self.attribute)
        if attribute_bytes:
            base = GWEncoded._encoded(bytes([*self.get_text_color(), 0x81, 0xA, 0xA, 0x1, 0x58, 0xA, 0x1, 0x0, 0xB, 0x1, *attribute_bytes, 0x1, 0x0, 0x1, 0x0]), f"Halves skill recharge of {GWEncoded._attribute_name(self.attribute)} spells")
            return GWEncoded._append_line_with_fallback(base, GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")
        return GWEncoded._encoded(bytes(), f"Halves skill recharge of {GWEncoded._attribute_name(self.attribute)} spells (Chance: {self.chance}%)")

@dataclass
class HalvesSkillRechargeGeneral(ItemProperty):
    chance: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_RECHARGE_BYTES]), "Halves skill recharge of spells"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

@dataclass
class HalvesSkillRechargeItemAttribute(ItemProperty):
    chance: int
    attribute : Attribute = field(default=Attribute.None_)

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.HALVES_RECHARGE_ITEM_ATTRIBUTE_BYTES]), "Halves skill recharge on spells of item's attribute"), GWEncoded._dull_parenthesized(bytes([0x87, 0xA, 0xA, 0x1, 0x48, 0xA, 0x1, 0x0, 0x1, 0x1, self.chance, 0x1, 0x1, 0x0, 0x1, 0x0]), f"(Chance: {self.chance}%)"), f"(Chance: {self.chance}%)")

@dataclass
class HeadpieceAttribute(ItemProperty):
    attribute: Attribute
    attribute_level: int

    def create_encoded_description(self) -> GWStringEncoded:
        attribute_bytes = GWEncoded._attribute_bytes(self.attribute)
        if attribute_bytes:
            ##*ITEM_BONUS, 0x84, 0xA, 0xA, 0x1, *attribute, 0x1, 0x0, 0x1, 0x1, 0x1, attribute_level
            return GWEncoded._encoded(bytes([*self.get_text_color(), 0x84, 0xA, 0xA, 0x1, *attribute_bytes, 0x1, 0x0, 0x1, 0x1, 0x1, self.attribute_level]), f"{self.attribute.name} +{self.attribute_level}")
        return GWEncoded._encoded(bytes(), f"{GWEncoded._attribute_name(self.attribute)} +{self.attribute_level}")

@dataclass
class HeadpieceGenericAttribute(ItemProperty):
    attribute_level: int = 1

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._encoded(bytes([*self.get_text_color(), *GWEncoded.ITEM_ATTRIBUTE_PLUS_ONE_BYTES, self.attribute_level]), "Item's attribute +1")

@dataclass
class HealthDegen(ItemProperty):
    health_regen: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.HEALTH_REGEN_BYTES, self.health_regen, "Health regeneration")

@dataclass
class HealthMinus(ItemProperty):
    health: int

    encoded_string = GWEncoded.HEALTH_MINUS_75

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_minus_num(self.get_text_color(), GWEncoded.HEALTH_BYTES, self.health, "Health")

@dataclass
class HealthPlus(ItemProperty):
    health: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.HEALTH_BYTES, self.health, "Health")

@dataclass
class HealthPlusEnchanted(ItemProperty):
    health: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.HEALTH_BYTES, self.health, "Health"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_ENCHANTED_BYTES, "(while Enchanted)"), "(while Enchanted)")

@dataclass
class HealthPlusHexed(ItemProperty):
    health: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.HEALTH_BYTES, self.health, "Health"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEXED_BYTES, "(while Hexed)"), "(while Hexed)")

@dataclass
class HealthPlusStance(ItemProperty):
    health: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.HEALTH_BYTES, self.health, "Health"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_IN_A_STANCE_BYTES, "(while in a Stance)"), "(while in a Stance)")

@dataclass
class EnergyPlusWhileDown(ItemProperty):
    energy: int
    health_threshold: int

    def create_encoded_description(self) -> GWStringEncoded:
        clause_raw = bytes([0xBB, 0xA, 0xA, 0x1, 0x52, 0xA, 0x1, 0x0, 0x1, 0x1, self.health_threshold, 0x1, 0x1, 0x0, 0x1, 0x0])
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_plus_num(self.get_text_color(), GWEncoded.ENERGY_BYTES, self.energy, "Energy"), GWEncoded._dull_parenthesized(clause_raw, f"(while Health is below {self.health_threshold}%)"), f"(while Health is below {self.health_threshold}%)")

@dataclass
class HealthStealOnHit(ItemProperty):
    health_steal: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._bonus_colon_num(self.get_text_color(), GWEncoded.LIFE_DRAINING_BYTES, self.health_steal, "Life Draining")

@dataclass
class HighlySalvageable(ItemProperty):
    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes([*self.get_text_color(), *GWEncoded.HIGHLY_SALVAGEABLE_BYTES]), "Highly salvageable")

@dataclass
class IncreaseConditionDuration(ItemProperty):
    condition: Ailment

    def create_encoded_description(self) -> GWStringEncoded:
        encoded = GWEncoded.CONDITION_INCREASE_BYTES.get(self.condition)
        fallback = f"Lengthens {self.condition.name.replace('_', ' ')} duration on foes by 33%"
        if encoded:
            return GWStringEncoded(bytes([*self.get_text_color(), *encoded, *GWEncoded._dull_parenthesized(GWEncoded.STACKING_BYTES, "(Stacking)")]), fallback)
        return GWStringEncoded(bytes(), fallback)

@dataclass
class IncreaseEnchantmentDuration(ItemProperty):
    enchantment_duration: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes([*self.get_text_color(), 0xA, 0x1, 0xA2, 0xA, 0x1, 0x1, self.enchantment_duration, 0x1, 0x1, 0x0]), f"Enchantments last {self.enchantment_duration}% longer")

@dataclass
class IncreasedSaleValue(ItemProperty):
    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes([*self.get_text_color(), *GWEncoded.IMPROVED_SALE_VALUE_BYTES]), "Improved sale value")

@dataclass
class Infused(ItemProperty):
    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes([*GWEncoded.ITEM_BASIC, *GWEncoded.INFUSED_BYTES]), "Infused")

@dataclass
class OfTheProfession(ItemProperty):
    attribute: Attribute
    attribute_level: int
    profession: Profession

    def create_encoded_description(self) -> GWStringEncoded:
        encoded_bytes = bytes([*self.get_text_color(), 0x86, 0xA, 0xA, 0x1, *GWEncoded.ATTRIBUTE_NAMES.get(self.attribute, bytes()), 0x1, 0x0, 0x1, 0x1, 0x5, 0x1, 0x1, 0x0, 0x2, 0x0, 0x3E, 0xA, 0xA, 0x1, 0xA8, 0xA, 0xA, 0x1, 0x2, 0x81, 0xA8, 0x38, 0x1, 0x0])
        return GWStringEncoded(encoded_bytes, f"{AttributeNames.get(self.attribute)}: {self.attribute_level} (if your rank is lower. No effect in PvP.)")

@dataclass
class PrefixProperty(ItemProperty):
    upgrade_id: ItemUpgradeId
    upgrade: "Upgrade"

    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"{self.upgrade.name if self.upgrade else f'Unknown (ID {self.upgrade_id})'}\n{self.upgrade.description if self.upgrade else ''}")

@dataclass
class ReceiveLessDamage(ItemProperty):
    damage_reduction: int
    chance: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"Received damage -{self.damage_reduction} (Chance: {self.chance}%)")

@dataclass
class ReceiveLessPhysDamageEnchanted(ItemProperty):
    damage_reduction: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_minus_num(self.get_text_color(), bytes([0x1, 0x81, 0x4F, 0x5D, 0x1, 0x0]), self.damage_reduction, "Received physical damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_ENCHANTED_BYTES, "(while Enchanted)"), "(while Enchanted)")

@dataclass
class ReceiveLessPhysDamageHexed(ItemProperty):
    damage_reduction: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_minus_num(self.get_text_color(), bytes([0x1, 0x81, 0x4F, 0x5D, 0x1, 0x0]), self.damage_reduction, "Received physical damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_HEXED_BYTES, "(while Hexed)"), "(while Hexed)")

@dataclass
class ReceiveLessPhysDamageStance(ItemProperty):
    damage_reduction: int

    def create_encoded_description(self) -> GWStringEncoded:
        return GWEncoded._append_line_with_fallback(GWEncoded._bonus_minus_num(self.get_text_color(), bytes([0x1, 0x81, 0x4F, 0x5D, 0x1, 0x0]), self.damage_reduction, "Received physical damage"), GWEncoded._dull_parenthesized(GWEncoded.WHILE_IN_A_STANCE_BYTES, "(while in a Stance)"), "(while in a Stance)")

@dataclass
class ReduceConditionDuration(ItemProperty):
    condition: Reduced_Ailment

    def create_encoded_description(self) -> GWStringEncoded:
        encoded = GWEncoded.REDUCED_CONDITION_BYTES.get(self.condition)
        fallback = f"Reduces {self.condition.name} duration on you by 20%"
        base = GWStringEncoded(bytes([*self.get_text_color(), *encoded]), fallback) if encoded else GWStringEncoded(bytes(), fallback)
        return GWEncoded._append_line_with_fallback(base, GWEncoded._dull_parenthesized(GWEncoded.STACKING_BYTES, "(Stacking)"), "(Stacking)")

@dataclass
class ReduceConditionTupleDuration(ItemProperty):
    condition_1: Reduced_Ailment
    condition_2: Reduced_Ailment

    def create_encoded_description(self) -> GWStringEncoded:
        encoded_1 = GWEncoded.REDUCED_CONDITION_BYTES.get(self.condition_1, b"")
        encoded_2 = GWEncoded.REDUCED_CONDITION_BYTES.get(self.condition_2, b"")
        fallback_1 = f"Reduces {self.condition_1.name.replace('_', ' ')} duration on you by 20%"
        fallback_2 = f"Reduces {self.condition_2.name.replace('_', ' ')} duration on you by 20%"
        base_1 = bytes([*GWEncoded.ITEM_UNCOMMON, *encoded_1]) if encoded_1 else bytes()
        base_2 = bytes([*GWEncoded.ITEM_UNCOMMON, *encoded_2]) if encoded_2 else bytes()
        suffix = GWEncoded._dull_parenthesized(bytes([0xB2, 0xA, 0x1, 0x0]), "(Non-stacking)")
        encoded = bytes([*base_1, *suffix, *base_2, *suffix])
        fallback = f"{fallback_1} (Non-stacking)\n{fallback_2} (Non-stacking)"
        return GWStringEncoded(encoded, fallback)

@dataclass
class ReducesDiseaseDuration(ItemProperty):
    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes([*self.get_text_color(), *GWEncoded.REDUCES_DISEASE_DURATION_BYTES]), "Reduces disease duration on you by 20%")

@dataclass
class SuffixProperty(ItemProperty):    
    upgrade_id: ItemUpgradeId
    upgrade: "Upgrade"

    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"{self.upgrade.name if self.upgrade else f'Unknown (ID {self.upgrade_id})'}\n{self.upgrade.description if self.upgrade else ''}")

@dataclass
class AttributeRequirement(ItemProperty):
    attribute: Attribute
    attribute_level: int

    def create_encoded_description(self) -> GWStringEncoded:
        attribute_bytes = GWEncoded._attribute_bytes(self.attribute)
        if attribute_bytes:
            encoded = GWEncoded.REQUIRES_TEMPLATE + attribute_bytes + bytes([0x1, 0x0, 0x1, 0x1, self.attribute_level, 0x1, 0x1, 0x0, 0x1, 0x0])
            return GWStringEncoded(bytes([*GWEncoded.ITEM_DULL, *encoded]), f"(Requires {self.attribute_level} {GWEncoded._attribute_name(self.attribute)})")
        return GWStringEncoded(bytes(), f"(Requires {self.attribute_level} {GWEncoded._attribute_name(self.attribute)})")

@dataclass
class BaneProperty(ItemProperty):
    species: ItemBaneSpecies
    
    def create_encoded_description(self) -> GWStringEncoded:
        species = self.species.name if self.species != ItemBaneSpecies.Unknown else f"ID {self.modifier.arg1}"
        return GWStringEncoded(bytes(), f"Bane: {species}")
    
@dataclass
class DamageProperty(ItemProperty):
    min_damage: int
    max_damage: int
    damage_type : DamageType
        
    def create_encoded_description(self) -> GWStringEncoded:
        damage_bytes = GWEncoded.DAMAGE_TYPE_BYTES.get(self.damage_type, bytes())
        encoded_bytes = bytes([*GWEncoded.ITEM_BASIC, 0x89, 0xA, 0xA, 0x1, 0x4E, 0xA, 0x1, 0x0, 0xB, 0x1, *damage_bytes, 0x1, 0x0, 0x1, 0x1, self.min_damage, 0x1, 0x2, 0x1, self.max_damage, 0x1, 0x1, 0x0])
        return GWStringEncoded(encoded_bytes, f"{self.damage_type.name} Dmg: {self.min_damage}-{self.max_damage}")

@dataclass
class UnknownUpgradeProperty(ItemProperty):
    upgrade_id: ItemUpgradeId
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"Unknown Upgrade (ID {self.upgrade_id})")

@dataclass
class InscriptionProperty(ItemProperty):    
    upgrade_id: ItemUpgradeId
    upgrade: "Upgrade"

    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"{self.upgrade.name if self.upgrade else f'Unknown (ID {self.upgrade_id})'}\n{self.upgrade.description if self.upgrade else ''}")
    
@dataclass
class UpgradeRuneProperty(ItemProperty):    
    upgrade_id: ItemUpgradeId
    upgrade: "Upgrade"

    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"RUNE\n{self.upgrade.name if self.upgrade else f'Unknown (ID {self.upgrade_id})'}\n{self.upgrade.description if self.upgrade else ''}\n")
    
@dataclass
class AppliesToRuneProperty(ItemProperty):    
    upgrade_id: ItemUpgradeId
    upgrade: "Upgrade"

    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"{self.upgrade.name if self.upgrade else f'Unknown (ID {self.upgrade_id})'}")

@dataclass
class TooltipProperty(ItemProperty):
    pass

@dataclass
class TargetItemTypeProperty(ItemProperty):
    item_type : ItemType
    
    def create_encoded_description(self) -> GWStringEncoded:
        return GWStringEncoded(bytes(), f"{self.item_type.name}")
#endregion Item Properties
