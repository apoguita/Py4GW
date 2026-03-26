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
from Py4GWCoreLib import Agent, DXOverlay, Player

from typing import List, Tuple
from Py4GWCoreLib.Builds.CombatAutomatorExcluded.BuildHelpers import BuildDangerHelper

dx = DXOverlay()
ShowDXoverlay = False

# =============================================================================
# region DANGER TABLES
# =============================================================================
_DEFAULT_CRIPPLE_KD_TABLE = (
    ([6480, 6481, 6482, 6483],                          "Jotun"),
    ([6475, 6476, 6473],                                "Modniir"),
    ([6478, 331],                                       "Elementals"),
    ([4400, 4930, 4396, 4402, 4932,
      4401, 4931, 4307, 4306, 6658, 6657],              "Mandragor"),
    ([1802, 4323, 7326, 6491, 2547, 2598],              "Wurms"),
    ([6488],                                            "Mountain Pinesoul"),
    ([7038, 7040, 2740],                                "Skeletons"),
    ([7043, 7094],                                      "Zombie"),
    ([6862, 1866, 6869],                                "Enchanted"),
    ([6337, 6338, 6339, 6340, 6390],                    "Quetzal"),
    ([2646],                                            "Stone Summit Scout"),
    ([1797, 2493, 2486],                                "Minotaur"),
    ([2657],                                            "Summit Giant"),
    ([4678],                                            "Skree"),
    ([2312],                                            "Spiders"),
    ([2307],                                            "Roots"),
    ([2732, 2731],                                      "Ghouls"),
    ([2535],                                            "Asura"),
    ([6487],                                            "Bison"),
    ([6678],                                            "Tumbled Elementalist"),
    ([6627],                                            "Charr Axemaster"),
    ([2593],                                            "Grawl"),
    ([5099, 5110, 5094, 5102, 5101, 5080, 5083, 5081],  "Corsair"),
    ([4955],                                            "Mesa"),
    ([2530, 2581],                                      "Tundra Giant"),
)

_DEFAULT_EXTREME_KD_DANGER = (
    ([2530, 2581],                                            "Tundra Giant"),
)
# endregion

def vector_angle(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Returns the cosine similarity (dot product / magnitudes). 1 = same direction, -1 = opposite."""
    dot = a[0]*b[0] + a[1]*b[1]
    mag_a = math.hypot(*a)
    mag_b = math.hypot(*b)
    if mag_a == 0 or mag_b == 0:
        return 1  # safest fallback
    dot = a[0]*b[0] + a[1]*b[1]
    return dot / (mag_a * mag_b)

#region SF_Derv_Runner
class SF_Derv_Runner(BuildMgr):
    def __init__(self, build_danger_helper: BuildDangerHelper | None = None, match_only: bool = False):
        super().__init__(
            name="SF_Derv_Runner",
            required_primary=Profession.Dervish,
            required_secondary=Profession.Assassin,
            template_code="Ogei8xsMxjozMudgdXiAdARTCA", # with HoS
            #template_code="Ogei8xsMxjozMudgdXi7cARTCA", # with DeathsCharge
            is_combat_automator_compatible=False,
            required_skills=[
                GLOBAL_CACHE.Skill.GetID("Deadly_Paradox"),
                GLOBAL_CACHE.Skill.GetID("Shadow_Form"),
                GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress"),
                GLOBAL_CACHE.Skill.GetID("Pious_Haste"),
                GLOBAL_CACHE.Skill.GetID("Dwarven_Stability"),
                #GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow"),
                #GLOBAL_CACHE.Skill.GetID("Deaths_Charge"),
                GLOBAL_CACHE.Skill.GetID("Zealous_Renewal"),
                GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable"),
            ],
        )
        if match_only:
            return
        
        # Skill IDs
        self.deadly_paradox = GLOBAL_CACHE.Skill.GetID("Deadly_Paradox")
        self.shadow_form = GLOBAL_CACHE.Skill.GetID("Shadow_Form")
        self.shroud_of_distress = GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress")
        self.pious_haste = GLOBAL_CACHE.Skill.GetID("Pious_Haste")
        self.dwarven_stability = GLOBAL_CACHE.Skill.GetID("Dwarven_Stability")
        self.heart_of_shadow = GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow")
        self.deaths_charge = GLOBAL_CACHE.Skill.GetID("Deaths_Charge")
        self.zealous_renewal = GLOBAL_CACHE.Skill.GetID("Zealous_Renewal")
        self.i_am_unstoppable = GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable")
        self.muddy_terrain = GLOBAL_CACHE.Skill.GetID("Muddy_Terrain")

        # States
        self.is_looting = False
        self.routine_finished = False
        self._has_sf = False
        self._sf_timer = ThrottledTimer(600)
        self._sf_timer.Start()

        self.build_danger_helper = build_danger_helper if build_danger_helper is not None else BuildDangerHelper(cripple_kd_table=_DEFAULT_CRIPPLE_KD_TABLE, extreme_kd_danger=_DEFAULT_EXTREME_KD_DANGER)

    def SetRoutineFinished(self, routine_finished: bool):
        self.routine_finished = routine_finished

    def SetLootingSignal(self, is_looting: bool):
        self.is_looting = is_looting

    # Taken from YAVB HoS logic, casts an optimal Heart of Shadow target
    def _CastHeartOfShadow(self):
        center_point1 = (10980, -21532)
        center_point2 = (11461, -17282)
        player_pos = Player.GetXY()
        
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
        

        yield from self.CastSkillID(self.heart_of_shadow, log=False, aftercast_delay=125)
    
    def _CastDeathsCharge(self):
        # "Death's Charge to the farthest enemy within the forward cone
        if False:
            yield

        if not Routines.Checks.Skills.IsSkillIDReady(self.deaths_charge):
            return
        if not Routines.Checks.Skills.HasEnoughEnergy(Player.GetAgentID(), self.deaths_charge):
            return

        player_pos = Player.GetXY()
        heading = Agent.GetRotationAngle(Player.GetAgentID())
        facing = (math.cos(heading), math.sin(heading))

        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.Spellcast.value)

        best_narrow, best_narrow_dist = 0, -1.0   # <=15 degrees
        best_wide, best_wide_dist = 0, -1.0       # <=60 degrees

        for enemy in enemy_array:
            if Agent.IsDead(enemy):
                continue
            enemy_pos = Agent.GetXY(enemy)
            dx = enemy_pos[0] - player_pos[0]
            dy = enemy_pos[1] - player_pos[1]
            dist = math.hypot(dx, dy)

            dot = facing[0] * dx + facing[1] * dy
            det = facing[0] * dy - facing[1] * dx
            angle = abs(math.degrees(math.atan2(det, dot)))

            if angle <= 15.0 and dist > best_narrow_dist:
                best_narrow, best_narrow_dist = enemy, dist
            elif angle <= 60.0 and dist > best_wide_dist:
                best_wide, best_wide_dist = enemy, dist

        target = best_narrow or best_wide
        if not target:
            return

        yield from Routines.Yield.Agents.ChangeTarget(target)
        yield from self.CastSkillID(self.deaths_charge, log=False, aftercast_delay=125)


    def _ShadowFormWatcher(self):
        # Initial vars
        player_agent_id = Player.GetAgentID()
        self._has_sf = Routines.Checks.Effects.HasBuff(player_agent_id, self.shadow_form)
        is_sf_ready = yield from Routines.Yield.Skills.IsSkillIDUsable(self.shadow_form)
        self._is_sf_about_to_expire = self._has_sf and GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id, self.shadow_form) <= 3000

        # Check if enemies nearby (2000u range)
        px, py = Player.GetXY()
        self._enemies_nearby = len(Routines.Agents.GetFilteredEnemyArray(px, py, max_distance=2000.0)) > 0

        # No need to cast if we already have shadow form and not running out soon
        if self._has_sf and not self._is_sf_about_to_expire:
            yield None
            return

        # Only cast DP + SF if enemies are within 2000u
        if self._enemies_nearby and (not self._has_sf or self._is_sf_about_to_expire) and is_sf_ready:
            yield from self.CastSkillID(self.deadly_paradox, log=False, aftercast_delay=0)
            yield from self.CastSkillID(self.shadow_form, log=False, aftercast_delay=1000)
            self._has_sf = True

    def _ShroudOfDistressWatcher(self):
        # Initial vars
        player_agent_id = Player.GetAgentID()
        has_sod = Routines.Checks.Effects.HasBuff(player_agent_id, self.shroud_of_distress)
        is_sod_ready = yield from Routines.Yield.Skills.IsSkillIDUsable(self.shroud_of_distress)
        is_sod_about_to_expire = has_sod and GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id, self.shroud_of_distress) <= 2000
        is_sf_expiring = Routines.Checks.Effects.HasBuff(player_agent_id, self.shadow_form) and GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id, self.shadow_form) <= 1000
        is_low_health = Agent.GetHealth(player_agent_id) <= 0.55

        if is_sf_expiring:
            return  # Shadow Form has priority
        
        if is_sod_ready and is_low_health and (is_sod_about_to_expire or not has_sod):
            yield from self.CastSkillID(self.shroud_of_distress, log =False, aftercast_delay=1000)

    def _StabilityWatcher(self):
        # Initial vars
        player_agent_id = Player.GetAgentID()
        is_stability_ready = yield from Routines.Yield.Skills.IsSkillIDUsable(self.dwarven_stability)
        has_stability = Routines.Checks.Effects.HasBuff(player_agent_id, self.dwarven_stability)
        is_stability_expiring = Routines.Checks.Effects.HasBuff(player_agent_id, self.dwarven_stability) and GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id, self.dwarven_stability) <= 1000

        if (is_stability_expiring or not has_stability) and is_stability_ready:
            yield from self.CastSkillID(self.dwarven_stability, log=False, aftercast_delay=125)


    def _StanceWatcher(self):
        # Initial vars
        player_agent_id = Player.GetAgentID()
        has_mt = Routines.Checks.Effects.HasBuff(player_agent_id, self.muddy_terrain)

        is_pious_haste_ready = Routines.Checks.Skills.IsSkillIDReady(self.pious_haste)
        is_zealous_renewal_ready = Routines.Checks.Skills.IsSkillIDReady(self.zealous_renewal)

        # Dont handle if no energy to cast combo (energy < 10)
        if (Agent.GetEnergy(player_agent_id) * Agent.GetMaxEnergy(player_agent_id)) < 10:
            yield None
            return

        # Dont handle stance if enemies are near and no SF or SF is about to expire
        if self._enemies_nearby and (self._is_sf_about_to_expire or not self._has_sf):
            yield None
            return

        if is_pious_haste_ready and is_zealous_renewal_ready and not has_mt:
            yield from self.CastSkillID(self.zealous_renewal, log=False, aftercast_delay=0)
            yield from self.CastSkillID(self.pious_haste, log=False, aftercast_delay=0)

    def _IAUWatcher(self):
        player_agent_id = Player.GetAgentID()
        (px, py) = Player.GetXY()

        if Agent.IsCrippled(player_agent_id) or Agent.IsKnockedDown(player_agent_id) or self.build_danger_helper.check_cripple_kd(px, py):
            has_iau = Routines.Checks.Effects.HasBuff(player_agent_id, self.i_am_unstoppable)
            is_iau_ready = yield from Routines.Yield.Skills.IsSkillIDUsable(self.i_am_unstoppable)

            if is_iau_ready and not has_iau:
                yield from self.CastSkillID(self.i_am_unstoppable, aftercast_delay=0)


    def _DefensiveWatcher(self):
        player_agent_id = Player.GetAgentID()
        is_hos_ready = Routines.Checks.Skills.IsSkillIDReady(self.heart_of_shadow)
        is_emergency_health = Agent.GetHealth(player_agent_id) <= 0.2

        if is_emergency_health and is_hos_ready:
            yield from self._CastHeartOfShadow()


    def _BlockedEscapeWatcher(self):
        is_stuck = self.build_danger_helper.body_block_detection(seconds=4)
        is_hos_ready = yield from Routines.Yield.Skills.IsSkillIDUsable(self.heart_of_shadow)
        is_dc_ready = yield from Routines.Yield.Skills.IsSkillIDUsable(self.deaths_charge)

        if is_stuck and is_hos_ready:
            yield from self._CastHeartOfShadow()
        
        elif is_stuck and is_dc_ready:
            yield from self._CastDeathsCharge()

    def ProcessSkillCasting(self):
        current_map_id = Map.GetMapID()

        while True:
            # Check basic conditions where skill handling should be skipped
            
            # Check if map has fully loaded
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)
                continue
            
            # Player is dead
            if Agent.IsDead(Player.GetAgentID()):
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

            # Defensive watcher needed?
            yield from self._DefensiveWatcher()

            # Blocked Escape watcher
            yield from self._BlockedEscapeWatcher()

            # === IDLE WAIT ===
            yield from Routines.Yield.wait(100)
            
            # Log current map id and name
            ConsoleLog(self.build_name, f"Current Map ID: {current_map_id}, Name: {Map.GetMapName(current_map_id)}", Py4GW.Console.MessageType.Info, log=False)