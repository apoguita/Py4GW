from typing import TYPE_CHECKING
from dataclasses import dataclass
from Py4GWCoreLib.enums_src.GameData_enums import Ailment, Attribute, AttributeNames, DamageType, Profession, Reduced_Ailment
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Sources.frenkeyLib.ItemHandling.Mods.decoded_modifier import DecodedModifier
from Sources.frenkeyLib.ItemHandling.Mods.types import ItemBaneSpecies, ItemUpgradeId

if TYPE_CHECKING:
    from Sources.frenkeyLib.ItemHandling.Mods.upgrades import Upgrade

@dataclass
class ItemProperty:
    modifier: DecodedModifier

    def describe(self) -> str:
        return f"ItemProperty | Modifier {self.modifier.identifier}"
    
    def is_valid(self) -> bool:
        return True
    
@dataclass
class ArmorProperty(ItemProperty):
    armor: int

    def describe(self) -> str:
        return f"Armor: {self.armor}"

@dataclass
class ArmorEnergyRegen(ItemProperty):
    energy_regen: int

    def describe(self) -> str:
        return f"Energy recovery +{self.energy_regen}"

@dataclass
class ArmorMinusAttacking(ItemProperty):
    armor: int
    
    def describe(self) -> str:
        return f"-{self.armor} Armor (while attacking)"

@dataclass
class ArmorPenetration(ItemProperty):
    armor_pen: int
    chance: int

    def describe(self) -> str:
        return f"Armor penetration +{self.armor_pen}% (Chance: {self.chance}%)"

@dataclass
class ArmorPlus(ItemProperty):
    armor: int

    def describe(self) -> str:
        return f"+{self.armor} Armor"

@dataclass
class ArmorPlusAttacking(ItemProperty):
    armor: int

    def describe(self) -> str:
        return f"+{self.armor} Armor (while Attacking)"

@dataclass
class ArmorPlusCasting(ItemProperty):
    armor: int

    def describe(self) -> str:
        return f"+{self.armor} Armor (while Casting)"

@dataclass
class ArmorPlusEnchanted(ItemProperty):
    armor: int

    def describe(self) -> str:
        return f"+{self.armor} Armor (while Enchanted)"

@dataclass
class ArmorPlusHexed(ItemProperty):
    armor: int

    def describe(self) -> str:
        return f"+{self.armor} Armor (while Hexed)"

@dataclass
class ArmorPlusAbove(ItemProperty):
    armor: int

    def describe(self) -> str:
        return f"+{self.armor} Armor (while Hexed)"

@dataclass
class ArmorPlusVsDamage(ItemProperty):
    armor: int
    damage_type: DamageType

    def describe(self) -> str:
        return f"+{self.armor} Armor (vs. {self.damage_type.name} Dmg)"

@dataclass
class ArmorPlusVsElemental(ItemProperty):
    armor: int

    def describe(self) -> str:
        return f"+{self.armor} Armor (vs. Elemental Dmg)"

@dataclass
class ArmorPlusVsPhysical(ItemProperty):
    armor: int

    def describe(self) -> str:
        return f"+{self.armor} Armor (vs. Physical Dmg)"

@dataclass
class ArmorPlusVsSpecies(ItemProperty):
    armor: int
    species: ItemBaneSpecies

    def describe(self) -> str:
        species = self.species.name if self.species != ItemBaneSpecies.Unknown else f"ID {self.modifier.arg1}"
        return f"+{self.armor} Armor (vs. {species})"

@dataclass
class ArmorPlusWhileDown(ItemProperty):
    armor: int
    health_threshold: int

    def describe(self) -> str:
        return f"+{self.armor} Armor (while Health is below {self.health_threshold}%)"

@dataclass
class AttributePlusOne(ItemProperty):
    attribute: Attribute
    chance: int

    def describe(self) -> str:
        return f"{AttributeNames.get(self.attribute)} +1 ({self.chance}% chance while using skills)"

@dataclass
class AttributePlusOneItem(ItemProperty):
    chance: int

    def describe(self) -> str:
        return f"Item's attribute +1 (Chance: {self.chance}%)"

@dataclass
class DamageCustomized(ItemProperty):
    damage_increase: int

    def describe(self) -> str:
        increase = self.damage_increase
        return f"Damage +{increase}%"

@dataclass
class DamagePlusEnchanted(ItemProperty):
    damage_increase: int

    def describe(self) -> str:
        increase = self.damage_increase
        return f"Damage +{increase}% (while Enchanted)"

@dataclass
class DamagePlusHexed(ItemProperty):
    damage_increase: int

    def describe(self) -> str:
        increase = self.damage_increase
        return f"Damage +{increase}% (while Hexed)"

@dataclass
class DamagePlusPercent(ItemProperty):
    damage_increase: int

    def describe(self) -> str:
        increase = self.damage_increase
        return f"Damage +{increase}%"

@dataclass
class DamagePlusStance(ItemProperty):
    damage_increase: int

    def describe(self) -> str:
        increase = self.damage_increase
        return f"Damage +{increase}% (while in a Stance)"

@dataclass
class DamagePlusVsHexed(ItemProperty):
    damage_increase: int

    def describe(self) -> str:
        increase = self.damage_increase
        return f"Damage +{increase}% (vs. Hexed Foes)"

@dataclass
class DamagePlusVsSpecies(ItemProperty):
    damage_increase: int
    species: ItemBaneSpecies

    def describe(self) -> str:
        increase = self.damage_increase
        species = self.species.name if self.species != ItemBaneSpecies.Unknown else f"ID {self.modifier.arg1}"
        return f"Damage +{increase}% (vs. {species.lower()})"

@dataclass
class DamagePlusWhileDown(ItemProperty):
    damage_increase: int
    health_threshold: int

    def describe(self) -> str:
        increase = self.damage_increase
        threshold = self.health_threshold
        
        return f"Damage +{increase}% (while Health is below {threshold}%)"

@dataclass
class DamagePlusWhileUp(ItemProperty):
    damage_increase: int
    health_threshold: int

    def describe(self) -> str:
        increase = self.damage_increase
        threshold = self.health_threshold
        
        return f"Damage +{increase}% (while Health is above +{threshold}%)"

@dataclass
class DamageTypeProperty(ItemProperty):
    damage_type: DamageType

    def describe(self) -> str:
        return f"{self.damage_type.name} Dmg"

@dataclass
class EnergyProperty(ItemProperty):
    energy: int

    def describe(self) -> str:
        return f"Energy +{self.energy}"

@dataclass
class Energy2(ItemProperty):
    energy: int

    def describe(self) -> str:
        return f"Energy +{self.energy}"

@dataclass
class EnergyDegen(ItemProperty):
    energy_regen: int

    def describe(self) -> str:
        return f"Energy regeneration -{self.energy_regen}"

@dataclass
class EnergyGainOnHit(ItemProperty):
    energy_gain: int

    def describe(self) -> str:
        return f"Energy gain on hit: {self.energy_gain}"

@dataclass
class EnergyMinus(ItemProperty):
    energy: int

    def describe(self) -> str:
        return f"-{self.energy} Energy"

@dataclass
class EnergyPlus(ItemProperty):
    energy: int

    def describe(self) -> str:
        return f"+{self.energy} Energy"

@dataclass
class EnergyPlusEnchanted(ItemProperty):
    energy: int

    def describe(self) -> str:
        return f"+{self.energy} Energy (while Enchanted)"

@dataclass
class EnergyPlusHexed(ItemProperty):
    energy: int

    def describe(self) -> str:
        return f"+{self.energy} Energy (while Hexed)"

@dataclass
class EnergyPlusWhileBelow(ItemProperty):
    energy: int
    health_threshold: int

    def describe(self) -> str:
        return f"+{self.energy} Energy (while Health is below {self.health_threshold}%)"

@dataclass
class Furious(ItemProperty):
    chance: int

    def describe(self) -> str:
        return f"Double Adrenaline on hit (Chance: +{self.chance}%)"

@dataclass
class HalvesCastingTimeAttribute(ItemProperty):
    chance: int
    attribute: Attribute

    def describe(self) -> str:
        return f"Halves casting time of {AttributeNames.get(self.attribute)} spells (Chance: {self.chance}%)"

@dataclass
class HalvesCastingTimeGeneral(ItemProperty):
    chance: int

    def describe(self) -> str:
        return f"Halves casting time of spells (Chance: +{self.chance}%)"

@dataclass
class HalvesCastingTimeItemAttribute(ItemProperty):
    chance: int

    def describe(self) -> str:
        return f"Halves casting time on spells of item's attribute (Chance: {self.chance}%)"

@dataclass
class HalvesSkillRechargeAttribute(ItemProperty):
    chance: int
    attribute: Attribute

    def describe(self) -> str:
        return f"Halves skill recharge of {AttributeNames.get(self.attribute)} spells (Chance: {self.chance}%)"

@dataclass
class HalvesSkillRechargeGeneral(ItemProperty):
    chance: int

    def describe(self) -> str:
        return f"Halves skill recharge of spells (Chance: +{self.chance}%)"

@dataclass
class HalvesSkillRechargeItemAttribute(ItemProperty):
    chance: int

    def describe(self) -> str:
        return f"Halves skill recharge on spells of item's attribute (Chance: {self.chance}%)"

@dataclass
class HeadpieceAttribute(ItemProperty):
    attribute: Attribute
    attribute_level: int

    def describe(self) -> str:
        return f"{AttributeNames.get(self.attribute)} +{self.attribute_level}"

@dataclass
class HeadpieceGenericAttribute(ItemProperty):
    def describe(self) -> str:
        return f"Item's attribute +1"

@dataclass
class HealthDegen(ItemProperty):
    health_regen: int

    def describe(self) -> str:
        return f"Health regeneration -{self.health_regen}"

@dataclass
class HealthMinus(ItemProperty):
    health: int

    def describe(self) -> str:
        return f"Health -{self.health}"

@dataclass
class HealthPlus(ItemProperty):
    health: int

    def describe(self) -> str:
        return f"Health +{self.health}"

@dataclass
class HealthPlusEnchanted(ItemProperty):
    health: int

    def describe(self) -> str:
        return f"Health +{self.health} (while Enchanted)"

@dataclass
class HealthPlusHexed(ItemProperty):
    health: int

    def describe(self) -> str:
        return f"Health +{self.health} (while Hexed)"

@dataclass
class HealthPlusStance(ItemProperty):
    health: int

    def describe(self) -> str:
        return f"Health +{self.health} (while in a Stance)"

@dataclass
class EnergyPlusWhileDown(ItemProperty):
    energy: int
    health_threshold: int

    def describe(self) -> str:
        return f"Energy +{self.energy} (while Health is below {self.health_threshold}%)"

@dataclass
class HealthStealOnHit(ItemProperty):
    health_steal: int

    def describe(self) -> str:
        return f"Life Draining: {self.health_steal}"

@dataclass
class HighlySalvageable(ItemProperty):
    def describe(self) -> str:
        return f"Highly salvageable"

@dataclass
class IncreaseConditionDuration(ItemProperty):
    condition: Ailment

    def describe(self) -> str:
        return f"Lengthens {self.condition.name.replace('_', ' ')} duration on foes by 33%"

@dataclass
class IncreaseEnchantmentDuration(ItemProperty):
    enchantment_duration: int

    def describe(self) -> str:
        return f"Enchantments last {self.enchantment_duration}% longer"

@dataclass
class IncreasedSaleValue(ItemProperty):
    def describe(self) -> str:
        return f"Improved sale value"

@dataclass
class Infused(ItemProperty):
    def describe(self) -> str:
        return f"Infused"

@dataclass
class OfTheProfession(ItemProperty):
    attribute: Attribute
    attribute_level: int
    profession: Profession

    def describe(self) -> str:
        return f"{AttributeNames.get(self.attribute)}: {self.attribute_level} (if your rank is lower. No effect in PvP.) | {self.profession.name if self.profession != Profession._None else f'Unknown Profession (ID {self.modifier.arg1})'}"

@dataclass
class PrefixProperty(ItemProperty):
    upgrade_id: ItemUpgradeId
    upgrade: "Upgrade"

    def describe(self) -> str:
        return f"{self.upgrade.name if self.upgrade else f'Unknown (ID {self.upgrade_id})'}\n{self.upgrade.description if self.upgrade else ''}"

@dataclass
class ReceiveLessDamage(ItemProperty):
    damage_reduction: int
    chance: int

    def describe(self) -> str:
        return f"Received damage -{self.damage_reduction} (Chance: {self.chance}%)"

@dataclass
class ReceiveLessPhysDamageEnchanted(ItemProperty):
    damage_reduction: int

    def describe(self) -> str:
        return f"Received physical damage -{self.damage_reduction} (while Enchanted)"

@dataclass
class ReceiveLessPhysDamageHexed(ItemProperty):
    damage_reduction: int

    def describe(self) -> str:
        return f"Received physical damage -{self.damage_reduction} (while Hexed)"

@dataclass
class ReceiveLessPhysDamageStance(ItemProperty):
    damage_reduction: int

    def describe(self) -> str:
        return f"Received physical damage -{self.damage_reduction} (while in a Stance)"

@dataclass
class ReduceConditionDuration(ItemProperty):
    condition: Reduced_Ailment

    def describe(self) -> str:
        return f"Reduces {self.condition.name} duration on you by 20% (Stacking)"

@dataclass
class ReduceConditionTupleDuration(ItemProperty):
    condition_1: Reduced_Ailment
    condition_2: Reduced_Ailment

    def describe(self) -> str:
        return f"Reduces {self.condition_1.name.replace('_', ' ')} duration on you by 20% (Non-stacking)\nReduces {self.condition_2.name.replace('_', ' ')} duration on you by 20% (Non-stacking)"

@dataclass
class ReducesDiseaseDuration(ItemProperty):
    def describe(self) -> str:
        return f"Reduces disease duration on you by 20%"

@dataclass
class SuffixProperty(ItemProperty):    
    upgrade_id: ItemUpgradeId
    upgrade: "Upgrade"

    def describe(self) -> str:
        return f"{self.upgrade.name if self.upgrade else f'Unknown (ID {self.upgrade_id})'}\n{self.upgrade.description if self.upgrade else ''}"

@dataclass
class AttributeRequirement(ItemProperty):
    attribute: Attribute
    attribute_level: int

    def describe(self) -> str:
        return f"(Requires {self.attribute_level} {AttributeNames.get(self.attribute)})"

@dataclass
class BaneProperty(ItemProperty):
    species: ItemBaneSpecies
    
    def describe(self) -> str:
        species = self.species.name if self.species != ItemBaneSpecies.Unknown else f"ID {self.modifier.arg1}"
        return f"Bane: {species}"
    
@dataclass
class DamageProperty(ItemProperty):
    min_damage: int
    max_damage: int
    
    def describe(self) -> str:
        return f"{self.min_damage}-{self.max_damage} Damage"

@dataclass
class UnknownUpgradeProperty(ItemProperty):
    upgrade_id: ItemUpgradeId
    
    def describe(self) -> str:
        return f"Unknown Upgrade (ID {self.upgrade_id})"

@dataclass
class InscriptionProperty(ItemProperty):    
    upgrade_id: ItemUpgradeId
    upgrade: "Upgrade"

    def describe(self) -> str:
        return f"{self.upgrade.name if self.upgrade else f'Unknown (ID {self.upgrade_id})'}\n{self.upgrade.description if self.upgrade else ''}"
    
@dataclass
class UpgradeRuneProperty(ItemProperty):    
    upgrade_id: ItemUpgradeId
    upgrade: "Upgrade"

    def describe(self) -> str:
        return f"RUNE\n{self.upgrade.name if self.upgrade else f'Unknown (ID {self.upgrade_id})'}\n{self.upgrade.description if self.upgrade else ''}\n"
    
@dataclass
class AppliesToRuneProperty(ItemProperty):    
    upgrade_id: ItemUpgradeId
    upgrade: "Upgrade"

    def describe(self) -> str:
        return f"{self.upgrade.name if self.upgrade else f'Unknown (ID {self.upgrade_id})'}"

@dataclass
class TooltipProperty(ItemProperty):
    pass

@dataclass
class TargetItemTypeProperty(ItemProperty):
    item_type : ItemType
    
    def describe(self) -> str:
        return f"{self.item_type.name}"
#endregion Item Properties

