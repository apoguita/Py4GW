# python
from typing import Any, Generator, List, override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class PreparationUtility(CustomSkillUtilityBase):
    """
    Cast a preparation skill (e.g. Intensity) only when at least one of the provided
    target utilities currently has a valid evaluation (i.e. a follow-up will be available).

    Ensures `_execute` is a generator and uses `yield from` for action calls so callers
    that expect a generator do not encounter `StopIteration`.
    """

    def __init__(
        self,
        event_bus: EventBus,
        prep_skill: CustomSkill,
        target_utilities: List[CustomSkillUtilityBase],
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(60),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=prep_skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )
        self.target_utilities = target_utilities
        self.score_definition = score_definition

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        # If the prep skill is not present in the in-game build, don't try
        if not any(getattr(s, "skill_id", None) == self.custom_skill.skill_id for s in self.in_game_build):
            return None

        # If any target utility currently evaluates to a score, allow the prep skill
        for util in self.target_utilities:
            try:
                score = util.evaluate(current_state, previously_attempted_skills)
            except Exception:
                # safety: if a target utility throws, treat it as not available
                score = None
            if score is not None:
                return self.score_definition.get_score()
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        # Use yield from so this function remains a generator and action helpers are invoked correctly.
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result
