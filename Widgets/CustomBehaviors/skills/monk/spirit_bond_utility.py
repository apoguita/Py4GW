from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Range, Agent, Player
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class SpiritBondUtility(CustomSkillUtilityBase):
    """
    Utility to decide casting Spirit_Bond.

    Rules:
    - Use Spirit_Bond only when the caster's energy is below 40% (energy as fraction, e.g. 0.39).
    - Target the lowest-health alive ally in spellcast range (excluding the caster).
    This is a general (non-buff) skill utility — no profession/buff configuration is applied.
    """

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(33),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Spirit_Bond"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition: ScoreStaticDefinition = score_definition

    def _get_target(self) -> int | None:
        """
        Return the agent id of the lowest-health alive ally within spellcast range,
        or None if none match.
        """
        target: int | None = custom_behavior_helpers.Targets.get_first_or_default_from_allies_ordered_by_priority(
            within_range=Range.Spellcast.value,
            condition=lambda agent_id:
                agent_id != Player.GetAgentID() and
                (Agent.GetHealth(agent_id) is not None and Agent.GetHealth(agent_id) > 0.0),
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
            range_to_count_enemies=None,
            range_to_count_allies=None,
        )

        return target

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        """
        Decide whether Spirit_Bond should be attempted right now.

        - Check caster energy (< 0.40)
        - Confirm a valid target exists
        - If both true, return configured static score, otherwise None
        """
        try:
            player_agent = Player.GetAgentID()
            player_energy = Agent.GetEnergy(player_agent)
        except Exception:
            # If we cannot read player energy, do not attempt
            return None

        if player_energy is None:
            return None

        # Use when energy is strictly less than 40% (energy is a fraction 0..1)
        if player_energy >= 0.4:
            return None

        if self._get_target() is None:
            return None

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        """
        Execute the cast on the chosen lowest-health ally.
        """
        target = self._get_target()
        if target is None:
            return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target)
        return result