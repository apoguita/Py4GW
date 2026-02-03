from typing import Any, Generator, override

from Py4GWCoreLib import Routines, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class LifeUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerHealthGravityDefinition = ScorePerHealthGravityDefinition(1),
        mana_required_to_cast: int = 10,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Life"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScorePerHealthGravityDefinition = score_definition

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if current_state is BehaviorState.FAR_FROM_AGGRO: return None

        spirit_exists:bool = custom_behavior_helpers.Resources.is_spirit_exist(
            within_range=Range.Spirit,
            associated_to_skill=self.custom_skill
        )

        if spirit_exists:
            return None
        if current_state is BehaviorState.CLOSE_TO_AGGRO:
            return self.score_definition.get_score(HealingScore.PARTY_HEALTHY)

        return self.score_definition.get_score(HealingScore.PARTY_DAMAGE)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        if result is BehaviorResult.ACTION_PERFORMED:
            yield from self.event_bus.publish(EventType.SPIRIT_CREATED, state, data=self.custom_skill.skill_id)
        return result