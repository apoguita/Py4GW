from datetime import datetime
import math
from PyAgent import PyAgent
from PySkillbar import SkillbarSkill
import PySkillbar
from Py4GWCoreLib import AgentArray, Agent
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog, Keystroke, Utils
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.Skillbar import SkillBar
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.enums import Allegiance, Key
from Widgets.frenkey.Polymock import state
from Widgets.frenkey.Polymock.data import Polymock_Quest, Polymock_Quests, Polymock_Spawns, PolymockBar, PolymockPieces, SkillReaction

# Check how many times we have used a skill with the same Energy. If Energy does not change we have to set a new energy base level
# If we had no target and now have the first target, we have to use our opener


class Combat:
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super(Combat, cls).__new__(cls)
            cls.state: state.WidgetState = state.WidgetState()
            cls.cancel_casting: bool = False
            
            cls.target_id: int = 0
            cls.map_id: int = 0
            cls.map_name: str = "Unknown Map"
            cls.target_agent_id: int = 0
            cls.target_skill_id: int = 0
            cls.target_model_id: int = 0
            cls.target_hp: float = 0
            
            cls.target_interrupt_ready: bool = False
            cls.target_block_ready: bool = False
            
            cls.target_casted_block: datetime = datetime.min
            cls.target_casted_interrupt: datetime = datetime.min
            
            cls.remove_block: bool = False

            cls.player_id: int = 0
            cls.player_hp: float = 0.0
            cls.player_hp_percent: float = 0.0
            cls.player_energy: float = 0.0
            cls.player_energy_raw: float = 0.0
            cls.player_energy_raw_percent: float = 0.0

            cls.target_name: str = 'None'
            cls.player_name: str = 'Unknown Player'
            cls.target_allegiance: Allegiance = Allegiance.Neutral
            cls.opener_used: bool = False

            cls.last_energy: float = 0.0
            cls.last_energy_tries: int = 0

            cls.skills: dict[int, SkillbarSkill] = {}

        return cls.instance

    def IsSkillReady(self, slot: int) -> bool:
        if slot not in self.skills:
            return False

        energy_cost = Routines.Checks.Skills.GetEnergyCostWithEffects(
            self.skills[slot].id.id, self.player_id)

        if slot in self.skills and self.skills[slot].recharge == 0 and energy_cost <= self.player_energy:
            return True

        return False

    def UseSkill(self, slot: int, target_id: int) -> bool:
        if slot in self.skills and self.IsSkillReady(slot):
            skill = self.skills[slot]
            target_name = self.target_name if target_id != self.player_id else "Player"
            self.state.Log(f"Using skill {GLOBAL_CACHE.Skill.GetName(skill.id.id)} from slot {slot} on {target_name} ({target_id})")
                
            if target_id == self.player_id:
                SkillBar.UseSkillTargetless(slot)
            else:
                SkillBar.UseSkill(slot, target_id)      
                      
            return True

        return False

    def ShouldInterruptSkill(self, skill_id: int) -> bool:
        if self.state.quest is None:
            return False
        
        for polymock_piece in self.state.quest.polymock_pieces:
            if polymock_piece.value.has_skill(skill_id):
                reaction = polymock_piece.value.get_skill_reaction(skill_id)
                if reaction == SkillReaction.Interrupt or reaction == SkillReaction.BlockOrInterrupt:
                    return True

        return False

    def InterruptSkill(self, skill_id: int) -> bool:
        slot = 4

        if self.IsSkillReady(slot):
            self.state.Log(f"Trying to interrupt skill {GLOBAL_CACHE.Skill.GetName(skill_id)}.")
            self.UseSkill(slot, self.target_id)
            return True

        return False

    def ShouldBlockSkill(self, skill_id: int) -> bool:
        if self.state.quest is None:
            return False
        
        for polymock_piece in self.state.quest.polymock_pieces:
            if polymock_piece.value.has_skill(skill_id):
                reaction = polymock_piece.value.get_skill_reaction(skill_id)
                if reaction == SkillReaction.Block or reaction == SkillReaction.BlockOrInterrupt:
                    return True

        return False

    def BlockSkill(self, skill_id: int) -> bool:
        slot = 5

        if self.IsSkillReady(slot):
            self.state.Log(f"Trying to block skill {GLOBAL_CACHE.Skill.GetName(skill_id)}.")
            self.UseSkill(slot, self.target_id)
            return True

        return False

    def UseGlyphOfPower(self) -> bool:
        slot = 8

        if self.player_hp_percent <= 50.0 and self.player_energy >= 5.0:
            if self.IsSkillReady(slot):
                self.UseSkill(slot, self.player_id)
                return True

        return False

    def UsePolymock_Ether_Signet(self) -> bool:
        slot = 7

        if self.player_energy < 1.0:
            if self.IsSkillReady(slot):
                self.UseSkill(slot, self.player_id)
                return True

        return False

    def ShouldUsePolymock_Glyph_of_Concentration(self, skill_id: int) -> bool:
        if self.state.quest is None:
            return False
        
        for polymock_piece in self.state.quest.counter_pieces:
            if polymock_piece.value.has_skill(skill_id):
                return polymock_piece.value.should_use_glyph(skill_id)

        return False

    def UsePolymock_Glyph_of_Concentration(self) -> bool:
        slot = 6

        if self.IsSkillReady(slot):
            self.UseSkill(slot, self.player_id)
            return True

        return False

    def UsePolymock_Damage_Skills(self) -> bool:
        if not self.state.quest:
            return False
                        
        skill_slot_order = []
        
        for i in [1, 2]:            
            for polymock_piece in self.state.quest.counter_pieces:
                for slot, skill in reversed(polymock_piece.value.damage_skills.items()):
                    equipped_skill = self.skills.get(slot)
                    
                    if equipped_skill and equipped_skill.id.id == skill.skill_id:
                        if slot not in skill_slot_order:
                            if (i == 1 and skill.use_glyph_of_concentration) or i == 2:
                                skill_slot_order.append(slot)
        
        if self.remove_block:
            skill_slot_order = [1]
                    
        for skill_slot in skill_slot_order:
            skill = self.skills.get(skill_slot)
            
            if not skill:
                continue

            slot_health_thresholds = {
                3: 400,
                2: 200,
                1: 0
            }
            
            if skill_slot == 1:
                if self.UseGlyphOfPower():
                    return True
            
            if self.IsSkillReady(skill_slot) and self.target_hp >= slot_health_thresholds[skill_slot]:
                should_use_glyph = self.ShouldUsePolymock_Glyph_of_Concentration(skill.id.id)
            
                required_energy = GLOBAL_CACHE.Skill.Data.GetEnergyCost(skill.id.id) + GLOBAL_CACHE.Skill.Data.GetEnergyCost(GLOBAL_CACHE.Skill.GetID("Polymock_Glyph_of_Concentration"))
                
                if self.opener_used and should_use_glyph and self.UsePolymock_Glyph_of_Concentration():
                    return True

                has_glyph = GLOBAL_CACHE.Effects.BuffExists(self.player_id, GLOBAL_CACHE.Skill.GetID(
                    "Polymock_Glyph_of_Concentration")) or GLOBAL_CACHE.Effects.EffectExists(self.player_id, GLOBAL_CACHE.Skill.GetID("Polymock_Glyph_of_Concentration"))
                glyph_recharge = PySkillbar.Skillbar().GetSkill(6).get_recharge / 1000
                
                if not self.opener_used or not should_use_glyph or has_glyph or (glyph_recharge > 5.0) or not self.target_interrupt_ready:
                    if self.remove_block:
                        self.state.Log(f"Removing block from target {self.target_name} ({self.target_id}) by using skill {GLOBAL_CACHE.Skill.GetName(skill.id.id)} from slot {skill_slot}.")
                                            
                    if not self.opener_used:
                        self.state.Log(f"Using opener skill {GLOBAL_CACHE.Skill.GetName(skill.id.id)} from slot {skill_slot} on target {self.target_name} ({self.target_id}).")
                    
                    self.opener_used = True  
                    
                    self.UseSkill(skill_slot, self.target_id)                  

                    return True
        return False

    def GetAgentAtPosition(self, agent_id: int) -> int:
        agents = AgentArray.GetAgentArray()
        map_id = Map.GetMapID()

        spawn_point = next(
            (spawn for spawn in Polymock_Spawns if spawn.value[0] == map_id), None)

        if not spawn_point:
            # self.state.Log(f"No spawn point found for map ID {map_id}.")
            return 0

        spawn_point = spawn_point.value[1]
        # self.state.Log(f"Spawn point for map ID {map_id} is {spawn_point}.")

        agent_array = AgentArray.Filter.ByDistance(agents, spawn_point, 250)
        agent_array = AgentArray.Sort.ByDistance(agent_array, spawn_point)
        agent_id = Utils.GetFirstFromArray(agent_array)

        if agent_id:
            x, y = Agent.GetXY(agent_id)
            distance = Utils.Distance(spawn_point, [x, y])
            if distance < 250.0:
                return agent_id

        return 0

    def Fight(self):        
        target_id = Routines.Agents.GetNearestEnemy()

        if target_id == 0 or target_id != self.target_id:
            self.opener_used = False

        target_id = self.GetAgentAtPosition(target_id)

        self.map_id = Map.GetMapID()
        self.map_name = Map.GetMapName() or "Unknown Map"
        self.target_id = target_id
        self.target_agent = Agent.GetAgentByID(self.target_id) if self.target_id > 0 else None
        self.target_name = Agent.GetNameByID(
            self.target_agent.agent_id) if self.target_agent and self.target_agent.agent_id > 0 else 'None'
        self.target_allegiance = Allegiance(Agent.GetAllegiance(
            self.target_id)[0]) if self.target_agent else Allegiance.Neutral
        self.target_skill_id = Agent.GetCastingSkill(
            self.target_id) if self.target_agent else 0
        self.target_model_id = Agent.GetModelID(
            self.target_id) if self.target_agent else 0
        self.target_hp = Agent.GetHealth(
            self.target_id) * Agent.GetMaxHealth(self.target_id) if self.target_agent else 0
        
        if self.target_hp <= 0.0:
            self.target_hp = 4000            

        self.player_id = GLOBAL_CACHE.Player.GetAgentID()
        self.player_name = GLOBAL_CACHE.Player.GetName() or "Unknown Player"
        self.player_energy = round(Agent.GetEnergy(
            self.player_id) * Agent.GetMaxEnergy(self.player_id))
        self.player_hp = Agent.GetHealth(
            self.player_id) * Agent.GetMaxHealth(self.player_id)
        self.player_hp_percent = Agent.GetHealth(
            self.player_id) * 100.0

        self.skills = {}
        for slot in range(1, 9):
            skill = GLOBAL_CACHE.SkillBar.GetSkillData(slot)

            if skill and skill.id.id > 0:
                self.skills[slot] = skill
        
        is_casting =  Agent.IsCasting(self.player_id)

        if self.target_id > 0 and GLOBAL_CACHE.Player.GetTargetID() != self.target_id and self.target_allegiance == Allegiance.Enemy:
            GLOBAL_CACHE.Player.ChangeTarget(self.target_id)
        
        if self.target_skill_id == GLOBAL_CACHE.Skill.GetID("Polymock_Block"):
            self.target_casted_block = datetime.now()
        
        if self.target_skill_id == GLOBAL_CACHE.Skill.GetID("Polymock_Power_Drain"):
            self.target_casted_interrupt = datetime.now()
        
        passed_milliseconds = (datetime.now() - self.target_casted_interrupt).seconds * 1000        
        self.target_interrupt_ready = passed_milliseconds > 20000
        
        passed_milliseconds = (datetime.now() - self.target_casted_block).seconds * 1000        
        self.target_block_ready = passed_milliseconds > 12000        
        
        self.remove_block = False        
        if Agent.IsEnchanted(self.target_id):
            time_since_block = datetime.now() - self.target_casted_block
            passed_milliseconds = time_since_block.total_seconds() * 1000
            
            if passed_milliseconds > 150 and passed_milliseconds < 2000:
                self.remove_block = True

        if self.target_skill_id > 0:
            if self.ShouldInterruptSkill(self.target_skill_id):
                can_interrupt = self.IsSkillReady(4)  # Assuming slot 4 is the interrupt skill
                
                if can_interrupt:
                    if self.cancel_casting:
                        if is_casting and Agent.GetCastingSkill(self.player_id) != self.skills[4].id.id:                   
                            self.state.Log(f"Cancel casting current skill.")
                            Keystroke.PressAndRelease(Key.Escape.value)

                        self.InterruptSkill(self.target_skill_id)
                        return True
                    
                    else:
                        self.InterruptSkill(self.target_skill_id)
                        return True
            
            if self.ShouldBlockSkill(self.target_skill_id):
                can_block = self.IsSkillReady(5)
                
                if can_block:
                    if self.cancel_casting:
                        if is_casting and Agent.GetCastingSkill(self.player_id) != self.skills[5].id.id: 
                            self.state.Log(f"Cancel casting current skill.")
                            Keystroke.PressAndRelease(Key.Escape.value)
                        
                        self.BlockSkill(self.target_skill_id)
                        return True
                            
                    elif self.opener_used:
                        self.BlockSkill(self.target_skill_id)
                        return True

        if is_casting:
            return False

        # if self.target_allegiance == Allegiance.Enemy and self.UseGlyphOfPower():
        #     return True

        if self.UsePolymock_Ether_Signet():
            return True

        if self.target_allegiance == Allegiance.Enemy and self.UsePolymock_Damage_Skills():
            return True

        return False
