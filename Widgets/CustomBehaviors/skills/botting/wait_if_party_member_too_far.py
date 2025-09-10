from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, Routines, Range
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
import time
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class WaitIfPartyMemberTooFarUtility(CustomSkillUtilityBase):
    def __init__(
            self, 
            current_build: list[CustomSkill]
        ) -> None:
        
        super().__init__(
            skill=CustomSkill("wait_if_party_member_too_far"), 
            in_game_build=current_build, 
            score_definition=ScoreStaticDefinition(CommonScore.BOTTING.value+ 0.0091), 
            allowed_states=[BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.BOTTING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.BOTTING.value)
        
    def __should_wait_for_party(self) -> bool:
        player_pos: tuple[float, float] = GLOBAL_CACHE.Player.GetXY()
        agent_ids: list[int] = GLOBAL_CACHE.AgentArray.GetAllyArray()
        party_size = len(agent_ids)
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        agent_ids = AgentArray.Filter.ByDistance(agent_ids, player_pos, Range.Spellcast.value * 0.75)
        party_size_within_range = len(agent_ids)
        return party_size_within_range < party_size

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True
    
    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        should_wait_for_party = self.__should_wait_for_party()
        if should_wait_for_party:
            return self.score_definition.get_score()
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        yield from Routines.Yield.wait(300) # we stuck the flow. (not yield from)
        return BehaviorResult.ACTION_PERFORMED