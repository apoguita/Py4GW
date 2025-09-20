import Py4GW
import math
from typing import Tuple
from Py4GWCoreLib import Profession
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Agent
from Py4GWCoreLib import Range
from Py4GWCoreLib import Utils


#region SFAssassinVaettir
class ShadowFormAssassinVaettir(BuildMgr):
    def __init__(self):
        super().__init__(
            name="Shadow Form Assassin Vaettir",
            required_primary=Profession.Assassin,
            required_secondary=Profession.Mesmer,
            template_code="OwVUI2h5lPP8Id2BkAiAvpLBTAA",
            skills=[
                GLOBAL_CACHE.Skill.GetID("Deadly_Paradox"),
                GLOBAL_CACHE.Skill.GetID("Shadow_Form"),
                GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress"),
                GLOBAL_CACHE.Skill.GetID("Way_of_Perfection"),
                GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow"),
                GLOBAL_CACHE.Skill.GetID("Wastrels_Demise"),
                GLOBAL_CACHE.Skill.GetID("Arcane_Echo"),
                GLOBAL_CACHE.Skill.GetID("Channeling"),
            ]
        )
        

        self.deadly_paradox_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Deadly_Paradox"))
        self.shadow_form_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Shadow_Form"))
        self.shroud_of_distress_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress"))
        self.way_of_perfection_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Way_of_Perfection"))
        self.heart_of_shadow_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow"))
        self.wastrels_demise_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Wastrels_Demise"))
        self.arcane_echo_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Arcane_Echo"))
        self.channeling_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Channeling"))
        
        self.shadow_form = GLOBAL_CACHE.Skill.GetID("Shadow_Form")
        self.deadly_paradox = GLOBAL_CACHE.Skill.GetID("Deadly_Paradox")
        self.shroud_of_distress = GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress")
        self.channeling = GLOBAL_CACHE.Skill.GetID("Channeling")
        self.way_of_perfection = GLOBAL_CACHE.Skill.GetID("Way_of_Perfection")
        self.heart_of_shadow = GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow")
                     
        self.in_killing_routine = False
        self.routine_finished = False
        self.stuck_counter = 0
        self.waypoint = (0,0)
        
    def SetKillingRoutine(self, in_killing_routine: bool):
        self.in_killing_routine = in_killing_routine
        
    def SetRoutineFinished(self, routine_finished: bool):
        self.routine_finished = routine_finished

        
    def SetStuckCounter(self, stuck_counter: int):
        self.stuck_counter = stuck_counter
        
    def _CastSkillID(self, skill_id:int, extra_condition:bool=True, log:bool=True, aftercast_delay:int=1000):
        result = yield from Routines.Yield.Skills.CastSkillID(skill_id, extra_condition=extra_condition, log=log, aftercast_delay=aftercast_delay)
        return result
    
    def _CastSkillSlot(self, slot:int, extra_condition:bool=True, log:bool=True, aftercast_delay:int=1000):
        result = yield from Routines.Yield.Skills.CastSkillSlot(slot, extra_condition=extra_condition, log=log, aftercast_delay=aftercast_delay)
        return result
        
    def DefensiveActions(self):
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_agent_id, self.deadly_paradox)
        if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.shadow_form)):
            if (yield from self._CastSkillID(self.deadly_paradox,extra_condition=(not has_deadly_paradox), log=False, aftercast_delay=100)):
                ConsoleLog(self.build_name, "Casting Deadly Paradox.", Py4GW.Console.MessageType.Info, log=False)
            if (yield from self._CastSkillID(self.shadow_form, log=False, aftercast_delay=1750)):
                ConsoleLog(self.build_name, "Casting Shadow Form.", Py4GW.Console.MessageType.Info, log=False)
                
    def CastShroudOfDistress(self):
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        if GLOBAL_CACHE.Agent.GetHealth(player_agent_id) < 0.45:
            ConsoleLog(self.build_name, "Casting Shroud of Distress.", Py4GW.Console.MessageType.Info, log=False)
            # ** Cast Shroud of Distress **
            yield from self._CastSkillID(self.shroud_of_distress, log =False, aftercast_delay=1750)
                
    def vector_angle(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        """Returns the cosine similarity (dot product / magnitudes). 1 = same direction, -1 = opposite."""
        dot = a[0]*b[0] + a[1]*b[1]
        mag_a = math.hypot(*a)
        mag_b = math.hypot(*b)
        if mag_a == 0 or mag_b == 0:
            return 1  # safest fallback
        dot = a[0]*b[0] + a[1]*b[1]
        return dot / (mag_a * mag_b)
            
    def CastHeartOfShadow(self):
        center_point1 = (10980, -21532)
        center_point2 = (11461, -17282)
        player_pos = GLOBAL_CACHE.Player.GetXY()
        
        distance_to_center1 = Utils.Distance(player_pos, center_point1)
        distance_to_center2 = Utils.Distance(player_pos, center_point2)
        goal = center_point1 if distance_to_center1 < distance_to_center2 else center_point2
        #Compute direction to goal
        to_goal = (goal[0] - player_pos[0], goal[1] - player_pos[1])
        
        best_enemy = 0
        most_opposite_score = 1 
        
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.Spellcast.value)
        
        for enemy in enemy_array:
            if GLOBAL_CACHE.Agent.IsDead(enemy):
                continue
            enemy_pos = GLOBAL_CACHE.Agent.GetXY(enemy)
            to_enemy = (enemy_pos[0] - player_pos[0], enemy_pos[1] - player_pos[1])
            angle_score = self.vector_angle(to_goal, to_enemy)  # -1 is most opposite
            if angle_score < most_opposite_score:
                most_opposite_score = angle_score
                best_enemy = enemy
        if best_enemy:
            yield from Routines.Yield.Agents.ChangeTarget(best_enemy)    
        else:
            yield from Routines.Yield.Agents.TargetNearestEnemy(Range.Earshot.value)
        yield from self._CastSkillID(self.heart_of_shadow, log=False, aftercast_delay=350)
            
            
    def ProcessSkillCasting(self):
        def GetNotHexedEnemy():
            player_pos =  GLOBAL_CACHE.Player.GetXY()
            enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
            for enemy in enemy_array:
                if GLOBAL_CACHE.Agent.IsDead(enemy):
                    continue
                if Agent.IsHexed(enemy):
                    continue 
                return enemy
        
        
        
        while True:
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)
                continue
            
            if not GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Jaga Moraine"):
                yield from Routines.Yield.wait(1000)
                return
            
            
            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(1000)
                continue
            
            if not Routines.Checks.Skills.CanCast():
                yield from Routines.Yield.wait(100)
                continue
            
            if self.routine_finished:
                return

            player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            has_shadow_form = Routines.Checks.Effects.HasBuff(player_agent_id,self.shadow_form)
            shadow_form_buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id,self.shadow_form) if has_shadow_form else 0
            if Routines.Checks.Agents.InDanger(Range.Spellcast):
                has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_agent_id, self.deadly_paradox)
                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.shadow_form)):
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                    if (yield from self._CastSkillID(self.deadly_paradox,extra_condition=(not has_deadly_paradox), log=False, aftercast_delay=200)):
                        ConsoleLog(self.build_name, "Casting Deadly Paradox.", Py4GW.Console.MessageType.Info, log=False)
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                    if (yield from self._CastSkillID(self.shadow_form, log=False, aftercast_delay=1950)):
                        ConsoleLog(self.build_name, "Casting Shadow Form.", Py4GW.Console.MessageType.Info, log=False)
                        continue
            has_shroud_of_distress = Routines.Checks.Effects.HasBuff(player_agent_id,self.shroud_of_distress)
            if not has_shroud_of_distress:
                ConsoleLog(self.build_name, "Casting Shroud of Distress.", Py4GW.Console.MessageType.Info, log=False)
                # ** Cast Shroud of Distress **
                GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                if (yield from self._CastSkillID(self.shroud_of_distress, log =False, aftercast_delay=1950)):
                    continue
                        
            has_channeling = Routines.Checks.Effects.HasBuff(player_agent_id,self.channeling)
            if not has_channeling:
                ConsoleLog(self.build_name, "Casting Channeling.", Py4GW.Console.MessageType.Info, log=False)
                # ** Cast Channeling **
                if (yield from self._CastSkillID(self.channeling, log =False, aftercast_delay=1850)):
                    continue
            if (yield from self._CastSkillID(self.way_of_perfection, log=False, aftercast_delay=1000)):
                ConsoleLog(self.build_name, "Casting Way of Perfection.", Py4GW.Console.MessageType.Info, log=False)
                continue
            if not self.in_killing_routine or GLOBAL_CACHE.Agent.GetHealth(player_agent_id) < 0.05:
                if GLOBAL_CACHE.Agent.GetHealth(player_agent_id) < 0.05:
                    ConsoleLog(self.build_name, "Forcing HoS to survive, run was going to fail anyways :(", Py4GW.Console.MessageType.Warning, log=False)
                if GLOBAL_CACHE.Agent.GetHealth(player_agent_id) < 0.35 or self.stuck_counter > 0:
                    center_point1 = (10980, -21532)
                    center_point2 = (11461, -17282)
                    player_pos = GLOBAL_CACHE.Player.GetXY()
                    
                    distance_to_center1 = Utils.Distance(player_pos, center_point1)
                    distance_to_center2 = Utils.Distance(player_pos, center_point2)
                    goal = center_point1 if distance_to_center1 < distance_to_center2 else center_point2
                    #Compute direction to goal
                    to_goal = (goal[0] - player_pos[0], goal[1] - player_pos[1])
                    
                    best_enemy = 0
                    most_opposite_score = 1 
                    
                    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.Spellcast.value)
                    
                    for enemy in enemy_array:
                        if GLOBAL_CACHE.Agent.IsDead(enemy):
                            continue
                        enemy_pos = GLOBAL_CACHE.Agent.GetXY(enemy)
                        to_enemy = (enemy_pos[0] - player_pos[0], enemy_pos[1] - player_pos[1])
                        angle_score = self.vector_angle(to_goal, to_enemy)  # -1 is most opposite
                        if angle_score < most_opposite_score:
                            most_opposite_score = angle_score
                            best_enemy = enemy
                    if best_enemy:
                        yield from Routines.Yield.Agents.ChangeTarget(best_enemy)    
                    else:
                        yield from Routines.Yield.Agents.TargetNearestEnemy(Range.Earshot.value)
                    if (yield from self._CastSkillID(self.heart_of_shadow, log=False, aftercast_delay=350)):
                        continue
                        
            if self.in_killing_routine and has_shadow_form and has_shroud_of_distress and has_channeling:
                both_ready = Routines.Checks.Skills.IsSkillSlotReady(self.wastrels_demise_slot) and Routines.Checks.Skills.IsSkillSlotReady(self.arcane_echo_slot)
                target = GetNotHexedEnemy()
                if target and shadow_form_buff_time_remaining >= 4000:
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                    GLOBAL_CACHE.Player.ChangeTarget(target)
                    if (yield from self._CastSkillSlot(self.arcane_echo_slot, extra_condition=both_ready, log=False, aftercast_delay=2850)):
                        GLOBAL_CACHE.Player.Interact(target,False)
                        ConsoleLog(self.build_name, "Casting Arcane Echo.", Py4GW.Console.MessageType.Info, log=False)
                    else:
                        if (yield from self._CastSkillSlot(self.arcane_echo_slot, log=False, aftercast_delay=1000)):
                            GLOBAL_CACHE.Player.Interact(target,False)
                            ConsoleLog(self.build_name, "Casting Echoed Wastrel.", Py4GW.Console.MessageType.Info, log=False)
                
                target = GetNotHexedEnemy()  
                if target and not Routines.Checks.Skills.IsSkillSlotReady(self.arcane_echo_slot): 
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                    GLOBAL_CACHE.Player.ChangeTarget(target)
                    if (yield from self._CastSkillSlot(self.wastrels_demise_slot, log=False, aftercast_delay=1000)):
                        GLOBAL_CACHE.Player.Interact(target,False)
            yield from Routines.Yield.wait(100)
            
#endregion