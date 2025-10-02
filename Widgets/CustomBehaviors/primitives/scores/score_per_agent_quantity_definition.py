from abc import abstractmethod
from ast import TypeVar
from typing import Callable, Generic, override

from Widgets.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition


class ScorePerAgentQuantityDefinition(ScoreDefinition):

    def __init__(self, callable_score: Callable[[int], float]):
        super().__init__()
        self.callable_score: Callable[[int], float] = callable_score

    def get_score(self, agent_quantity: int) -> float:
        return self.callable_score(agent_quantity)

    @override
    def score_definition_debug_ui(self) -> str:
        score_one = self.callable_score(1)
        score_two = self.callable_score(2)
        score_three = self.callable_score(3)
        return f"score is per agent({score_three:06.4f}->{score_two:06.4f}->{score_one:06.4f})"