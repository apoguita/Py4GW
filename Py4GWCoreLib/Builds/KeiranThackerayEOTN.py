from Py4GWCoreLib import (GLOBAL_CACHE, Agent, Player, Routines, BuildMgr, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          Map, ImGui, ActionQueueManager, AgentArray)
from .AutoCombat import AutoCombat

# ── Combat AI constants ───────────────────────────────────────────────────────
_MIKU_MODEL_ID      = 8443
_SHADOWSONG_ID      = 4264
_SOS_SPIRIT_IDS     = frozenset({4280, 4281, 4282})  # Anger, Hate, Suffering
_AOE_SKILLS         = {1380: 2000, 1372: 2000, 1083: 2000, 830: 2000, 192: 5000}
_MIKU_MODEL_ID = 8443
_MIKU_FAR_DIST      = 1400.0
_MIKU_CLOSE_DIST    = 1100.0
_SPIRIT_FLEE_DIST   = 1600.0
_AOE_SIDESTEP_DIST  = 500.0

# White Mantle Ritualist priority targets (in kill priority order, highest first).
# IDs are base values + 10 adjustment for post-update model IDs.
_PRIORITY_TARGET_MODELS = [
    8301,  # PRIMARY  – Shadowsong / Bloodsong / Pain / Anguish rit
    8299,  # PRIMARY  – Rit/Monk: Preservation, strong heal, hex-remove, spirits
    8303,  # PRIORITY – Weapon of Remedy rit (hard-rez)
    8298,  #            Rit/Paragon spear caster
    8300,  #            SoS rit
    8302,  # 2nd prio – Minion-summoning rit
    8254,  #            Ritualist (additional)
]
_TARGET_SWITCH_INTERVAL = 1.0   # seconds between priority-target checks
_PRIORITY_TARGET_RANGE  = 1600  # only target priority enemies within this distance

_DEBUG = True

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
        """
        Managed coroutine that runs every frame (even when FSM is paused).
        Handles: Miku dead/far, spirit avoidance, AoE dodge, priority targeting.
        """

        def _escape_point(me_x: float, me_y: float, threat_x: float, threat_y: float, dist: float):
            """Return a point 'dist' away from threat, in the direction away from it."""
            import math
            dx = me_x - threat_x
            dy = me_y - threat_y
            length = math.sqrt(dx * dx + dy * dy)
            if length < 1:
                return me_x + dist, me_y
            return me_x + (dx / length) * dist, me_y + (dy / length) * dist


        def _perp_point(me_x: float, me_y: float, enemy_x: float, enemy_y: float, dist: float):
            """Return a point 'dist' perpendicular to the line from me to enemy."""
            import math
            dx = enemy_x - me_x
            dy = enemy_y - me_y
            length = math.sqrt(dx * dx + dy * dy)
            if length < 1:
                return me_x + dist, me_y
            return me_x + (dy / length) * dist, me_y + (-dx / length) * dist


        def _dist(x1: float, y1: float, x2: float, y2: float) -> float:
            import math
            return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        import time

        last_target_check = 0.0
        locked_target_id = 0                            # priority target we're locked onto
        locked_priority = len(_PRIORITY_TARGET_MODELS)  # priority index of locked target

        me_id = Player.GetAgentID()

        me_x, me_y = Agent.GetXY(me_id)
        enemy_array = AgentArray.GetEnemyArray()

        if (Routines.Checks.Agents.HasEffect(Player.GetAgentID(), GLOBAL_CACHE.Skill.GetID("Empathy")) or 
            Routines.Checks.Agents.HasEffect(Player.GetAgentID(), GLOBAL_CACHE.Skill.GetID("Empathy_(PVP)")) or
            Routines.Checks.Agents.HasEffect(Player.GetAgentID(), GLOBAL_CACHE.Skill.GetID("Spirit_Shackles"))):
            has_empathy = True
            Player.ChangeTarget(0)
            ConsoleLog("Empathy Test", f"Empathy Status: {has_empathy} ", Py4GW.Console.MessageType.Info)
        else:
            has_empathy = False
        
        now = time.time()

        # ── 3. Priority target selection (runs every frame, before movement) ──
        if now - last_target_check >= _TARGET_SWITCH_INTERVAL:
            last_target_check = now
            # Validate locked target: drop it if dead or out of range
            if locked_target_id != 0:
                if not Agent.IsValid(locked_target_id) or Agent.IsDead(locked_target_id):
                    locked_target_id = 0
                    locked_priority = len(_PRIORITY_TARGET_MODELS)
                else:
                    lx, ly = Agent.GetXY(locked_target_id)
                    if _dist(me_x, me_y, lx, ly) > _PRIORITY_TARGET_RANGE:
                        locked_target_id = 0
                        locked_priority = len(_PRIORITY_TARGET_MODELS)
            # Scan for a strictly higher-priority target (or any if none locked)
            best_id = 0
            best_priority = len(_PRIORITY_TARGET_MODELS)
            for eid in enemy_array:
                if Agent.IsDead(eid):
                    continue
                ex, ey = Agent.GetXY(eid)
                if _dist(me_x, me_y, ex, ey) > _PRIORITY_TARGET_RANGE:
                    continue
                model = Agent.GetModelID(eid)
                if model in _PRIORITY_TARGET_MODELS:
                    prio = _PRIORITY_TARGET_MODELS.index(model)
                    if prio < best_priority:
                        best_priority = prio
                        best_id = eid
            # Lock onto new target only if strictly higher priority than current lock
            if best_id != 0 and best_priority < locked_priority:
                locked_target_id = best_id
                locked_priority = best_priority
                ConsoleLog("Target Test",
                            f"Locked priority target: model {_PRIORITY_TARGET_MODELS[locked_priority]} "
                            f"(prio {locked_priority}) agent {locked_target_id}",
                            Py4GW.Console.MessageType.Info)
            # Call the locked target every interval until dead
            if locked_target_id != 0:
                Player.ChangeTarget(locked_target_id)

        life_threshold = 0.80
        if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.natures_blessing)):
            player_life = Agent.GetHealth(Player.GetAgentID())
            low_on_life = player_life < life_threshold

            miku_low_on_life = False
            nearest_npc = Routines.Agents.GetNearestNPC(2000)
            if (nearest_npc != 0 and not Agent.IsDead(nearest_npc)
                    and Agent.GetModelID(nearest_npc) == _MIKU_MODEL_ID):
                miku_life = Agent.GetHealth(nearest_npc)
                miku_low_on_life = miku_life < life_threshold

            if low_on_life or miku_low_on_life:
                yield from Routines.Yield.Skills.CastSkillID(self.natures_blessing, aftercast_delay=100)
                return
            
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
            
        if Routines.Checks.Agents.InDanger():
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.keiran_sniper_shot)):
                hexed_enemy = Routines.Targeting.GetEnemyHexed(2000)
                if hexed_enemy != 0:
                    yield from _CastSkill(hexed_enemy, self.keiran_sniper_shot, aftercast)
                    return

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.relentless_assaunlt)):
                if (Agent.IsDegenHexed(Player.GetAgentID()) or 
                    #Agent.IsConditioned(Player.GetAgentID()) or
                    Agent.IsBleeding(Player.GetAgentID()) or
                    Agent.IsPoisoned(Player.GetAgentID()) or
                    Routines.Checks.Agents.HasEffect(Player.GetAgentID(), GLOBAL_CACHE.Skill.GetID("Deep_Wound")) or
                    Routines.Checks.Agents.HasEffect(Player.GetAgentID(), GLOBAL_CACHE.Skill.GetID("Cracked_Armor")) or
                    Routines.Checks.Agents.HasEffect(Player.GetAgentID(), GLOBAL_CACHE.Skill.GetID("Burning"))):
                    injured_enemy = Routines.Targeting.GetEnemyInjured(1200)
                    enemy = Routines.Targeting.GetEnemyInjured(1200)

                    if locked_target_id != 0 and not has_empathy:
                        Player.ChangeTarget(locked_target_id)
                        yield from _CastSkill(locked_target_id, self.relentless_assaunlt, aftercast)
                        return
                    elif injured_enemy != 0 and not has_empathy:
                        yield from _CastSkill(injured_enemy, self.relentless_assaunlt, aftercast)
                        return
                    elif enemy != 0 and not has_empathy:
                        yield from _CastSkill(enemy, self.relentless_assaunlt, aftercast)
                        return
                    
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.terminal_velocity)):
                casting_enemy = Routines.Targeting.GetEnemyCasting(1500)
                if locked_target_id != 0 and not has_empathy:
                    yield from _CastSkill(locked_target_id, self.terminal_velocity, aftercast)
                    return
                elif casting_enemy != 0 and not has_empathy:
                    yield from _CastSkill(casting_enemy, self.terminal_velocity, aftercast)
                    return
                bleeding_enemy = Routines.Targeting.GetEnemyBleeding(1500)

                if locked_target_id != 0 and not has_empathy:
                    yield from _CastSkill(locked_target_id, self.terminal_velocity, aftercast)
                    return
                elif bleeding_enemy != 0 and not has_empathy:
                    yield from _CastSkill(bleeding_enemy, self.terminal_velocity, aftercast)
                
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.gravestone_marker)):
                spirit_enemy = Routines.Targeting.GetNearestSpirit(1500)
                if locked_target_id != 0 and not has_empathy:
                    yield from _CastSkill(locked_target_id, self.gravestone_marker, aftercast)
                    return
                elif spirit_enemy != 0 and not has_empathy:
                    yield from _CastSkill(spirit_enemy, self.gravestone_marker, aftercast)
                    return
                
                gravestone_enemy = Routines.Targeting.GetEnemyHealthy(1500)
                if locked_target_id != 0 and not has_empathy:
                    yield from _CastSkill(locked_target_id, self.gravestone_marker, aftercast)
                    return
                elif gravestone_enemy != 0 and not has_empathy:
                    yield from _CastSkill(gravestone_enemy, self.gravestone_marker, aftercast)
                    return
                
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.rain_of_arrows)):
                spirit_enemy = Routines.Targeting.GetNearestSpirit(1500)
                if locked_target_id != 0 and not has_empathy:
                    yield from _CastSkill(locked_target_id, self.rain_of_arrows, aftercast)
                    return
                elif spirit_enemy != 0:
                    yield from _CastSkill(spirit_enemy, self.rain_of_arrows, aftercast)
                    return
                
                enemy = Routines.Targeting.TargetClusteredEnemy(1500)
                if locked_target_id != 0 and not has_empathy:
                    yield from _CastSkill(locked_target_id, self.rain_of_arrows, aftercast)
                    return
                elif enemy != 0 and not has_empathy:
                    yield from _CastSkill(enemy, self.rain_of_arrows, aftercast)
                    return

           
        yield from self.auto_combat_handler.ProcessSkillCasting()