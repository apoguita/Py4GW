from typing import Any, Generator, override

from Py4GWCoreLib import Agent, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class PutridBile_NearDeathUtility(CustomSkillUtilityBase):
    """
    Utility for the 'Putrid Bile' and 'Icy Veins'.

    Behavior:
    - Try and target near death targets first.
    - This utility will only consider enemies whose health fraction is below 75% and will prefer the
      lowest-health valid enemy in spellcast range.
    - By default it's only considered while engaged (IN_AGGRO) to avoid wasting it out of combat.

    Note: This implementation assumes Agent.GetHealth(agent_id) returns a normalized fraction (0.0 - 1.0).
    If your code uses absolute HP values, tell me and I'll change the check to compare against max HP.
    """

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        skill: CustomSkill = CustomSkill("Putrid_Bile"),
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(30),
        mana_required_to_cast: int = 15,
        required_hp_fraction: float = 0.75,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition = score_definition
        self.REQUIRED_TARGET_HP_FRACTION = required_hp_fraction

    def _get_candidates(self) -> tuple[int, ...]:
        """
        Return enemy agent IDs ordered by priority (lowest HP, then distance) within shout/spellcast range.

        Only include enemies with known health fraction > 0 and < REQUIRED_TARGET_HP_FRACTION.
        """
        def condition(agent_id: int) -> bool:
            hp = Agent.GetHealth(agent_id)
            return hp is not None and 0.0 < hp < self.REQUIRED_TARGET_HP_FRACTION and not Agent.IsSpirit(agent_id)

        return custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority(
            within_range=Range.Spellcast,
            condition=condition,
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
        )

    def _get_best_target(self) -> int | None:
        candidates = self._get_candidates()
        if not candidates:
            return None
        return candidates[0]

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        """
        Return the configured score if there is a valid target under 50% health in range, otherwise None.
        """
        target = self._get_best_target()
        if target is None:
            return None

        try:
            target_health = Agent.GetHealth(target)
        except Exception:
            return None

        if target_health is None:
            return None

        if target_health >= self.REQUIRED_TARGET_HP_FRACTION:
            return None

        if self.nature_has_been_attempted_last(previously_attempted_skills):
            return self.score_definition.get_score() * 0.5
        else:
            return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        """
        Cast the shout at the chosen target.
        """
        target = self._get_best_target()
        if target is None:
            return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target)
        return result