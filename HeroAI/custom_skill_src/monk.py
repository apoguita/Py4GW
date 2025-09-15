
from Py4GWCoreLib import GLOBAL_CACHE, Range
from HeroAI.types import SkillNature, Skilltarget, SkillType
from HeroAI.custom_skill import CustomSkill

class MonkSkills:
    def __init__(self, skill_data):
        #region DIVINE_FAVOR

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Blessed_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Blessed_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.65
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Blessed_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.IsOutOfCombat = True
        skill.Conditions.LessEnergy = 0.6
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Boon_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Contemplation_of_Purity")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.HasEnchantment = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Deny_Hexes")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Divine_Boon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Divine_Healing")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.8
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Earshot.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Divine_Intervention")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.35
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Divine_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Healers_Boon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Heavens_Delight")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Earshot.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Holy_Haste")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Peace_and_Harmony")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasCondition = True
        skill.Conditions.HasHex = True
        skill.Conditions.UniqueProperty = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Release_Enchantments")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.HasEnchantment = True
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.SafeCompass.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Scribes_Insight")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Signet_of_Devotion")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.85
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Smiters_Boon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spell_Breaker")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spell_Shield")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Unyielding_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.UniqueProperty = True
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Watchful_Healing")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.8
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Watchful_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Withdraw_Hexes")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Cure_Hex")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Dwaynas_Kiss")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.8
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Dwaynas_Sorrow")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.25
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ethereal_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Gift_of_Health")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.65
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glimmer_of_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.7
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Heal_Area")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Adjacent.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Heal_Other")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Heal_Party")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.80
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.SafeCompass.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Healers_Covenant")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Healing_Breeze")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.65
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Healing_Burst")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Healing_Hands")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.50
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Healing_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Healing_Ribbon")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Healing_Ring")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Adjacent.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Healing_Seed")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.5
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Adjacent.value
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Healing_Touch")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Healing_Whisper")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Infuse_Health")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.CustomA.value
        skill.Conditions.LessLife = 0.40
        skill.Conditions.SacrificeHealth = 0.50
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Jameis_Gaze")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Kareis_Healing_Circle")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Adjacent.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Light_of_Deliverance")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.8
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.SafeCompass.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Live_Vicariously")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mending")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Orison_of_Healing")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.8
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Patient_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.7
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Renew_Life")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Restful_Breeze")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Restore_Life")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Resurrection_Chant")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Signet_of_Rejuvenation")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.8
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spotless_Mind")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spotless_Soul")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Supportive_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Vigorous_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Word_of_Healing")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Words_of_Comfort")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        #region PROTECTION_PRAYERS

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Aegis")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Air_of_Enchantment")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Amity")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Aura_of_Faith")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Aura_of_Stability")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Convert_Hexes")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Dismiss_Condition")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Divert_Hexes")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Draw_Conditions")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Extinguish")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.LessLife = 0.75
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.SafeCompass.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Guardian")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Life_Attunement")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Life_Barrier")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Life_Bond")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Life_Sheath")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mark_of_Protection")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.5
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mend_Ailment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mend_Condition")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mending_Touch")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Pacifism")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Pensive_Guardian")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Protective_Bond")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Protective_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.CustomA.value
        skill.Conditions.LessLife = 0.8
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Purifying_Veil")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Rebirth")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Restore_Condition")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Reversal_of_Fortune")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.85
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Reverse_Hex")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shield_Guardian")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Earshot.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shield_of_Absorption")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.6
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shield_of_Deflection")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shield_of_Regeneration")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shielding_Hands")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.4
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spirit_Bond")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.7
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Vital_Blessing")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Zealous_Benediction")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.5
        skill_data[skill.SkillID] = skill

        #region SMITHING_PRAYERS

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Balthazars_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Balthazars_Pendulum")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Balthazars_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Bane_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.EnemyAttacking.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAttacking = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Castigation_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.EnemyAttacking.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAttacking = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Defenders_Zeal")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Holy_Strike")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Holy_Wrath")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Judges_Insight")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Judges_Intervention")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.25
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Kirins_Wrath")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ray_of_Judgment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Retribution")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Reversal_of_Damage")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.8
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Scourge_Enchantment")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Scourge_Healing")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Scourge_Sacrifice")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shield_of_Judgment")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Signet_of_Judgment")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Signet_of_Mystic_Wrath")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Signet_of_Rage")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Smite")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.EnemyAttacking.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAttacking = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Smite_Condition")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Smite_Hex")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spear_of_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.EnemyAttacking.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAttacking = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Stonesoul_Strike")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Strength_of_Honor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        #skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Symbol_of_Wrath")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Word_of_Censure")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.MoreLife = 0.33
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Zealots_Fire")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        #region NO_ATTRIBUTE

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Empathic_Removal")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.HasHex = True
        skill.Conditions.UniqueProperty = True
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Essence_Bond")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Holy_Veil")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Light_of_Dwayna")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Martyr")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Purge_Conditions")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Purge_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.HasHex = True
        skill.Conditions.UniqueProperty = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Remove_Hex")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Resurrect")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Signet_of_Removal")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasCondition = True
        skill.Conditions.HasHex = True
        skill.Conditions.HasEnchantment = True
        skill.Conditions.UniqueProperty = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Succor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyCaster.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Vengeance")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        skill_data[skill.SkillID] = skill
