from abc import abstractmethod
from ast import TypeVar
from typing import Callable, Generic, override

from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition


class ScorePerStatusDefinition(ScoreDefinition):

    def __init__(self, callable_score: Callable[[BehaviorState], float]):
        super().__init__()
        self.callable_score: Callable[[BehaviorState], float] = callable_score

    def get_score(self, behavior_state: BehaviorState) -> float:
        return self.callable_score(behavior_state)

    @override
    def score_definition_debug_ui(self) -> str:
        score_one = self.callable_score(BehaviorState.IN_AGGRO)
        score_two = self.callable_score(BehaviorState.CLOSE_TO_AGGRO)
        score_three = self.callable_score(BehaviorState.FAR_FROM_AGGRO)
        score_four = self.callable_score(BehaviorState.IDLE)
        return f"score is IN_AGGRO:{score_one:06.4f} | CLOSE_TO_AGGRO:{score_two:06.4f} | FAR_FROM_AGGRO:{score_three:06.4f} | IDLE:{score_four:06.4f}"