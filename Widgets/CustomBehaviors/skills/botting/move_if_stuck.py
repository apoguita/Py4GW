import random
import math
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer, Utils
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

class MoveIfStuckUtility(CustomSkillUtilityBase):
    def __init__(
            self, 
            current_build: list[CustomSkill], 
        ) -> None:
        
        super().__init__(
            skill=CustomSkill("move_if_stuck"), 
            in_game_build=current_build, 
            score_definition=ScoreStaticDefinition(CommonScore.BOTTING.value), 
            allowed_states=[BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.BOTTING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.BOTTING.value)
        
        EVENT_BUS.subscribe(EventType.PLAYER_STUCK, self.player_critical_stuck) # we do through event as there is other skill that could subscribe to that, as heart_of_shadow

    def player_critical_stuck(self, message: EventMessage):
        current_x, current_y = GLOBAL_CACHE.Player.GetXY()
        # Keep the nudge smaller than the threshold so it doesn't falsely clear stuck state
        threshold:float = message.data
        max_nudge = max(1.0, (threshold / 2) - 2.0)
        offset_x = random.uniform(-max_nudge, max_nudge)
        offset_y = random.uniform(-max_nudge, max_nudge)
        GLOBAL_CACHE.Player.Move(current_x + offset_x, current_y + offset_y)

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        # Initialize the previous position on first run and wait for next tick
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        yield
        return BehaviorResult.ACTION_SKIPPED