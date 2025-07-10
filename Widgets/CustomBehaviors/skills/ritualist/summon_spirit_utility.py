from typing import Any, Generator, override, Optional, Callable

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.enums import SpiritModelID
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.bus.event_bus import EVENT_BUS
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage


class SummonSpiritUtility(CustomSkillUtilityBase):
    def __init__(self, 
                 current_build: list[CustomSkill], 
                 score_definition: ScoreStaticDefinition) -> None:
        
        super().__init__(
            skill=CustomSkill("Summon_Spirits_luxon"), 
            in_game_build=current_build, 
            score_definition=score_definition, 
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        
        self.score_definition: ScoreStaticDefinition = score_definition
        self.owned_spirits: list[SpiritModelID] = []

        EVENT_BUS.subscribe(EventType.SPIRIT_CREATED, self.on_spirit_created)

    def on_spirit_created(self, message: EventMessage):

        spirit_model_id: SpiritModelID = message.data
        if spirit_model_id is None: return
        
        if spirit_model_id not in self.owned_spirits:
            self.owned_spirits.append(spirit_model_id)

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
       
       # we check life & distance of owned spirits

       spirits: list[custom_behavior_helpers.SpiritAgentData] = custom_behavior_helpers.Targets.get_all_spirits_raw(
        within_range=Range.Compass,
        spirit_model_ids=self.owned_spirits,
        condition=lambda agent_id: True
       )

       for spirit in spirits:
        print(f"spirit: {spirit.agent_id} - {spirit.hp}")

       # if distance > Spirit, we summon spirit
       if current_state is BehaviorState.FAR_FROM_AGGRO:
            for spirit in spirits:
                if spirit.distance_from_player > Range.Compass.value * 0.75:
                    return self.score_definition.get_score()

       if current_state is BehaviorState.CLOSE_TO_AGGRO or current_state is BehaviorState.IN_AGGRO:
            for spirit in spirits:
                if spirit.distance_from_player > Range.Area.value:
                    return self.score_definition.get_score()

       # if any spirit has life lower than < x, we summon spirit
       for spirit in spirits:
        if spirit.hp < 0.9:
            return self.score_definition.get_score()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result