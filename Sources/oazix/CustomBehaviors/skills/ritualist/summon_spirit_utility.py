from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import Range
from Py4GWCoreLib.enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class SummonSpiritUtility(CustomSkillUtilityBase):
    def __init__(self,
                 event_bus: EventBus,
                 skill: CustomSkill,
                 current_build: list[CustomSkill],
                 score_definition: ScoreStaticDefinition) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])

        self.score_definition: ScoreStaticDefinition = score_definition
        self.owned_spirits: list[SpiritModelID] = []

        self.event_bus.subscribe(EventType.SPIRIT_CREATED, self.on_spirit_created, subscriber_name=self.custom_skill.skill_name)

    def on_spirit_created(self, message: EventMessage) -> Generator[Any, Any, Any]:

        spirit_model_id: SpiritModelID = message.data
        if spirit_model_id is None: return

        if spirit_model_id not in self.owned_spirits:
            self.owned_spirits.append(spirit_model_id)
        yield

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        # we check life & distance of owned spirits
        spirits: list[custom_behavior_helpers.SpiritAgentData] = custom_behavior_helpers.Targets.get_all_spirits_raw(
            within_range=Range.Compass,
            spirit_model_ids=self.owned_spirits,
            condition=lambda agent_id: True
        )

        for spirit in spirits:
            if current_state is BehaviorState.FAR_FROM_AGGRO and spirit.distance_from_player > Range.Compass.value * 0.75:
                return self.score_definition.get_score()
            if (current_state is BehaviorState.CLOSE_TO_AGGRO or current_state is BehaviorState.IN_AGGRO) and spirit.distance_from_player > Range.Area.value:
                return self.score_definition.get_score()
            # if any spirit has life lower than < x, we summon spirit
            if spirit.hp < 0.9:
                return self.score_definition.get_score()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result
    
    @override
    def customized_debug_ui(self, current_state):
        PyImGui.bullet_text(f"owned_spirits :")
        for spirit in self.owned_spirits:
            PyImGui.text(f"spirit : {spirit}")

        spirits: list[custom_behavior_helpers.SpiritAgentData] = custom_behavior_helpers.Targets.get_all_spirits_raw(
            within_range=Range.Compass,
            spirit_model_ids=self.owned_spirits,
            condition=lambda agent_id: True
        )

        PyImGui.bullet_text(f"spirits on map :")
        for spirit in spirits:
            PyImGui.text(f"spirit_agent_id : {spirit.agent_id}, distance : {spirit.distance_from_player:.2f}, hp : {spirit.hp:.2f}")
        return