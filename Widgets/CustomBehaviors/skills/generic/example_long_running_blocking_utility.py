from collections import deque
import time
from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class ExampleLongRunningBlockingUtility(CustomSkillUtilityBase):
    def __init__(self, 
    current_build: list[CustomSkill], 
    ) -> None:

        super().__init__(
            skill=CustomSkill("example_long_running_blocking_utility"), 
            in_game_build=current_build, 
            score_definition=ScoreStaticDefinition(99.99), 
            allowed_states=[BehaviorState.IDLE, BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.DAEMON,
            execution_strategy=UtilitySkillExecutionStrategy.EXECUTE_THROUGH_THE_END)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(99.99)

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        # print("score is evaluated each game loop. regardless what we are doing in _execute.")
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        print("EXECUTE_THROUGH_THE_END start")
        yield from self.wait_for_count(60)
        print("EXECUTE_THROUGH_THE_END end")

        # we are executing the yield operation each game-loop
        # even if score are changing, we will terminate this execution.
        # this is usefull for combat skills where we must respect some aftercast or engage some movements, or where we need to perform some attacks-over-time
        return BehaviorResult.ACTION_PERFORMED

    @staticmethod
    def wait_for_count(number) -> Generator[Any, Any, bool]:
        for i in range(number):
            print(f"counted {i}")
            yield 'wait'  # Pause and allow resumption while waiting
        return True
