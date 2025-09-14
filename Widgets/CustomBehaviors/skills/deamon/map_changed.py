import random
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Widgets.CustomBehaviors.primitives.bus.event_bus import EVENT_BUS
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
import time
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class MapChangedUtility(CustomSkillUtilityBase):
    def __init__(
            self, 
            current_build: list[CustomSkill], 
        ) -> None:
        
        super().__init__(
            skill=CustomSkill("map_changed"), 
            in_game_build=current_build, 
            score_definition=ScoreStaticDefinition(CommonScore.DEAMON.value), 
            allowed_states=[BehaviorState.IDLE, BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.DAEMON)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.BOTTING.value)
        self.throttle_timer = ThrottledTimer(1_000)
        self.__previous_map_id = 0

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if not self.throttle_timer.IsExpired(): return None

        if self.__previous_map_id == GLOBAL_CACHE.Map.GetMapID():
            return None

        if self.__previous_map_id != GLOBAL_CACHE.Map.GetMapID():
            self.__previous_map_id = GLOBAL_CACHE.Map.GetMapID()
            return self.score_definition.get_score()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        
        EVENT_BUS.publish(EventType.MAP_CHANGED)
        self.throttle_timer.Reset()
        yield
        return BehaviorResult.ACTION_PERFORMED