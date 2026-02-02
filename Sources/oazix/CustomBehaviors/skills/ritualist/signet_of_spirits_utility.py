from typing import Any, Generator, override

from Py4GWCoreLib import Range
from Py4GWCoreLib.enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class SignetOfSpiritsUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(85),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Signet_of_Spirits"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
                
        self.score_definition: ScoreStaticDefinition = score_definition

        self.hate_spirit: SpiritModelID = SpiritModelID.HATE
        self.suffering_spirit: SpiritModelID = SpiritModelID.SUFFERING
        self.anger_spirit: SpiritModelID = SpiritModelID.ANGER
        self.owned_spirit_model_ids: list[SpiritModelID] = [self.hate_spirit, self.suffering_spirit, self.anger_spirit]

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        # we only recast if one of the 3 spirits is dead

        spirits: list[custom_behavior_helpers.SpiritAgentData] = custom_behavior_helpers.Targets.get_all_spirits_raw(
            within_range=Range.Spirit,
            spirit_model_ids=self.owned_spirit_model_ids,
            condition=lambda agent_id: True
        )

        if len(spirits) >= 3: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        if result == BehaviorResult.ACTION_PERFORMED:
            yield from self.event_bus.publish(EventType.SPIRIT_CREATED, state, data=self.hate_spirit)
            yield from self.event_bus.publish(EventType.SPIRIT_CREATED, state, data=self.suffering_spirit)
            yield from self.event_bus.publish(EventType.SPIRIT_CREATED, state, data=self.anger_spirit)

        return result