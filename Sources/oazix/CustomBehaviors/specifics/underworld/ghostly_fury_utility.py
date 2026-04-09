from typing import Any, Generator, override

from Py4GWCoreLib import Agent, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.specifics.underworld.dhuum_helpers import is_uw_chest_present
from Sources.oazix.CustomBehaviors.specifics.underworld.reaper_mode_tracker import ReaperModeTracker


class GhostlyFuryUtility(CustomSkillUtilityBase):
    """Mirror a Reaper's Ghostly Fury cast.

    Mode detection (DREST vs FURY) is provided by ReaperModeTracker.
    Score: 97 (same tier as DhuumsRestUtility; only one fires per mode).
    Suppressed when the Underworld Chest is present.
    Target: nearest living enemy; the party's current target is prioritised.
    """

    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill]):
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Ghostly_Fury"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(97),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )

    def _get_target(self) -> int | None:
        return custom_behavior_helpers.Targets.get_nearest_or_default_from_enemy_ordered_by_priority(
            within_range=Range.Spellcast.value,
            should_prioritize_party_target=True,
            condition=lambda agent_id: Agent.IsValid(agent_id) and Agent.IsAlive(agent_id),
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if is_uw_chest_present():
            return None
        if not ReaperModeTracker.is_ghostly_fury_mode():
            return None
        if self._get_target() is None:
            return None
        return 97.0

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        target_id = self._get_target()
        if target_id is None:
            if False:
                yield None
            return BehaviorResult.ACTION_SKIPPED
        return (yield from custom_behavior_helpers.Actions.cast_skill_to_target(
            self.custom_skill,
            target_agent_id=target_id,
        ))


