from typing import Any, Generator, override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.specifics.underworld.dhuum_helpers import is_uw_chest_present
from Sources.oazix.CustomBehaviors.specifics.underworld.reaper_mode_tracker import ReaperModeTracker


class DhuumsRestUtility(CustomSkillUtilityBase):
    """Mirror a Reaper's Dhuum's Rest cast.

    Mode detection (DREST vs FURY) is provided by ReaperModeTracker.
    Score: 97 (highest active utility). Suppressed when the Underworld Chest is present.
    """

    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill]):
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Dhuums_Rest"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(97),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if is_uw_chest_present():
            return None
        if not ReaperModeTracker.is_dhuums_rest_mode():
            return None
        return 97.0

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        return (yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill))


