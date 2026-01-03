from typing import Any, Callable, Generator, override
from Py4GWCoreLib import Routines, Agent
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.enums import Profession, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Widgets.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class EbonBattleStandardOfHonorUtility(CustomSkillUtilityBase):

    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 65 if enemy_qte >= 3 else 50 if enemy_qte <= 2 else 25),
        mana_required_to_cast: int = 20,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Ebon_Battle_Standard_of_Honor"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScorePerAgentQuantityDefinition = score_definition
        self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget(event_bus, self.custom_skill, buff_configuration_per_profession= BuffConfigurationPerProfession.BUFF_CONFIGURATION_MARTIAL)

        # Combat start timer - 5 second delay when combat begins
        self.combat_start_timer = ThrottledTimer(5000)  # 5 seconds
        self.previous_state: BehaviorState | None = None

        # Subscribe to map change events to reset timer
        self.event_bus.subscribe(EventType.MAP_CHANGED, self.map_changed, subscriber_name=self.custom_skill.skill_name)

    def map_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:
        """Reset combat timer when map changes"""
        self.combat_start_timer.Reset()
        self.previous_state = None
        yield

    def _get_agent_array(self) -> list[int]:

        agent_array = AgentArray.GetAllyArray()
        agent_array = AgentArray.Filter.ByCondition(agent_array, lambda agent_id: Agent.IsAlive(agent_id))
        agent_array = AgentArray.Filter.ByCondition(agent_array, lambda agent_id: agent_id != GLOBAL_CACHE.Player.GetAgentID())
        agent_array = AgentArray.Filter.ByCondition(agent_array, lambda agent_id: self.buff_configuration.get_agent_id_predicate()(agent_id))
        agent_array = AgentArray.Filter.ByDistance(agent_array, GLOBAL_CACHE.Player.GetXY(), Range.Spellcast.value)
        return [agent_id for agent_id in agent_array]

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        # Track state transitions to detect when combat starts
        if self.previous_state != current_state:
            if self.previous_state != BehaviorState.IN_AGGRO and current_state == BehaviorState.IN_AGGRO:
                # Combat just started - reset the timer
                self.combat_start_timer.Reset()
                print("EbonBattleStandardOfHonorUtility: Combat started, waiting 5 seconds before casting")
            self.previous_state = current_state

        # If we're in combat and the timer hasn't expired yet, don't cast
        if current_state == BehaviorState.IN_AGGRO and not self.combat_start_timer.IsExpired():
            return None

        agent_ids: list[int] = self._get_agent_array()
        gravity_center: custom_behavior_helpers.GravityCenter | None = custom_behavior_helpers.Targets.find_optimal_gravity_center(Range.Area, agent_ids=agent_ids)
        if gravity_center is None: return None
        if gravity_center.distance_from_player > Range.Area.value: # else it doesn't worth moving, we are too far
            # if self.DEBUG: print("EbonBattleStandardOfHonorUtility: moving to a better place (gravity center).")
            return None # it doesn't worth moving, we are too far

        if gravity_center.agent_covered_count >= 1: return self.score_definition.get_score(gravity_center.agent_covered_count)
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        agent_ids: list[int] = self._get_agent_array()

        gravity_center: custom_behavior_helpers.GravityCenter | None = custom_behavior_helpers.Targets.find_optimal_gravity_center(Range.Area, agent_ids=agent_ids)
        exit_condition: Callable[[], bool] = lambda: False
        tolerance: float = 30

        if gravity_center is not None and gravity_center.distance_from_player < Range.Area.value: # else it doesn't worth moving, we are too far
            path_points: list[tuple[float, float]] = [gravity_center.coordinates]

            yield from Routines.Yield.Movement.FollowPath(
                path_points=path_points, 
                custom_exit_condition=exit_condition, 
                tolerance=tolerance, log=True, 
                timeout=4000, 
                progress_callback=lambda progress: print(f"EbonBattleStandardOfHonorUtility: progress: {progress}"))
            
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result 
    
    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return self.buff_configuration