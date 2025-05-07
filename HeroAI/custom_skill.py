from Py4GWCoreLib import *

from .types import *

class CustomSkillClass:
    # Constants
    MaxSkillData = 3433

    class CastConditions:
            def __init__(self):
                # Conditions
                self.IsAlive = True
                self.HasCondition = False
                self.HasBleeding = False
                self.HasBlindness = False
                self.HasBurning = False
                self.HasCrackedArmor = False
                self.HasCrippled = False
                self.HasDazed = False
                self.HasDeepWound = False
                self.HasDisease = False
                self.HasPoison = False
                self.HasWeakness = False
            
                # Special Conditions
                self.HasWeaponSpell = False
                self.WeaponSpellList = []
                self.HasEnchantment = False
                self.EnchantmentList = []
                self.HasDervishEnchantment = False
                self.HasHex = False
                self.HexList = []
                self.HasChant = False
                self.ChantList = []
                self.IsCasting = False
                self.CastingSkillList = []
                self.IsKnockedDown = False
                self.IsMoving = False
                self.IsAttacking = False
                self.IsHoldingItem = False
            
                # Targeting Rules
                self.TargetingStrict = True
                self.SelfFirst = False
            
                # Resource and Health Constraints
                self.LessLife = 0.0
                self.MoreLife = 0.0
                self.LessEnergy = 0.0
                self.Overcast = 0.0
                self.Overcast = 0.0
                self.SacrificeHealth = 0.0

                # Usage Flags
                self.IsPartyWide = False
                self.PartyWideArea = 0
                self.UniqueProperty = False
                self.IsOutOfCombat = False
                self.IgnoreEffectCheck = False

    class CustomSkill:
        def __init__(self):
            self.SkillID = 0
            self.SkillType = SkillType.Skill.value
            self.TargetAllegiance = Skilltarget.Enemy.value
            self.Nature = SkillNature.Offensive.value
            self.Conditions = CustomSkillClass.CastConditions()

    def __init__(self):
        self.skill_data = [self.CustomSkill() for _ in range(self.MaxSkillData)]
        self.load_skills()

    def get_skill(self, skill_id):
        """Fetch skill by ID."""
        if 0 <= skill_id < self.MaxSkillData:
            return self.skill_data[skill_id]
        raise ValueError(f"Invalid SkillID: {skill_id}")

    def set_skill(self, skill_id, skill):
        """Update a skill."""
        if 0 <= skill_id < self.MaxSkillData:
            self.skill_data[skill_id] = skill
        else:
            raise ValueError(f"Invalid SkillID: {skill_id}")

    def is_empty_skill(self, skill_id):
        """Check if the slot is empty."""
        return self.skill_data[skill_id].SkillID == 0

    def load_skills(self):
        """Populate skill data using hardcoded definitions."""
        # WARRIOR STRENGTH
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("I_Meant_to_Do_That")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("I_Will_Avenge_You")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("I_Will_Survive")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasCondition = True
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("You_Will_Die")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Battle_Rage")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Berserker_Stance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Body_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Bulls_Charge")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Bulls_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Burst_of_Aggression")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Charging_Strike")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Counterattack")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAttacking = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Defy_Pain")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Disarm")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsAttacking = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dolyak_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dwarven_Battle_Stance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Endure_Pain")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Enraging_Charge")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Flail")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Flourish")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Griffons_Sweep")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Headbutt")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Leviathans_Sweep")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lions_Comfort")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Magehunter_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Power_Attack")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Primal_Rage")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Protectors_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rage_of_the_Ntouka")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rush")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shield_Bash")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Stamina")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.5
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Strength")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sprint")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Tiger_Stance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Warriors_Cunning")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Warriors_Endurance")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.75
        self.skill_data[skill.SkillID] = skill

        # WARRIOR AXE MASTERY
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Agonizing_Chop")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.HasDeepWound = True
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Axe_Rake")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasDeepWound = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Axe_Twist")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasDeepWound = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Cleave")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Critical_Chop")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Cyclone_Axe")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Decapitate")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dismember")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Disrupting_Chop")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Eviscerate")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Executioners_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Furious_Axe")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Keen_Chop")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lacerating_Chop")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Penetrating_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Penetrating_Chop")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Swift_Chop")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Triple_Chop")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Whirling_Axe")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        # WARRIOR HAMMER MASTERY
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Auspicious_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Backbreaker")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Belly_Smash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Counter_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAttacking = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Crude_Swing")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Crushing_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Devastating_Hammer")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Earth_Shaker")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Enraged_Smash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Fierce_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Forceful_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Hammer_Bash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Heavy_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Irresistible_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Magehunters_Smash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mighty_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mokele_Smash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Overbearing_Smash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pulverizing_Smash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Renewing_Smash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Staggering_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Yeti_Smash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        # WARRIOR SWORDSMANSHIP
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Barbarous_Slice")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Crippling_Slash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dragon_Slash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Final_Thrust")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Galrath_Slash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Gash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasBleeding = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Hamstring")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Hundred_Blades")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Jaizhenju_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Knee_Cutter")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCrippled = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pure_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Quivering_Blade")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Savage_Slash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Seeking_Blade")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sever_Artery")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Silverwing_Slash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Standing_Slash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Steelfang_Slash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sun_and_Moon_Slash")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        # WARRIOR TACTICS
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Charge")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Fear_Me")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("None_Shall_Pass")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Retreat")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsAlive = False
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shields_Up")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("To_the_Limit")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IgnoreEffectCheck = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Victory_Is_Mine")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Watch_Yourself")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Auspicious_Parry")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Balanced_Stance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Bonettis_Defense")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Deadly_Riposte")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Defensive_Stance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Deflect_Arrows")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Desperation_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Disciplined_Stance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Drunken_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Gladiators_Defense")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Healing_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Protectors_Defense")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Riposte")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shield_Stance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shove")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soldiers_Defense")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soldiers_Speed")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.UniqueProperty = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soldiers_Stance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soldiers_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Steady_Stance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Thrill_of_Victory")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wary_Stance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        # WARRIOR NO ATTRIBUTE
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Coward")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("For_Great_Justice")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill
        skill.Conditions.IsOutOfCombat = False
        

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("On_Your_Knees")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Youre_All_Alone")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Distracting_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Distracting_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Flurry")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Frenzied_Defense")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Frenzy")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Grapple")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Skull_Crack")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Symbolic_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wild_Blow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        # RANGER EXPERTISE
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Archers_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Distracting_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dodge")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Escape")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Expert_Focus")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Experts_Dexterity")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glass_Arrows")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Infuriating_Heat")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lightning_Reflexes")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Marksmans_Wager")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Oath_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Point_Blank_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Practiced_Stance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Throw_Dirt")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Trappers_Focus")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Trappers_Speed")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Whirling_Defense")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Zojuns_Haste")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Zojuns_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        # RANGER BEAST MASTERY
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Bestial_Fury")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Bestial_Mauling")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Bestial_Pounce")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Brutal_Strike")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Call_of_Haste")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Call_of_Protection")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Charm_Animal")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Comfort_Animal")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.UniqueProperty = True
        skill.Conditions.LessLife = 0.50
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Companionship")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Disrupting_Lunge")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Edge_of_Extinction")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Energizing_Wind")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Enraged_Lunge")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Feral_Aggression")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Feral_Lunge")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ferocious_Strike")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Fertile_Season")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Heal_as_One")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Healing.value
        skill.unique_property = True
        skill.Conditions.LessLife = 0.7
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Hekets_Rampage")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lacerate")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Maiming_Strike")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Melandrus_Assault")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Otyughs_Cry")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Poisonous_Bite")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pounce")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Predators_Pounce")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Predatory_Bond")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Predatory_Season")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Primal_Echoes")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rampage_as_One")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Revive_Animal")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Run_as_One")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Savage_Pounce")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Scavenger_Strike")
        skill.SkillType = SkillType.PetAttack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Strike_as_One")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Symbiosis")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Symbiotic_Bond")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Pet.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Tigers_Fury")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Toxicity")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vipers_Nest")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        # RANGER MARKSMANSHIP
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Arcing_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Barrage")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Body_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Broad_Head_Arrow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Burning_Arrow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Concussion_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Crippling_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Crossfire")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Debilitating_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Determined_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Disrupting_Accuracy")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Disrupting_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Favorable_Winds")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Focused_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Hunters_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Keen_Arrow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Marauders_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Melandrus_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Needling_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Penetrating_Attack")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pin_Down")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Power_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Precision_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Prepared_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Punishing_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rapid_Fire")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Read_the_Wind")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Savage_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Screaming_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Seeking_Arrows")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sloth_Hunters_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsCasting = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Splinter_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sundering_Attack")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Volley")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        # RANGER WILDERNESS SURVIVAL
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Apply_Poison")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Barbed_Arrows")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Barbed_Trap")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Brambles")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Choking_Gas")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Conflagration")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dryders_Defenses")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dust_Trap")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Equinox")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Famine")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Flame_Trap")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Frozen_Soil")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Greater_Conflagration")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Healing_Spring")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ignite_Arrows")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Incendiary_Arrows")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Kindle_Arrows")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Melandrus_Arrows")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Melandrus_Resilience")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.UniqueProperty = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Muddy_Terrain")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Natural_Stride")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Natures_Renewal")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pestilence")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Piercing_Trap")
        skill.SkillType = SkillType.Preparation.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Poison_Arrow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Poison_Tip_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Quickening_Zephyr")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Quicksand")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Roaring_Winds")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Scavengers_Focus")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Serpents_Quickness")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Smoke_Trap")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Snare")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spike_Trap")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Storm_Chaser")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Tranquility")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Tripwire")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Troll_Unguent")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.65
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Winnowing")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Winter")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        # RANGER NO ATTRIBUTE
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Antidote_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Called_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dual_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Forked_Arrow")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Magebane_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Quick_Shot")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Storms_Embrace")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        # MONK DIVINE FAVOR
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blessed_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blessed_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.65
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blessed_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.IsOutOfCombat = True
        skill.Conditions.LessEnergy = 0.6
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Boon_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Contemplation_of_Purity")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Deny_Hexes")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Divine_Boon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Divine_Healing")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.8
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Earshot.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Divine_Intervention")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.35
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Divine_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Healers_Boon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Heavens_Delight")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Earshot.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Holy_Haste")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Peace_and_Harmony")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasCondition = True
        skill.Conditions.HasHex = True
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Release_Enchantments")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.HasEnchantment = True
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.SafeCompass.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Scribes_Insight")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Devotion")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Smiters_Boon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spell_Breaker")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spell_Shield")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Unyielding_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.UniqueProperty = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Watchful_Healing")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.8
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Watchful_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Withdraw_Hexes")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Cure_Hex")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dwaynas_Kiss")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.HasHex = True
        skill.Conditions.HasEnchantment = True
        skill.Conditions.UniqueProperty = True
        skill.Conditions.TargetingStrict = True
        skill.Conditions.LessLife = 0.7
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dwaynas_Sorrow")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.25
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ethereal_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Gift_of_Health")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.65
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glimmer_of_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.7
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Heal_Area")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Adjacent.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Heal_Other")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Heal_Party")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.SafeCompass.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Healers_Covenant")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Healing_Breeze")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.65
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Healing_Burst")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Healing_Hands")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.50
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Healing_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Healing_Ribbon")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Healing_Ring")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Adjacent.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Healing_Seed")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.5
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Adjacent.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Healing_Touch")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Healing_Whisper")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Infuse_Health")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.25
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Jameis_Gaze")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Kareis_Healing_Circle")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Adjacent.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Light_of_Deliverance")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.8
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.SafeCompass.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Live_Vicariously")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mending")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Orison_of_Healing")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.8
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Patient_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.7
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Renew_Life")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Restful_Breeze")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Restore_Life")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Resurrection_Chant")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Rejuvenation")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.OutOfCombat = False
        skill.Conditions.LessLife = 0.65
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spotless_Mind")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spotless_Soul")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Supportive_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vigorous_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Word_of_Healing")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Words_of_Comfort")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill
        #MONK PROTECTION PRAYERS
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aegis")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Air_of_Enchantment")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Amity")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aura_of_Faith")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aura_of_Stability")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Convert_Hexes")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dismiss_Condition")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Divert_Hexes")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Draw_Conditions")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Extinguish")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.LessLife = 0.75
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.SafeCompass.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Guardian")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Life_Attunement")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Life_Barrier")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Life_Bond")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Life_Sheath")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mark_of_Protection")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mend_Ailment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mend_Condition")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mending_Touch")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pacifism")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pensive_Guardian")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Protective_Bond")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Protective_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Purifying_Veil")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rebirth")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Restore_Condition")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Reversal_of_Fortune")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.8
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Reverse_Hex")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shield_Guardian")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Earshot.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shield_of_Absorption")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.6
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shield_of_Deflection")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shield_of_Regeneration")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shielding_Hands")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.4
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirit_Bond")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.6
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vital_Blessing")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Zealous_Benediction")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        #SMITHING PRAYERS

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Balthazars_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Balthazars_Pendulum")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Balthazars_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Bane_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAttacking = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Castigation_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAttacking = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Defenders_Zeal")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Holy_Strike")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Holy_Wrath")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Judges_Insight")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Judges_Intervention")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.25
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Kirins_Wrath")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ray_of_Judgment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Retribution")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Reversal_of_Damage")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.8
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Scourge_Enchantment")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Scourge_Healing")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Scourge_Sacrifice")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shield_of_Judgment")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Judgment")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Mystic_Wrath")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Rage")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Smite")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAttacking = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Smite_Condition")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Smite_Hex")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spear_of_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAttacking = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Stonesoul_Strike")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Strength_of_Honor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Symbol_of_Wrath")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Word_of_Censure")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.MoreLife = 0.33
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Zealots_Fire")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill
        #MONK NO ATTRIBUTE
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Empathic_Removal")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.HasHex = True
        skill.Conditions.UniqueProperty = True
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Essence_Bond")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Holy_Veil")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Light_of_Dwayna")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Martyr")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Purge_Conditions")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Purge_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.HasHex = True
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Remove_Hex")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Resurrect")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Removal")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasCondition = True
        skill.Conditions.HasHex = True
        skill.Conditions.HasEnchantment = True
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Succor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyCaster.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vengeance")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill
        #NECROMANCER SOUL REAPING
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Angorodons_Gaze")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Foul_Feast")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Condi_Cleanse.value
        skill.Conditions.HasCondition = True
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Hexers_Vigor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Icy_Veins")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Masochism")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Reapers_Mark")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Lost_Souls")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Sorrow")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wail_of_Doom")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        # NECROMANCER BLOOD MAGIC
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Awaken_the_Blood")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Barbed_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.SacrificeHealth = 0.3
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blood_Bond")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blood_Drinker")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blood_Renewal")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.SacrificeHealth = 0.25
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blood_Ritual")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.4
        skill.Conditions.SacrificeHealth = 0.4
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blood_is_Power")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.4
        skill.Conditions.SacrificeHealth = 0.5
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blood_of_the_Aggressor")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAttacking = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Cultists_Fervor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dark_Bond")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dark_Fury")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.SacrificeHealth = 0.4
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dark_Fury")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.SacrificeHealth = 0.3
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Demonic_Flesh")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Jaundiced_Gaze")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Life_Siphon")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Life_Transfer")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lifebane_Strike")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.MoreLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mark_of_Fury")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mark_of_Subversion")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Offering_of_Blood")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.SacrificeHealth = 0.4
        skill.Conditions.LessEnergy = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Oppressive_Gaze")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Order_of_Pain")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.SacrificeHealth = 0.4
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Order_of_the_Vampire")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.SacrificeHealth = 0.4
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ravenous_Gaze")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.SacrificeHealth = 0.3
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadow_Strike")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.MoreLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Agony")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.SacrificeHealth = 0.3
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Suffering")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soul_Leech")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spoil_Victor")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Strip_Enchantment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Touch_of_Agony")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.SacrificeHealth = 0.4
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Unholy_Feast")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vampiric_Bite")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vampiric_Gaze")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vampiric_Spirit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vampiric_Swarm")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vampiric_Touch")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wallows_Bite")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.SacrificeHealth = 0.3
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Well_of_Blood")
        skill.SkillType = SkillType.Well.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Well_of_Power")
        skill.SkillType = SkillType.Well.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill
        #NECROMANCER CURSES
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Atrophy")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Barbs")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Cacophony")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Chilblains")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Corrupt_Enchantment")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Defile_Defenses")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Defile_Enchantments")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Defile_Flesh")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.SacrificeHealth = 0.4
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Depravity")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Desecrate_Enchantments")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Enfeeble")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Enfeebling_Blood")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.SacrificeHealth = 0.4
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Enfeebling_Touch")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Envenom_Enchantments")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Faintheartedness")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Feast_of_Corruption")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Insidious_Parasite")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lingering_Curse")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Malaise")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mark_of_Pain")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Meekness")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.SacrificeHealth = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Order_of_Apostasy")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pain_of_Disenchantment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Parasitic_Bond")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Plague_Sending")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Plague_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Plague_Touch")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Poisoned_Heart")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Price_of_Failure")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Reckless_Haste")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rend_Enchantments")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rigor_Mortis")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rip_Enchantment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadow_of_Fear")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shivers_of_Dread")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soul_Barbs")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soul_Bind")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spinal_Shivers")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spiteful_Spirit")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Suffering")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ulcerous_Lungs")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vocal_Minority")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Weaken_Armor")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Weaken_Knees")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Well_of_Darkness")
        skill.SkillType = SkillType.Well.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Well_of_Ruin")
        skill.SkillType = SkillType.Well.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Well_of_Silence")
        skill.SkillType = SkillType.Well.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Well_of_Weariness")
        skill.SkillType = SkillType.Well.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wither")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        # NECROMANCER DEATH MAGIC
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Animate_Bone_Fiend")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Corpse.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Animate_Bone_Horror")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Corpse.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Animate_Bone_Minions")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Corpse.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Animate_Flesh_Golem")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Corpse.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAlive = False
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Animate_Shambling_Horror")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Corpse.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Animate_Vampiric_Horror")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Corpse.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aura_of_the_Lich")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Bitter_Chill")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blood_of_the_Master")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.SacrificeHealth = 0.4
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Consume_Corpse")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Corpse.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Contagion")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dark_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Death_Nova")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Minion.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.35
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Deathly_Chill")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.MoreLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Deathly_Swarm")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Discord")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        skill.Conditions.HasHex = True
        skill.Conditions.HasEnchantment = True
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Feast_for_the_Dead")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Minion.value
        skill.Nature = SkillNature.Healing.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Fetid_Ground")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Infuse_Condition")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Jagged_Bones")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Minion.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Malign_Intervention")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Necrotic_Traversal")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Corpse.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Order_of_Undeath")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Putrid_Bile")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Putrid_Explosion")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Corpse.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Putrid_Flesh")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Minion.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rising_Bile")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rotting_Flesh")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soul_Feast")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Corpse.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Tainted_Flesh")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Taste_of_Death")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Minion.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.4
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Taste_of_Pain")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Toxic_Chill")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasHex = True
        skill.Conditions.HasEnchantment = True
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Veratas_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.SacrificeHealth = 0.5
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Veratas_Gaze")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Minion.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Veratas_Sacrifice")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.SacrificeHealth = 0.4
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vile_Miasma")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vile_Touch")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Virulence")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Well_of_Suffering")
        skill.SkillType = SkillType.Well.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Well_of_the_Profane")
        skill.SkillType = SkillType.Well.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Withering_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill
        #NECROMANCER NO ATTRIBUTE
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Gaze_of_Contempt")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        skill.Conditions.MoreLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Grenths_Balance")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.5
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill
        #MESMER FAST CASTING

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Arcane_Languor")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Keystone_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mantra_of_Recovery")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Persistence_of_Memory")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Power_Return")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Psychic_Instability")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Stolen_Speed")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Symbolic_Celerity")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill  
        
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Symbolic_Posture")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Symbols_of_Inspiration")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill
        #MESMER DOMINATION
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aneurysm")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Arcane_Larceny")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Arcane_Thievery")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Backfire")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blackout")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Chaos_Storm")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Complicate")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Cry_of_Frustration")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Diversion")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Empathy")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Enchanters_Conundrum")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Energy_Burn")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Energy_Surge")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Guilt")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Hex_Breaker")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Hex_Eater_Vortex")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ignorance")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mind_Wrack")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mistrust")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Overload")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Panic")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Power_Block")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Power_Flux")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Power_Leak")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Power_Lock")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Power_Spike")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Price_of_Pride")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Psychic_Distraction")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shame")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shatter_Delusions")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shatter_Enchantment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shatter_Hex")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Disruption")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Distraction")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Weariness")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Simple_Thievery")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spiritual_Pain")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Unnatural_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Visions_of_Regret")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wastrels_Demise")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wastrels_Worry")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill
        #MESMER ILLUSION MAGIC
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Accumulated_Pain")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Air_of_Disenchantment")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ancestors_Visage")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Arcane_Conundrum")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Calculated_Risk")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Clumsiness")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Confusing_Images")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Conjure_Nightmare")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Conjure_Phantasm")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Crippling_Anguish")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Distortion")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ethereal_Burden")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Fevered_Dreams")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Fragility")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Frustration")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Illusion_of_Haste")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Illusion_of_Pain")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Illusion_of_Weakness")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Illusionary_Weaponry")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Images_of_Remorse")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Imagined_Burden")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ineptitude")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Kitahs_Burden")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Migraine")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Phantom_Pain")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Recurring_Insecurity")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shared_Burden")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shrinking_Armor")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Clumsiness")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsAttacking = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Illusions")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soothing_Images")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sum_of_All_Fears")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sympathetic_Visage")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wandering_Eye")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill
        #MESMER INSPIRATION MAGIC
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Auspicious_Incantation")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessEnergy = 0.7
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Channeling")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Discharge_Enchantment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Drain_Delusions")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasHex = True
        skill.Conditions.LessEnergy = 0.7
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Drain_Enchantment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Elemental_Resistance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Energy_Drain")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessEnergy = 0.5
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Energy_Tap")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessEnergy = 0.7
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ether_Feast")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Healing.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ether_Lord")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessEnergy = 0.2
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ether_Phantom")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ether_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.15
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Extend_Conditions")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Feedback")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Hex_Eater_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Inspired_Enchantment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Inspired_Hex")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Leech_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lyssas_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mantra_of_Concentration")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mantra_of_Earth")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mantra_of_Flame")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mantra_of_Frost")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mantra_of_Inscriptions")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mantra_of_Lightning")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mantra_of_Persistence")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mantra_of_Recall")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mantra_of_Resolve")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mantra_of_Signets")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Physical_Resistance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Power_Drain")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Power_Leech")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Revealed_Enchantment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Revealed_Hex")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Hex_Removal.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Humility")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Recall")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirit_Shackles")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirit_of_Failure")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Tease")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Waste_Not_Want_Not")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.75
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill
        #MESMER NO ATTRIBUTE
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Arcane_Echo")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Arcane_Mimicry")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Echo")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Epidemic")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Expel_Hexes")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Hypochondria")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lyssas_Balance")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mirror_of_Disenchantment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shatter_Storm")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Disenchantment")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        skill.Conditions.LessEnergy = 0.3
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Midnight")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Web_of_Disruption")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        #ELEMENTALIST ENERGY STORAGE
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aura_of_Restoration")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Elemental_Attunement")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Energy_Blast")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Energy_Boon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ether_Prism")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ether_Prodigy")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ether_Renewal")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Interrupt.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glyph_of_Energy")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glyph_of_Lesser_Energy")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glyph_of_Restoration")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Master_of_Magic")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill
        #ELEMENTALIST AIR MAGIC

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Air_Attunement")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Arc_Lightning")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blinding_Flash")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blinding_Surge")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsAttacking = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Chain_Lightning")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Chilling_Winds")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Conjure_Lightning")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Enervating_Charge")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Gale")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glimmering_Mark")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glyph_of_Swiftness")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Gust")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Invoke_Lightning")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lightning_Bolt")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lightning_Hammer")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lightning_Javelin")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsAttacking = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lightning_Orb")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lightning_Strike")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lightning_Surge")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lightning_Touch")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mind_Shock")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ride_the_Lightning")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shell_Shock")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shock")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shock_Arrow")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Storm_Djinns_Haste")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Teinais_Wind")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Thunderclap")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Whirlwind")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Windborne_Speed")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill
        #ELEMENTALIST EARTH MAGIC

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aftershock")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Armor_of_Earth")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ash_Blast")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Churning_Earth")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Crystal_Wave")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dragons_Stomp")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Earth_Attunement")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Earthen_Shackles")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Earthquake")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ebon_Hawk")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Eruption")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glowstone")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Grasping_Earth")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Iron_Mist")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Kinetic_Armor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Magnetic_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Magnetic_Surge")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Obsidian_Flame")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Obsidian_Flesh")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sandstorm")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shockwave")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sliver_Armor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Stone_Daggers")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Stone_Sheath")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Stone_Striker")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Stoneflesh_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Stoning")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Teinais_Crystals")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Unsteady_Ground")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ward_Against_Elements")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ward_Against_Foes")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ward_Against_Melee")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ward_of_Stability")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ward_of_Weakness")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill
        #ELEMENTALIST FIRE MAGIC

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Bed_of_Coals")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Breath_of_Fire")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Burning_Speed")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Conjure_Flame")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Double_Dragon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Elemental_Flame")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Fire_Attunement")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Fire_Storm")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Fireball")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Flame_Burst")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Flame_Djinns_Haste")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Flare")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glowing_Gaze")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glyph_of_Immolation")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Immolate")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Incendiary_Bonds")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Inferno")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lava_Arrows")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lava_Font")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Liquid_Flame")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mark_of_Rodgort")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Meteor")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Meteor_Shower")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mind_Blast")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mind_Burn")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Phoenix")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rodgorts_Invocation")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Savannah_Heat")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Searing_Flames")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Searing_Heat")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Smoldering_Embers")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Star_Burst")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Teinais_Heat")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        #ELEMENTALIST WATER MAGIC

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Armor_of_Frost")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Armor_of_Mist")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blurred_Vision")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Conjure_Frost")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Deep_Freeze")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Freezing_Gust")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Frigid_Armor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Frozen_Burst")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glowing_Ice")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ice_Prison")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ice_Spear")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ice_Spikes")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Icy_Prism")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Icy_Shackles")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Maelstrom")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mind_Freeze")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mirror_of_Ice")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mist_Form")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rust")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shard_Storm")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shatterstone")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Slippery_Ground")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Steam")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Swirling_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Teinais_Prison")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vapor_Blade")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasEnchantment = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ward_Against_Harm")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Water_Attunement")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Water_Trident")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Winters_Embrace")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        #ELEMENTALIST NO ATTRIBUTE
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glyph_of_Concentration")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glyph_of_Elemental_Power")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glyph_of_Essence")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glyph_of_Renewal")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glyph_of_Sacrifice")
        skill.SkillType = SkillType.Glyph.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Second_Wind")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        #ASSASSIN CRITICAL STRIKES
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Assassins_Remedy")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Black_Lotus_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Critical_Defenses")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Critical_Eye")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Critical_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dark_Apostasy")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Deadly_Haste")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Locusts_Fury")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Malicious_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Palm_Strike")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Seeping_Wound")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sharpen_Daggers")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shattering_Assault")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Twisting_Fangs")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Unsuspecting_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Way_of_the_Assassin")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Way_of_the_Master")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        #ASSASSIN DAGGER MASTERY
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Black_Mantis_Thrust")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Black_Spider_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blades_of_Steel")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Desperate_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.8
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Disrupting_Stab")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Exhausting_Assault")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Falling_Lotus_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Falling_Spider")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Flashing_Blades")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Fox_Fangs")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Foxs_Promise")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Golden_Fang_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Golden_Fox_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Golden_Lotus_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Golden_Phoenix_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Golden_Skull_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Horns_of_the_Ox")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Jagged_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Jungle_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Leaping_Mantis_Sting")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lotus_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Moebius_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Nine_Tail_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Repeating_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Temple_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Trampling_Ox")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCrippled = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wild_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        #ASSASSIN DEADLY ARTS
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Assassins_Promise")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Augury_of_Death")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Crippling_Dagger")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dancing_Daggers")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dark_Prison")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Deadly_Paradox")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Disrupting_Dagger")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Enduring_Toxin")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Entangling_Asp")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Expose_Defenses")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Expunge_Enchantments")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Impale")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Iron_Palm")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        skill.Conditions.HasHex = True
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mantis_Touch")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mark_of_Death")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mark_of_Insecurity")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sadists_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Scorpion_Wire")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadow_Fang")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadow_Prison")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shameful_Fear")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shroud_of_Silence")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Deadly_Corruption")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Shadows")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Toxic_Shock")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasPoison = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Siphon_Speed")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Siphon_Strength")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vampiric_Assault")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Way_of_the_Empty_Palm")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        #ASSASSIN SHADOW ARTS
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Beguiling_Haze")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blinding_Powder")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Caltrops")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dark_Escape")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Deaths_Charge")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Deaths_Retreat")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Feigned_Neutrality")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Heart_of_Shadow")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Healing.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Hidden_Caltrops")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mirrored_Stance")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Return")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadow_Form")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadow_Refuge")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadow_Shroud")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadow_of_Haste")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadowy_Burden")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shroud_of_Distress")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.5
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Smoke_Powder_Defense")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Unseen_Fury")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vipers_Defense")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Way_of_Perfection")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Way_of_the_Fox")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Way_of_the_Lotus")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        #ASSASSIN NO ATTRIBUTE

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Assault_Enchantments")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aura_of_Displacement")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dash")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lift_Enchantment")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mark_of_Instability")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Recall")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.UniqueProperty = True
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadow_Meld")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.UniqueProperty = True
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadow_Walk")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Malice")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Twilight")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Enchantment_Removal.value
        skill.Conditions.HasEnchantment = True
        skill.Conditions.HasHex = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirit_Walk")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Spirit.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Swap")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Spirit.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wastrels_Collapse")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsCasting = False
        self.skill_data[skill.SkillID] = skill

        #RITUALIST SPAWNING POWER
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Anguished_Was_Lingwah")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Attuned_Was_Songkai")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Boon_of_Creation")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Consume_Soul")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Doom")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Empowerment")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Energetic_Was_Lee_Sa")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Explosive_Growth")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Feast_of_Souls")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Nearby.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ghostly_Haste")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Reclaim_Essence")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.3
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Renewing_Memories")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsHoldingItem = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ritual_Lord")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.SacrificeHealth = 0.2
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rupture_Soul")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Spirit.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sight_Beyond_Sight")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Binding")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Spirit.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.SacrificeHealth = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Creation")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.75
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soul_Twisting")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirit_Channeling")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.75
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirit_to_Flesh")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Spirit.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.45
        skill.Conditions.IsPartyWide = True
        skill.Conditions.UniqueProperty = True
        skill.Conditions.PartyWideArea = Range.Nearby.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirits_Gift")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirits_Strength")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Weapon_of_Renewal")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wielders_Remedy")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wielders_Zeal")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        #RITUALIST CHANNELLING MAGIC

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Agony")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ancestors_Rage")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Bloodsong")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Caretakers_Charge")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsHoldingItem = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Channeled_Strike")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsHoldingItem = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Clamor_of_Souls")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessEnergy = 0.75
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Cruel_Was_Daoshen")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Destruction")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Destructive_Was_Glaive")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Essence_Strike")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Gaze_from_Beyond")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Gaze_of_Fury")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Spirit.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Grasping_Was_Kuurong")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lamentation")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Nightmare_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Offering_of_Spirit")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.75
        skill.Conditions.SacrificeHealth = 0.35
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Painful_Bond")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Renewing_Surge")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Spirits")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirit_Boon_Strike")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirit_Burn")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirit_Rift")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirit_Siphon")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Splinter_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wailing_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Warmongers_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Weapon_of_Aggression")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Weapon_of_Fury")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wielders_Strike")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        #RITUALIST COMMUNING
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Anguish")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Armor_of_Unfeeling")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Binding_Chains")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Brutal_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasEnchantment = True
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Disenchantment")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Displacement")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dissonance")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dulled_Weapon")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.EnemyMartial.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Earthbind")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ghostly_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Guided_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mighty_Was_Vorizun")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pain")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Restoration")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadowsong")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shelter")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Ghostly_Might")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soothing")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sundering_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Union")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vital_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wanderlust")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Weapon_of_Quickening")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyCaster.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        #RITUALIST RESTORATION MAGIC

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blind_Was_Mingson")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Death_Pact_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Defiant_Was_Xinrae")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Flesh_of_My_Flesh")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Generous_Was_Tsungrai")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.SacrificeHealth = 0.4
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ghostmirror_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Life")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.OutOfCombat = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lively_Was_Naomei")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mend_Body_and_Soul")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.70
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mending_Grip")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.HasWeaponSpell = True
        skill.Conditions.LessLife = 0.8
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Preservation")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Protective_Was_Kaolai")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pure_Was_Li_Ming")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Recovery")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Recuperation")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        self.skill_data[skill.SkillID] = skill
 
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rejuvenation")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Resilient_Was_Xiko")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Resilient_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyCaster.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasHex = True
        skill.Conditions.HasCondition = True
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soothing_Memories")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirit_Light")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        skill.Conditions.SacrificeHealth = 0.3
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirit_Light_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spirit_Transfer")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.8
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spiritleech_Aura")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Tranquil_Was_Tanasen")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vengeful_Was_Khanhei")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vengeful_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vocal_Was_Sogolon")
        skill.SkillType = SkillType.ItemSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Weapon_of_Remedy")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Weapon_of_Shadow")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Weapon_of_Warding")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wielders_Boon")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.HasWeaponSpell = True
        skill.Conditions.LessLife = 0.7
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Xinraes_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        #RITUALIST NO ATTRIBUTE
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Draw_Spirit")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Spirit.value
        skill.Nature = SkillNature.Neutral.value
        self.skill_data[skill.SkillID] = skill

        #PARAGON LEADERSHIP
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lead_the_Way")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Make_Your_Time")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Theyre_on_Fire")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aggressive_Refrain")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Angelic_Bond")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.25
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Angelic_Protection")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Anthem_of_Flame")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Anthem_of_Fury")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Awe")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsKnockedDown = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blazing_Finale")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Burning_Refrain")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Burning_Shield")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Defensive_Anthem")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Enduring_Harmony")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Focused_Anger")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Glowing_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Hasty_Refrain")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Leaders_Comfort")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.6
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Natural_Temper")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasEnchantment = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Return")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soldiers_Fury")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spear_Swipe")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        #PARAGON COMMAND
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Brace_Yourself")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Cant_Touch_This")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Fall_Back")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Find_Their_Weakness")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Go_for_the_Eyes")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Help_Me")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Incoming")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Make_Haste")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Never_Give_Up")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.75
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Never_Surrender")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.IsPartyWide = True
        skill.Conditions.LessLife = 0.75
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Stand_Your_Ground")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("We_Shall_Return")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Anthem_of_Disruption")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Anthem_of_Envy")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Anthem_of_Guidance")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Anthem_of_Weariness")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Bladeturn_Refrain")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Crippling_Anthem")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Godspeed")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasEnchantment = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        #PARAGON MOTIVATION
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Its_Just_a_Flesh_Wound")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasCondition = False
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("The_Power_Is_Yours")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.EnergyBuff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aria_of_Restoration")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aria_of_Zeal")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ballad_of_Restoration")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Chorus_of_Restoration")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Energizing_Chorus")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Energizing_Finale")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Finale_of_Restoration")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Inspirational_Speech")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Leaders_Zeal")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.EnergyBuff.value
        skill.Conditions.LessEnergy = 0.75
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lyric_of_Purification")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lyric_of_Zeal")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mending_Refrain")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Purifying_Finale")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Synergy")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Song_of_Power")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Song_of_Purification")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Song_of_Restoration")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.Earshot.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Zealous_Anthem")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        #PARAGON SPEAR MASTERY
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Barbed_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Blazing_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Chest_Thumper")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Cruel_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Disrupting_Throw")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Harriers_Toss")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.IsMoving = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Holy_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Maiming_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasBleeding = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Merciless_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mighty_Throw")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Slayers_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spear_of_Lightning")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spear_of_Redemption")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Stunning_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.EnemyCaster.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Swift_Javelin")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Unblockable_Throw")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wearying_Spear")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wild_Throw")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        #PARAGON NO ATTRIBUTE
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Cautery_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Hexbreaker_Aria")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Remedy_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasCondition = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Aggression")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Song_of_Concentration")
        skill.SkillType = SkillType.Chant.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        #DERVISH MYSTICISM
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Arcane_Zeal")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aura_Slicer")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Avatar_of_Balthazar")
        skill.SkillType = SkillType.Form.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Avatar_of_Dwayna")
        skill.SkillType = SkillType.Form.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Avatar_of_Grenth")
        skill.SkillType = SkillType.Form.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Avatar_of_Lyssa")
        skill.SkillType = SkillType.Form.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Avatar_of_Melandru")
        skill.SkillType = SkillType.Form.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Balthazars_Rage")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Banishing_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Eremites_Zeal")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Extend_Enchantments")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Faithful_Intervention")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Heart_of_Fury")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Heart_of_Holy_Flame")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Imbue_Health")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.50
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Intimidating_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Meditation")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mystic_Corruption")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasEnchantment = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mystic_Sweep")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mystic_Vigor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pious_Fury")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pious_Haste")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pious_Renewal")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rending_Touch")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vow_of_Silence")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Watchful_Intervention")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.LessLife = 0.35
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Zealous_Renewal")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        #DERVISH EARTH PRAYERS
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Armor_of_Sanctity")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aura_of_Thorns")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Conviction")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dust_Cloak")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ebon_Dust_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Fleeting_Stability")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mirage_Cloak")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mystic_Regeneration")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.HasEnchantment = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mystic_Sandstorm")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pious_Concentration")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sand_Shards")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shield_of_Force")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Pious_Light")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.65
        skill.Conditions.HasDervishEnchantment = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Staggering_Force")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Veil_of_Thorns")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vital_Boon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vow_of_Strength")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        #DERVISH SCYTHE MASTERY
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Chilling_Victory")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Crippling_Sweep")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Crippling_Victory")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Eremites_Attack")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Farmers_Scythe")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Irresistible_Sweep")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lyssas_Assault")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pious_Assault")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Radiant_Scythe")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Reap_Impurities")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Reapers_Sweep")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rending_Sweep")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Twin_Moon_Sweep")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Victorious_Sweep")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wearying_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Wounding_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Zealous_Sweep")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        #DERVISH WIND PRAYERS
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Attackers_Insight")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dwaynas_Touch")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.HasDervishEnchantment = True
        skill.Conditions.LessLife = 0.70
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Featherfoot_Grace")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Grenths_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Grenths_Fingers")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Grenths_Grasp")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Guiding_Hands")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Harriers_Grasp")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mystic_Healing")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.75
        skill.Conditions.IsPartyWide = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mystic_Twister")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Natural_Healing")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.LessLife = 0.60
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Onslaught")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Rending_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Mystic_Speed")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Pious_Restraint")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Test_of_Faith")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vow_of_Piety")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Whirling_Charge")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Winds_of_Disenchantment")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Zealous_Vow")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        #DERVISH NO ATTRIBUTE
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Enchanted_Haste")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        #CORE NO ATTRIBUTE
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Resurrection_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        #PVE-ONLY ANNIVERSARY
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Together_as_one")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Heroic_Refrain")
        skill.SkillType = SkillType.EchoRefrain.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Judgement_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Over_the_Limit")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Seven_Weapon_Stance")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadow_Theft")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Soul_Taker")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Time_Ward")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Interrupt.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vow_of_Revolution")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Weapons_of_Three_Forges")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        #PVE-ONLY KURZICK-LUXON
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Save_Yourselves_kurzick")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Save_Yourselves_luxon")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aura_of_Holy_Might_kurzick")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Aura_of_Holy_Might_luxon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Elemental_Lord_kurzick")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Elemental_Lord_luxon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ether_Nightmare_luxon")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ether_Nightmare_kurzick")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Selfless_Spirit_kurzick")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Selfless_Spirit_luxon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadow_Sanctuary_kurzick")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Shadow_Sanctuary_luxon")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Corruption_kurzick")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Corruption_luxon")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spear_of_Fury_kurzick")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Spear_of_Fury_luxon")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Summon_Spirits_kurzick")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Neutral.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Summon_Spirits_luxon")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Neutral.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Triple_Shot_kurzick")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Triple_Shot_luxon")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        #PVE-ONLY SUNSPEAR
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Theres_Nothing_to_Fear")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Critical_Agility")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Cry_of_Pain")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Interrupt.value
        skill.Conditions.IsCasting = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Eternal_Aura")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Intensity")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Necrosis")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasCondition = True
        skill.Conditions.HasHex = True
        skill.Conditions.UniqueProperty = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Never_Rampage_Alone")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Seed_of_Life")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill.Conditions.LessLife = 0.75
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.SafeCompass.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sunspear_Rebirth_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Vampirism")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Whirlwind_Attack")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        #PVE-ONLY LIGHTBRINGER
        # Lightbringer Skills
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lightbringer_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Lightbringers_Gaze")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        # PvE-Only Asura Skills
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Air_of_Superiority")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Asuran_Scan")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mental_Block")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Mindbender")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Pain_Inverter")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Radiation_Field")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Smooth_Criminal")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Summon_Ice_Imp")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Summon_Mursaat")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Summon_Naga_Shaman")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Summon_Ruby_Djinn")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Technobabble")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill
        
        # PvE-Only Deldrimor Skills
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("By_Urals_Hammer")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.DeadAlly.value
        skill.Nature = SkillNature.Resurrection.value
        skill.Conditions.IsAlive = False
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dont_Trip")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Alkars_Alchemical_Acid")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Black_Powder_Mine")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Brawling_Headbutt")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Breath_of_the_Great_Dwarf")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.HasBurning = True
        skill.Conditions.LessLife = 0.75
        skill.Conditions.IsPartyWide = True
        skill.Conditions.PartyWideArea = Range.SafeCompass.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Drunken_Master")
        skill.SkillType = SkillType.Stance.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dwarven_Stability")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ear_Bite")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Great_Dwarf_Armor")
        skill.SkillType = SkillType.Enchantment.value
        skill.TargetAllegiance = Skilltarget.Ally.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Great_Dwarf_Weapon")
        skill.SkillType = SkillType.WeaponSpell.value
        skill.TargetAllegiance = Skilltarget.AllyMartial.value
        skill.Nature = SkillNature.Buff.value
        skill.Conditions.TargetingStrict = True
        skill.Conditions.IsOutOfCombat = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Light_of_Deldrimor")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Low_Blow")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Snow_Storm")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        # PVE-ONLY EBON VANGUARD
        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Deft_Strike")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ebon_Battle_Standard_of_Courage")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ebon_Battle_Standard_of_Honor")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ebon_Battle_Standard_of_Wisdom")
        skill.SkillType = SkillType.Ward.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ebon_Escape")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.OtherAlly.value
        skill.Nature = SkillNature.Healing.value
        skill.Conditions.TargetingStrict = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ebon_Vanguard_Sniper_Support")
        skill.SkillType = SkillType.Spell.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Signet_of_Infection")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.HasBleeding = True
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Sneak_Attack")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Tryptophan_Signet")
        skill.SkillType = SkillType.Signet.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Weakness_Trap")
        skill.SkillType = SkillType.Trap.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Winds")
        skill.SkillType = SkillType.Ritual.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        #PVE-ONLY NORN

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Dodge_This")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Finish_Him")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        skill.Conditions.LessLife = 0.5
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("I_Am_Unstoppable")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("I_Am_the_Strongest")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("You_Are_All_Weaklings")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("You_Move_Like_a_Dwarf")
        skill.SkillType = SkillType.Shout.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("A_Touch_of_Guile")
        skill.SkillType = SkillType.Hex.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Club_of_a_Thousand_Bears")
        skill.SkillType = SkillType.Attack.value
        skill.TargetAllegiance = Skilltarget.Enemy.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Feel_No_Pain")
        skill.SkillType = SkillType.Skill.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Buff.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Raven_Blessing")
        skill.SkillType = SkillType.Form.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Ursan_Blessing")
        skill.SkillType = SkillType.Form.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill

        skill = self.CustomSkill()
        skill.SkillID = Skill.GetID("Volfen_Blessing")
        skill.SkillType = SkillType.Form.value
        skill.TargetAllegiance = Skilltarget.Self.value
        skill.Nature = SkillNature.Offensive.value
        self.skill_data[skill.SkillID] = skill
