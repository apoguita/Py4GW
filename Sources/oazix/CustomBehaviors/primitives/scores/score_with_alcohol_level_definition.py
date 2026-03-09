from typing import override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition

class ScoreWithAlcoholLevelDefinition(ScoreDefinition):

    def __init__(self, score_with_alcohol: float, score_without_alcohol: float):
        super().__init__()
        self.score_with_alcohol: float = score_with_alcohol
        self.score_without_alcohol: float = score_without_alcohol

    def get_score(self, has_alcohol: bool) -> float:
        return self.score_with_alcohol if has_alcohol else self.score_without_alcohol
    
    @override
    def score_definition_debug_ui(self) -> str:
        return f"score is {self.score_with_alcohol:06.4f} if alcohol is present, {self.score_without_alcohol:06.4f} otherwise"