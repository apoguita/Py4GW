
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import Range
from Py4GWCoreLib import AutoPathing
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
                GetEnemyHealthy,
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
        self.rain_of_arrows = GLOBAL_CACHE.Skill.GetID("Rain_of_Arrows")
        
    
    def CheckSkillValidity(self):
        skills = [
            self.natures_blessing,
            self.relentless_assaunlt,
            self.keiran_sniper_shot,
            self.terminal_velocity,
            self.gravestone_marker,
            self.rain_of_arrows
        ]
        valid = True
        for skill in skills:
            if skill == 0:
                valid = False
        return valid
        
    def ProcessSkillCasting(self):
        def _CastSkill(target, skill_id, aftercast=750):
            if Routines.Checks.Map.MapValid():
                yield from Routines.Yield.Agents.ChangeTarget(target)
            if Routines.Checks.Map.MapValid():
                yield from Routines.Yield.Skills.CastSkillID(skill_id, aftercast_delay=aftercast)
            yield


        if not (Routines.Checks.Map.MapValid() and
            Routines.Checks.Player.CanAct() and
            GLOBAL_CACHE.Map.IsExplorable() and
            Routines.Checks.Skills.CanCast() and
            self.CheckSkillValidity()):

            ActionQueueManager().ResetAllQueues()
            yield from Routines.Yield.wait(1000) 
            return 

        life_threshold = 0.70
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
                    yield from _CastSkill(hexed_enemy, self.keiran_sniper_shot, aftercast)
                    return
                
                
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.relentless_assaunlt)):
                if GLOBAL_CACHE.Agent.IsHexed(GLOBAL_CACHE.Player.GetAgentID()) or GLOBAL_CACHE.Agent.IsConditioned(GLOBAL_CACHE.Player.GetAgentID()):
                    enemy = GetEnemyInjured(Range.Earshot.value)
                    if enemy != 0:
                        yield from _CastSkill(enemy, self.relentless_assaunlt, aftercast)
                        return
                    
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.terminal_velocity)):
                casting_enemy = GetEnemyCasting(Range.Earshot.value)
                bleeding_enemy = GetEnemyBleeding(Range.Earshot.value)
                
                #if Routines.Checks.Agents.HasEffect(bleeding_enemy,skill_id=GLOBAL_CACHE.Skill.GetID("Deep_Wound")):
                #    bleeding_enemy = 0  # ignore deep wound bleeding enemies
                
                target_enemy = casting_enemy if casting_enemy != 0 else bleeding_enemy
                if target_enemy != 0:
                    yield from _CastSkill(target_enemy, self.terminal_velocity, aftercast)
                    return
                
            """if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.gravestone_marker)):
                injured_enemy = GetEnemyInjured(Range.Earshot.value)
                if injured_enemy != 0:
                    yield from _CastSkill(injured_enemy, self.gravestone_marker, aftercast)
                    return"""
                
            if Routines.Checks.Agents.HasEffect(GLOBAL_CACHE.Player.GetAgentID(), skill_id="Burning"):
                import math
                current_xy = GLOBAL_CACHE.Player.GetXY()
                distance = Range.Area.value

                # Facing angle in radians
                facing_angle = GLOBAL_CACHE.Agent.GetRotationAngle(GLOBAL_CACHE.Player.GetAgentID())

                # Left = facing_angle + 90° (π/2)
                left_x = math.cos(facing_angle + math.pi / 2)
                left_y = math.sin(facing_angle + math.pi / 2)

                desired_xy = (
                    current_xy[0] + left_x * distance,
                    current_xy[1] + left_y * distance
                )

                path = yield from AutoPathing().get_path_to(*desired_xy)
                yield from Routines.Yield.Movement.FollowPath(path_points=path)

                
               
                            
        yield from self.auto_combat_handler.ProcessSkillCasting()