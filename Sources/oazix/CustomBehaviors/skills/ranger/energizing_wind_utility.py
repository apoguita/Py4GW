from typing import Any, Generator, override

from Py4GWCoreLib import Range, Agent, Player
from Py4GWCoreLib.enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class EnergizingWindUtility(CustomSkillUtilityBase):
    def __init__(self,
                 event_bus: EventBus,
                 current_build: list[CustomSkill],
                 score_definition: ScoreStaticDefinition = ScoreStaticDefinition(97),
                 mana_required_to_cast: int = 0,
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Energizing_Wind"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])

        self.score_definition: ScoreStaticDefinition = score_definition
        self.owned_spirit_model_id: SpiritModelID = SpiritModelID.ENERGIZING_WIND

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        spirit_agent = custom_behavior_helpers.Targets.get_first_or_default_from_spirits_raw(
            within_range=Range.Spirit,
            spirit_model_ids=[self.owned_spirit_model_id],
            condition=lambda agent_id: True)

        # Cast if spirit doesn't exist or is about to die
        if spirit_agent is None:
            return self.score_definition.get_score()
        if spirit_agent.hp < 0.2:
            return self.score_definition.get_score()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)

        if result == BehaviorResult.ACTION_PERFORMED:
            yield from self.event_bus.publish(EventType.SPIRIT_CREATED, state, data=self.owned_spirit_model_id)

        return result
