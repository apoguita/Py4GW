from typing import override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Player

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_energy_definition import ScorePerEnergyDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.interrupt_skill_base import InterruptSkillBase


class PowerDrainUtility(InterruptSkillBase):
    """
    Power Drain is an energy-return interrupt. It only fires when the mesmer
    needs energy, and scores progressively higher the lower the current energy is.
    """

    def __init__(self,
                    event_bus: EventBus,
                    current_build: list[CustomSkill],
                    score_definition: ScorePerEnergyDefinition = ScorePerEnergyDefinition(
                        score_nominal=40,
                        score_boosted=100,
                        block_threshold=0.85,
                        floor_threshold=0.30),
                    mana_required_to_cast: int = 5,
            ) -> None:

            super().__init__(
                event_bus=event_bus,
                skill=CustomSkill("Power_Drain"),
                in_game_build=current_build,
                score_definition=score_definition,
                mana_required_to_cast=mana_required_to_cast,
                min_activation_seconds=1.00)

            self.score_definition: ScorePerEnergyDefinition = score_definition

    @override
    def _filter_target(self, skill_id: int, activation_seconds: float) -> bool:
        return (GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id) or
                GLOBAL_CACHE.Skill.Flags.IsChant(skill_id))

    @override
    def _compute_score(self, target_id: int) -> float | None:
        energy_pct = Agent.GetEnergy(Player.GetAgentID())
        return self.score_definition.get_score(energy_pct)
