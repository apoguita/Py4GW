from typing import override

from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition


class ScoreBoostedDefinition(ScoreDefinition):
    """
    Score definition with two values: boosted and nominal.
    Used when a skill should have different priorities based on conditions.
    """

    def __init__(self, score_nominal: float, score_boosted: float | None = None):
        super().__init__()
        self.score_nominal: float = score_nominal
        self.score_boosted: float = score_boosted if score_boosted is not None else score_nominal

    def get_score(self, is_boosted: bool) -> float:
        """
        Get the score based on whether the boost condition is met.
        
        Args:
            is_boosted: True to return boosted score, False for nominal score
            
        Returns:
            The appropriate score value
        """
        return self.score_boosted if is_boosted else self.score_nominal

    @override
    def score_definition_debug_ui(self) -> str:
        return f"score is {self.score_boosted:06.4f} (boosted) / {self.score_nominal:06.4f} (nominal)"

