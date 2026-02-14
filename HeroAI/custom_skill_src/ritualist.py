
from Py4GWCoreLib import GLOBAL_CACHE, Range
from HeroAI.types import SkillNature, Skilltarget, SkillType
from HeroAI.custom_skill import CustomSkill

class RitualistSkills:
    def __init__(self, skill_data):
        #region SPAWNING_POWER

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Anguished_Was_Lingwah")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Attuned_Was_Songkai")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Boon_of_Creation")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Consume_Soul")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Doom")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Empowerment")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Energetic_Was_Lee_Sa")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Explosive_Growth")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Feast_of_Souls")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Nearby.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ghostly_Haste")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Reclaim_Essence")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.3
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Renewing_Memories")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsHoldingItem = True
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ritual_Lord")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.SacrificeHealth = 0.2
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Rupture_Soul")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Spirit.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Sight_Beyond_Sight")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Signet_of_Binding")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Spirit.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.SacrificeHealth = 0.5
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Signet_of_Creation")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.75
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Soul_Twisting")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spirit_Channeling")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.75
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spirit_to_Flesh")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Spirit.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.45
        skill.Conditions.IsPartyWide = True
        skill.Conditions.UniqueProperty = True
        skill.Conditions.PartyWideArea = Range.Nearby.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spirits_Gift")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spirits_Strength")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Weapon_of_Renewal")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Wielders_Remedy")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Wielders_Zeal")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        #region CHANNELLING_MAGIC

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Agony")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ancestors_Rage")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Bloodsong")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Caretakers_Charge")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsHoldingItem = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Channeled_Strike")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsHoldingItem = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Clamor_of_Souls")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessEnergy = 0.75
        skill.Conditions.UniqueProperty = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Cruel_Was_Daoshen")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Destruction")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Destructive_Was_Glaive")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Essence_Strike")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Gaze_from_Beyond")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Gaze_of_Fury")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Spirit.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Grasping_Was_Kuurong")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lamentation")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Nightmare_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Offering_of_Spirit")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.75
        skill.Conditions.SacrificeHealth = 0.35
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Painful_Bond")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.SpiritsInRange = 1
        skill.Conditions.SpiritsInRangeArea = Range.Earshot.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Renewing_Surge")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Signet_of_Spirits")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spirit_Boon_Strike")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spirit_Burn")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spirit_Rift")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spirit_Siphon")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.5
        skill.Conditions.SpiritsInRange = 1
        skill.Conditions.SpiritsInRangeArea = Range.Earshot.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Splinter_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Wailing_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Warmongers_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Weapon_of_Aggression")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Weapon_of_Fury")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Wielders_Strike")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        #region COMMUNING

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Anguish")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Armor_of_Unfeeling")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Spirit.value
        skill.Nature = SkillNature.Neutral.value
        skill.Conditions.IsOutOfCombat = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Binding_Chains")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Brutal_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasEnchantment = True
        skill.Conditions.UniqueProperty = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Disenchantment")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Displacement")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Dissonance")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Dulled_Weapon")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Earthbind")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ghostly_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Guided_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mighty_Was_Vorizun")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Pain")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Restoration")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsOutOfCombat = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shadowsong")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shelter")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Signet_of_Ghostly_Might")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.UniqueProperty = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Soothing")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Sundering_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Union")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Vital_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyCaster.value
        skill.Nature = SkillNature.CustomC.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Wanderlust")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Weapon_of_Quickening")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyCaster.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        #region RESTORATION_MAGIC

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Blind_Was_Mingson")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Death_Pact_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Defiant_Was_Xinrae")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Flesh_of_My_Flesh")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Generous_Was_Tsungrai")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.SacrificeHealth = 0.4
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ghostmirror_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Life")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lively_Was_Naomei")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mend_Body_and_Soul")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.70
        skill.Conditions.UniqueProperty = True
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mending_Grip")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.HasWeaponSpell = True
        skill.Conditions.HasCondition = True
        skill.Conditions.IsOutOfCombat = True
        skill.Conditions.LessLife = 0.8
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Preservation")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.IsOutOfCombat = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Protective_Was_Kaolai")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Pure_Was_Li_Ming")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Recovery")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Recuperation")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.IsOutOfCombat = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Rejuvenation")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.CustomC.value
        skill.Conditions.IsOutOfCombat = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Resilient_Was_Xiko")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Resilient_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyCaster.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasHex = True
        skill.Conditions.HasCondition = True
        skill.Conditions.UniqueProperty = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Soothing_Memories")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spirit_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.SacrificeHealth = 0.3
        skill.Conditions.RequiresSpiritInEarshot = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spirit_Light_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spirit_Transfer")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.5
        skill.Conditions.RequiresSpiritInEarshot = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spiritleech_Aura")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Tranquil_Was_Tanasen")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Vengeful_Was_Khanhei")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Vengeful_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Vocal_Was_Sogolon")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Weapon_of_Remedy")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Weapon_of_Shadow")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Weapon_of_Warding")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Wielders_Boon")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.HasWeaponSpell = True
        skill.Conditions.IsOutOfCombat = True
        skill.Conditions.LessLife = 0.7
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Xinraes_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        #region NO_ATTRIBUTE

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Draw_Spirit")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Spirit.value
        skill.Nature = SkillNature.Neutral.value
        skill_data[skill.SkillID] = skill
