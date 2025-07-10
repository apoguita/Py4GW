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