from typing import Any, Generator, override

from Py4GWCoreLib import Agent, Range
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class IcyVeins_NearDeathUtility(CustomSkillUtilityBase):

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        skill: CustomSkill = CustomSkill("Icy_Veins"),
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(40),
        mana_required_to_cast: int = 15,
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

    def _get_candidates(self) -> tuple[int, ...]:
        """
        Return enemy agent IDs ordered by priority (lowest HP, then distance) within shout/spellcast range.
        """

        return custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority(
            within_range=Range.Spellcast,
            condition=lambda agent_id: not Agent.IsSpirit(agent_id),
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
        )

    def _get_best_target(self) -> int | None:
        candidates = self._get_candidates()
        if not candidates:
            return None
        return candidates[0]

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        target = self._get_best_target()
        if target is None:
            if constants.DEBUG: print("No candidates")
            return None

        mult = 0.5
        if self.nature_has_been_attempted_last(previously_attempted_skills):
            mult = 0.25

        # if the target is not hexed
        if not Agent.IsHexed(target):
            mult += 0.51

        # if the lowest hp target is below 50% health lets try and get that eoe like effect
        if Agent.GetHealth(target) < 0.5:
            mult += 0.51

        scored = self.score_definition.get_score() * mult

        # default max is 61.28 but in case of overrides
        if scored > 99:
            scored = 99

        return scored

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        """
        Cast the spell at the chosen target.
        """
        target = self._get_best_target()
        if target is None:
            return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target)
        return result