from typing import Callable, Optional

import Py4GW

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

def get_upgrade_property(modifier: DecodedModifier, modifiers: list[DecodedModifier], upgrade_type: ItemUpgradeType | None = None, rarity: Rarity = Rarity.Blue) -> Optional[ItemProperty]:
    upgrade, upgrade_type = get_upgrade(modifier, modifiers, upgrade_type, rarity)
        
    if upgrade and upgrade.mod_type != ItemUpgradeType.Unknown:
        match upgrade_type:
            case ItemUpgradeType.Prefix:
                return PrefixProperty(modifier=modifier, upgrade_id=modifier.upgrade_id, upgrade=upgrade, rarity=rarity)
            
            case ItemUpgradeType.Suffix:
                return SuffixProperty(modifier=modifier, upgrade_id=modifier.upgrade_id, upgrade=upgrade, rarity=rarity)
            
            case ItemUpgradeType.Inscription:
                return InscriptionProperty(modifier=modifier, upgrade_id=modifier.upgrade_id, upgrade=upgrade, rarity=rarity)
            
            case ItemUpgradeType.UpgradeRune:
                return UpgradeRuneProperty(modifier=modifier, upgrade_id=modifier.upgrade_id, upgrade=upgrade, rarity=rarity)
            
            case ItemUpgradeType.AppliesToRune:
                return AppliesToRuneProperty(modifier=modifier, upgrade_id=modifier.upgrade_id, upgrade=upgrade, rarity=rarity)
    
    return None

def get_upgrade(modifier : DecodedModifier, modifiers: list[DecodedModifier], upgrade_type: ItemUpgradeType | None = None, rarity: Rarity = Rarity.Blue) -> tuple["Upgrade", ItemUpgradeType]:
    creator_type = next((t for t in _UPGRADES if t.has_id(modifier.upgrade_id) and (upgrade_type is None or t.mod_type == upgrade_type)), None)     

    if creator_type is not None:        
        upgrade = creator_type.compose_from_modifiers(modifier, modifiers, rarity)
        if upgrade is not None:
            return upgrade, creator_type.mod_type
        
    return UnknownUpgrade(), ItemUpgradeType.Unknown

def get_damage_type(modifiers: list[DecodedModifier]) -> DamageType:
    damage_type_mod = next((m for m in modifiers if m.identifier == ModifierIdentifier.DamageTypeProperty), None)
    
    if damage_type_mod:
        return DamageType(damage_type_mod.arg1)
    
    return DamageType.Unknown

def get_item_requirement(modifiers: list[DecodedModifier]) -> Attribute:
    item_req_mod = next((m for m in modifiers if m.identifier == ModifierIdentifier.AttributeRequirement), None)
    
    if item_req_mod:
        return Attribute(item_req_mod.arg1)
    
    return Attribute.None_


def get_property_factory() -> dict[ModifierIdentifier, Callable[[DecodedModifier, list[DecodedModifier], Rarity], ItemProperty]]:
    return {
        ModifierIdentifier.Armor1: lambda m, _, rarity: ArmorProperty(modifier=m, armor=m.arg1, rarity=rarity),
        ModifierIdentifier.Armor2: lambda m, _, rarity: ArmorProperty(modifier=m, armor=m.arg1, rarity=rarity),
        ModifierIdentifier.ArmorEnergyRegen: lambda m, _, rarity: ArmorEnergyRegen(modifier=m, energy_regen=m.arg1, rarity=rarity),
        ModifierIdentifier.ArmorMinusAttacking: lambda m, _, rarity: ArmorMinusAttacking(modifier=m, armor=m.arg2, rarity=rarity),
        ModifierIdentifier.ArmorPenetration: lambda m, _, rarity: ArmorPenetration(modifier=m, armor_pen=m.arg2, chance=m.arg1, rarity=rarity),
        ModifierIdentifier.ArmorPlus: lambda m, _, rarity: ArmorPlus(modifier=m, armor=m.arg2, rarity=rarity),
        ModifierIdentifier.ArmorPlusAttacking: lambda m, _, rarity: ArmorPlusAttacking(modifier=m, armor=m.arg2, rarity=rarity),
        ModifierIdentifier.ArmorPlusCasting: lambda m, _, rarity: ArmorPlusCasting(modifier=m, armor=m.arg2, rarity=rarity),
        ModifierIdentifier.ArmorPlusEnchanted: lambda m, _, rarity: ArmorPlusEnchanted(modifier=m, armor=m.arg2, rarity=rarity),
        ModifierIdentifier.ArmorPlusHexed: lambda m, _, rarity: ArmorPlusHexed(modifier=m, armor=m.arg2, rarity=rarity),
        ModifierIdentifier.ArmorPlusAbove: lambda m, _, rarity: ArmorPlusAbove(modifier=m, armor=m.arg2, rarity=rarity),
        ModifierIdentifier.ArmorPlusVsDamage: lambda m, _, rarity: ArmorPlusVsDamage(modifier=m, armor=m.arg2, damage_type=DamageType(m.arg1), rarity=rarity),
        ModifierIdentifier.ArmorPlusVsElemental: lambda m, _, rarity: ArmorPlusVsElemental(modifier=m, armor=m.arg2, rarity=rarity),
        ModifierIdentifier.ArmorPlusVsPhysical: lambda m, _, rarity: ArmorPlusVsPhysical(modifier=m, armor=m.arg2, rarity=rarity),
        ModifierIdentifier.ArmorPlusVsPhysical2: lambda m, _, rarity: ArmorPlusVsPhysical(modifier=m, armor=m.arg2, rarity=rarity),
        ModifierIdentifier.ArmorPlusVsSpecies: lambda m, _, rarity: ArmorPlusVsSpecies(modifier=m, armor=m.arg2, species=ItemBaneSpecies(m.arg1), rarity=rarity),
        ModifierIdentifier.ArmorPlusWhileDown: lambda m, _, rarity: ArmorPlusWhileDown(modifier=m, armor=m.arg2, health_threshold=m.arg1, rarity=rarity),
        ModifierIdentifier.AttributePlusOne: lambda m, _, rarity: AttributePlusOne(modifier=m, attribute=Attribute(m.arg1), chance=m.arg2, rarity=rarity),
        ModifierIdentifier.AttributePlusOneItem: lambda m, _, rarity: AttributePlusOneItem(modifier=m, chance=m.arg1, rarity=rarity),
        ModifierIdentifier.AttributeRequirement: lambda m, _, rarity: AttributeRequirement(modifier=m, attribute=Attribute(m.arg1), attribute_level=m.arg2, rarity=rarity),
        ModifierIdentifier.BaneSpecies: lambda m, _, rarity: BaneProperty(modifier=m, species=ItemBaneSpecies(m.arg1), rarity=rarity),
        ModifierIdentifier.Damage: lambda m, mods, rarity: DamageProperty(modifier=m, min_damage=m.arg2, max_damage=m.arg1, damage_type=get_damage_type(mods), rarity=rarity),
        ModifierIdentifier.Damage2: lambda m, mods, rarity: DamageProperty(modifier=m, min_damage=m.arg2, max_damage=m.arg1, damage_type=get_damage_type(mods), rarity=rarity),
        ModifierIdentifier.DamageCustomized: lambda m, _, rarity: DamageCustomized(modifier=m, damage_increase=m.arg1 - 100, rarity=rarity),
        ModifierIdentifier.DamagePlusEnchanted: lambda m, _, rarity: DamagePlusEnchanted(modifier=m, damage_increase=m.arg2, rarity=rarity),
        ModifierIdentifier.DamagePlusHexed: lambda m, _, rarity: DamagePlusHexed(modifier=m, damage_increase=m.arg2, rarity=rarity),
        ModifierIdentifier.DamagePlusPercent: lambda m, _, rarity: DamagePlusPercent(modifier=m, damage_increase=m.arg2, rarity=rarity),
        ModifierIdentifier.DamagePlusStance: lambda m, _, rarity: DamagePlusStance(modifier=m, damage_increase=m.arg2, rarity=rarity),
        ModifierIdentifier.DamagePlusVsHexed: lambda m, _, rarity: DamagePlusVsHexed(modifier=m, damage_increase=m.arg2, rarity=rarity),
        ModifierIdentifier.DamagePlusVsSpecies: lambda m, mods, rarity: DamagePlusVsSpecies(modifier=m, damage_increase=m.arg1, species=get_species(mods), rarity=rarity),
        ModifierIdentifier.DamagePlusWhileDown: lambda m, _, rarity: DamagePlusWhileDown(modifier=m, damage_increase=m.arg2, health_threshold=m.arg1, rarity=rarity),
        ModifierIdentifier.DamagePlusWhileUp: lambda m, _, rarity: DamagePlusWhileUp(modifier=m, damage_increase=m.arg2, health_threshold=m.arg1, rarity=rarity),
        ModifierIdentifier.DamageTypeProperty: lambda m, _, rarity: DamageTypeProperty(modifier=m, damage_type=DamageType(m.arg1), rarity=rarity),
        ModifierIdentifier.Energy: lambda m, _, rarity: EnergyProperty(modifier=m, energy=m.arg1, rarity=rarity),
        ModifierIdentifier.Energy2: lambda m, _, rarity: EnergyProperty(modifier=m, energy=m.arg1, rarity=rarity),
        ModifierIdentifier.EnergyDegen: lambda m, _, rarity: EnergyDegen(modifier=m, energy_regen=m.arg2, rarity=rarity),
        ModifierIdentifier.EnergyGainOnHit: lambda m, _, rarity: EnergyGainOnHit(modifier=m, energy_gain=m.arg2, rarity=rarity),
        ModifierIdentifier.EnergyMinus: lambda m, _, rarity: EnergyMinus(modifier=m, energy=m.arg2, rarity=rarity),
        ModifierIdentifier.EnergyPlus : lambda m, _, rarity: EnergyPlus(modifier=m, energy=m.arg2, rarity=rarity),
        ModifierIdentifier.EnergyPlusEnchanted: lambda m, _, rarity: EnergyPlusEnchanted(modifier=m, energy=m.arg2, rarity=rarity),
        ModifierIdentifier.EnergyPlusHexed: lambda m, _, rarity: EnergyPlusHexed(modifier=m, energy=m.arg2, rarity=rarity),
        ModifierIdentifier.EnergyPlusWhileBelow: lambda m, _, rarity: EnergyPlusWhileBelow(modifier=m, energy=m.arg2, health_threshold=m.arg1, rarity=rarity),
        ModifierIdentifier.EnergyPlusWhileDown: lambda m, _, rarity: EnergyPlusWhileDown(modifier=m, energy=m.arg2, health_threshold=m.arg1, rarity=rarity),
        ModifierIdentifier.Furious: lambda m, _, rarity: Furious(modifier=m, chance=m.arg2, rarity=rarity),
        ModifierIdentifier.HalvesCastingTimeAttribute: lambda m, _, rarity: HalvesCastingTimeAttribute(modifier=m, chance=m.arg1, attribute=Attribute(m.arg2), rarity=rarity),
        ModifierIdentifier.HalvesCastingTimeGeneral: lambda m, _, rarity: HalvesCastingTimeGeneral(modifier=m, chance=m.arg1, rarity=rarity),
        ModifierIdentifier.HalvesCastingTimeItemAttribute: lambda m, mods, rarity: HalvesCastingTimeItemAttribute(modifier=m, chance=m.arg1, attribute=get_item_requirement(mods), rarity=rarity),
        ModifierIdentifier.HalvesSkillRechargeAttribute: lambda m, _, rarity: HalvesSkillRechargeAttribute(modifier=m, chance=m.arg1, attribute=Attribute(m.arg2), rarity=rarity),
        ModifierIdentifier.HalvesSkillRechargeGeneral: lambda m, _, rarity: HalvesSkillRechargeGeneral(modifier=m, chance=m.arg1, rarity=rarity),
        ModifierIdentifier.HalvesSkillRechargeItemAttribute: lambda m, mods, rarity: HalvesSkillRechargeItemAttribute(modifier=m, chance=m.arg1, attribute=get_item_requirement(mods), rarity=rarity),
        ModifierIdentifier.HeadpieceAttribute: lambda m, _, rarity: HeadpieceAttribute(modifier=m, attribute=Attribute(m.arg1), attribute_level=m.arg2, rarity=rarity),
        ModifierIdentifier.HeadpieceGenericAttribute: lambda m, _, rarity: HeadpieceGenericAttribute(modifier=m, rarity=rarity),
        ModifierIdentifier.HealthDegen: lambda m, _, rarity: HealthDegen(modifier=m, health_regen=m.arg2, rarity=rarity),
        ModifierIdentifier.HealthMinus: lambda m, _, rarity: HealthMinus(modifier=m, health=m.arg2, rarity=rarity),
        ModifierIdentifier.HealthPlus: lambda m, _, rarity: HealthPlus(modifier=m, health=m.arg1, rarity=rarity),
        ModifierIdentifier.HealthPlus2 : lambda m, _, rarity: HealthPlus(modifier=m, health=m.arg2, rarity=rarity),
        ModifierIdentifier.HealthPlusEnchanted: lambda m, _, rarity: HealthPlusEnchanted(modifier=m, health=m.arg1, rarity=rarity),
        ModifierIdentifier.HealthPlusHexed: lambda m, _, rarity: HealthPlusHexed(modifier=m, health=m.arg1, rarity=rarity),
        ModifierIdentifier.HealthPlusStance: lambda m, _, rarity: HealthPlusStance(modifier=m, health=m.arg1, rarity=rarity),
        ModifierIdentifier.HealthStealOnHit: lambda m, _, rarity: HealthStealOnHit(modifier=m, health_steal=m.arg1, rarity=rarity),
        ModifierIdentifier.HighlySalvageable: lambda m, _, rarity: HighlySalvageable(modifier=m, rarity=rarity),
        ModifierIdentifier.IncreaseConditionDuration: lambda m, _, rarity: IncreaseConditionDuration(modifier=m, condition=Ailment(m.arg2), rarity=rarity),
        ModifierIdentifier.IncreaseEnchantmentDuration: lambda m, _, rarity: IncreaseEnchantmentDuration(modifier=m, enchantment_duration=m.arg2, rarity=rarity),
        ModifierIdentifier.IncreasedSaleValue: lambda m, _, rarity: IncreasedSaleValue(modifier=m, rarity=rarity),
        ModifierIdentifier.Infused: lambda m, _, rarity: Infused(modifier=m, rarity=rarity),
        ModifierIdentifier.OfTheProfession: lambda m, _, rarity: OfTheProfession(modifier=m, attribute=Attribute(m.arg1), attribute_level=m.arg2, profession=get_profession_from_attribute(Attribute(m.arg1)) or Profession._None, rarity=rarity),
        ModifierIdentifier.ReceiveLessPhysDamageEnchanted: lambda m, _, rarity: ReceiveLessPhysDamageEnchanted(modifier=m, damage_reduction=m.arg2, rarity=rarity),
        ModifierIdentifier.ReceiveLessPhysDamageHexed: lambda m, _, rarity: ReceiveLessPhysDamageHexed(modifier=m, damage_reduction=m.arg2, rarity=rarity),
        ModifierIdentifier.ReceiveLessPhysDamageStance: lambda m, _, rarity: ReceiveLessPhysDamageStance(modifier=m, damage_reduction=m.arg2, rarity=rarity),
        ModifierIdentifier.ReduceConditionDuration: lambda m, _, rarity: ReduceConditionDuration(modifier=m, condition=Reduced_Ailment(m.arg1), rarity=rarity),
        ModifierIdentifier.ReduceConditionTupleDuration: lambda m, _, rarity: ReduceConditionTupleDuration(modifier=m, condition_1=Reduced_Ailment(m.arg2), condition_2=Reduced_Ailment(m.arg1), rarity=rarity),
        ModifierIdentifier.ReducesDiseaseDuration: lambda m, _, rarity: ReducesDiseaseDuration(modifier=m, rarity=rarity),
        ModifierIdentifier.ReceiveLessDamage: lambda m, _, rarity: ReceiveLessDamage(modifier=m, damage_reduction=m.arg2, chance=m.arg1, rarity=rarity),
        ModifierIdentifier.TargetItemType: lambda m, _, rarity: TargetItemTypeProperty(modifier=m, item_type=ItemType(m.arg1), rarity=rarity),
        
        ModifierIdentifier.AttributeRune: lambda m, mods, rarity:   get_upgrade_property(m, mods, ItemUpgradeType.Suffix, rarity) or
                                                            UnknownUpgradeProperty(modifier=m, upgrade_id=m.upgrade_id, rarity=rarity),
                                                            
        ModifierIdentifier.Upgrade: lambda m, mods, rarity: 
                                                                        get_upgrade_property(m, mods, ItemUpgradeType.Prefix, rarity) or
                                                                        get_upgrade_property(m, mods, ItemUpgradeType.Inscription, rarity) or
                                                                        get_upgrade_property(m, mods, ItemUpgradeType.Suffix, rarity) or
                                                                        UnknownUpgradeProperty(modifier=m, upgrade_id=m.upgrade_id, rarity=rarity),
    }