
from typing import override
from Widgets.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Widgets.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition


class ScorePerHealthGravityDefinition(ScoreDefinition):
    def __init__(self, additive_score_weight: float):
        super().__init__()
        if additive_score_weight > 10: raise ValueError("Additive score weight for healing score must be less than 10")
        self.additive_score_weight: float = additive_score_weight

    def get_score(self, health_gravity: HealingScore) -> float:
        return float(health_gravity) + self.additive_score_weight

    @override
    def score_definition_debug_ui(self) -> str:
        score_1 = self.get_score(HealingScore.PARTY_DAMAGE_EMERGENCY)
        score_2 = self.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY)
        score_3 = self.get_score(HealingScore.MEMBER_DAMAGED)
        score_4 = self.get_score(HealingScore.PARTY_DAMAGE)
        score_5 = self.get_score(HealingScore.MEMBER_CONDITIONED)
        score_6 = self.get_score(HealingScore.PARTY_HEALTHY)

        return f"score is per heal gravity({score_1:06.4f}->{score_2:06.4f}->{score_3:06.4f}->{score_4:06.4f}->{score_5:06.4f}->{score_6:06.4f})"