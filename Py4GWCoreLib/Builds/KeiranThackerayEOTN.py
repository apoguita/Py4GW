
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import Range
from .AutoCombat import AutoCombat

from HeroAI.targeting import (
                TargetLowestAlly, 
                TargetLowestAllyCaster, 
                TargetLowestAllyMartial, 
                TargetLowestAllyMelee, 
                TargetLowestAllyRanged, 
                TargetLowestAllyEnergy,
                TargetClusteredEnemy,
                GetEnemyAttacking,
                GetEnemyCasting,
                GetEnemyCastingSpell,
                GetEnemyInjured,
                GetEnemyConditioned,
                GetEnemyHexed,
                GetEnemyDegenHexed,
                GetEnemyEnchanted,
                GetEnemyMoving,
                GetEnemyKnockedDown,
                GetEnemyBleeding,
                GetEnemyCrippled,
                GetEnemyPoisoned,
                GetEnemyWithEffect,
            )

class KeiranThackerayEOTN(BuildMgr):
    def __init__(self):
        super().__init__(name="AutoCombat Build")  # minimal init
        self.auto_combat_handler:BuildMgr = AutoCombat()
        self.natures_blessing = GLOBAL_CACHE.Skill.GetID("Natures_Blessing")
        self.relentless_assaunlt = GLOBAL_CACHE.Skill.GetID("Relentless_Assault")
        self.keiran_sniper_shot = GLOBAL_CACHE.Skill.GetID("Keirans_Sniper_Shot_Hearts_of_the_North")
        self.terminal_velocity = GLOBAL_CACHE.Skill.GetID("Terminal_Velocity")
        self.gravestone_marker = GLOBAL_CACHE.Skill.GetID("Gravestone_Marker")
        
    def ProcessSkillCasting(self):
        if (Routines.Checks.Map.MapValid() and 
            Routines.Checks.Player.CanAct() and
            GLOBAL_CACHE.Map.IsExplorable() and
            Routines.Checks.Skills.CanCast()):
            
            life_threshold = 0.80
            aftercast = 750
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.natures_blessing)):
                player_life = GLOBAL_CACHE.Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID())
                low_on_life = player_life < life_threshold

                nearest_npc = Routines.Agents.GetNearestNPC(Range.Spirit.value)
                npc_low_on_life = False

                if nearest_npc != 0:
                    nearest_NPC_life = GLOBAL_CACHE.Agent.GetHealth(nearest_npc)
                    if nearest_NPC_life > 0:  # only count if alive
                        npc_low_on_life = nearest_NPC_life < life_threshold

                if low_on_life or npc_low_on_life:
                    yield from Routines.Yield.Skills.CastSkillID(self.natures_blessing, aftercast_delay=100)
                    return
             
            if Routines.Checks.Agents.InDanger():
                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.keiran_sniper_shot)):
                    hexed_enemy = GetEnemyHexed(Range.Earshot.value)
                    if hexed_enemy != 0:
                        yield from Routines.Yield.Agents.ChangeTarget(hexed_enemy)
                        yield from Routines.Yield.Skills.CastSkillID(self.keiran_sniper_shot, aftercast_delay=aftercast)
                        return
                
                
                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.relentless_assaunlt)):
                    if GLOBAL_CACHE.Agent.IsHexed(GLOBAL_CACHE.Player.GetAgentID()) or GLOBAL_CACHE.Agent.IsConditioned(GLOBAL_CACHE.Player.GetAgentID()):
                        enemy = GetEnemyInjured(Range.Earshot.value)
                        if enemy != 0:
                            yield from Routines.Yield.Agents.ChangeTarget(enemy)
                            yield from Routines.Yield.Skills.CastSkillID(self.relentless_assaunlt, aftercast_delay=aftercast)
                            return
                        
                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.terminal_velocity)):
                    casting_enemy = GetEnemyCasting(Range.Earshot.value)
                    bleeding_enemy = GetEnemyBleeding(Range.Earshot.value)
                    
                    if Routines.Checks.Agents.HasEffect(bleeding_enemy,skill_id=GLOBAL_CACHE.Skill.GetID("Deep_Wound")):
                        bleeding_enemy = 0  # ignore deep wound bleeding enemies
                    
                    target_enemy = casting_enemy if casting_enemy != 0 else bleeding_enemy
                    if target_enemy != 0:
                        yield from Routines.Yield.Agents.ChangeTarget(target_enemy)
                        yield from Routines.Yield.Skills.CastSkillID(self.terminal_velocity, aftercast_delay=aftercast)
                        return
                    
                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.gravestone_marker)):
                    hurt_enemy = GetEnemyWithEffect(effect_skill_id="Deep_Wound", max_distance=Range.Earshot.value)
                    if hurt_enemy != 0:
                        yield from Routines.Yield.Agents.ChangeTarget(hurt_enemy)
                        yield from Routines.Yield.Skills.CastSkillID(self.gravestone_marker, aftercast_delay=aftercast)
                        return
                    
        else:
            ActionQueueManager().ResetAllQueues()
            yield from Routines.Yield.wait(500) 
            return        

        yield from self.auto_combat_handler.ProcessSkillCasting()