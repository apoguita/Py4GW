from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
import time
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition

class AutoAttackUtility(CustomSkillUtilityBase):
    def __init__(
            self, 
            current_build: list[CustomSkill], 
            allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:
        
        super().__init__(
            skill=CustomSkill("auto_attack"), 
            in_game_build=current_build, 
            score_definition=ScoreStaticDefinition(CommonScore.AUTO_ATTACK.value), 
            allowed_states=allowed_states)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.AUTO_ATTACK.value)
        self.throttle_timer = ThrottledTimer(1000)
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        return True

    def __get_target_agent_id(self) -> int:
        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            sort_key=(TargetingOrder.DISTANCE_ASC, TargetingOrder.HP_ASC))
        
        if len(targets) == 0: return 0
        return targets[0].agent_id

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if self.allowed_states is not None and current_state not in self.allowed_states:
            return None

        if not self.throttle_timer.IsExpired():
            return None

        if custom_behavior_helpers.Resources.is_player_holding_an_item():
            return None

        target_agent_id = self.__get_target_agent_id()
        if target_agent_id == 0: return None

        if GLOBAL_CACHE.Agent.IsAttacking(GLOBAL_CACHE.Player.GetAgentID()):
            self.throttle_timer.Reset()
            return None

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        target_agent_id: int = self.__get_target_agent_id()
        if target_agent_id == 0: return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.auto_attack(target_id=target_agent_id)
        self.throttle_timer.Reset()
        return result