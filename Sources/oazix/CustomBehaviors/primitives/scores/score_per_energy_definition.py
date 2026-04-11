from typing import override

from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition


class ScorePerEnergyDefinition(ScoreDefinition):
    """
    Score that ramps linearly between a nominal and boosted value based on
    the player's current energy percentage.

    - Above `block_threshold`: returns None (skill is not applicable)
    - Between `block_threshold` and `floor_threshold`: linear ramp from nominal to boosted
    - At or below `floor_threshold`: returns boosted (clamped)

    Used for energy-recovery interrupts like Power Drain, where the skill
    should fire more urgently the lower the player's energy is.
    """

    def __init__(self,
                 score_nominal: float,
                 score_boosted: float,
                 block_threshold: float = 0.85,
                 floor_threshold: float = 0.0):
        super().__init__()
        self.score_nominal: float = score_nominal
        self.score_boosted: float = score_boosted
        self.block_threshold: float = block_threshold
        self.floor_threshold: float = floor_threshold

    def get_score(self, energy_pct: float) -> float | None:
        """
        Args:
            energy_pct: Player energy as a fraction 0.0-1.0

        Returns:
            A score on the linear ramp from nominal to boosted, or None if
            the player is above block_threshold (skill not applicable).
        """
        if energy_pct > self.block_threshold:
            return None

        span = self.block_threshold - self.floor_threshold
        if span <= 0:
            return self.score_boosted

        # t = 0 at block_threshold, t = 1 at floor_threshold
        t = (self.block_threshold - energy_pct) / span
        t = max(0.0, min(1.0, t))
        return self.score_nominal + (self.score_boosted - self.score_nominal) * t

    @override
    def score_definition_debug_ui(self) -> str:
        return (f"score is {self.score_boosted:06.4f} (<={self.floor_threshold*100:.0f}%) "
                f"/ {self.score_nominal:06.4f} (@{self.block_threshold*100:.0f}%) "
                f"/ blocked above {self.block_threshold*100:.0f}%")
