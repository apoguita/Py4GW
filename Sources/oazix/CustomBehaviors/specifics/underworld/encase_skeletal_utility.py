from typing import Any, Generator, override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class EncaseSkeletalUtility(CustomSkillUtilityBase):
    """Encase Skeletal slot holder.

    The skill is loaded into the utility list so that the framework
    recognises it on the bar, but _evaluate always returns None so it
    is never actually cast.
    """

    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill]):
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Encase_Skeletal"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(0),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        if False:
            yield None
        return BehaviorResult.ACTION_SKIPPED
