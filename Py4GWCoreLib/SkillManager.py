from HeroAI.custom_skill import CustomSkillClass
from HeroAI.types import SkillType,SkillNature, Skilltarget
from HeroAI.combat import (UniqueSkills, _PrioritizeSkills, _IsSkillReady,
    _InCastingRoutine, _GetPartyTarget, _GetAppropiateTarget,
    _AreCastConditionsMet, _SpiritBuffExists, _IsReadyToCast,
    _IsOOCSkill, _ChooseTarget, _GetWeaponAttackAftercast,
    _HandleCombat
                           
)
from .Agent import Agent
from.AgentArray import AgentArray
from .Player import Player
from .Skill import Skill
from typing import Optional
from .Py4GWcorelib import ThrottledTimer
from .Py4GWcorelib import Console
from .Py4GWcorelib import ConsoleLog
from .Py4GWcorelib import *
from .Routines import Routines
from .enums import Range
from .Effect import Effects
from HeroAI.players import *

MAX_SKILLS = 8
MAX_NUM_PLAYERS = 8


class SkillManager:
    class Autocombat: 
        custom_skill_data_handler = CustomSkillClass()
        class _SkillData:
            def __init__(self, slot):
                self.skill_id = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot)  # slot is 1 based
                self.skillbar_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)  # Fetch additional data from the skill bar
                self.custom_skill_data = SkillManager.Autocombat.custom_skill_data_handler.get_skill(self.skill_id)  # Retrieve custom skill data
                                
        def __init__(self):
            import Py4GW
            self.unique_skills = UniqueSkills()
            self.skills: list[SkillManager.Autocombat._SkillData] = []
            self.skill_order = [0] * MAX_SKILLS
            self.skill_pointer = 0
            self.aftercast_timer = ThrottledTimer()
            self.stay_alert_timer = ThrottledTimer(2500)
            self.game_throttle_timer = ThrottledTimer(75)
            weapon_aftercast = self.GetWeaponAttackAftercast()
            self.weapon_aftercast_initialized = False
            self.auto_attack_timer = ThrottledTimer(weapon_aftercast)
            self.ping_handler = Py4GW.PingHandler()
            self.in_casting_routine = False
            self.aggressive_enemies_only = False
            self.is_skill_enabled = [True] * MAX_SKILLS

            attributes = GLOBAL_CACHE.Agent.GetAttributes(GLOBAL_CACHE.Player.GetAgentID())

            self.fast_casting_exists = False
            self.fast_casting_level = 0
            self.expertise_exists = False
            self.expertise_level = 0

            for attribute in attributes:
                if attribute.GetName() == "Fast Casting":
                    self.fast_casting_exists = True
                    self.fast_casting_level = attribute.level
                    
                if attribute.GetName() == "Expertise":
                    self.expertise_exists = True
                    self.expertise_level = attribute.level
                    
        def SetWeaponAttackAftercast(self):
            if not self.weapon_aftercast_initialized:
                weapon_aftercast = self.GetWeaponAttackAftercast()
                self.auto_attack_timer = ThrottledTimer(weapon_aftercast)
                self.weapon_aftercast_initialized = True
            if not Routines.Checks.Map.MapValid():
                self.weapon_aftercast_initialized = False

        def SetAggressiveEnemiesOnly(self, state, log_action=False):
            self.aggressive_enemies_only = state
            if log_action:
                if state:
                    ConsoleLog("Autocombat", f"Fighting aggressive enemies only.", Console.MessageType.Info)
                else:
                    ConsoleLog("Autocombat", f"Fighting all enemies", Console.MessageType.Info)

        def SetSkillEnabled(self, slot:int, state:bool):
            if 0 <= slot < MAX_SKILLS:
                self.is_skill_enabled[slot] = state

        def PrioritizeSkills(self):
            """
            Create a priority-based skill execution order.
            """
            self.skills = _PrioritizeSkills(self._SkillData, self.skill_order)
            
  
        def GetSkills(self):
            """
            Retrieve the prioritized skill set.
            """
            return self.skills
        
        def GetOrderedSkill(self, index:int)-> Optional[_SkillData]:
            """
            Retrieve the skill at the given index in the prioritized order.
            """
            if 0 <= index < MAX_SKILLS:
                return self.skills[index]
            return None  # Return None if the index is out of bounds
        
        def AdvanceSkillPointer(self):
            self.skill_pointer += 1
            if self.skill_pointer >= MAX_SKILLS:
                self.skill_pointer = 0
                
        def ResetSkillPointer(self):
            self.skill_pointer = 0
            
        def SetSkillPointer(self, pointer):
            if 0 <= pointer < MAX_SKILLS:
                self.skill_pointer = pointer
            else:
                self.skill_pointer = 0
                
        def GetSkillPointer(self):
            return self.skill_pointer
                
        def GetEnergyValues(self,agent_id):
            agent_energy = GLOBAL_CACHE.Agent.GetEnergy(agent_id)
            if agent_energy <= 0:
                return 1.0 #default return full energy to prevent issues
            
            return agent_energy

        def IsSkillReady(self, slot):
            return _IsSkillReady(slot, self.skill_order, self.skills, self.is_skill_enabled)
        
        def InCastingRoutine(self):
            return _InCastingRoutine(self.aftercast_timer, self.in_casting_routine)

        
        def GetPartyTargetID(self):
            return Routines.Party.GetPartyTargetID()
            
        def SafeChangeTarget(self, target_id):
            Routines.Targeting.SafeChangeTarget(target_id)
                
        def SafeInteract(self, target_id):
            Routines.Agents.SafeInteract(target_id)
                
            
        def GetPartyTarget(self):
            return _GetPartyTarget()
        
        def InAggro(self):
            if self.stay_alert_timer.IsExpired():
                in_danger = Routines.Checks.Agents.InDanger(Range.Earshot, self.aggressive_enemies_only)
            else:
                in_danger = Routines.Checks.Agents.InDanger(Range.Spellcast, self.aggressive_enemies_only)
                
            if in_danger:
                self.stay_alert_timer.Reset()
                return True
                
        
        def get_combat_distance(self):
            return Range.Spellcast.value if self.InAggro() else Range.Earshot.value
        
        def GetAppropiateTarget(self, slot):
            return _GetAppropiateTarget(
                self.skills,
                self.unique_skills,
                self.HasEffect,
                self.GetPartyTarget,
                multibox=False,
                slot=slot,
                is_targeting_enabled=True,
                is_combat_enabled=True,
                combat_distance=self.get_combat_distance(),
        )
                
                
 
        def IsPartyMember(self, agent_id):
            return Routines.Party.IsPartyMember(agent_id)
        
        def HasEffect(self, agent_id, skill_id, exact_weapon_spell=False):
            return Routines.Checks.Effects.HasEffect(agent_id, skill_id, exact_weapon_spell)
            
        def GetAgentBuffList(self, agent_id):
                result_list = []
                buff_list = Effects.GetBuffs(agent_id)
                for buff in buff_list:
                    result_list.append(buff.skill_id)
                        
                effect_list = Effects.GetEffects(agent_id)
                for effect in effect_list:
                    result_list.append(effect.skill_id)    
                return result_list
                        
        def AreCastConditionsMet(self, slot, vTarget):
            return _AreCastConditionsMet(
                slot,
                vTarget,
                self.skills, 
                self.unique_skills, 
                self.HasEffect, 
                self.GetEnergyValues(GLOBAL_CACHE.Player.GetAgentID()),
                self.IsPartyMember,
                self.GetAgentBuffList(GLOBAL_CACHE.Player.GetAgentID()),
                self.GetAgentBuffList(vTarget)
            )


        def SpiritBuffExists(self, skill_id):
            return _SpiritBuffExists(skill_id)

        
        def IsReadyToCast(self, slot):
            result = _IsReadyToCast(
                slot,
                self.GetAppropiateTarget(slot),
                self.skills,
                self.GetEnergyValues,
                self.expertise_exists,
                self.expertise_level,
                self.AreCastConditionsMet,
                self.SpiritBuffExists,
                self.HasEffect
            )
            
            self.in_casting_routine = result[2]
            return result[0], result[1]
        
        
        def IsOOCSkill(self, slot):
            return _IsOOCSkill(slot, self.skills)

        
        def ChooseTarget(self, interact=True):  
            return _ChooseTarget(
                True,
                self.InAggro(),
                self.GetPartyTarget,
                self.SafeInteract,
                self.get_combat_distance()
            )

                
        def GetWeaponAttackAftercast(self):
            """
            Returns the attack speed of the current weapon in ms (int).
            """
            return _GetWeaponAttackAftercast()

                
        def ExecuteHandleCombat(self,ooc=False):
            """
            tries to Execute the next skill in the skill order.
            """
            
            result = _HandleCombat(
                self.skills,
                self.skill_pointer,
                self.IsSkillReady(self.skill_pointer),
                self.AdvanceSkillPointer,
                self.IsOOCSkill(self.skill_pointer),
                self.IsReadyToCast,
                self.fast_casting_exists,
                self.fast_casting_level,
                self.GetWeaponAttackAftercast,
                self.ping_handler.GetCurrentPing(),
                ooc
            )
        
            self.in_casting_routine = result[1]
            self.aftercast = result[2]
            return result[0]

        
        def HandleCombat(self):
            if self.game_throttle_timer.IsExpired():
                self.game_throttle_timer.Reset()
                self.PrioritizeSkills()
                if not self.InAggro():
                    if self.ExecuteHandleCombat(ooc=True):
                        #self.auto_attack_timer.Reset()
                        pass
                    return
                   

                if self.ExecuteHandleCombat(ooc=False):
                    #self.auto_attack_timer.Reset()
                    return
                
                if self.auto_attack_timer.IsExpired():
                    if (
                        not GLOBAL_CACHE.Agent.IsAttacking(GLOBAL_CACHE.Player.GetAgentID()) and
                        not GLOBAL_CACHE.Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID()) #and
                        #not GLOBAL_CACHE.Agent.IsMoving(GLOBAL_CACHE.Player.GetAgentID())    
                    ):
                        self.ChooseTarget()

                    self.auto_attack_timer.Reset()
                    self.ResetSkillPointer()
                    return
                
                