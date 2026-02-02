from typing import Any, Callable, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.enums import SharedCommandType
from Sources.oazix.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class ResignIfNeededUtility_Deprecated(CustomSkillUtilityBase):
    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
            on_failure: Callable[[], Generator[Any, Any, Any]]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("resign_if_needed"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.BOTTING.value),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.BOTTING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.BOTTING.value)
        self.on_failure: Callable[[], Generator[Any, Any, Any]] = on_failure

        self.event_bus.subscribe(EventType.PLAYER_CRITICAL_STUCK, self.resign_or_raise_failure, subscriber_name=self.custom_skill.skill_name)
        self.event_bus.subscribe(EventType.PLAYER_CRITICAL_DEATH, self.resign_or_raise_failure, subscriber_name=self.custom_skill.skill_name)
        self.event_bus.subscribe(EventType.PARTY_DEATH, self.resign_or_raise_failure, subscriber_name=self.custom_skill.skill_name)

    def resign_or_raise_failure(self, message: EventMessage) -> Generator[Any, Any, Any]:
        if not self.are_common_pre_checks_valid(message.current_state): return

        result = yield from BottingHelpers.wait_until_party_resign(15_000)
        if result == False:
            yield from self.on_failure()

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        yield
        return BehaviorResult.ACTION_SKIPPED