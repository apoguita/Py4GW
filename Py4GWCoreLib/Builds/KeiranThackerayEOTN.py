
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import Range
from .AutoCombat import AutoCombat


class KeiranThackerayEOTN(BuildMgr):
    def __init__(self):
        super().__init__(name="AutoCombat Build")  # minimal init
        self.auto_combat_handler:BuildMgr = AutoCombat()
        self.natures_blessing = GLOBAL_CACHE.Skill.GetID("Natures_Blessing")
        self.relentless_assaunlt = GLOBAL_CACHE.Skill.GetID("Relentless_Assault")
        self.keiran_sniper_shot = GLOBAL_CACHE.Skill.GetID("Keirans_Sniper_Shot_Hearts_of_the_North") # or 3235
        self.terminal_velocity = GLOBAL_CACHE.Skill.GetID("Terminal_Velocity")
        self.gravestone_marker = GLOBAL_CACHE.Skill.GetID("Gravestone_Marker")
        self.rain_of_arrows = GLOBAL_CACHE.Skill.GetID("Rain_of_Arrows")
        self.auto_combat_handler.auto_combat_handler.SetSkillEnabled(1, False)
        self.auto_combat_handler.auto_combat_handler.SetSkillEnabled(2, False)
        self.auto_combat_handler.auto_combat_handler.SetSkillEnabled(3, False)
        self.auto_combat_handler.auto_combat_handler.SetSkillEnabled(4, False)
        self.auto_combat_handler.auto_combat_handler.SetSkillEnabled(5, False)
        self.auto_combat_handler.auto_combat_handler.SetSkillEnabled(6, False)
        
    def ProcessSkillCasting(self):
        def _CastSkill(target, skill_id, aftercast=750):
            if Routines.Checks.Map.IsExplorable():
                yield from Routines.Yield.Agents.ChangeTarget(target)
            if Routines.Checks.Map.IsExplorable():
                yield from Routines.Yield.Skills.CastSkillID(skill_id, aftercast_delay=aftercast)
            yield
            
        aftercast = 750  # ms

        if not (Routines.Checks.Map.IsExplorable() and
            Routines.Checks.Player.CanAct() and
            Routines.Checks.Map.IsExplorable() and
            Routines.Checks.Skills.CanCast()):

            ActionQueueManager().ResetAllQueues()
            yield from Routines.Yield.wait(1000) 
            return 
        
        life_threshold = 0.80
        if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.natures_blessing)):
            player_life = GLOBAL_CACHE.Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID())
            low_on_life = player_life < life_threshold

            nearest_npc = Routines.Agents.GetNearestNPC(Range.Spirit.value)
            npc_low_on_life = False
            if nearest_npc != 0:
                npc_life = GLOBAL_CACHE.Agent.GetHealth(nearest_npc)
                npc_low_on_life = npc_life < life_threshold

            if low_on_life or npc_low_on_life:
                yield from Routines.Yield.Skills.CastSkillID(self.natures_blessing, aftercast_delay=100)
                return
            
        if Routines.Checks.Agents.InDanger():
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.keiran_sniper_shot)):
                hexed_enemy = Routines.Targeting.GetEnemyHexed(Range.Earshot.value)
                if hexed_enemy != 0:
                    yield from _CastSkill(hexed_enemy, self.keiran_sniper_shot, aftercast)
                    return

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.relentless_assaunlt)):
                if (GLOBAL_CACHE.Agent.IsDegenHexed(GLOBAL_CACHE.Player.GetAgentID()) or 
                    #GLOBAL_CACHE.Agent.IsConditioned(GLOBAL_CACHE.Player.GetAgentID()) or
                    GLOBAL_CACHE.Agent.IsBleeding(GLOBAL_CACHE.Player.GetAgentID()) or
                    GLOBAL_CACHE.Agent.IsPoisoned(GLOBAL_CACHE.Player.GetAgentID()) or
                    Routines.Checks.Agents.HasEffect(GLOBAL_CACHE.Player.GetAgentID(), GLOBAL_CACHE.Skill.GetID("Deep_Wound")) or
                    Routines.Checks.Agents.HasEffect(GLOBAL_CACHE.Player.GetAgentID(), GLOBAL_CACHE.Skill.GetID("Cracked_Armor")) or
                    Routines.Checks.Agents.HasEffect(GLOBAL_CACHE.Player.GetAgentID(), GLOBAL_CACHE.Skill.GetID("Burning"))):
                    enemy = Routines.Targeting.GetEnemyInjured(Range.Earshot.value)
                    if enemy != 0:
                        yield from _CastSkill(enemy, self.relentless_assaunlt, aftercast)
                        return
                    
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.terminal_velocity)):
                casting_enemy = Routines.Targeting.GetEnemyCasting(Range.Earshot.value)
                if casting_enemy != 0:
                    yield from _CastSkill(casting_enemy, self.terminal_velocity, aftercast)
                    return
                bleeding_enemy = Routines.Targeting.GetEnemyBleeding(Range.Earshot.value)

                if bleeding_enemy != 0:
                    yield from _CastSkill(bleeding_enemy, self.terminal_velocity, aftercast)
                
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.gravestone_marker)):
                spirit_enemy = Routines.Targeting.GetNearestSpirit(Range.Earshot.value)
                if spirit_enemy != 0:
                    yield from _CastSkill(spirit_enemy, self.gravestone_marker, aftercast)
                    return
                gravestone_enemy = Routines.Targeting.GetEnemyHealthy(Range.Earshot.value)
                if gravestone_enemy != 0:
                    yield from _CastSkill(gravestone_enemy, self.gravestone_marker, aftercast)
                    
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.rain_of_arrows)):
                spirit_enemy = Routines.Targeting.GetNearestSpirit(Range.Earshot.value)
                if spirit_enemy != 0:
                    yield from _CastSkill(spirit_enemy, self.rain_of_arrows, aftercast)
                    return
                enemy = Routines.Targeting.TargetClusteredEnemy(Range.Earshot.value)
                if enemy != 0:
                    yield from _CastSkill(enemy, self.rain_of_arrows, aftercast)
                    return

           
        yield from self.auto_combat_handler.ProcessSkillCasting()