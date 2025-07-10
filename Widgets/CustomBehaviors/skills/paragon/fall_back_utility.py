from re import S
from typing import Any, Callable, Generator, override
import random

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.enums import Profession, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class FallBackUtility(CustomSkillUtilityBase):
    def __init__(
            self, 
            current_build: list[CustomSkill], 
            score_definition: ScoreStaticDefinition = ScoreStaticDefinition(99.99), 
            allowed_states: list[BehaviorState] = [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
            ) -> None:
        
        super().__init__(
            skill=CustomSkill("Fall_Back"), 
            in_game_build=current_build, 
            score_definition=score_definition, 
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        
        if self._check_before_fallback(): return self.score_definition.get_score()
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        result: BehaviorResult = yield from custom_behavior_helpers.Helpers.wait_for_condition_before_execution(
            milliseconds=random.randint(500, 1500), # just to avoid the collision between accounts (until we have a global lock mecanism)
            action=lambda: custom_behavior_helpers.Actions.cast_skill(self.custom_skill), 
            condition_check= lambda: self._check_before_fallback())

        return result 

    def _check_before_fallback(self) -> bool:
        has_buff = Routines.Checks.Effects.HasBuff(GLOBAL_CACHE.Player.GetAgentID(), self.custom_skill.skill_id)
        is_moving = GLOBAL_CACHE.Agent.IsMoving(GLOBAL_CACHE.Player.GetAgentID())

        return not has_buff and is_moving


