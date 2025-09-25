
from Py4GWCoreLib import GLOBAL_CACHE, Range
from HeroAI.types import SkillNature, Skilltarget, SkillType
from HeroAI.custom_skill import CustomSkill

class ParagonSkills:
    def __init__(self, skill_data):
        #region LEADERSHIP

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lead_the_Way")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Make_Your_Time")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Theyre_on_Fire")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Aggressive_Refrain")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Angelic_Bond")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.25
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Angelic_Protection")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Anthem_of_Flame")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Anthem_of_Fury")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Awe")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Blazing_Finale")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Burning_Refrain")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Burning_Shield")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Defensive_Anthem")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Enduring_Harmony")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Focused_Anger")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glowing_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        skill.Conditions.UniqueProperty = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Hasty_Refrain")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Leaders_Comfort")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Natural_Temper")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasEnchantment = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Signet_of_Return")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Soldiers_Fury")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spear_Swipe")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        #region COMMAND

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Brace_Yourself")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Cant_Touch_This")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Fall_Back")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill.Conditions.SharedEffects = [GLOBAL_CACHE.Skill.GetID("Incoming")]
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Find_Their_Weakness")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Go_for_the_Eyes")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Help_Me")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Incoming")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill.Conditions.SharedEffects = [GLOBAL_CACHE.Skill.GetID("Fall_Back")]
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Make_Haste")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Never_Give_Up")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.75
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Never_Surrender")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.IsPartyWide = True
        skill.Conditions.LessLife = 0.75
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Stand_Your_Ground")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("We_Shall_Return")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Anthem_of_Disruption")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Anthem_of_Envy")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Anthem_of_Guidance")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Anthem_of_Weariness")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Bladeturn_Refrain")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Crippling_Anthem")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Godspeed")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasEnchantment = True
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        #region MOTIVATION

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Its_Just_a_Flesh_Wound")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasCondition = False
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("The_Power_Is_Yours")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Aria_of_Restoration")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Aria_of_Zeal")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ballad_of_Restoration")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Chorus_of_Restoration")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Energizing_Chorus")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Energizing_Finale")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Finale_of_Restoration")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Inspirational_Speech")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Leaders_Zeal")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.75
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lyric_of_Purification")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lyric_of_Zeal")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mending_Refrain")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Purifying_Finale")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Signet_of_Synergy")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Song_of_Power")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Song_of_Purification")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Song_of_Restoration")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Earshot.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Zealous_Anthem")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        #region SPEAR_MASTERY

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Barbed_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Blazing_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Chest_Thumper")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Cruel_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Disrupting_Throw")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.EnemyCasting.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Harriers_Toss")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Holy_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Maiming_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasBleeding = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Merciless_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.5
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mighty_Throw")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Slayers_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spear_of_Lightning")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spear_of_Redemption")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Stunning_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Swift_Javelin")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Unblockable_Throw")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Wearying_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Wild_Throw")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        #region NO_ATTRIBUTE

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Cautery_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Hexbreaker_Aria")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Remedy_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Signet_of_Aggression")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Song_of_Concentration")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill