from abc import abstractmethod
from typing import Callable, override

from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

class ScoreCombotDefinition(ScoreDefinition):
    def __init__(self, score: float):
        super().__init__()
        self.score: float = score

    def get_score(self, combot_type: int, party_forced_target_prioritized: bool = False) -> float:
        # 1,2,3 for lead(1) - offhand(2) - dual(3)
        return self.score + combot_type * 0.001 + (0.01 if party_forced_target_prioritized else 0.0)

    @override
    def score_definition_debug_ui(self) -> str:
        return f"{self.score:06.4f} + combot_type * 0.001"