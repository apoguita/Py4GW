
from Widgets.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Widgets.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition


class ScorePerHealthGravityDefinition(ScoreDefinition):
    def __init__(self, additive_score_weight: float):
        super().__init__()
        if additive_score_weight > 10: raise ValueError("Additive score weight for healing score must be less than 10")
        self.additive_score_weight: float = additive_score_weight

    def get_score(self, health_gravity: HealingScore) -> float:
        return float(health_gravity) + self.additive_score_weight