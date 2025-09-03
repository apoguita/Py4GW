from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
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

class MoveToPartyMemberIfInAggroUtility(CustomSkillUtilityBase):
    def __init__(
            self, 
            current_build: list[CustomSkill], 
            allowed_states: list[BehaviorState] = [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:
        
        super().__init__(
            skill=CustomSkill("move_to_party_member_if_in_aggro"), 
            in_game_build=current_build, 
            score_definition=ScoreStaticDefinition(CommonScore.BOTTING.value), 
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.BOTTING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.BOTTING.value + 0.0092) 
        self.throttle_timer = ThrottledTimer(1_500)

    def _get_first_party_member_in_aggro(self) -> int | None:
        players = GLOBAL_CACHE.Party.GetPlayers()
        for player in players:
            agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
            if custom_behavior_helpers.Targets.is_party_member_in_aggro(agent_id):
                return agent_id
        return None
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if not self.throttle_timer.IsExpired(): return None

        agent_id_in_aggro = self._get_first_party_member_in_aggro()
        if agent_id_in_aggro is None: return None
        if agent_id_in_aggro == GLOBAL_CACHE.Player.GetAgentID(): return None
        
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        yield
        return BehaviorResult.ACTION_SKIPPED