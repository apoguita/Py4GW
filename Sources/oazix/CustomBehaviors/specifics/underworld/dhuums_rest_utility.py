from typing import Any, Generator, override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.specifics.underworld.dhuum_helpers import is_uw_chest_present, resolve_first_known_skill
from Sources.oazix.CustomBehaviors.specifics.underworld.reaper_mode_tracker import ReaperModeTracker


class DhuumsRestUtility(CustomSkillUtilityBase):
    """Mirror a Reaper's Dhuum's Rest cast.

    Mode detection (DREST vs FURY) is provided by ReaperModeTracker.
    Score: 97 (highest active utility). Suppressed when the Underworld Chest is present.
    """

    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill]):
        skill = resolve_first_known_skill("Dhuum_s_Rest", "Dhuum's Rest", "Dhuums_Rest")
        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(97),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )
        # Register resolved ID so the tracker recognises it even in non-en locales.
        ReaperModeTracker.register_dhuums_rest_skill_id(int(self.custom_skill.skill_id))
        ReaperModeTracker._ensure_initialized()

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

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        pass

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return None

    @override
    def has_persistence(self) -> bool:
        return False

    @override
    def delete_persisted_configuration(self):
        pass

    @override
    def persist_configuration_as_global(self):
        pass

    @override
    def persist_configuration_for_account(self):
        pass
