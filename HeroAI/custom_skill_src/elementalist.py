
from Py4GWCoreLib import GLOBAL_CACHE, Range
from HeroAI.types import SkillNature, Skilltarget, SkillType
from HeroAI.custom_skill import CustomSkill

class ElementalistSkills:
    def __init__(self, skill_data):
        #region ENERGY_STORAGE

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Aura_of_Restoration")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.CustomC.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Elemental_Attunement")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Energy_Blast")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Energy_Boon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ether_Prism")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ether_Prodigy")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ether_Renewal")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.CustomC.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glyph_of_Energy")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glyph_of_Lesser_Energy")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glyph_of_Restoration")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Master_of_Magic")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        #region AIR_MAGIC

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Air_Attunement")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Arc_Lightning")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Blinding_Flash")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Blinding_Surge")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.EnemyAttacking.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAttacking = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Chain_Lightning")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Chilling_Winds")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Conjure_Lightning")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Enervating_Charge")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Gale")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glimmering_Mark")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glyph_of_Swiftness")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Gust")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Invoke_Lightning")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lightning_Bolt")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lightning_Hammer")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lightning_Javelin")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.EnemyAttacking.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsAttacking = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lightning_Orb")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lightning_Strike")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lightning_Surge")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lightning_Touch")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mind_Shock")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ride_the_Lightning")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shell_Shock")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shock")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shock_Arrow")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Storm_Djinns_Haste")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Teinais_Wind")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Thunderclap")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Whirlwind")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.EnemiesInRange = 3
        skill.Conditions.EnemiesInRangeArea = Range.Area.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Windborne_Speed")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        #region EARTH_MAGIC

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Aftershock")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Armor_of_Earth")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ash_Blast")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Churning_Earth")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Crystal_Wave")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Dragons_Stomp")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Earth_Attunement")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Earthen_Shackles")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Earthquake")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ebon_Hawk")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Eruption")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glowstone")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Grasping_Earth")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Iron_Mist")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Kinetic_Armor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Magnetic_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Magnetic_Surge")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Obsidian_Flame")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Obsidian_Flesh")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Sandstorm")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shockwave")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.EnemiesInRange = 3
        skill.Conditions.EnemiesInRangeArea = Range.Area.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Sliver_Armor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Stone_Daggers")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Stone_Sheath")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Stone_Striker")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Stoneflesh_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Stoning")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Teinais_Crystals")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Unsteady_Ground")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ward_Against_Elements")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.EnemiesInRange = 3
        skill.Conditions.EnemiesInRangeArea = Range.Area.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ward_Against_Foes")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.EnemiesInRange = 3
        skill.Conditions.EnemiesInRangeArea = Range.Area.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ward_Against_Melee")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.EnemiesInRange = 3
        skill.Conditions.EnemiesInRangeArea = Range.Area.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ward_of_Stability")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.AlliesInRange = 3
        skill.Conditions.AlliesInRangeArea = Range.Area.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ward_of_Weakness")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.EnemiesInRange = 3
        skill.Conditions.EnemiesInRangeArea = Range.Area.value
        skill_data[skill.SkillID] = skill

        #region FIRE_MAGIC

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Bed_of_Coals")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Breath_of_Fire")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Burning_Speed")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Conjure_Flame")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Double_Dragon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Elemental_Flame")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Fire_Attunement")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Fire_Storm")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.EnemyClustered.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Fireball")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Flame_Burst")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Flame_Djinns_Haste")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Flare")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glowing_Gaze")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glyph_of_Immolation")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Immolate")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Incendiary_Bonds")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Inferno")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.EnemiesInRange = 3
        skill.Conditions.EnemiesInRangeArea = Range.Area.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lava_Arrows")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Lava_Font")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.EnemiesInRange = 3
        skill.Conditions.EnemiesInRangeArea = Range.Area.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Liquid_Flame")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mark_of_Rodgort")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Meteor")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Meteor_Shower")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mind_Blast")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mind_Burn")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Phoenix")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Rodgorts_Invocation")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Savannah_Heat")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Searing_Flames")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Searing_Heat")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Smoldering_Embers")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Star_Burst")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Teinais_Heat")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.EnemiesInRange = 3
        skill.Conditions.EnemiesInRangeArea = Range.Area.value
        skill_data[skill.SkillID] = skill

        #region WATER_MAGIC

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Armor_of_Frost")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Armor_of_Mist")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Blurred_Vision")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Conjure_Frost")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Deep_Freeze")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Freezing_Gust")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Frigid_Armor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Frozen_Burst")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glowing_Ice")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ice_Prison")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ice_Spear")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ice_Spikes")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Icy_Prism")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Icy_Shackles")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Maelstrom")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mind_Freeze")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mirror_of_Ice")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Mist_Form")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Rust")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shard_Storm")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Shatterstone")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Slippery_Ground")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Steam")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Swirling_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Teinais_Prison")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Vapor_Blade")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasEnchantment = False
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Ward_Against_Harm")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.EnemiesInRange = 3
        skill.Conditions.EnemiesInRangeArea = Range.Area.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Water_Attunement")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Water_Trident")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Winters_Embrace")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill_data[skill.SkillID] = skill

        #region NO_ATTRIBUTE

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glyph_of_Concentration")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glyph_of_Elemental_Power")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glyph_of_Essence")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glyph_of_Renewal")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Glyph_of_Sacrifice")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill

        skill = CustomSkill()
        skill.SkillID = GLOBAL_CACHE.Skill.GetID("Second_Wind")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill_data[skill.SkillID] = skill