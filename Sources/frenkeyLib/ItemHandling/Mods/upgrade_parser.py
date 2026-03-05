from typing import Callable, Optional

from Py4GWCoreLib.enums_src.GameData_enums import _ATTRIBUTE_TO_PROFESSION, Ailment, Attribute, DamageType, Profession, Reduced_Ailment
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Sources.frenkeyLib.ItemHandling.Mods.decoded_modifier import DecodedModifier
from Sources.frenkeyLib.ItemHandling.Mods.properties import *
from Sources.frenkeyLib.ItemHandling.Mods.types import ItemBaneSpecies, ItemUpgradeType, ModifierIdentifier
from Sources.frenkeyLib.ItemHandling.Mods.upgrades import Upgrade, UnknownUpgrade, _UPGRADES

def get_profession_from_attribute(attribute: Attribute) -> Optional[Profession]:
    return _ATTRIBUTE_TO_PROFESSION.get(attribute, Profession._None)

def get_species(modifiers: list[DecodedModifier]) -> ItemBaneSpecies:
    bane_mod = next((m for m in modifiers if m.identifier == ModifierIdentifier.BaneSpecies), None)
    if bane_mod:
        return ItemBaneSpecies(bane_mod.arg1)
    
    return ItemBaneSpecies.Unknown

def get_upgrade_property(modifier: DecodedModifier, modifiers: list[DecodedModifier], upgrade_type: ItemUpgradeType | None = None) -> Optional[ItemProperty]:
    upgrade, upgrade_type = get_upgrade(modifier, modifiers, upgrade_type)
        
    if upgrade and upgrade.mod_type != ItemUpgradeType.Unknown:
        match upgrade_type:
            case ItemUpgradeType.Prefix:
                return PrefixProperty(modifier=modifier, upgrade_id=modifier.upgrade_id, upgrade=upgrade)
            
            case ItemUpgradeType.Suffix:
                return SuffixProperty(modifier=modifier, upgrade_id=modifier.upgrade_id, upgrade=upgrade)
            
            case ItemUpgradeType.Inscription:
                return InscriptionProperty(modifier=modifier, upgrade_id=modifier.upgrade_id, upgrade=upgrade)
            
            case ItemUpgradeType.UpgradeRune:
                return UpgradeRuneProperty(modifier=modifier, upgrade_id=modifier.upgrade_id, upgrade=upgrade)
            
            case ItemUpgradeType.AppliesToRune:
                return AppliesToRuneProperty(modifier=modifier, upgrade_id=modifier.upgrade_id, upgrade=upgrade)
    
    return None

def get_upgrade(modifier : DecodedModifier, modifiers: list[DecodedModifier], upgrade_type: ItemUpgradeType | None = None) -> tuple["Upgrade", ItemUpgradeType]:
    creator_type = next((t for t in _UPGRADES if t.has_id(modifier.upgrade_id) and (upgrade_type is None or t.mod_type == upgrade_type)), None)     

    if creator_type is not None:        
        upgrade = creator_type.compose_from_modifiers(modifier, modifiers)
        if upgrade is not None:
            return upgrade, creator_type.mod_type
        
    return UnknownUpgrade(), ItemUpgradeType.Unknown
       
_PROPERTY_FACTORY: dict[ModifierIdentifier, Callable[[DecodedModifier, list[DecodedModifier]], ItemProperty]] = {
    ModifierIdentifier.Armor1: lambda m, _: ArmorProperty(modifier=m, armor=m.arg1),
    ModifierIdentifier.Armor2: lambda m, _: ArmorProperty(modifier=m, armor=m.arg1),
    ModifierIdentifier.ArmorEnergyRegen: lambda m, _: ArmorEnergyRegen(modifier=m, energy_regen=m.arg1),
    ModifierIdentifier.ArmorMinusAttacking: lambda m, _: ArmorMinusAttacking(modifier=m, armor=m.arg2),
    ModifierIdentifier.ArmorPenetration: lambda m, _: ArmorPenetration(modifier=m, armor_pen=m.arg2, chance=m.arg1),
    ModifierIdentifier.ArmorPlus: lambda m, _: ArmorPlus(modifier=m, armor=m.arg2),
    ModifierIdentifier.ArmorPlusAttacking: lambda m, _: ArmorPlusAttacking(modifier=m, armor=m.arg2),
    ModifierIdentifier.ArmorPlusCasting: lambda m, _: ArmorPlusCasting(modifier=m, armor=m.arg2),
    ModifierIdentifier.ArmorPlusEnchanted: lambda m, _: ArmorPlusEnchanted(modifier=m, armor=m.arg2),
    ModifierIdentifier.ArmorPlusHexed: lambda m, _: ArmorPlusHexed(modifier=m, armor=m.arg2),
    ModifierIdentifier.ArmorPlusAbove: lambda m, _: ArmorPlusAbove(modifier=m, armor=m.arg2),
    ModifierIdentifier.ArmorPlusVsDamage: lambda m, _: ArmorPlusVsDamage(modifier=m, armor=m.arg2, damage_type=DamageType(m.arg1)),
    ModifierIdentifier.ArmorPlusVsElemental: lambda m, _: ArmorPlusVsElemental(modifier=m, armor=m.arg2),
    ModifierIdentifier.ArmorPlusVsPhysical: lambda m, _: ArmorPlusVsPhysical(modifier=m, armor=m.arg2),
    ModifierIdentifier.ArmorPlusVsPhysical2: lambda m, _: ArmorPlusVsPhysical(modifier=m, armor=m.arg2),
    ModifierIdentifier.ArmorPlusVsSpecies: lambda m, _: ArmorPlusVsSpecies(modifier=m, armor=m.arg2, species=ItemBaneSpecies(m.arg1)),
    ModifierIdentifier.ArmorPlusWhileDown: lambda m, _: ArmorPlusWhileDown(modifier=m, armor=m.arg2, health_threshold=m.arg1),
    ModifierIdentifier.AttributePlusOne: lambda m, _: AttributePlusOne(modifier=m, attribute=Attribute(m.arg1), chance=m.arg2),
    ModifierIdentifier.AttributePlusOneItem: lambda m, _: AttributePlusOneItem(modifier=m, chance=m.arg1),
    ModifierIdentifier.AttributeRequirement: lambda m, _: AttributeRequirement(modifier=m, attribute=Attribute(m.arg1), attribute_level=m.arg2),
    ModifierIdentifier.BaneSpecies: lambda m, _: BaneProperty(modifier=m, species=ItemBaneSpecies(m.arg1)),
    ModifierIdentifier.Damage: lambda m, _: DamageProperty(modifier=m, min_damage=m.arg2, max_damage=m.arg1),
    ModifierIdentifier.Damage2: lambda m, _: DamageProperty(modifier=m, min_damage=m.arg2, max_damage=m.arg1),
    ModifierIdentifier.DamageCustomized: lambda m, _: DamageCustomized(modifier=m, damage_increase=m.arg1 - 100),
    ModifierIdentifier.DamagePlusEnchanted: lambda m, _: DamagePlusEnchanted(modifier=m, damage_increase=m.arg2),
    ModifierIdentifier.DamagePlusHexed: lambda m, _: DamagePlusHexed(modifier=m, damage_increase=m.arg2),
    ModifierIdentifier.DamagePlusPercent: lambda m, _: DamagePlusPercent(modifier=m, damage_increase=m.arg2),
    ModifierIdentifier.DamagePlusStance: lambda m, _: DamagePlusStance(modifier=m, damage_increase=m.arg2),
    ModifierIdentifier.DamagePlusVsHexed: lambda m, _: DamagePlusVsHexed(modifier=m, damage_increase=m.arg2),
    ModifierIdentifier.DamagePlusVsSpecies: lambda m, mods: DamagePlusVsSpecies(modifier=m, damage_increase=m.arg1, species=get_species(mods)),
    ModifierIdentifier.DamagePlusWhileDown: lambda m, _: DamagePlusWhileDown(modifier=m, damage_increase=m.arg2, health_threshold=m.arg1),
    ModifierIdentifier.DamagePlusWhileUp: lambda m, _: DamagePlusWhileUp(modifier=m, damage_increase=m.arg2, health_threshold=m.arg1),
    ModifierIdentifier.DamageTypeProperty: lambda m, _: DamageTypeProperty(modifier=m, damage_type=DamageType(m.arg1)),
    ModifierIdentifier.Energy: lambda m, _: EnergyProperty(modifier=m, energy=m.arg1),
    ModifierIdentifier.Energy2: lambda m, _: EnergyProperty(modifier=m, energy=m.arg1),
    ModifierIdentifier.EnergyDegen: lambda m, _: EnergyDegen(modifier=m, energy_regen=m.arg2),
    ModifierIdentifier.EnergyGainOnHit: lambda m, _: EnergyGainOnHit(modifier=m, energy_gain=m.arg2),
    ModifierIdentifier.EnergyMinus: lambda m, _: EnergyMinus(modifier=m, energy=m.arg2),
    ModifierIdentifier.EnergyPlus : lambda m, _: EnergyPlus(modifier=m, energy=m.arg2),
    ModifierIdentifier.EnergyPlusEnchanted: lambda m, _: EnergyPlusEnchanted(modifier=m, energy=m.arg2),
    ModifierIdentifier.EnergyPlusHexed: lambda m, _: EnergyPlusHexed(modifier=m, energy=m.arg2),
    ModifierIdentifier.EnergyPlusWhileBelow: lambda m, _: EnergyPlusWhileBelow(modifier=m, energy=m.arg2, health_threshold=m.arg1),
    ModifierIdentifier.EnergyPlusWhileDown: lambda m, _: EnergyPlusWhileDown(modifier=m, energy=m.arg2, health_threshold=m.arg1),
    ModifierIdentifier.Furious: lambda m, _: Furious(modifier=m, chance=m.arg2),
    ModifierIdentifier.HalvesCastingTimeAttribute: lambda m, _: HalvesCastingTimeAttribute(modifier=m, chance=m.arg1, attribute=Attribute(m.arg2)),
    ModifierIdentifier.HalvesCastingTimeGeneral: lambda m, _: HalvesCastingTimeGeneral(modifier=m, chance=m.arg1),
    ModifierIdentifier.HalvesCastingTimeItemAttribute: lambda m, _: HalvesCastingTimeItemAttribute(modifier=m, chance=m.arg1),
    ModifierIdentifier.HalvesSkillRechargeAttribute: lambda m, _: HalvesSkillRechargeAttribute(modifier=m, chance=m.arg1, attribute=Attribute(m.arg2)),
    ModifierIdentifier.HalvesSkillRechargeGeneral: lambda m, _: HalvesSkillRechargeGeneral(modifier=m, chance=m.arg1),
    ModifierIdentifier.HalvesSkillRechargeItemAttribute: lambda m, _: HalvesSkillRechargeItemAttribute(modifier=m, chance=m.arg1),
    ModifierIdentifier.HeadpieceAttribute: lambda m, _: HeadpieceAttribute(modifier=m, attribute=Attribute(m.arg1), attribute_level=m.arg2),
    ModifierIdentifier.HeadpieceGenericAttribute: lambda m, _: HeadpieceGenericAttribute(modifier=m),
    ModifierIdentifier.HealthDegen: lambda m, _: HealthDegen(modifier=m, health_regen=m.arg2),
    ModifierIdentifier.HealthMinus: lambda m, _: HealthMinus(modifier=m, health=m.arg2),
    ModifierIdentifier.HealthPlus: lambda m, _: HealthPlus(modifier=m, health=m.arg1),
    ModifierIdentifier.HealthPlus2 : lambda m, _: HealthPlus(modifier=m, health=m.arg2),
    ModifierIdentifier.HealthPlusEnchanted: lambda m, _: HealthPlusEnchanted(modifier=m, health=m.arg1),
    ModifierIdentifier.HealthPlusHexed: lambda m, _: HealthPlusHexed(modifier=m, health=m.arg1),
    ModifierIdentifier.HealthPlusStance: lambda m, _: HealthPlusStance(modifier=m, health=m.arg1),
    ModifierIdentifier.HealthStealOnHit: lambda m, _: HealthStealOnHit(modifier=m, health_steal=m.arg1),
    ModifierIdentifier.HighlySalvageable: lambda m, _: HighlySalvageable(modifier=m),
    ModifierIdentifier.IncreaseConditionDuration: lambda m, _: IncreaseConditionDuration(modifier=m, condition=Ailment(m.arg2)),
    ModifierIdentifier.IncreaseEnchantmentDuration: lambda m, _: IncreaseEnchantmentDuration(modifier=m, enchantment_duration=m.arg2),
    ModifierIdentifier.IncreasedSaleValue: lambda m, _: IncreasedSaleValue(modifier=m),
    ModifierIdentifier.Infused: lambda m, _: Infused(modifier=m),
    ModifierIdentifier.OfTheProfession: lambda m, _: OfTheProfession(modifier=m, attribute=Attribute(m.arg1), attribute_level=m.arg2, profession=get_profession_from_attribute(Attribute(m.arg1)) or Profession._None),
    ModifierIdentifier.ReceiveLessPhysDamageEnchanted: lambda m, _: ReceiveLessPhysDamageEnchanted(modifier=m, damage_reduction=m.arg2),
    ModifierIdentifier.ReceiveLessPhysDamageHexed: lambda m, _: ReceiveLessPhysDamageHexed(modifier=m, damage_reduction=m.arg2),
    ModifierIdentifier.ReceiveLessPhysDamageStance: lambda m, _: ReceiveLessPhysDamageStance(modifier=m, damage_reduction=m.arg2),
    ModifierIdentifier.ReduceConditionDuration: lambda m, _: ReduceConditionDuration(modifier=m, condition=Reduced_Ailment(m.arg1)),
    ModifierIdentifier.ReduceConditionTupleDuration: lambda m, _: ReduceConditionTupleDuration(modifier=m, condition_1=Reduced_Ailment(m.arg2), condition_2=Reduced_Ailment(m.arg1)),
    ModifierIdentifier.ReducesDiseaseDuration: lambda m, _: ReducesDiseaseDuration(modifier=m),
    ModifierIdentifier.ReceiveLessDamage: lambda m, _: ReceiveLessDamage(modifier=m, damage_reduction=m.arg2, chance=m.arg1),
    ModifierIdentifier.TargetItemType: lambda m, _: TargetItemTypeProperty(modifier=m, item_type=ItemType(m.arg1)),
    
    ModifierIdentifier.AttributeRune: lambda m, mods:   get_upgrade_property(m, mods, ItemUpgradeType.Suffix) or
                                                        UnknownUpgradeProperty(modifier=m, upgrade_id=m.upgrade_id),
                                                        
    ModifierIdentifier.Upgrade: lambda m, mods: 
                                                                    get_upgrade_property(m, mods, ItemUpgradeType.Prefix) or
                                                                    get_upgrade_property(m, mods, ItemUpgradeType.Inscription) or
                                                                    get_upgrade_property(m, mods, ItemUpgradeType.Suffix) or
                                                                    UnknownUpgradeProperty(modifier=m, upgrade_id=m.upgrade_id),
}