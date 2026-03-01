import math
import time

from Py4GWCoreLib import (GLOBAL_CACHE, Agent, Player, Routines, BuildMgr, Range, Py4GW, ConsoleLog,
                          Map, ActionQueueManager, AgentArray, AutoPathing)
from .AutoCombat import AutoCombat

# ── Combat AI constants ───────────────────────────────────────────────────────
_MIKU_MODEL_ID          = 8456

_SHADOWSONG_ID          = 4264
_SOS_SPIRIT_IDS         = frozenset({4280, 4281, 4282})  # Anger, Hate, Suffering
_AOE_SKILLS             = {1380: 2000, 1372: 2000, 1083: 2000, 830: 2000, 192: 5000}
_SPIRIT_FLEE_DIST       = 2000.0
_AOE_SIDESTEP_DIST      = 600.0

# White Mantle Ritualist priority targets (kill priority order, highest first).
_PRIORITY_TARGET_MODELS = [
    #8314,  # PRIMARY  – Shadowsong / Bloodsong / Pain / Anguish rit
    8312,   # PRIMARY  – Rit/Monk: Preservation, strong heal, hex-remove, spirits
    8316,   # PRIORITY – Weapon of Remedy rit (hard-rez)
    8286,
    8287,   #            Abbot Mantra of Recall
    8288,   #            Abbot Restore Condition
    5818,   #            Mesmer Word of Healing
    8311,   #            Rit/Paragon spear caster
    #8313,  #            SoS rit
    8315,   # 2nd prio – Minion-summoning rit
    8267,   #            Ritualist (additional)
    8302,   #            Seeker 1
    8304,   #            Seeker 2 Conjure Flames

    #4264,  #            Shadowsong
    #4280,  #            Anger
    #4281,  #            Hate
    #4282,  #            Suffering
    #5771,  #            Anguish
    #4278,  #            Bloodsong
    #4265   #            Pain
]
_TARGET_SWITCH_INTERVAL = 1.0   # seconds between priority-target scans
_PRIORITY_TARGET_RANGE  = 1500  # only consider priority enemies within this distance
_WEAPON_RANGE           = Range.Longbow

# ── Module-level helper functions ─────────────────────────────────────────────

def _dist(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def _escape_point(me_x: float, me_y: float, threat_x: float, threat_y: float, dist: float, rotation: int = 0):
    """Return a point 'dist' away from threat, in the direction away from it.

    Tries navmesh-aware pathfinding; falls back to a straight-line escape if
    the navmesh is not yet loaded.
    """
    navmesh = AutoPathing().get_navmesh()  # read the module-level cache; None until _init_navmesh() succeeds

    dx = me_x - threat_x
    dy = me_y - threat_y
    escape_radians = math.atan2(dy, dx)
    escape_x   = me_x + dist * math.cos(escape_radians)
    escape_y   = me_y + dist * math.sin(escape_radians)

    # Sanity check: if the computed point is actually closer to the threat, flip 180°
    if _dist(escape_x, escape_y, threat_x, threat_y) < _dist(me_x, me_y, threat_x, threat_y):
        escape_radians += math.pi
        escape_x = me_x + dist * math.cos(escape_radians)
        escape_y = me_y + dist * math.sin(escape_radians)

    escape_pos = (escape_x, escape_y)

    # Try to find a walkable long-range point in the escape direction.
    # Rotate ±15° per step (up to ±180°) until a valid trapezoid is found.
    escape_x_far = me_x + 1500.0 * math.cos(escape_radians)
    escape_y_far = me_y + 1500.0 * math.sin(escape_radians)

    if navmesh:
        #Py4GW.Console.Log("KeiranThackerayEOTN", f"Navmesh fucking loaded", Py4GW.Console.MessageType.Warning)
        base_deg = math.degrees(escape_radians)
        found = False

        if rotation != 0:
            base_deg = (base_deg - rotation) % 360 - 180

        #ConsoleLog("Navmesh", f"Initinal Degree of Escape - {base_deg}", Py4GW.Console.MessageType.Warning)
        # Check the direct escape direction first before rotating
        if navmesh.find_trapezoid_id_by_coord((escape_x_far, escape_y_far)) is not None:
            if navmesh.has_line_of_sight((me_x, me_y), (escape_x_far, escape_y_far)):
                #ConsoleLog("Navmesh", f"Initial Escape Route is Good!", Py4GW.Console.MessageType.Warning)
                found = True
        else:
            for step in range(1, 13):       # 12 steps × 15° = 180° sweep each direction
                for sign in (1, -1):
                    #ConsoleLog("Navmesh", f"Attempting Step: {step}", Py4GW.Console.MessageType.Warning)
                    candidate_deg  = (base_deg + sign * step * 15) % 360 - 180        
                    candidate_rads = math.radians(candidate_deg)
                    #ConsoleLog("Navmesh", f"Testing Degree - {candidate_deg}", Py4GW.Console.MessageType.Warning)
                    escape_x_far   = me_x + 1500.0 * math.cos(candidate_rads)
                    escape_y_far   = me_y + 1500.0 * math.sin(candidate_rads)
                    goal_trap      = navmesh.find_trapezoid_id_by_coord((escape_x_far, escape_y_far))
                    if goal_trap:
                        if navmesh.has_line_of_sight((me_x, me_y), (escape_x_far, escape_y_far)):
                            #ConsoleLog("Navmesh", f"New Escape Route is Good!", Py4GW.Console.MessageType.Warning)
                            escape_radians   = candidate_rads
                            escape_x   = me_x + dist * math.cos(escape_radians)
                            escape_y   = me_y + dist * math.sin(escape_radians)
                            escape_pos = (escape_x, escape_y)
                            found = True
                            break
                    #ConsoleLog("Navmesh", f"Step: {step} Failed", Py4GW.Console.MessageType.Warning)
                if found:
                    break

    return escape_pos


# ── Build class ───────────────────────────────────────────────────────────────

class KeiranThackerayEOTN(BuildMgr):
    def __init__(self, fsm=None):
        super().__init__(name="AutoCombat Build")
        self.auto_combat_handler: BuildMgr = AutoCombat()

        self.natures_blessing   = GLOBAL_CACHE.Skill.GetID("Natures_Blessing")
        self.relentless_assault = GLOBAL_CACHE.Skill.GetID("Relentless_Assault")
        self.keiran_sniper_shot = GLOBAL_CACHE.Skill.GetID("Keirans_Sniper_Shot_Hearts_of_the_North")
        self.terminal_velocity  = GLOBAL_CACHE.Skill.GetID("Terminal_Velocity")
        self.gravestone_marker  = GLOBAL_CACHE.Skill.GetID("Gravestone_Marker")
        self.rain_of_arrows     = GLOBAL_CACHE.Skill.GetID("Rain_of_Arrows")

        # Priority-target state (persists between calls)
        self.last_target_check = 0.0
        self.locked_target_id  = 0
        self.locked_priority   = len(_PRIORITY_TARGET_MODELS)

        # Movement / combat-AI state (persists between calls)
        self.last_movement_run = 0.0
        self.miku_idle         = False
        self.me_combat         = False
        self.me_moving         = False
        self.miku_lazy         = 0
        self.miku_lazy_at      = 0.0
        self.aoe_caster_id     = 0
        self.aoe_sidestep_at   = 0.0
        self.last_cast_at      = 0.0   # tracks when the last attack skill was cast
        self.combat_approach_at = 0.0  # next timestamp to step toward nearest enemy

        # FSM pause/resume support
        self.fsm           = fsm
        self.pause_reasons: set = set()
        self.ai_paused_fsm = False

        for slot in range(1, 7):
            self.auto_combat_handler.auto_combat_handler.SetSkillEnabled(slot, False)

    def set_fsm(self, fsm) -> None:
        """Inject the bot's FSM so ProcessSkillCasting can pause/resume it."""
        self.fsm = fsm

    def _set_pause(self, reason: str) -> None:
        self.pause_reasons.add(reason)
        if self.fsm is not None and not self.fsm.is_paused():
            self.fsm.pause()
            self.ai_paused_fsm = True

    def _clear_pause(self, reason: str) -> None:
        self.pause_reasons.discard(reason)
        if (self.fsm is not None and not self.pause_reasons
                and self.ai_paused_fsm and self.fsm.is_paused()):
            self.fsm.resume()
            self.ai_paused_fsm = False

    def ProcessSkillCasting(self):
        """Managed coroutine called every frame.

        Top section: movement / combat-AI (Miku tracking, spirit avoidance,
                     AoE sidestep, kiting).
        Bottom section: skill priority ladder.
        """
        me_id = Player.GetAgentID()
        if not Agent.IsValid(me_id) or Agent.IsDead(me_id):
            yield
            return
        me_x, me_y  = Agent.GetXY(me_id)
        enemy_array = AgentArray.GetEnemyArray()
        now         = time.time()

        # ══════════════════════════════════════════════════════════════════════
        # MOVEMENT / COMBAT-AI
        # ══════════════════════════════════════════════════════════════════════

        # ── Miku tracking ─────────────────────────────────────────────────────
        miku_id   = Routines.Agents.GetAgentIDByModelID(_MIKU_MODEL_ID)
        miku_dead = miku_id != 0 and Agent.IsDead(miku_id)
        if miku_id != 0 and not miku_dead:
            self.miku_idle = Agent.IsIdle(miku_id)
            
        if not miku_dead:
            mk_x, mk_y = Agent.GetXY(miku_id)
            enemies_near_miku = Routines.Agents.GetFilteredEnemyArray(mk_x, mk_y, 1000)
            #miku_far = _dist(me_x, me_y, mk_x, mk_y) > _MIKU_FAR_DIST
            if (Agent.IsIdle(miku_id) and not Agent.IsInCombatStance(miku_id) and len(enemies_near_miku) == 0):
                self.miku_idle = True
            else:
                self.miku_idle = False

        # If Miku is dead and player is still in combat, kite to safety
        if miku_dead and self.me_combat and len(Routines.Agents.GetFilteredEnemyArray(me_x, me_y, 2000)) > 2:
            self._clear_pause("miku_dead")
            nearest_enemy = Routines.Agents.GetNearestEnemy(Range.Earshot.value)
            ne_x, ne_y    = Agent.GetXY(nearest_enemy)
            me_x, me_y  = Agent.GetXY(me_id)
            ex_x, ex_y    = _escape_point(me_x, me_y, ne_x, ne_y, 1500)
            ActionQueueManager().ResetAllQueues()
            Player.Move(ex_x, ex_y)
            yield from Routines.Yield.wait(500)
            return
        elif miku_dead and not self.me_combat:
            self._set_pause("miku_dead")
        else:
            self._clear_pause("miku_dead")

        # ── Spirit avoidance ──────────────────────────────────────────────────
        spirit_id = 0
        sp_x = sp_y = 0.0
        for eid in enemy_array:
            if Agent.IsDead(eid):
                continue
            model = Agent.GetModelID(eid)
            if model == _SHADOWSONG_ID or model in _SOS_SPIRIT_IDS:
                ex, ey = Agent.GetXY(eid)
                if _dist(me_x, me_y, ex, ey) < _SPIRIT_FLEE_DIST:
                    spirit_id = eid
                    sp_x, sp_y = ex, ey
                    break

        if spirit_id != 0:
            self._set_pause("spirit")
        else:
            self._clear_pause("spirit")

        # ── Movement (throttled to once per second) ───────────────────────────
        player_health     = Agent.GetHealth(me_id)
        enemy_array_close = Routines.Agents.GetFilteredEnemyArray(me_x, me_y, 500, True)
        enemies_in_range  = Routines.Agents.GetFilteredEnemyArray(me_x, me_y, 2000, True)
        self.me_moving = Agent.IsMoving(me_id)
        if Agent.IsInCombatStance(me_id) and len(enemies_in_range) > 0:
            self.me_combat = True
        else:
            self.me_combat = False

        # Start/reset the 20-second combat-approach timer
        if self.me_combat and self.combat_approach_at == 0.0:
            self.combat_approach_at = now + 20.0
        elif not self.me_combat:
            self.combat_approach_at = 0.0

        # Flee spirits while other enemies are alive, or player is low
        if (spirit_id != 0 and (len(enemies_in_range) > 1 or player_health < 0.5)) and now - self.last_movement_run >= 1.0:
            Py4GW.Console.Log("Avoidance", f"Spirit Trigger - {len(enemies_in_range)} Enemies", Py4GW.Console.MessageType.Warning)
            ex_x, ex_y = _escape_point(me_x, me_y, sp_x, sp_y, 600)
            ActionQueueManager().ResetAllQueues()
            self.last_movement_run = now
            Player.Move(ex_x, ex_y)
            yield from Routines.Yield.wait(500)
            return

        # Kite if overwhelmed or low health (no spirit present)
        if (spirit_id == 0 and (len(enemies_in_range) > 4 or player_health < 0.5)) and now - self.last_movement_run >= 1.0:
            Py4GW.Console.Log("Avoidance", f"Overwhelmed Trigger", Py4GW.Console.MessageType.Warning)
            nearest_enemy = Routines.Agents.GetNearestEnemy(1500)
            ne_x, ne_y   = Agent.GetXY(nearest_enemy)
            ex_x, ex_y   = _escape_point(me_x, me_y, ne_x, ne_y, 600)
            ActionQueueManager().ResetAllQueues()
            self.last_movement_run = now
            Player.Move(ex_x, ex_y)
            yield from Routines.Yield.wait(500)
            return

        # Nudge player away from enemies to force Miku into combat
        if self.me_combat and self.miku_idle:
            if self.miku_lazy_at == 0.0:
                self.miku_lazy_at = now                         # start the 3-second delay
            elif now - self.miku_lazy_at >= 3.0 and now - self.last_movement_run >= 1.0:
                Py4GW.Console.Log("Avoidance", f"Miku Lazy Trigger", Py4GW.Console.MessageType.Warning)
                nearest_enemy      = Routines.Agents.GetNearestEnemy(1500)
                ne_x, ne_y         = Agent.GetXY(nearest_enemy)
                ex_x, ex_y         = _escape_point(me_x, me_y, ne_x, ne_y, 300)
                ActionQueueManager().ResetAllQueues()
                self.last_movement_run = now
                self.miku_lazy_at      = now                    # reset for next 3-second window
                Player.Move(ex_x, ex_y)
                yield from Routines.Yield.wait(500)
        else:
            self.miku_lazy_at = 0.0                             # condition cleared, reset timer

        # Kite if two or more enemies are within melee range
        if len(enemy_array_close) > 1 and now - self.last_movement_run >= 1.0:
            Py4GW.Console.Log("Avoidance", f"Melee Swarm Trigger", Py4GW.Console.MessageType.Warning)
            avg_x = sum(Agent.GetXY(eid)[0] for eid in enemy_array_close) / len(enemy_array_close)
            avg_y = sum(Agent.GetXY(eid)[1] for eid in enemy_array_close) / len(enemy_array_close)
            ex_x, ex_y = _escape_point(me_x, me_y, avg_x, avg_y, 600)
            ActionQueueManager().ResetAllQueues()
            self.last_movement_run = now
            Player.Move(ex_x, ex_y)
            yield from Routines.Yield.wait(500)
            return

        # Step toward nearest enemy every 20 s in combat to ensure LOS / range
        if (self.me_combat and self.combat_approach_at != 0.0 and
                now >= self.combat_approach_at and now - self.last_movement_run >= 1.0):
            Py4GW.Console.Log("Avoidance", f"Combat Approach Trigger", Py4GW.Console.MessageType.Warning)
            nearest_enemy = Routines.Agents.GetNearestEnemy(2000)
            if nearest_enemy != 0:
                ne_x, ne_y = Agent.GetXY(nearest_enemy)
                ex_x, ex_y   = _escape_point(me_x, me_y, ne_x, ne_y, 750, rotation=180)
                ActionQueueManager().ResetAllQueues()
                self.last_movement_run  = now
                self.combat_approach_at = now + 15.0
                Player.Move(ex_x, ex_y)
                yield from Routines.Yield.wait(500)
                return
            else:
                self.combat_approach_at = 15 + 20.0

        # ── AoE sidestep ──────────────────────────────────────────────────────
        if self.aoe_caster_id != 0 and now >= self.aoe_sidestep_at:
            if Agent.IsValid(self.aoe_caster_id) and not Agent.IsDead(self.aoe_caster_id):
                tx, ty = Agent.GetXY(self.aoe_caster_id)
                sx, sy = _escape_point(me_x, me_y, tx, ty, _AOE_SIDESTEP_DIST, rotation=90)
                ActionQueueManager().ResetAllQueues()
                Player.Move(sx, sy)
                yield from Routines.Yield.wait(500)
                self.last_movement_run = now
            self.aoe_caster_id = 0
            return  # skip skill casting this frame after a sidestep
        elif self.aoe_caster_id == 0:
            for eid in enemy_array:
                if Agent.IsDead(eid):
                    continue
                skill = Agent.GetCastingSkillID(eid)
                if skill in _AOE_SKILLS:
                    self.aoe_sidestep_at = now + _AOE_SKILLS[skill] / 1000.0
                    self.aoe_caster_id   = eid
                    break

        # ══════════════════════════════════════════════════════════════════════
        # SKILL CASTING
        # ══════════════════════════════════════════════════════════════════════

        # ── Empathy / Spirit Shackles detection ───────────────────────────────
        has_empathy = (
            Routines.Checks.Agents.HasEffect(me_id, GLOBAL_CACHE.Skill.GetID("Empathy")) or
            Routines.Checks.Agents.HasEffect(me_id, GLOBAL_CACHE.Skill.GetID("Empathy_(PVP)")) or
            Routines.Checks.Agents.HasEffect(me_id, GLOBAL_CACHE.Skill.GetID("Spirit_Shackles"))
        )
        if has_empathy:
            Player.ChangeTarget(0)

        # ── Priority target selection (interval-gated) ────────────────────────
        if now - self.last_target_check >= _TARGET_SWITCH_INTERVAL:
            self.last_target_check = now

            # Drop the locked target if it is dead or out of range
            if self.locked_target_id != 0:
                lx, ly = Agent.GetXY(self.locked_target_id)
                if (not Agent.IsValid(self.locked_target_id) or
                        Agent.IsDead(self.locked_target_id) or
                        _dist(me_x, me_y, lx, ly) > _PRIORITY_TARGET_RANGE):
                    self.locked_target_id = 0
                    self.locked_priority  = len(_PRIORITY_TARGET_MODELS)

            # Scan for a strictly higher-priority (lower index) target
            best_id       = 0
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
                        best_id       = eid

            if best_id != 0 and best_priority < self.locked_priority:
                self.locked_target_id = best_id
                self.locked_priority  = best_priority

            if self.locked_target_id != 0:
                Player.ChangeTarget(self.locked_target_id)

        # ── Nature's Blessing — heal Keiran or Miku ───────────────────────────
        life_threshold = 0.80
        if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.natures_blessing)):
            player_life      = Agent.GetHealth(me_id)
            miku_low_on_life = False
            nearest_npc      = Routines.Agents.GetNearestNPC(2000)
            if (nearest_npc != 0 and not Agent.IsDead(nearest_npc) and
                    Agent.GetModelID(nearest_npc) == _MIKU_MODEL_ID):
                miku_low_on_life = Agent.GetHealth(nearest_npc) < life_threshold
            if player_life < life_threshold or miku_low_on_life:
                ActionQueueManager().ResetAllQueues()
                yield from Routines.Yield.Skills.CastSkillID(self.natures_blessing, aftercast_delay=100)
                return

        # ── Guard: only proceed when we can act ───────────────────────────────
        if not (Routines.Checks.Map.IsExplorable() and
                Routines.Checks.Player.CanAct() and
                Routines.Checks.Skills.CanCast()):
            ActionQueueManager().ResetAllQueues()
            yield from Routines.Yield.wait(1000)
            return

        # Skip attacks during aftercast window — healing and avoidance fire each frame
        if now - self.last_cast_at < 0.750:
            yield
            return

        def _cast(target, skill_id):
            if Routines.Checks.Map.IsExplorable():
                yield from Routines.Yield.Agents.ChangeTarget(target)
                yield from Routines.Yield.Skills.CastSkillID(skill_id, aftercast_delay=0)
            yield

        # ── Skill ladder (only when the AI is in weapon range) ──────────────────────
        in_danger = Routines.Checks.Agents.InDanger(aggro_area=_WEAPON_RANGE)
        if in_danger:
            self._set_pause("danger")
        elif Routines.Yield.Skills.IsSkillIDUsable(self.natures_blessing) or player_health > .90:
            self._clear_pause("danger")

        if in_danger:

            # Keiran's Sniper Shot — finish a hexed enemy
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.keiran_sniper_shot)):
                hexed_enemy = Routines.Targeting.GetEnemyHexed(2000)
                if hexed_enemy != 0 and not has_empathy:
                    ActionQueueManager().ResetAllQueues()
                    self.last_cast_at = now
                    yield from _cast(hexed_enemy, self.keiran_sniper_shot)
                    return

            # Relentless Assault — cleanse a condition from Keiran
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.relentless_assault)):
                player_conditioned = (
                    Agent.IsDegenHexed(me_id) or
                    Agent.IsBleeding(me_id) or
                    Agent.IsPoisoned(me_id) or
                    Routines.Checks.Agents.HasEffect(me_id, GLOBAL_CACHE.Skill.GetID("Blind")) or
                    Routines.Checks.Agents.HasEffect(me_id, GLOBAL_CACHE.Skill.GetID("Deep_Wound")) or
                    Routines.Checks.Agents.HasEffect(me_id, GLOBAL_CACHE.Skill.GetID("Cracked_Armor")) or
                    Routines.Checks.Agents.HasEffect(me_id, GLOBAL_CACHE.Skill.GetID("Burning"))
                )
                if player_conditioned and not has_empathy:
                    target = self.locked_target_id or Routines.Targeting.GetEnemyInjured(_WEAPON_RANGE.value)
                    if target != 0:
                        self.last_cast_at = now
                        yield from _cast(target, self.relentless_assault)
                        return

            # Terminal Velocity — interrupt a caster or apply to a bleeding enemy
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.terminal_velocity)):
                if not has_empathy:
                    target = (self.locked_target_id or
                              Routines.Targeting.GetEnemyCasting(_WEAPON_RANGE.value) or
                              Routines.Targeting.GetEnemyBleeding(_WEAPON_RANGE.value))
                    if target != 0:
                        self.last_cast_at = now
                        yield from _cast(target, self.terminal_velocity)
                        return

            # Gravestone Marker — spirits first, then healthy enemies
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.gravestone_marker)):
                if not has_empathy:
                    target = (self.locked_target_id or
                              Routines.Targeting.GetNearestSpirit(_WEAPON_RANGE.value) or
                              Routines.Targeting.GetEnemyHealthy(_WEAPON_RANGE.value))
                    if target != 0:
                        self.last_cast_at = now
                        yield from _cast(target, self.gravestone_marker)
                        return

            # Rain of Arrows — spirits first, then clustered enemies
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.rain_of_arrows)):
                if not has_empathy:
                    target = (self.locked_target_id or
                              Routines.Targeting.GetNearestSpirit(_WEAPON_RANGE.value) or
                              Routines.Targeting.TargetClusteredEnemy(_WEAPON_RANGE.value))
                    if target != 0:
                        self.last_cast_at = now
                        yield from _cast(target, self.rain_of_arrows)
                        return

        yield from self.auto_combat_handler.ProcessSkillCasting()
