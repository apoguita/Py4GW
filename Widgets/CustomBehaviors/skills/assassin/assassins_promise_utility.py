from typing import Any, Generator, override

from Py4GWCoreLib import Agent, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class AssassinsPromiseUtility(CustomSkillUtilityBase):
    """
    Utility for the Assassin elite hex 'Assassin's Promise'.

    Behaviour:
    - Elite hex: when the hexed target dies while hex is active you gain energy and all your skills recharge.
    - Will only consider enemies below 50% health and prefers the lowest-health one in cast range.
    - Only considered when engaged (IN_AGGRO) by default to avoid wasting the elite out of combat.

    Note: target selection is restricted to enemies with health fraction < 0.5 as requested.
    """

    # Hard requirement for target HP fraction
    REQUIRED_TARGET_HP_FRACTION = 0.6

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(90),
        mana_required_to_cast: int = 5,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Assassins_Promise"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition = score_definition

    def _get_candidates(self) -> tuple[int, ...]:
        """
        Return enemy agent IDs ordered by priority (lowest HP, then distance) within spellcast range.

        Only includes enemies whose health fraction is below REQUIRED_TARGET_HP_FRACTION (0.5).
        """
        def condition(agent_id: int) -> bool:
            hp = Agent.GetHealth(agent_id)
            # Include only alive agents with a known health fraction below 0.5
            return hp is not None and hp > 0.0 and hp < self.REQUIRED_TARGET_HP_FRACTION

        return custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority(
            within_range=Range.Spellcast,
            condition=condition,
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
        )

    def _get_best_target(self) -> int | None:
        """
        Pick the lowest-health valid enemy within range whose health < 0.5, or None.
        """
        candidates = self._get_candidates()
        if not candidates:
            return None
        return candidates[0]

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        """
        Decide whether to attempt casting Assassin's Promise.

        Conditions:
        - There must be a valid target in range with health < 0.5.
        - Returns configured static score if conditions met, otherwise None.
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

        # Safety: ensure the picked target still meets the required HP fraction
        if target_health >= self.REQUIRED_TARGET_HP_FRACTION:
            return None

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        """
        Cast Assassin's Promise on the chosen target.
        """
        target = self._get_best_target()
        if target is None:
            return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target)
        return result