from enum import Enum
import time
from typing import Any, Generator, Callable, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Player
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.mesmer.arcane_echo_utility import ArcaneEchoUtility


class ArcaneEchoVaettirFarmUtility(ArcaneEchoUtility):

    def __init__(self, 
                    event_bus: EventBus,
                    current_build: list[CustomSkill], 
                    original_skill_to_copy: CustomSkillUtilityBase,
                    new_copied_instance: CustomSkillUtilityBase,
                    arcane_echo_score_definition: ScoreStaticDefinition = ScoreStaticDefinition(82),
                    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
            ) -> None:

            super().__init__(
                event_bus=event_bus,
                current_build=current_build, 
                original_skill_to_copy=original_skill_to_copy,
                new_copied_instance=new_copied_instance,
                arcane_echo_score_definition=arcane_echo_score_definition,
                allowed_states=allowed_states)

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        original_score:float | None = self.original_skill_to_copy.evaluate(current_state, previously_attempted_skills)
        if original_score is None: return None

        has_shadow_form_buff = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.custom_skill.skill_id)
        if not has_shadow_form_buff: return None

        shadow_form_buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(Player.GetAgentID(), self.custom_skill.skill_id)
        if shadow_form_buff_time_remaining <= 6000: return None # we want to wait for shadow form before casting echo.
        
        return original_score
    
    
            


