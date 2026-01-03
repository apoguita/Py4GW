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
from Py4GWCoreLib import Map


# region SFMesmerVaettir
class SF_Mes_vaettir(BuildMgr):
    def __init__(self):
        super().__init__(
            name="Shadow Form Mesmer Vaettir",
            required_primary=Profession.Mesmer,
            required_secondary=Profession.Assassin,
            template_code="OQdUAQROqPP8Id2BkAiAvpLBDAA",
            skills=[
                GLOBAL_CACHE.Skill.GetID("Deadly_Paradox"),
                GLOBAL_CACHE.Skill.GetID("Shadow_Form"),
                GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress"),
                GLOBAL_CACHE.Skill.GetID("Way_of_Perfection"),
                GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow"),
                GLOBAL_CACHE.Skill.GetID("Wastrels_Demise"),
                GLOBAL_CACHE.Skill.GetID("Arcane_Echo"),
                GLOBAL_CACHE.Skill.GetID("Mantra_of_Earth"),
            ],
        )

        self.deadly_paradox_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Deadly_Paradox"))
        self.shadow_form_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Shadow_Form"))
        self.shroud_of_distress_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(
            GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress")
        )
        self.way_of_perfection_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(
            GLOBAL_CACHE.Skill.GetID("Way_of_Perfection")
        )
        self.heart_of_shadow_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow"))
        self.wastrels_demise_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Wastrels_Demise"))
        self.arcane_echo_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Arcane_Echo"))
        self.mantra_of_earth_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Mantra_of_Earth"))

        self.shadow_form = GLOBAL_CACHE.Skill.GetID("Shadow_Form")
        self.deadly_paradox = GLOBAL_CACHE.Skill.GetID("Deadly_Paradox")
        self.shroud_of_distress = GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress")
        self.mantra_of_earth = GLOBAL_CACHE.Skill.GetID("Mantra_of_Earth")
        self.way_of_perfection = GLOBAL_CACHE.Skill.GetID("Way_of_Perfection")
        self.heart_of_shadow = GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow")

        self.in_killing_routine = False
        self.routine_finished = False
        self.stuck_signal = False
        self.waypoint = (0, 0)

    def SetKillingRoutine(self, in_killing_routine: bool):
        self.in_killing_routine = in_killing_routine

    def SetRoutineFinished(self, routine_finished: bool):
        self.routine_finished = routine_finished

    def SetStuckSignal(self, stuck_counter: int):
        # self.stuck_counter = stuck_counter
        self.stuck_signal = stuck_counter > 3

    def GetStuckSignal(self) -> bool:
        return self.stuck_signal

    def _CastSkillID(self, skill_id: int, extra_condition: bool = True, log: bool = True, aftercast_delay: int = 1000):
        result = yield from Routines.Yield.Skills.CastSkillID(
            skill_id, extra_condition=extra_condition, log=log, aftercast_delay=aftercast_delay
        )
        return result

    def _CastSkillSlot(self, slot: int, extra_condition: bool = True, log: bool = True, aftercast_delay: int = 1000):
        result = yield from Routines.Yield.Skills.CastSkillSlot(
            slot, extra_condition=extra_condition, log=log, aftercast_delay=aftercast_delay
        )
        return result

    def DefensiveActions(self):
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        player_hp = Agent.GetHealth(player_agent_id)
        has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_agent_id, self.deadly_paradox)
        if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.shadow_form)):
            if (
                yield from self._CastSkillID(
                    self.deadly_paradox, extra_condition=(not has_deadly_paradox), log=False, aftercast_delay=100
                )
            ):
                ConsoleLog(self.build_name, "Casting Deadly Paradox.", Py4GW.Console.MessageType.Info, log=False)

            if (yield from self._CastSkillID(self.shadow_form, log=False, aftercast_delay=1750)):
                ConsoleLog(self.build_name, "Casting Shadow Form.", Py4GW.Console.MessageType.Info, log=False)

        if player_hp < 0.7 and (yield from Routines.Yield.Skills.IsSkillIDUsable(self.shroud_of_distress)):
            yield from self._CastSkillID(self.shroud_of_distress, log=False, aftercast_delay=500)
            ConsoleLog(self.build_name, "Casting Shroud for defense.", Py4GW.Console.MessageType.Info, log=False)

        if player_hp < 0.8 and (yield from Routines.Yield.Skills.IsSkillIDUsable(self.way_of_perfection)):
            yield from self._CastSkillID(self.way_of_perfection, log=False, aftercast_delay=500)
            ConsoleLog(self.build_name, "Casting Way of Perfection for defense.", Py4GW.Console.MessageType.Info, log=False)

        if player_hp < 0.25 and (yield from Routines.Yield.Skills.IsSkillIDUsable(self.heart_of_shadow)):
            yield from self.CastHeartOfShadow()

    def CastShroudOfDistress(self):
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        if Agent.GetHealth(player_agent_id) < 0.45:
            ConsoleLog(self.build_name, "Casting Shroud of Distress.", Py4GW.Console.MessageType.Info, log=False)
            # ** Cast Shroud of Distress **
            yield from self._CastSkillID(self.shroud_of_distress, log=False, aftercast_delay=1750)

    def vector_angle(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        """Returns the cosine similarity (dot product / magnitudes). 1 = same direction, -1 = opposite."""
        dot = a[0] * b[0] + a[1] * b[1]
        mag_a = math.hypot(*a)
        mag_b = math.hypot(*b)
        if mag_a == 0 or mag_b == 0:
            return 1  # safest fallback
        dot = a[0] * b[0] + a[1] * b[1]
        return dot / (mag_a * mag_b)

    def CastHeartOfShadow(self):
        center_point1 = (10980, -21532)
        center_point2 = (11461, -17282)
        player_pos = GLOBAL_CACHE.Player.GetXY()

        distance_to_center1 = Utils.Distance(player_pos, center_point1)
        distance_to_center2 = Utils.Distance(player_pos, center_point2)
        goal = center_point1 if distance_to_center1 < distance_to_center2 else center_point2
        # Compute direction to goal
        to_goal = (goal[0] - player_pos[0], goal[1] - player_pos[1])

        best_enemy = 0
        most_opposite_score = 1

        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.Spellcast.value)

        for enemy in enemy_array:
            if Agent.IsDead(enemy):
                continue
            enemy_pos = Agent.GetXY(enemy)
            to_enemy = (enemy_pos[0] - player_pos[0], enemy_pos[1] - player_pos[1])

            angle_score = self.vector_angle(to_goal, to_enemy)  # -1 is most opposite

            if angle_score < most_opposite_score:
                most_opposite_score = angle_score
                best_enemy = enemy
        if best_enemy:
            yield from Routines.Yield.Agents.ChangeTarget(best_enemy)
        else:
            yield from Routines.Yield.Agents.TargetNearestEnemy(Range.Earshot.value)

        self.stuck_signal = False  # Manaully set to False, to avoid recasting in case the value doesn't reset on time.
        yield from self._CastSkillID(self.heart_of_shadow, log=False, aftercast_delay=350)

    def ProcessSkillCasting(self):
        def GetNotHexedEnemy():
            player_pos = GLOBAL_CACHE.Player.GetXY()
            enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.Spellcast.value)
            for enemy in enemy_array:
                if Agent.IsDead(enemy):
                    continue
                if Agent.IsHexed(enemy):
                    continue
                return enemy

        if not Routines.Checks.Map.MapValid():
            yield from Routines.Yield.wait(1000)
            return

        if not Map.GetMapID() == Map.GetMapIDByName("Jaga Moraine"):
            from Py4GWCoreLib import AgentArray  # TODO: FIx
            from Py4GWCoreLib import AgentModelID  # TODO: FIx

            agent_array = AgentArray.GetEnemyArray()
            agent_array = AgentArray.Filter.ByCondition(
                agent_array,
                lambda agent: Agent.GetModelID(agent)
                in (AgentModelID.FROZEN_ELEMENTAL.value, AgentModelID.FROST_WURM.value),
            )
            agent_array = AgentArray.Filter.ByDistance(agent_array, GLOBAL_CACHE.Player.GetXY(), Range.Spellcast.value)
            if len(agent_array) > 0:
                yield from self.DefensiveActions()

            if Routines.Checks.Agents.InDanger(Range.Earshot):
                yield from self.DefensiveActions()
            yield from Routines.Yield.wait(1000)
            return

        if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            yield from Routines.Yield.wait(1000)
            return

        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return

        if self.routine_finished:
            yield from Routines.Yield.wait(1000)
            return

        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        has_shadow_form = Routines.Checks.Effects.HasBuff(player_agent_id, self.shadow_form)
        shadow_form_buff_time_remaining = (
            GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id, self.shadow_form) if has_shadow_form else 0
        )
        if Routines.Checks.Agents.InDanger(Range.Spellcast):
            has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_agent_id, self.deadly_paradox)

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.shadow_form)):
                GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                if (
                    yield from self._CastSkillID(
                        self.deadly_paradox, extra_condition=(not has_deadly_paradox), log=False, aftercast_delay=200
                    )
                ):
                    ConsoleLog(self.build_name, "Casting Deadly Paradox.", Py4GW.Console.MessageType.Info, log=False)
                GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                if (yield from self._CastSkillID(self.shadow_form, log=False, aftercast_delay=1950)):
                    ConsoleLog(self.build_name, "Casting Shadow Form.", Py4GW.Console.MessageType.Info, log=False)
                    return

        has_shroud_of_distress = Routines.Checks.Effects.HasBuff(player_agent_id, self.shroud_of_distress)
        if not has_shroud_of_distress or (
            shadow_form_buff_time_remaining > 8000
            and (yield from Routines.Yield.Skills.IsSkillIDUsable(self.shroud_of_distress))
        ):
            ConsoleLog(self.build_name, "Casting Shroud of Distress.", Py4GW.Console.MessageType.Info, log=False)
            # ** Cast Shroud of Distress **
            GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
            if (yield from self._CastSkillID(self.shroud_of_distress, log=False, aftercast_delay=1950)):
                return

        has_mantra_of_earth = Routines.Checks.Effects.HasBuff(player_agent_id, self.mantra_of_earth)
        if not has_mantra_of_earth:
            ConsoleLog(self.build_name, "Casting Mantra Of Earth.", Py4GW.Console.MessageType.Info, log=False)
            # ** Cast mantra of earth **
            if (yield from self._CastSkillID(self.mantra_of_earth, log=False, aftercast_delay=200)):
                return

        if (yield from self._CastSkillID(self.way_of_perfection, log=False, aftercast_delay=1000)):
            ConsoleLog(self.build_name, "Casting Way of Perfection.", Py4GW.Console.MessageType.Info, log=False)
            return

        if not self.in_killing_routine:
            player_hp = Agent.GetHealth(player_agent_id)
            kill_spot_x, kill_spot_y = (12684, -17184)
            player_x, player_y = GLOBAL_CACHE.Player.GetXY()
            dx = kill_spot_x - player_x
            dy = kill_spot_y - player_y
            distance_threshold = Range.Area.value * 1.5
            within_range_distance = dx * dx + dy * dy <= distance_threshold * distance_threshold
            if (player_hp < 0.35 and not within_range_distance) or self.stuck_signal:
                center_point1 = (10980, -21532)
                center_point2 = (11461, -17282)
                player_pos = GLOBAL_CACHE.Player.GetXY()

                distance_to_center1 = Utils.Distance(player_pos, center_point1)
                distance_to_center2 = Utils.Distance(player_pos, center_point2)
                goal = center_point1 if distance_to_center1 < distance_to_center2 else center_point2
                # Compute direction to goal
                to_goal = (goal[0] - player_pos[0], goal[1] - player_pos[1])

                best_enemy = 0
                most_opposite_score = 1

                enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.Spellcast.value)

                for enemy in enemy_array:
                    if Agent.IsDead(enemy):
                        continue
                    enemy_pos = Agent.GetXY(enemy)
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
                    return

        if self.in_killing_routine and has_shadow_form and has_shroud_of_distress and has_mantra_of_earth:
            is_wastrels_slot_ready = Routines.Checks.Skills.IsSkillSlotReady(self.wastrels_demise_slot)
            is_arcane_echo_slot_ready = Routines.Checks.Skills.IsSkillSlotReady(self.arcane_echo_slot)
            target = GetNotHexedEnemy()
            px, py = GLOBAL_CACHE.Player.GetXY()
            num_enemies = len(Routines.Agents.GetFilteredEnemyArray(px, py, Range.Earshot.value))
            if target and shadow_form_buff_time_remaining >= 4000 and num_enemies >= 3:
                GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                GLOBAL_CACHE.Player.ChangeTarget(target)
                if is_wastrels_slot_ready and is_arcane_echo_slot_ready:
                    yield from self._CastSkillSlot(self.arcane_echo_slot, log=False, aftercast_delay=1200)
                    GLOBAL_CACHE.Player.Interact(target, False)
                    ConsoleLog(self.build_name, "Casting Arcane Echo.", Py4GW.Console.MessageType.Info, log=False)
                elif is_arcane_echo_slot_ready:
                    yield from self._CastSkillSlot(self.arcane_echo_slot, log=False, aftercast_delay=500)
                    GLOBAL_CACHE.Player.Interact(target, False)
                    ConsoleLog(self.build_name, "Casting Echoed Wastrel.", Py4GW.Console.MessageType.Info, log=False)

            target = GetNotHexedEnemy()
            if target and not Routines.Checks.Skills.IsSkillSlotReady(self.arcane_echo_slot):
                GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                GLOBAL_CACHE.Player.ChangeTarget(target)
                if (yield from self._CastSkillSlot(self.wastrels_demise_slot, log=False, aftercast_delay=500)):
                    GLOBAL_CACHE.Player.Interact(target, False)

        yield from Routines.Yield.wait(100)


# endregion
