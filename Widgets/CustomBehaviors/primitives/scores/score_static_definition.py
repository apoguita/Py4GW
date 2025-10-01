from abc import abstractmethod
from typing import Callable, override

from Widgets.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition

class ScoreStaticDefinition(ScoreDefinition):
    def __init__(self, score: float):
        super().__init__()
        self.score: float = score

    def get_score(self) -> float:
        return self.score