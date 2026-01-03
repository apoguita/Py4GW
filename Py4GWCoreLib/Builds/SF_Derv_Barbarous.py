import Py4GW
import math
from typing import Tuple
from Py4GWCoreLib import Profession
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Map
from Py4GWCoreLib import Range
from Py4GWCoreLib import Utils
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import Agent, DXOverlay

from typing import List, Tuple
from Py4GWCoreLib.Builds.BuildHelpers import BuildDangerHelper

dx = DXOverlay()
ShowDXoverlay = False

def vector_angle(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Returns the cosine similarity (dot product / magnitudes). 1 = same direction, -1 = opposite."""
    dot = a[0]*b[0] + a[1]*b[1]
    mag_a = math.hypot(*a)
    mag_b = math.hypot(*b)
    if mag_a == 0 or mag_b == 0:
        return 1  # safest fallback
    dot = a[0]*b[0] + a[1]*b[1]
    return dot / (mag_a * mag_b)

#region SFAssassinBarbarous
class SF_Derv_Barbarous(BuildMgr):
    def __init__(self, build_danger_helper: BuildDangerHelper = BuildDangerHelper()):
        super().__init__(
            name="SF Barbarous Shore Dervish Runner",
            required_primary=Profession.Dervish,
            required_secondary=Profession.Assassin,
            template_code="Ogei8xsMxjozcAdgdXiANuRTCA",
            skills=[
                GLOBAL_CACHE.Skill.GetID("Deadly_Paradox"),
                GLOBAL_CACHE.Skill.GetID("Shadow_Form"),
                GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress"),
                GLOBAL_CACHE.Skill.GetID("Pious_Haste"),
                GLOBAL_CACHE.Skill.GetID("Dwarven_Stability"),
                GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow"),
                GLOBAL_CACHE.Skill.GetID("Zealous_Renewal"),
                GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable"),
            ],
        )
        
        # Skill IDs
        self.deadly_paradox = GLOBAL_CACHE.Skill.GetID("Deadly_Paradox")
        self.shadow_form = GLOBAL_CACHE.Skill.GetID("Shadow_Form")
        self.shroud_of_distress = GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress")
        self.pious_haste = GLOBAL_CACHE.Skill.GetID("Pious_Haste")
        self.dwarven_stability = GLOBAL_CACHE.Skill.GetID("Dwarven_Stability")
        self.heart_of_shadow = GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow")
        self.zealous_renewal = GLOBAL_CACHE.Skill.GetID("Zealous_Renewal")
        self.i_am_unstoppable = GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable")

        # States
        self.is_looting = False
        self.routine_finished = False
        self._has_sf = False
        self._sf_timer = ThrottledTimer(600)
        self._sf_timer.Start()

        self.build_danger_helper = build_danger_helper

    def SetRoutineFinished(self, routine_finished: bool):
        self.routine_finished = routine_finished

    def SetLootingSignal(self, is_looting: bool):
        self.is_looting = is_looting


    def _CastSkillID(self, skill_id:int, extra_condition:bool=True, log:bool=True, aftercast_delay:int=1000):
        result = yield from Routines.Yield.Skills.CastSkillID(skill_id, extra_condition=extra_condition, log=log, aftercast_delay=aftercast_delay)
        return result
    

    def _CastSkillSlot(self, slot:int, extra_condition:bool=True, log:bool=True, aftercast_delay:int=1000):
        result = yield from Routines.Yield.Skills.CastSkillSlot(slot, extra_condition=extra_condition, log=log, aftercast_delay=aftercast_delay)
        return result


    # Taken from YAVB HoS logic, casts an optimal Heart of Shadow target
    def _CastHeartOfShadow(self):
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
        
        # Find enemy most opposite to goal direction
        for enemy in enemy_array:
            if Agent.IsDead(enemy):
                continue
            enemy_pos = Agent.GetXY(enemy)
            to_enemy = (enemy_pos[0] - player_pos[0], enemy_pos[1] - player_pos[1])
            angle_score = vector_angle(to_goal, to_enemy)  # -1 is most opposite
            if angle_score < most_opposite_score:
                most_opposite_score = angle_score
                best_enemy = enemy
        if best_enemy:
            yield from Routines.Yield.Agents.ChangeTarget(best_enemy)    
        else:
            yield from Routines.Yield.Agents.TargetNearestEnemy(Range.Earshot.value)
        

        yield from self._CastSkillID(self.heart_of_shadow, log=False, aftercast_delay=350)
    
    # Shroud of Distress watcher
    def _ShroudOfDistressWatcher(self):
        # Initial vars
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        has_sod = Routines.Checks.Effects.HasBuff(player_agent_id, self.shroud_of_distress)
        is_sod_ready = Routines.Checks.Skills.IsSkillIDReady(self.shroud_of_distress)
        is_sod_about_to_expire = has_sod and GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id, self.shroud_of_distress) <= 2000
        is_sf_expiring = Routines.Checks.Effects.HasBuff(player_agent_id, self.shadow_form) and GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id, self.shadow_form) <= 1000

        if is_sf_expiring:
            return  # Shadow Form has priority

        if is_sod_ready and (is_sod_about_to_expire or not has_sod):
            # ** Cast Shroud of Distress **
            yield from self._CastSkillID(self.shroud_of_distress, log =False, aftercast_delay=1000)

    def _ShadowFormWatcher(self):
        # Initial vars
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        self._has_sf = Routines.Checks.Effects.HasBuff(player_agent_id, self.shadow_form)
        is_sf_ready = yield from Routines.Yield.Skills.IsSkillIDUsable(self.shadow_form)
        self._is_sf_about_to_expire = self._has_sf and GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id, self.shadow_form) <= 3000

        # No need to cast if we already have shadow form and not running out soon
        if self._has_sf and not self._is_sf_about_to_expire:
            yield None
            return
        
        # Compute spellcast danger only when necessary
        is_spellcast_danger = self.build_danger_helper.check_spellcaster(custom_distance=Range.Spellcast.value + 150, include_non_specified=False)

        # Cast Shadow Form if we dont have it or its about to expire, and there is spellcast danger
        if (not self._has_sf or self._is_sf_about_to_expire) and is_sf_ready and is_spellcast_danger:
            yield from self._CastSkillID(self.deadly_paradox, log=False, aftercast_delay=250)
            yield from self._CastSkillID(self.shadow_form, log=False, aftercast_delay=1000)
            self._has_sf = True


    def _StabilityWatcher(self):
        # Initial vars
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        is_stability_ready = Routines.Checks.Skills.IsSkillIDReady(self.dwarven_stability)
        has_stability = Routines.Checks.Effects.HasBuff(player_agent_id, self.dwarven_stability)

        # With high enough dwarven skill, this will only run at the start of the run
        if not has_stability and is_stability_ready:
            yield from self._CastSkillID(self.dwarven_stability, log=False, aftercast_delay=1000)


    def _StanceWatcher(self):
        # Initial vars
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()

        is_pious_haste_ready = Routines.Checks.Skills.IsSkillIDReady(self.pious_haste)
        is_zealous_renewal_ready = Routines.Checks.Skills.IsSkillIDReady(self.zealous_renewal)

        if self._is_sf_about_to_expire:
            yield None
            return


        # Dont handle stance if vow of silence is about to expire -- VOS has priority
        if is_pious_haste_ready and is_zealous_renewal_ready:
            yield from self._CastSkillID(self.zealous_renewal, log=False, aftercast_delay=250)
            yield from self._CastSkillID(self.pious_haste, log=False, aftercast_delay=250)


    def _IAUWatcher(self):
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        (px, py) = GLOBAL_CACHE.Player.GetXY()

        if Agent.IsCrippled(player_agent_id) or self.build_danger_helper.check_cripple_kd(px, py):
            has_iau = Routines.Checks.Effects.HasBuff(player_agent_id, self.i_am_unstoppable)
            is_iau_ready = Routines.Checks.Skills.IsSkillIDReady(self.i_am_unstoppable)

            if is_iau_ready and not has_iau:
                yield from Routines.Yield.Skills.CastSkillID(self.i_am_unstoppable, aftercast_delay=0)


    def _DefensiveWatcher(self):
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        is_hos_ready = Routines.Checks.Skills.IsSkillIDReady(self.heart_of_shadow)
        is_emergency_health = Agent.GetHealth(player_agent_id) <= 0.2

        if is_emergency_health and is_hos_ready:
            yield from self._CastHeartOfShadow()


    def _BlockedEscapeWatcher(self):
        is_stuck = self.build_danger_helper.body_block_detection(seconds=4)
        is_hos_ready = Routines.Checks.Skills.IsSkillIDReady(self.heart_of_shadow)

        if is_stuck and is_hos_ready:
            yield from self._CastHeartOfShadow()


    def ProcessSkillCasting(self):
        current_map_id = Map.GetMapID()

        while True:
            # Check basic conditions where skill handling should be skipped
            
            # Check if map has fully loaded
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)
                continue
            
            # Player is dead
            if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(1000)
                continue

            # Cannot cast skills right now, throttle 100ms
            if not Routines.Checks.Skills.CanCast():
                yield from Routines.Yield.wait(100)
                continue

            # Check if routine is finished
            if self.routine_finished:
                yield from Routines.Yield.wait(1000)
                continue

            if self.is_looting:
                yield from Routines.Yield.wait(1000)
                continue

            # === Skill Watchers ===

            # Shadow Form watcher
            yield from self._ShadowFormWatcher()

            # Shroud of Distress watcher
            yield from self._ShroudOfDistressWatcher()

            # Stability watcher
            yield from self._StabilityWatcher()

            # Stance watcher
            yield from self._StanceWatcher()

            # IAU Watcher === Anti Cripple/KD ===
            yield from self._IAUWatcher()

            # Shadow Sanctuary watcher
            yield from self._DefensiveWatcher()

            # Blocked Escape watcher
            yield from self._BlockedEscapeWatcher()

            # === IDLE WAIT ===
            yield from Routines.Yield.wait(100)
            
            # Log current map id and name
            ConsoleLog(self.build_name, f"Current Map ID: {current_map_id}, Name: {Map.GetMapName(current_map_id)}", Py4GW.Console.MessageType.Info, log=False)



    # # Taken from aC's Build_Manager for Death's Charge targeting 
    # def DeathsChargeToBestEnemy(self, fsm_helpers):
    #     def angle_between_player_and_enemy(facing_vec, enemy_vec):
    #         """
    #         Returns absolute angle (0..180°) between player's facing vector
    #         and the vector from player -> enemy.
    #         """
    #         fx, fy = facing_vec
    #         ex, ey = enemy_vec
    #         dot = fx * ex + fy * ey            
    #         det = fx * ey - fy * ex            
    #         angle_rad = math.atan2(det, dot)
    #         angle_deg = abs(math.degrees(angle_rad))

    #         return angle_deg
        

    #     SPELLCAST_RANGE = 1248.0
    #     px, py = GLOBAL_CACHE.Player.GetXY()
    #     pz = Overlay().FindZ(px, py)
    #     heading = Agent.GetRotationAngle(GLOBAL_CACHE.Player.GetAgentID())
    #     facing_vec = (math.cos(heading), math.sin(heading))

    #     enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, max_distance=SPELLCAST_RANGE)

    #     best_15deg = None
    #     best_15deg_dist = -1
    #     best_30deg = None
    #     best_30deg_dist = -1

    #     for enemy in enemy_array:
    #         if Agent.IsDead(enemy):
    #             continue

    #         ex, ey = Agent.GetXY(enemy)
    #         enemy_vec = (ex - px, ey - py)
    #         dist = math.hypot(enemy_vec[0], enemy_vec[1])
    #         angle = angle_between_player_and_enemy(facing_vec, enemy_vec)

    #         if angle <= 15.0:
    #             if dist > best_15deg_dist:
    #                 best_15deg_dist = dist
    #                 best_15deg = enemy
    #         elif angle <= 60.0:
    #             if dist > best_30deg_dist:
    #                 best_30deg_dist = dist
    #                 best_30deg = enemy

    #     best_target = best_15deg if best_15deg else best_30deg

    #     if not best_target:
    #         ConsoleLog(self.build_name, "Deaths Charge Handler ::: No valid target in 15° or 30° cone → skip", Py4GW.Console.MessageType.Debug)
    #         return

    #     ex, ey = Agent.GetXY(best_target)
    #     ez = Overlay().FindZ(ex, ey)
    #     target_dist = math.hypot(ex - px, ey - py)
    #     ConsoleLog(
    #         self.build_name,
    #         f"Chosen enemy at ({ex:.1f}, {ey:.1f}) | Cone: {'15°' if best_target == best_15deg else '30°'} | Distance={target_dist:.1f}",
    #         Py4GW.Console.MessageType.Debug
    #     )

    #     if ShowDXoverlay:
    #         overlay = Overlay()
    #         overlay.BeginDraw()
    #         overlay.DrawLine3D(px, py, pz, ex, ey, ez, 0xFFFFFF00, 3.0)  # thick yellow/white line
    #         overlay.EndDraw()

    #     yield from Routines.Yield.Agents.ChangeTarget(best_target)
    #     yield from self._CastSkillID(self.deaths_charge, aftercast_delay=1000)