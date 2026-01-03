from typing import Any, Callable, Generator, override
from Py4GWCoreLib import Routines, Agent
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.enums import Profession, Range
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class EbonBattleStandardOfWisdom(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 65 if enemy_qte >= 3 else 50 if enemy_qte <= 2 else 25),
        mana_required_to_cast: int = 20,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Ebon_Battle_Standard_of_Wisdom"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
        
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    def _get_agent_array(self) -> list[int]:
        allowed_classes = [Profession.Mesmer.value, Profession.Necromancer.value, Profession.Ritualist.value]
        allowed_agent_names = ["to_be_implemented"]
        agent_array = AgentArray.GetAllyArray()
        agent_array = AgentArray.Filter.ByCondition(agent_array, lambda agent_id: Agent.IsAlive(agent_id))
        agent_array = AgentArray.Filter.ByCondition(agent_array, lambda agent_id: agent_id != GLOBAL_CACHE.Player.GetAgentID())
        agent_array = AgentArray.Filter.ByCondition(agent_array, lambda agent_id: Agent.GetProfessionIDs(agent_id)[0] in allowed_classes)
        agent_array = AgentArray.Filter.ByDistance(agent_array, GLOBAL_CACHE.Player.GetXY(), Range.Spellcast.value)
        return [agent_id for agent_id in agent_array]

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        agent_ids: list[int] = self._get_agent_array()

        gravity_center: custom_behavior_helpers.GravityCenter | None = custom_behavior_helpers.Targets.find_optimal_gravity_center(Range.Area, agent_ids=agent_ids)
        if gravity_center is None: return None

        if gravity_center.distance_from_player > Range.Area.value:
            return None # it doesn't worth moving, we are too far

        if gravity_center.agent_covered_count >= 2: 
            if constants.DEBUG: print("EbonBattleStandardOfWisdomUtility: moving to a better place (gravity center).")
            return self.score_definition.get_score(gravity_center.agent_covered_count)
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        agent_ids: list[int] = self._get_agent_array()

        gravity_center: custom_behavior_helpers.GravityCenter | None = custom_behavior_helpers.Targets.find_optimal_gravity_center(Range.Area, agent_ids=agent_ids)

        exit_condition: Callable[[], bool] = lambda: False
        tolerance: float = 30

        if gravity_center is not None: # and gravity_center.distance_from_player < Range.Area.value:
            path_points: list[tuple[float, float]] = [gravity_center.coordinates]
            yield from Routines.Yield.Movement.FollowPath(
                path_points=path_points, 
                custom_exit_condition=exit_condition, 
                tolerance=tolerance, 
                log=True, 
                timeout=4000, 
                progress_callback=lambda progress: print(f"EbonBattleStandardOfWisdomUtility: progress: {progress}") if constants.DEBUG else None)
        
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result 