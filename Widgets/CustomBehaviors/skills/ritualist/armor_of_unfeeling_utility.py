from typing import Any, Generator, override

from Py4GWCoreLib.enums import SpiritModelID
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EVENT_BUS
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class ArmorOfUnfeelingUtility(CustomSkillUtilityBase):
    def __init__(self, 
        current_build: list[CustomSkill], 
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(80),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
        ) -> None:

        super().__init__(
            skill=CustomSkill("Armor_of_Unfeeling"), 
            in_game_build=current_build, 
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)
                
        self.score_definition: ScoreStaticDefinition = score_definition
        self.owned_spirits: list[SpiritModelID] = []

        EVENT_BUS.subscribe(EventType.SPIRIT_CREATED, self.on_spirit_created)

    def on_spirit_created(self, message: EventMessage):
        spirit_model_id: SpiritModelID = message.data
        if spirit_model_id is None: return

        if spirit_model_id == SpiritModelID.DISPLACEMENT: return

        if spirit_model_id in self.owned_spirits:
            return

        self.owned_spirits.append(spirit_model_id)

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if current_state is BehaviorState.FAR_FROM_AGGRO: return None

        if len(self.owned_spirits) > 1: #we have at least 2 spirits that require armor of unfeeling ; we could wait for only 1 spirit + a duration...
            return self.score_definition.get_score()      

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        if result is BehaviorResult.ACTION_PERFORMED:
            self.owned_spirits.clear()
        return result 