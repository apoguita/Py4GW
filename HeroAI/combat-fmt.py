from Py4GWCoreLib import *
from Py4GW_DEMO import ShowSkillDataWindow
from .custom_skill import *
from .types import *
from .utils import *
from .targetting import *

MAX_SKILLS = 8
custom_skill_data_handler = CustomSkillClass()

class CombatClass:
    global MAX_SKILLS, custom_skill_data_handler

    class SkillData:
        def __init__(self, slot):
            self.skill_id = SkillBar.GetSkillIDBySlot(slot)  # Fetch the skill ID for the slot
            self.skillbar_data = SkillBar.GetSkillData(slot)  # Fetch additional data from the skill bar
            self.custom_skill_data = custom_skill_data_handler.get_skill(self.skill_id)  # Retrieve custom skill data

    def __init__(self):
        """
        Initializes the CombatClass with an empty skill set and order.
        """
        self.skills: list[CombatClass.SkillData] = [None] * MAX_SKILLS
        self.skill_order = [0] * MAX_SKILLS
        self.skill_pointer = 0
        self.in_casting_routine = False

    def PrioritizeSkills(self):
        """
        Create a priority-based skill execution order.
        """
        #initialize skillbar
        for i in range(MAX_SKILLS):
            self.skills[i] = self.SkillData(i + 1)


        # Initialize the pointer and tracking list
        ptr = 0
        ptr_chk = [False] * MAX_SKILLS

        for i in range(MAX_SKILLS):
            skill = self.skills[i]
            if not ptr_chk[i] and skill.custom_skill_data.Nature == SkillNature.Interrupt.value:
                self.skill_order[ptr] = i
                ptr_chk[i] = True
                ptr += 1


        priorities = [
            SkillNature.Interrupt,
            SkillNature.Enchantment_Removal,
            SkillNature.Healing,
            SkillNature.Hex_Removal,
            SkillNature.Condi_Cleanse,
            SkillNature.EnergyBuff,
            SkillNature.Resurrection,
            #SkillNature.Buff
        ]

        for priority in priorities:
            for i in range(MAX_SKILLS):
                skill = self.skills[i]
                if not ptr_chk[i] and skill.custom_skill_data.Nature == priority.value:
                    self.skill_order[ptr] = i
                    ptr_chk[i] = True
                    ptr += 1
        
        skill_types = [
            SkillType.Form,
            SkillType.Enchantment,
            SkillType.EchoRefrain,
            SkillType.WeaponSpell,
            SkillType.Chant,
            SkillType.Preparation,
            SkillType.Ritual,
            SkillType.Ward,
            SkillType.Hex,
            SkillType.Trap,
            SkillType.Stance,
            SkillType.Shout,
            SkillType.Glyph,
            SkillType.Signet
        ]

        for skill_type in skill_types:
            for i in range(MAX_SKILLS):
                skill = self.skills[i]
                if not ptr_chk[i] and skill.custom_skill_data.SkillType == skill_type.value:
                    self.skill_order[ptr] = i
                    ptr_chk[i] = True
                    ptr += 1

        for skill_type in skill_types:
            for i in range(MAX_SKILLS):
                skill = self.skills[i]
                skill_type_id, _ = Skill.GetType(skill.skill_id)
                if not ptr_chk[i] and skill_type_id == skill_type.value:
                    self.skill_order[ptr] = i
                    ptr_chk[i] = True
                    ptr += 1

        for i in range(MAX_SKILLS):
            skill = self.skills[i]
            if not ptr_chk[i] and skill.custom_skill_data.Nature ==  SkillNature.Buff.value:
                self.skill_order[ptr] = i
                ptr_chk[i] = True
                ptr += 1


        combos = [3, 2, 1]  # Dual attack, off-hand attack, lead attack
        for combo in combos:
            for i in range(MAX_SKILLS):
                skill = self.skills[i]
                if not ptr_chk[i] and Skill.Data.GetCombo(skill.skill_id) == combo:
                    self.skill_order[ptr] = i
                    ptr_chk[i] = True
                    ptr += 1

        # Fill in remaining unprioritized skills
        for i in range(MAX_SKILLS):
            if not ptr_chk[i]:
                self.skill_order[ptr] = i
                ptr_chk[i] = True
                ptr += 1

        

    def GetOrderedSkill(self, index):
        return self.skills[self.skill_order[index]]

    def AdvanceSkillPointer(self):
        self.skill_pointer += 1
        if self.skill_pointer >= MAX_SKILLS:
            self.skill_pointer = 0

    def IsSkillReady(self, slot):
        if self.skills[slot].skill_id == 0:
            return False
        if Skill.Data.GetRecharge(self.skills[slot].skill_id) != 0:
            return False
        return True
        
    def InCastingRoutine(self):
        return self.in_casting_routine

    def GetAppropiateTarget(self, slot):
        v_target = 0

        party_number = Party.GetOwnPartyNumber()
        if not IsTargettingEnabled(party_number):
            return Player.GetTargetID()

        targetting_strict = self.skills[slot].custom_skill_data.TargetingStrict
        target_alliegance = self.skills[slot].custom_skill_data.TargetAllegiance

        if target_alliegance == Skilltarget.Enemy.value:
            v_target = GetPartyTarget()
            if v_target == 0:
                v_target = TargetNearestEnemy()
        elif target_alliegance == Skilltarget.EnemyCaster.value:
            v_target = TargetNearestEnemyCaster()
            if v_target == 0 and not targetting_strict:
                v_target = TargetNearestEnemy()
        elif target_alliegance == Skilltarget.EnemyMartial.value:
            v_target = TargetNearestEnemyMartial()
            if v_target == 0 and not targetting_strict:
                v_target = TargetNearestEnemy()
        elif target_alliegance == Skilltarget.EnemyMartialMelee.value:
            v_target = TargetNearestEnemyMelee()
            if v_target == 0 and not targetting_strict:
                v_target = TargetNearestEnemy()
        elif target_alliegance == Skilltarget.AllyMartialRanged.value:
            v_target = TargetNearestEnemyRanged()
            if v_target == 0 and not targetting_strict:
                v_target = TargetNearestEnemy()
        elif target_alliegance == Skilltarget.Ally.value:
            v_target = TargetLowestAlly()
        elif target_alliegance == Skilltarget.AllyCaster.value:
            v_target = TargetLowestAllyCaster()
            if v_target == 0 and not targetting_strict:
                v_target = TargetLowestAlly()
        elif target_alliegance == Skilltarget.AllyMartial.value:
            v_target = TargetLowestAllyMartial()
            if v_target == 0 and not targetting_strict:
                v_target = TargetLowestAlly()
        elif target_alliegance == Skilltarget.AllyMartialMelee.value:
            v_target = TargetLowestAllyMelee()
            if v_target == 0 and not targetting_strict:
                v_target = TargetLowestAlly()
        elif target_alliegance == Skilltarget.AllyMartialRanged.value:
            v_target = TargetLowestAllyRanged()
            if v_target == 0 and not targetting_strict:
                v_target = TargetLowestAlly()
        elif target_alliegance == Skilltarget.OtherAlly.value:
            if self.skills[slot].custom_skill_data.Nature == SkillNature.EnergyBuff.value:
                v_target = TargetLowestAllyEnergy(other_ally=True)
            else:
                v_target = TargetLowestAlly(other_ally=True)
        elif target_alliegance == Skilltarget.Self.value:
            v_target = Player.GetAgentID()
        elif target_alliegance == Skilltarget.DeadAlly.value:
            v_target = TargetDeadAllyInAggro()
        elif target_alliegance == Skilltarget.Spirit.value:
            v_target = TargetNearestSpirit()
        elif target_alliegance == Skilltarget.Minion.value:
            v_target = TargetLowestMinion()
        elif target_alliegance == Skilltarget.Corpse.value:
            v_target = TargetNearestCorpse()
        else:
            v_target = GetPartyTarget()
            if v_target == 0:
                v_target = TargetNearestEnemy()



    def IsReadyToCast(self, slot):
        is_casting = Agent.IsCasting(Player.GetAgentID())
        no_skill = self.skills[slot].skill_id == 0
        skill_recharging = Skill.Data.GetRecharge(self.skills[slot].skill_id) != 0
        current_energy = Agent.GetEnergy(Player.GetAgentID()) * Agent.GetMaxEnergy(Player.GetAgentID())
        not_enough_energy = current_energy < Skill.Data.GetEnergyCost(self.skills[slot].skill_id)
        current_hp = Agent.GetHealth( Player.GetAgentID())
        target_hp = self.skills[slot].custom_skill_data.SacrificeHealth
        helth_cost = Skill.Data.GetHealthCost(self.skills[slot].skill_id)
        not_enough_hp = (current_hp < target_hp) and helth_cost > 0
        enough_adrenaline = (Skill.Data.GetAdrenaline(self.skills[slot].skill_id) > 0) and (self.skills[slot].skillbar_data.adrenaline_a >= Skill.Data.GetAdrenaline(self.skills[slot].skill_id))
        current_overcast = Agent.GetOvercast(Player.GetAgentID())
        overcast_target = self.skills[slot].custom_skill_data.Overcast
        skill_overcast = Skill.Data.GetOvercast(self.skills[slot].skill_id)
        can_overcast = (current_overcast >= overcast_target) and (skill_overcast > 0)

        v_target = GetAppropiateTarget(slot)


        if (is_casting or 
            no_skill or
            skill_recharging or 
            not_enough_energy or 
            not_enough_hp or 
            not enough_adrenaline or
            not can_overcast or 
            v_target == 0
            ):
        ):
            self.in_casting_routine = False
            return False


    def HandleCombat(self, ooc=False):
        """
        tries to Execute the next skill in the skill order.
        """

        is_skill_ready = self.IsSkillReady(self.skill_order[self.skill_pointer])
        