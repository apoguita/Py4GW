
from Py4GWCoreLib import GLOBAL_CACHE, Range
from HeroAI.types import SkillNature, Skilltarget, SkillType
from HeroAI.custom_skill import CustomSkill

class RangerSkills:
    def __init__(self, skill_data):
         #region EXPERTISE

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Archers_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Distracting_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.EnemyCasting.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Dodge")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Escape")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Expert_Focus")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Experts_Dexterity")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glass_Arrows")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Infuriating_Heat")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lightning_Reflexes")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Marksmans_Wager")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Oath_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Point_Blank_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Practiced_Stance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Throw_Dirt")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.TargetingStrict = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Trappers_Focus")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Trappers_Speed")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Whirling_Defense")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Zojuns_Haste")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Zojuns_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        #region BEAST_MASTERY

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Bestial_Fury")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Bestial_Mauling")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Bestial_Pounce")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsCasting = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Brutal_Strike")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.5
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Call_of_Haste")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Call_of_Protection")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Charm_Animal")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Comfort_Animal")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.UniqueProperty = True
        skill.Conditions.LessLife = 0.50
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Companionship")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.5
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Disrupting_Lunge")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.EnemyCasting.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Edge_of_Extinction")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Energizing_Wind")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Enraged_Lunge")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Feral_Aggression")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Feral_Lunge")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ferocious_Strike")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Fertile_Season")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Heal_as_One")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Healing.value
        skill.unique_property = True
        skill.Conditions.LessLife = 0.7
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Hekets_Rampage")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lacerate")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Maiming_Strike")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Melandrus_Assault")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Otyughs_Cry")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Poisonous_Bite")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Pounce")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Predators_Pounce")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Predatory_Bond")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Predatory_Season")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Primal_Echoes")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Rampage_as_One")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Revive_Animal")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Run_as_One")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Savage_Pounce")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Scavenger_Strike")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Strike_as_One")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Symbiosis")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Symbiotic_Bond")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Tigers_Fury")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Toxicity")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Vipers_Nest")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        #region MARKSMANSHIP

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Arcing_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Barrage")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Body_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Broad_Head_Arrow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.EnemyCasting.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Burning_Arrow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Concussion_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.EnemyCasting.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Crippling_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Crossfire")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Debilitating_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Determined_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Disrupting_Accuracy")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Disrupting_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.EnemyCasting.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Favorable_Winds")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Focused_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Hunters_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Keen_Arrow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Marauders_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Melandrus_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Needling_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.5
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Penetrating_Attack")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Pin_Down")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Power_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Precision_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Prepared_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Punishing_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.EnemyAttacking.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsAttacking = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Rapid_Fire")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Read_the_Wind")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Savage_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.EnemyCastingSpell.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Screaming_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Seeking_Arrows")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Sloth_Hunters_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsCasting = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Splinter_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Sundering_Attack")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Volley")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        #region WILDERNESS_SURVIVAL

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Apply_Poison")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Barbed_Arrows")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Barbed_Trap")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Brambles")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Choking_Gas")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Conflagration")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Dryders_Defenses")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Dust_Trap")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Equinox")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Famine")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Flame_Trap")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Frozen_Soil")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Greater_Conflagration")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Healing_Spring")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ignite_Arrows")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Incendiary_Arrows")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Kindle_Arrows")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Melandrus_Arrows")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Melandrus_Resilience")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.UniqueProperty = True
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Muddy_Terrain")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Natural_Stride")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Natures_Renewal")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Pestilence")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Piercing_Trap")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Poison_Arrow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Poison_Tip_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Quickening_Zephyr")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Quicksand")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Roaring_Winds")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Scavengers_Focus")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Serpents_Quickness")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Smoke_Trap")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Snare")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Spike_Trap")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Storm_Chaser")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Tranquility")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Tripwire")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Troll_Unguent")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.65
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Winnowing")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Winter")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        #region NO_ATTRIBUTE

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Antidote_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Called_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Dual_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Forked_Arrow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Magebane_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.EnemyCasting.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Quick_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Storms_Embrace")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill