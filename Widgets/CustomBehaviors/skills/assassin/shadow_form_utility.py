from tkinter.constants import N
from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class ShadowFormUtility(CustomSkillUtilityBase):
    def __init__(self, 
    current_build: list[CustomSkill], 
    score_definition: ScoreStaticDefinition,
    mana_required_to_cast: int = 0,
    is_deadly_paradox_required: bool = False,
    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
    ) -> None:

        super().__init__(
            skill=CustomSkill("Shadow_Form"), 
            in_game_build=current_build, 
            score_definition=score_definition, 
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition
        self.is_deadly_paradox_required: bool = is_deadly_paradox_required
        self.deadly_paradox_skill: CustomSkill = CustomSkill("Deadly_Paradox")
        self.renew_before_expiration_in_milliseconds: int = 1200

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        has_shadow_form_buff = Routines.Checks.Effects.HasBuff(GLOBAL_CACHE.Player.GetAgentID(), self.custom_skill.skill_id)
        has_deadly_paradox_buff = Routines.Checks.Effects.HasBuff(GLOBAL_CACHE.Player.GetAgentID(), self.deadly_paradox_skill.skill_id)

        if self.is_deadly_paradox_required:
            if not has_deadly_paradox_buff: return None

        deadly_paradox_buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(GLOBAL_CACHE.Player.GetAgentID(), self.deadly_paradox_skill.skill_id)
        if deadly_paradox_buff_time_remaining <= 1200: return None # we wait for deadly paradox refresh to be buffed

        if not has_shadow_form_buff: 
            return self.score_definition.get_score() 

        shadow_form_buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(GLOBAL_CACHE.Player.GetAgentID(), self.custom_skill.skill_id)
        if shadow_form_buff_time_remaining <= self.renew_before_expiration_in_milliseconds: return self.score_definition.get_score()
        
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result