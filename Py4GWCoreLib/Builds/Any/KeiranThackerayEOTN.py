import ctypes
import math
import time
from typing import Callable, Optional

from Py4GWCoreLib import (GLOBAL_CACHE, Agent, Player, Routines, BuildMgr, Range, Py4GW, ConsoleLog,
                          Map, ActionQueueManager, AgentArray, AutoPathing)
#from Py4GWCoreLib.CombatEvents import CombatEvents as CombatEvents   # import the manager directly to avoid module shadowing
from .HeroAI import HeroAI_Build

# ── Combat AI constants ───────────────────────────────────────────────────────
_MIKU_MODEL_ID = 8513

_SHADOWSONG_ID          = 4264
_SOS_SPIRIT_IDS         = frozenset({4280, 4281, 4282})  # Anger, Hate, Suffering
_AOE_SKILLS             = {1380: 2000, 1372: 2000, 1083: 2000, 830: 2000, 192: 5000}
_SPIRIT_FLEE_DIST       = 1900
_AOE_SIDESTEP_DIST      = 600.0

_MIKU_PATH = [
    # initial stretch after entering map
    (10165.07, -6181.43),
    (8270.00, -9010.00),
    (4245.00, -7412.00),
    (2025.00, -10726.00),
    (-1822.00, -11230.00),
    (-2292.00, -9034.00),
    (-4190.00, -10460.00),
    (-5640.00, -10371.00),
    (-8748.00, -8329.00),
    (-12122.00, -7530.00),
    (-15170.00, -8951.00),
]

# White Mantle Ritualist priority targets (kill priority order, highest first).
_PRIORITY_TARGET_MODELS = [
    8369,   #           Ritualist: Preservation, strong heal, hex-remove, spirits
    8373,   #           Ritualist: Weapon of Remedy rit (hard-rez)
    8343,   #           Abbot: Prot Boon Signet, Spiritbond
    8344,   #           Abbot: Mantra of Recall
    8345,   #           Abbot: Restore Condition
    8322,   #           Sycophant: Word of Healing
    8368,   #           Ritualist: spear caster
    8372,   #           Ritualist: Minion-summoning rit
    8324,   #           Ritualist (additional)
    8359,   #           Seeker 1
    8361,   #           Seeker 2 Conjure Flames

]
_TARGET_SWITCH_INTERVAL = 1.0   # seconds between priority-target scans
_PRIORITY_TARGET_RANGE  = 1500  # only consider priority enemies within this distance
_WEAPON_RANGE           = Range.Longbow

# ── Module-level helper functions ─────────────────────────────────────────────

def _dist(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def _escape_point(me_x: float, me_y: float, threat_x: float, threat_y: float, dist: float, rotation: int = 0, debug_fn=None):
    """Return a point 'dist' away from threat, in the direction away from it.

    Tries navmesh-aware pathfinding; falls back to a straight-line escape if
    the navmesh is not yet loaded.
    """
    _dbg = debug_fn if debug_fn is not None else (lambda: False)
    navmesh = AutoPathing().get_navmesh()  # read the module-level cache; None until _init_navmesh() succeeds

    dx = me_x - threat_x
    dy = me_y - threat_y
    escape_radians = math.atan2(dy, dx)

    if rotation != 0:
        escape_radians = escape_radians + math.radians(rotation)

    escape_x   = me_x + dist * math.cos(escape_radians)
    escape_y   = me_y + dist * math.sin(escape_radians)
    escape_x_far   = me_x + 1000 * math.cos(escape_radians)
    escape_y_far   = me_y + 1000 * math.sin(escape_radians)
    escape_pos = (escape_x, escape_y)

    if navmesh:
        base_deg = math.degrees(escape_radians) % 360 - 180
        found = False

        #if _dbg(): ConsoleLog("Navmesh", f"Initial Degree of Escape => {base_deg}", Py4GW.Console.MessageType.Warning)
        # Check the direct escape direction first before rotating
        if navmesh.find_trapezoid_id_by_coord((escape_x_far, escape_y_far)) is not None:
            if navmesh.has_line_of_sight((me_x, me_y), (escape_x_far, escape_y_far)):
                #if _dbg(): ConsoleLog("Navmesh", f"Initial Escape Route is Good!", Py4GW.Console.MessageType.Warning)
                found = True
        if not found:
            for step in range(1, 19):       # 18 steps × 10° = 180° sweep each direction
                for sign in (1, -1):
                    candidate_deg  = (base_deg + sign * step * 10) % 360 - 180
                    candidate_rads = math.radians(candidate_deg)
                    escape_x_far   = me_x + 1000.0 * math.cos(candidate_rads)
                    escape_y_far   = me_y + 1000.0 * math.sin(candidate_rads)
                    goal_trap      = navmesh.find_trapezoid_id_by_coord((escape_x_far, escape_y_far))
                    if goal_trap:
                        if navmesh.has_line_of_sight((me_x, me_y), (escape_x_far, escape_y_far)):
                            #if _dbg(): ConsoleLog("Navmesh", f"New Escape Route is Good!", Py4GW.Console.MessageType.Warning)
                            escape_radians   = candidate_rads
                            escape_x   = me_x + dist * math.cos(escape_radians)
                            escape_y   = me_y + dist * math.sin(escape_radians)
                            escape_pos = (escape_x, escape_y)
                            found = True
                            break
                    #if _dbg(): ConsoleLog("Navmesh", f"Step: {sign * step} Failed", Py4GW.Console.MessageType.Warning)
                if found:
                    break

    return escape_pos

def _nearest_from(array, origin_x: float, origin_y: float, max_dist: float = 0) -> int:
    """Return the ID of the closest agent in *array* to (origin_x, origin_y).

    Optionally restricted to agents within max_dist. Returns 0 if the array is
    empty or no agent falls within the requested range.
    """
    best_id   = 0
    best_dist = float("inf")
    for eid in array:
        ex, ey = Agent.GetXY(eid)
        d = _dist(origin_x, origin_y, ex, ey)
        if max_dist != 0 and d > max_dist:
            continue
        if d < best_dist:
            best_dist = d
            best_id   = eid
    return best_id


# ── Build class ───────────────────────────────────────────────────────────────

class KeiranThackerayEOTN(BuildMgr):
    def __init__(self, fsm=None, debug_fn: Optional[Callable[[], bool]] = None):
        super().__init__(name="Keiran HeroAI Build")
        self.debug_fn: Callable[[], bool] = debug_fn if debug_fn is not None else (lambda: False)
        self.hero_ai_handler: BuildMgr = HeroAI_Build(standalone_fallback=True)

        self.natures_blessing        = GLOBAL_CACHE.Skill.GetID("Natures_Blessing")
        self.relentless_assault      = GLOBAL_CACHE.Skill.GetID("Relentless_Assault")
        self.keiran_sniper_shot      = GLOBAL_CACHE.Skill.GetID("Keirans_Sniper_Shot_Hearts_of_the_North")
        self.terminal_velocity       = GLOBAL_CACHE.Skill.GetID("Terminal_Velocity")
        self.gravestone_marker       = GLOBAL_CACHE.Skill.GetID("Gravestone_Marker")
        self.rain_of_arrows          = GLOBAL_CACHE.Skill.GetID("Rain_of_Arrows")
        self.find_their_weakness     = GLOBAL_CACHE.Skill.GetID("Find_Their_Weakness_Thackeray")
        self.theres_nothing_to_fear  = GLOBAL_CACHE.Skill.GetID("Theres_Nothing_To_Fear_Thackeray")
        # Priority-target state
        self.last_target_check    = 0.0
        self.locked_target_id     = 0
        self.locked_priority      = len(_PRIORITY_TARGET_MODELS)

        # Movement / combat-AI state
        self.last_movement_run    = 0.0
        self.miku_idle            = False
        self.player_combat        = False
        self.miku_lazy_at         = 0.0
        self.miku_reset_at        = 0.0
        self.miku_reset_active    = False
        self.miku_retrace_issued  = False

        # Miku retrace path-following state
        self._retrace_ph          = None
        self._return_ph           = None
        self._miku_follow         = None
        self._retrace_phase       = ''

        # LoS / combat approach
        self.aoe_caster_id        = 0
        self.aoe_caster_pos       = (0.0, 0.0)
        self.aoe_sidestep_at      = 0.0
        self.last_cast_at         = 0.0
        self.combat_approach_at   = 0.0
        self.los_fail_since       = 0.0
        self.los_debug_at         = 0.0

        # FSM pause/resume support
        self.fsm           = fsm
        self.pause_reasons: set = set()
        self.ai_paused_fsm = False

    @property
    def debug(self) -> bool:
        return self.debug_fn()

    def _sync_hero_ai_fallback_skill_blocks(self) -> None:
        blocked_fallback_skill_ids = [
            GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot)
            for slot in range(2, 8)
        ]
        self.hero_ai_handler.ApplyBlockedSkillIDs(blocked_fallback_skill_ids)

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
        player_id = Player.GetAgentID()
        if not Agent.IsValid(player_id) or Agent.IsDead(player_id):
            yield
            return
        player_x, player_y  = Agent.GetXY(player_id)
        _raw        = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByCondition(
            _raw,
            lambda eid: Agent.IsValid(eid) and not Agent.IsDead(eid) and Agent.GetHealth(eid) > 0.0
        )
        now         = time.time()

        # ── Empathy / Spirit Shackles detection (early -- needed by LoS block) ─
        empathy_id         = GLOBAL_CACHE.Skill.GetID("Empathy")
        spirit_shackles_id = GLOBAL_CACHE.Skill.GetID("Spirit_Shackles")
        has_empathy = (
            Routines.Checks.Agents.HasEffect(player_id, empathy_id) or
            Routines.Checks.Agents.HasEffect(player_id, spirit_shackles_id)
        )

        # ══════════════════════════════════════════════════════════════════════
        # MOVEMENT / COMBAT-AI
        # ══════════════════════════════════════════════════════════════════════
        # ── Movement (throttled to once per second) ───────────────────────────
        player_health     = Agent.GetHealth(player_id)
        enemies_close = AgentArray.Filter.ByCondition(enemy_array, lambda eid: _dist(player_x, player_y, *Agent.GetXY(eid)) <= 300)
        enemies_agro = AgentArray.Filter.ByCondition(enemy_array, lambda eid: _dist(player_x, player_y, *Agent.GetXY(eid)) <= 1500)
        enemies_far  = AgentArray.Filter.ByCondition(enemy_array, lambda eid: _dist(player_x, player_y, *Agent.GetXY(eid)) <= 2000)
        if Agent.IsInCombatStance(player_id) and len(enemies_far) > 0:
            self.player_combat = True
        else:
            self.player_combat = False

        # ── Miku tracking ─────────────────────────────────────────────────────
        miku_id   = Routines.Agents.GetAgentIDByModelID(_MIKU_MODEL_ID)
        miku_dead = miku_id != 0 and Agent.IsDead(miku_id)
        miku_reset = miku_id == 0 and Map.GetMapID() == 849

        if miku_id != 0 and not miku_dead:
            mk_x, mk_y = Agent.GetXY(miku_id)
            enemies_near_miku = AgentArray.Filter.ByCondition(enemy_array, lambda eid: _dist(mk_x, mk_y, *Agent.GetXY(eid)) <= 1000)
            self.miku_idle = (Agent.IsIdle(miku_id) and not Agent.IsInCombatStance(miku_id) and len(enemies_near_miku) == 0)
        else:
            # Miku is dead or absent -- clear idle flag so the lazy-Miku trigger
            # cannot fire with stale state in the current or next combat.
            self.miku_idle = False

        # Miku dead -- hold FSM path only when out of combat.
        # While in combat, keep fighting normally; overwhelmed and critical HP triggers handle retreat.
                    # Miku dead -- retreat from enemies until she revives
        if miku_dead and self.player_combat and len(enemies_far) > 1 and now - self.last_movement_run >= 1.0:
            if self.debug:
                Py4GW.Console.Log("Avoidance", "Miku Dead Trigger -- retreating", Py4GW.Console.MessageType.Warning)
            avg_x = sum(Agent.GetXY(eid)[0] for eid in enemies_far) / len(enemies_far)
            avg_y = sum(Agent.GetXY(eid)[1] for eid in enemies_far) / len(enemies_far)
            ex_x, ex_y = _escape_point(player_x, player_y, avg_x, avg_y, 300, debug_fn=self.debug_fn)
            ActionQueueManager().ResetAllQueues()
            self.last_movement_run  = now
            self.combat_approach_at = 0.0
            self.los_fail_since     = 0.0
            Player.Move(ex_x, ex_y)
            yield from Routines.Yield.wait(500)
            return
        elif miku_dead and not self.player_combat:
            self._set_pause("miku_dead")
        else:
            self._clear_pause("miku_dead")

        # If Miku fell through the world, activate reset and issue the backtrack once after 5 s.
        if miku_reset:
            Py4GW.Console.Log("Miku Model ID", f"{_MIKU_MODEL_ID}", Py4GW.Console.MessageType.Warning)
            Py4GW.Console.Log("Miku ID", f"{miku_id}", Py4GW.Console.MessageType.Warning)
            self.miku_reset_active = True
            if self.miku_reset_at == 0.0:
                self.miku_reset_at = now                        # start the 5-second window
            elif now - self.miku_reset_at >= 5.0 and not self.miku_retrace_issued:
                if self.debug:
                    Py4GW.Console.Log("Avoidance", "Miku Reset - retracing path", Py4GW.Console.MessageType.Warning)
                # Find the path index closest to current location
                nearest_idx = min(range(len(_MIKU_PATH)), key=lambda i: _dist(player_x, player_y, *_MIKU_PATH[i]))
                # Step one point back if possible so retrace starts "behind" us
                start_idx = nearest_idx - 1 if nearest_idx > 0 else 0
                _retrace_coords = list(reversed(_MIKU_PATH[: start_idx + 1]))   # backward: start_idx → 0
                _return_coords  = list(_MIKU_PATH[: nearest_idx + 1])            # forward:  0 → nearest_idx

                self._retrace_ph    = Routines.Movement.PathHandler(_retrace_coords)
                self._return_ph     = Routines.Movement.PathHandler(_return_coords)
                self._miku_follow   = Routines.Movement.FollowXY(tolerance=150)
                self._retrace_phase = 'retrace'

                self.miku_retrace_issued = True
                self._set_pause("miku_reset")
        # ── Drive the active retrace/return leg one frame at a time ──────────
        if self._retrace_phase:
            _ph = self._retrace_ph if self._retrace_phase == 'retrace' else self._return_ph
            Routines.Movement.FollowPath(_ph, self._miku_follow)
            if Routines.Movement.IsFollowPathFinished(_ph, self._miku_follow):
                if self._retrace_phase == 'retrace':
                    # Backward leg done -- start the forward leg with a fresh follow handler
                    self._miku_follow   = Routines.Movement.FollowXY(tolerance=150)
                    self._retrace_phase = 'return'
                else:
                    # Round-trip complete -- clear all state and resume FSM
                    self.miku_reset_active   = False
                    self.miku_reset_at       = 0.0
                    self.miku_retrace_issued = False
                    self._retrace_ph         = None
                    self._return_ph          = None
                    self._miku_follow        = None
                    self._retrace_phase      = ''
                    self._clear_pause("miku_reset")
            yield
            return

        # While waiting for the 5-second timer before the retrace begins,
        # hold the FSM paused and idle each frame.
        if self.miku_reset_active:
            self._set_pause("miku_reset")
            yield
            return

        # ── Spirit avoidance ──────────────────────────────────────────────────
        spirit_id = 0
        sp_x = sp_y = 0.0
        for eid in enemy_array:
            model = Agent.GetModelID(eid)
            if model == _SHADOWSONG_ID or model in _SOS_SPIRIT_IDS:
                ex, ey = Agent.GetXY(eid)
                if _dist(player_x, player_y, ex, ey) < _SPIRIT_FLEE_DIST:
                    spirit_id = eid
                    sp_x, sp_y = ex, ey
                    break

        if spirit_id != 0:
            self._set_pause("spirit")
        else:
            self._clear_pause("spirit")


        if Routines.Checks.Player.CanAct():
            # Start/reset the LOS-check grace period (3 s after entering combat)
            if self.player_combat and self.combat_approach_at == 0.0:
                self.combat_approach_at = now + 3.0
            elif not self.player_combat:
                # Combat ended -- reset per-encounter state so fight N doesn't bleed into fight N+1.
                self.combat_approach_at   = 0.0
                self.los_fail_since       = 0.0
                self.locked_target_id     = 0
                self.locked_priority      = len(_PRIORITY_TARGET_MODELS)
                        # Clear miku lazy timer so the 3-second delay is always respected
                # at the start of the next encounter, not bypassed by a leftover stamp.
                self.miku_lazy_at         = 0.0
                # Clear any stale AoE caster so fight N+1 doesn't open with a sidestep
                # toward a position from fight N.
                self.aoe_caster_id        = 0
                self.aoe_caster_pos       = (0.0, 0.0)

            # Flee spirits while other enemies are alive
            if spirit_id != 0 and len(enemies_far) > 4 and now - self.last_movement_run >= 1.0:
                if self.debug:
                    Py4GW.Console.Log("Avoidance", f"Spirit Trigger - {len(enemies_far)} Enemies", Py4GW.Console.MessageType.Warning)
                ex_x, ex_y = _escape_point(player_x, player_y, sp_x, sp_y, 500, debug_fn=self.debug_fn)
                ActionQueueManager().ResetAllQueues()
                self.last_movement_run  = now
                self.combat_approach_at = 0.0
                self.los_fail_since     = 0.0
                Player.Move(ex_x, ex_y)
                yield from Routines.Yield.wait(500)
                return

            # Basic avoidance when spirits are not present
            if spirit_id == 0 and len(enemies_agro) > 4 and now - self.last_movement_run >= 1.0:
                if self.debug:
                    Py4GW.Console.Log("Avoidance", f"Overwhelmed Trigger - {len(enemies_agro)} Enemies", Py4GW.Console.MessageType.Warning)
                avg_x = sum(Agent.GetXY(eid)[0] for eid in enemies_far) / len(enemies_far)
                avg_y = sum(Agent.GetXY(eid)[1] for eid in enemies_far) / len(enemies_far)
                ex_x, ex_y = _escape_point(player_x, player_y, avg_x, avg_y, 300, debug_fn=self.debug_fn)
                ActionQueueManager().ResetAllQueues()
                self.last_movement_run  = now
                self.combat_approach_at = 0.0
                self.los_fail_since     = 0.0
                Player.Move(ex_x, ex_y)
                yield from Routines.Yield.wait(500)
                return

            # Critical HP -- retreat regardless of spirit state
            if player_health < 0.5 and len(enemies_far) > 0 and now - self.last_movement_run >= 1.0:
                if self.debug:
                    Py4GW.Console.Log("Avoidance", f"Critical HP Trigger - {player_health:.0%} HP", Py4GW.Console.MessageType.Warning)
                avg_x = sum(Agent.GetXY(eid)[0] for eid in enemies_far) / len(enemies_far)
                avg_y = sum(Agent.GetXY(eid)[1] for eid in enemies_far) / len(enemies_far)
                ex_x, ex_y = _escape_point(player_x, player_y, avg_x, avg_y, 300, debug_fn=self.debug_fn)
                ActionQueueManager().ResetAllQueues()
                self.last_movement_run  = now
                self.combat_approach_at = 0.0
                self.los_fail_since     = 0.0
                Player.Move(ex_x, ex_y)
                yield from Routines.Yield.wait(500)
                return

            # ── Hit detection (shared by lazy Miku and LoS blocks below) ──────────
            # CombatEvents timestamps are GetTickCount() ms -- not time.time().
            _LOS_WINDOW_MS = 4000   # ms with no outgoing hits before gap-close triggers
            _tick_now      = ctypes.windll.kernel32.GetTickCount()
            _los_recent    = [] #CombatEvents.GetRecentDamage(count=100)
            damage_dealt   = any(
                src == player_id and (_tick_now - ts) < _LOS_WINDOW_MS
                for ts, tgt, src, _dmg, _skill, _crit in _los_recent
            )
            damage_received   = any(
                tgt == player_id and (_tick_now - ts) < _LOS_WINDOW_MS
                for ts, tgt, src, _dmg, _skill, _crit in _los_recent
            )

            # Try to engage Miku by pulling enemies towards her -- if 1 enemy remains move towards enemy instead
            # Only fires when actively dealing damage and LoS is not broken.
            if self.player_combat and self.miku_idle and damage_dealt and self.los_fail_since == 0.0:
                if self.miku_lazy_at == 0.0:
                    self.miku_lazy_at = now                         # start the 3-second delay
                elif now - self.miku_lazy_at >= 3.0 and now - self.last_movement_run >= 1.0:
                    if self.debug:
                        Py4GW.Console.Log("Avoidance", f"Lazy Miku Trigger", Py4GW.Console.MessageType.Warning)
                    nearest_enemy      = _nearest_from(enemy_array, player_x, player_y, 1500)
                    if nearest_enemy != 0:
                        ne_x, ne_y         = Agent.GetXY(nearest_enemy)
                        if len(enemies_far) > 1:
                            ex_x, ex_y         = _escape_point(player_x, player_y, ne_x, ne_y, 300, debug_fn=self.debug_fn)
                        else:
                            ex_x, ex_y         = _escape_point(player_x, player_y, ne_x, ne_y, 300, rotation=180, debug_fn=self.debug_fn)
                        ActionQueueManager().ResetAllQueues()
                        self.last_movement_run  = now
                        self.combat_approach_at = 0.0
                        self.miku_lazy_at       = 0.0                   # reset for next 3-second window
                        Player.Move(ex_x, ex_y)
                        self._set_pause("miku_lazy")
                        yield from Routines.Yield.wait(500)
                        self._clear_pause("miku_lazy")
            else:
                self.miku_lazy_at = 0.0                             # condition cleared or LoS blocked, reset timer

            # Kite if two or more enemies are within melee range
            if enemies_agro and len(enemies_close) > 1 and now - self.last_movement_run >= 1.0:
                if self.debug:
                    Py4GW.Console.Log("Avoidance", f"Melee Swarm Trigger", Py4GW.Console.MessageType.Warning)
                avg_x = sum(Agent.GetXY(eid)[0] for eid in enemies_agro) / len(enemies_agro)
                avg_y = sum(Agent.GetXY(eid)[1] for eid in enemies_agro) / len(enemies_agro)
                ex_x, ex_y = _escape_point(player_x, player_y, avg_x, avg_y, 300, debug_fn=self.debug_fn)
                ActionQueueManager().ResetAllQueues()
                self.last_movement_run  = now
                self.combat_approach_at = 0.0
                Player.Move(ex_x, ex_y)
                yield from Routines.Yield.wait(500)
                return

            # ── LoS gap-close ─────────────────────────────────────────────────────
            if (self.player_combat and self.combat_approach_at != 0.0 and
                    now >= self.combat_approach_at and now - self.last_movement_run >= 1.0 and
                    not has_empathy):

                _priority_valid = (self.locked_target_id != 0 and
                                   Agent.IsValid(self.locked_target_id) and
                                   not Agent.IsDead(self.locked_target_id))

                if _priority_valid:
                    if damage_dealt:
                        # Dealing damage to / near priority target -- LoS fine
                        self.los_fail_since = 0.0
                    else:
                        # Priority target exists but not dealing damage -- close the gap
                        if self.los_fail_since == 0.0:
                            self.los_fail_since = now
                        pl_x, pl_y = Agent.GetXY(self.locked_target_id)
                        if self.debug:
                            Py4GW.Console.Log("LoS", "Not hitting priority target -- closing gap", Py4GW.Console.MessageType.Warning)
                        ActionQueueManager().ResetAllQueues()
                        ep_x, ep_y = _escape_point(player_x, player_y, pl_x, pl_y, 300, rotation=180, debug_fn=self.debug_fn)
                        self.last_movement_run  = now
                        self.combat_approach_at = 0.0
                        Player.Move(ep_x, ep_y)
                        yield from Routines.Yield.wait(500)
                        return
                else:
                    if damage_dealt or damage_received:
                        # No priority target but dealing damage -- LoS fine
                        self.los_fail_since = 0.0
                    else:
                        # No priority target and not dealing damage -- move toward group
                        if self.los_fail_since == 0.0:
                            self.los_fail_since = now
                        move_target = _nearest_from(enemies_agro, player_x, player_y)
                        if move_target != 0:
                            if self.debug:
                                Py4GW.Console.Log("LoS", "No damage dealt or received -- moving toward group", Py4GW.Console.MessageType.Warning)
                            ne_x, ne_y = Agent.GetXY(move_target)
                            ep_x, ep_y = _escape_point(player_x, player_y, ne_x, ne_y, 300, rotation=180, debug_fn=self.debug_fn)
                            self.last_movement_run  = now
                            self.combat_approach_at = 0.0
                            Player.Move(ep_x, ep_y)
                            yield from Routines.Yield.wait(500)
                            return
            # ── AoE sidestep ──────────────────────────────────────────────────────
            if self.aoe_caster_id != 0 and now >= self.aoe_sidestep_at:
                # Refresh caster position if still alive, otherwise fall back to cached position
                if Agent.IsValid(self.aoe_caster_id) and not Agent.IsDead(self.aoe_caster_id):
                    self.aoe_caster_pos = Agent.GetXY(self.aoe_caster_id)
                tx, ty = self.aoe_caster_pos
                if tx != 0.0 or ty != 0.0:
                    if self.debug:
                        Py4GW.Console.Log("Avoidance", "AoE Sidestep", Py4GW.Console.MessageType.Warning)
                    sx, sy = _escape_point(player_x, player_y, tx, ty, _AOE_SIDESTEP_DIST, rotation=90, debug_fn=self.debug_fn)
                    ActionQueueManager().ResetAllQueues()
                    Player.Move(sx, sy)
                    yield from Routines.Yield.wait(500)
                    self.last_movement_run = now
                self.aoe_caster_id  = 0
                self.aoe_caster_pos = (0.0, 0.0)
                return  # skip skill casting this frame after a sidestep
            elif self.aoe_caster_id == 0:
                for eid in enemy_array:
                    skill = Agent.GetCastingSkillID(eid)
                    if skill in _AOE_SKILLS:
                        self.aoe_sidestep_at = now + _AOE_SKILLS[skill] / 1000.0
                        self.aoe_caster_id   = eid
                        self.aoe_caster_pos  = Agent.GetXY(eid)
                        break

        # ══════════════════════════════════════════════════════════════════════
        # SKILL CASTING
        # ══════════════════════════════════════════════════════════════════════

        # ── Empathy / Spirit Shackles action (detection is early, before movement) ─
        if has_empathy:
            ActionQueueManager().ResetAllQueues()   # flush any queued interact/attack commands
            Player.ChangeTarget(player_id)              # clear target to cancel auto-attack
            self.los_fail_since = 0.0               # don't let gap-close trigger while hexed

        # ── Priority target selection (interval-gated) ────────────────────────
        # Suppressed entirely during Empathy/Spirit Shackles -- the drop above must not be undone.
        if not has_empathy and now - self.last_target_check >= _TARGET_SWITCH_INTERVAL:
            self.last_target_check = now

            # Drop the locked target if it is dead or out of range
            if self.locked_target_id != 0:
                pl_x, pl_y = Agent.GetXY(self.locked_target_id)
                if (not Agent.IsValid(self.locked_target_id) or
                        Agent.IsDead(self.locked_target_id) or
                        _dist(player_x, player_y, pl_x, pl_y) > _PRIORITY_TARGET_RANGE):
                    self.locked_target_id   = 0
                    self.locked_priority    = len(_PRIORITY_TARGET_MODELS)
                    self.los_fail_since     = 0.0

            # Scan for a strictly higher-priority (lower index) target
            best_id       = 0
            best_priority = len(_PRIORITY_TARGET_MODELS)
            for eid in enemy_array:
                ex, ey = Agent.GetXY(eid)
                if _dist(player_x, player_y, ex, ey) > _PRIORITY_TARGET_RANGE:
                    continue
                model = Agent.GetModelID(eid)
                if model in _PRIORITY_TARGET_MODELS:
                    prio = _PRIORITY_TARGET_MODELS.index(model)
                    if prio < best_priority:
                        best_priority = prio
                        best_id       = eid

            if best_id != 0 and best_priority < self.locked_priority:
                self.locked_target_id   = best_id
                self.locked_priority    = best_priority
                self.los_fail_since     = 0.0

            if self.locked_target_id != 0 and Player.GetTargetID() != self.locked_target_id:
                Player.ChangeTarget(self.locked_target_id)

        # ── Nature's Blessing -- heal Keiran or Miku ──────────────────────────
        health_threshold      = 0.80
        miku_health_threshold = 0.50
        miku_low_health         = False
        miku_in_earshot     = False
        mk_x_h = mk_y_h    = 0.0

        if miku_id != 0 and not miku_dead:
            mk_x_h, mk_y_h = Agent.GetXY(miku_id)
            if Agent.GetHealth(miku_id) < miku_health_threshold:
                miku_low_health     = True
                miku_in_earshot = _dist(player_x, player_y, mk_x_h, mk_y_h) <= Range.Earshot.value

        if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.natures_blessing)):
            if player_health < health_threshold or has_empathy or (miku_low_health and miku_in_earshot):
                ActionQueueManager().ResetAllQueues()
                yield from Routines.Yield.Skills.CastSkillID(self.natures_blessing, aftercast_delay=100)
                return

            # Miku critically low but out of earshot -- move toward her
            #if miku_low_health and not miku_in_earshot and now - self.last_movement_run >= 1.0:
            #    if self.debug:
            #        Py4GW.Console.Log("Avoidance", f"Moving toward Miku to heal (HP {Agent.GetHealth(miku_id):.0%})", Py4GW.Console.MessageType.Warning)
            #    Player.Move(mk_x_h, mk_y_h)
            #    yield
            #    return

        # ── Guard: only proceed when we can act ───────────────────────────────
        if not (Routines.Checks.Map.IsExplorable() and
                Routines.Checks.Player.CanAct() and
                Routines.Checks.Skills.CanCast()):
            ActionQueueManager().ResetAllQueues()
            yield from Routines.Yield.wait(1000)
            return

        # Skip attacks during aftercast window -- healing and avoidance fire each frame
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
        keiran_sniper_shot_ready       = yield from Routines.Yield.Skills.IsSkillIDUsable(self.keiran_sniper_shot)
        relentless_assault_ready       = yield from Routines.Yield.Skills.IsSkillIDUsable(self.relentless_assault)
        terminal_velocity_ready        = yield from Routines.Yield.Skills.IsSkillIDUsable(self.terminal_velocity)
        gravestone_marker_ready        = yield from Routines.Yield.Skills.IsSkillIDUsable(self.gravestone_marker)
        rain_of_arrows_ready           = yield from Routines.Yield.Skills.IsSkillIDUsable(self.rain_of_arrows)
        theres_nothing_to_fear_ready   = self.theres_nothing_to_fear != 0 and (yield from Routines.Yield.Skills.IsSkillIDUsable(self.theres_nothing_to_fear))
        find_their_weakness_ready      = self.find_their_weakness    != 0 and (yield from Routines.Yield.Skills.IsSkillIDUsable(self.find_their_weakness))
        
        if in_danger:

            # Keiran's Sniper Shot -- finish a hexed enemy
            if keiran_sniper_shot_ready:
                hexed_enemy = Routines.Targeting.GetEnemyHexed(2000)
                if hexed_enemy != 0 and not has_empathy:
                    ActionQueueManager().ResetAllQueues()
                    self.last_cast_at = now
                    yield from _cast(hexed_enemy, self.keiran_sniper_shot)
                    return

            # Relentless Assault -- cleanse a condition from Keiran
            if relentless_assault_ready:
                player_conditioned = (
                    Agent.IsDegenHexed(player_id) or
                    Agent.IsBleeding(player_id) or
                    Agent.IsPoisoned(player_id) or
                    Routines.Checks.Agents.HasEffect(player_id, GLOBAL_CACHE.Skill.GetID("Blind")) or
                    Routines.Checks.Agents.HasEffect(player_id, GLOBAL_CACHE.Skill.GetID("Deep_Wound")) or
                    Routines.Checks.Agents.HasEffect(player_id, GLOBAL_CACHE.Skill.GetID("Cracked_Armor")) or
                    Routines.Checks.Agents.HasEffect(player_id, GLOBAL_CACHE.Skill.GetID("Burning"))
                )
                if player_conditioned and not has_empathy:
                    target = self.locked_target_id or Routines.Targeting.GetEnemyInjured(_WEAPON_RANGE.value)
                    if target != 0:
                        self.last_cast_at = now
                        yield from _cast(target, self.relentless_assault)
                        return

            # There is Nothing to Fear! -- 10% dmg reduction + 35 HP heal shout; 20s CD / 60s duration (mission 3)
            # Buff-check guards against double-cast if the shout affects Keiran himself.
            if theres_nothing_to_fear_ready:
                has_tntf = Routines.Checks.Agents.HasEffect(player_id, self.theres_nothing_to_fear)
                if not has_empathy and self.player_combat and not has_tntf:
                    ActionQueueManager().ResetAllQueues()
                    self.last_cast_at = now
                    yield from self.CastSkillID(self.theres_nothing_to_fear, aftercast_delay=0)
                    return

            # Terminal Velocity -- interrupt a caster or apply to a bleeding enemy
            if terminal_velocity_ready:
                if not has_empathy:
                    target = (self.locked_target_id or
                              Routines.Targeting.GetEnemyCasting(_WEAPON_RANGE.value) or
                              Routines.Targeting.GetEnemyBleeding(_WEAPON_RANGE.value))
                    if target != 0:
                        self.last_cast_at = now
                        yield from _cast(target, self.terminal_velocity)
                        return

            # Find Their Weakness! -- ally shout; targets Miku, only when in combat and she is in earshot (mission 2)
            if find_their_weakness_ready:
                if not has_empathy and self.player_combat and miku_id != 0:
                    mk_x_f, mk_y_f = Agent.GetXY(miku_id)
                    if _dist(player_x, player_y, mk_x_f, mk_y_f) <= Range.Earshot.value:
                        self.last_cast_at = now
                        yield from _cast(miku_id, self.find_their_weakness)
                        return

            # Gravestone Marker -- spirits first, then healthy enemies
            if gravestone_marker_ready:
                if not has_empathy:
                    target = (self.locked_target_id or
                              Routines.Targeting.GetNearestSpirit(_WEAPON_RANGE.value) or
                              Routines.Targeting.GetEnemyHealthy(_WEAPON_RANGE.value))
                    if target != 0:
                        self.last_cast_at = now
                        yield from _cast(target, self.gravestone_marker)
                        return

            # Rain of Arrows -- spirits first, then clustered enemies
            if rain_of_arrows_ready:
                if not has_empathy:
                    target = (self.locked_target_id or
                              Routines.Targeting.GetNearestSpirit(_WEAPON_RANGE.value) or
                              Routines.Targeting.TargetClusteredEnemy(_WEAPON_RANGE.value))
                    if target != 0:
                        self.last_cast_at = now
                        yield from _cast(target, self.rain_of_arrows)
                        return

        if not has_empathy:
            self._sync_hero_ai_fallback_skill_blocks()
            yield from self.hero_ai_handler.ProcessSkillCasting()
        else:
            yield  # don't let HeroAI re-target and re-attack while Empathy/Spirit Shackles is active
