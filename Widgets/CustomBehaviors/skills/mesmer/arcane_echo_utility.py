from enum import Enum
import time
from typing import Any, Generator, Callable, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Routines
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class ArcaneEchoState(Enum):
        CAST_ARCANE_ECHO=1
        CAST_SKILL_TO_COPY=2
        CAST_COPIED_SKILL=3
        IDLE=4

class ArcaneEchoUtility(CustomSkillUtilityBase):

    def __init__(self, 
                    current_build: list[CustomSkill], 
                    original_skill_to_copy: CustomSkillUtilityBase,
                    new_copied_instance: CustomSkillUtilityBase,
                    arcane_echo_score_definition: ScoreStaticDefinition = ScoreStaticDefinition(82),
                    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
            ) -> None:

            super().__init__(
                skill=CustomSkill("Arcane_Echo"), 
                in_game_build=current_build, 
                score_definition=arcane_echo_score_definition,
                allowed_states=allowed_states)
            
            self.arcane_echo_score_definition: ScoreStaticDefinition = arcane_echo_score_definition
            self.original_skill_to_copy: CustomSkillUtilityBase = original_skill_to_copy
            
            self.new_copied_instance: CustomSkillUtilityBase = new_copied_instance
            self.new_copied_instance.custom_skill.skill_slot = self.custom_skill.skill_slot # we affect the good skill slot to the copied skill

            self.echo_total_duration: int = 19_500
            self.echo_remaining_duration: float = self.echo_total_duration # we will expose it through UI
            self.last_arcane_echo_time: float = 0

    def __current_time_in_ms(self) -> float:
        return int(time.time() * 1000)
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        # arcane echo is a particular. we can't check it when it is replacing another skill.
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if custom_behavior_helpers.Resources.get_player_absolute_energy() < self.mana_required_to_cast: return False
        return True

    def _get_arcane_echo_state(self, current_state: BehaviorState) -> ArcaneEchoState:

        # if under ArcaneEcho effect, we are top priority to cast the skill we want to copy
        if Routines.Checks.Effects.HasBuff(GLOBAL_CACHE.Player.GetAgentID(), self.custom_skill.skill_id):
            return ArcaneEchoState.CAST_SKILL_TO_COPY

        # arcane echo + skill to copy are available, and we have enough resources
        if GLOBAL_CACHE.SkillBar.GetSkillData(self.custom_skill.skill_slot).event == 0: # arcane echo is available
            is_arcane_echo_ready = Routines.Checks.Skills.IsSkillIDReady(self.custom_skill.skill_id)
            is_skill_to_copy_ready = Routines.Checks.Skills.IsSkillIDReady(self.original_skill_to_copy.custom_skill.skill_id)
            has_enough_energy_to_cast_arcane_echo = custom_behavior_helpers.Resources.has_enough_resources(self.custom_skill)
            has_enough_energy_to_cast_skill_to_copy = custom_behavior_helpers.Resources.has_enough_resources(self.original_skill_to_copy.custom_skill)
            # todo sum both costs (complex if not energy...)
            is_skill_to_copy_pre_checks_valid = self.original_skill_to_copy.are_common_pre_checks_valid(current_state)

            if is_arcane_echo_ready and is_skill_to_copy_ready and has_enough_energy_to_cast_arcane_echo and has_enough_energy_to_cast_skill_to_copy and is_skill_to_copy_pre_checks_valid:
                return ArcaneEchoState.CAST_ARCANE_ECHO

        # copied skill available, and we have enough resources
        if GLOBAL_CACHE.SkillBar.GetSkillData(self.custom_skill.skill_slot).event == -1: # arcane echo is in copy mode
            is_copied_skill_ready = GLOBAL_CACHE.SkillBar.GetSkillData(self.new_copied_instance.custom_skill.skill_slot).get_recharge == 0
            is_copied_skill_cast_duration_short_enough = GLOBAL_CACHE.Skill.Data.GetActivation(self.new_copied_instance.custom_skill.skill_id) * 1000 + 200 < self.echo_remaining_duration
            has_enough_energy_to_cast_copied_skill = custom_behavior_helpers.Resources.has_enough_resources(self.new_copied_instance.custom_skill)

            if is_copied_skill_ready and is_copied_skill_cast_duration_short_enough and has_enough_energy_to_cast_copied_skill:
                return ArcaneEchoState.CAST_COPIED_SKILL

        return ArcaneEchoState.IDLE

    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        delay = (self.__current_time_in_ms() - self.last_arcane_echo_time)

        if delay > self.echo_total_duration:
            self.echo_remaining_duration = 0
        else:
            self.echo_remaining_duration = self.echo_total_duration - delay
            # we only allow auto attack refresh once per 500 ms

        echo_state = self._get_arcane_echo_state(current_state)

        match echo_state:
            case ArcaneEchoState.CAST_ARCANE_ECHO:
                return self.arcane_echo_score_definition.get_score()
            case ArcaneEchoState.CAST_SKILL_TO_COPY:
                return 95 #higher priority over everything, we are under echo effect. nothing else matters.
            case ArcaneEchoState.CAST_COPIED_SKILL:
                return self.new_copied_instance.evaluate(current_state, previously_attempted_skills)
            case ArcaneEchoState.IDLE:
                return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:

        echo_state = self._get_arcane_echo_state(state)

        match echo_state:
            case ArcaneEchoState.CAST_ARCANE_ECHO:  
                result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
                if result is BehaviorResult.ACTION_PERFORMED:
                    self.last_arcane_echo_time = self.__current_time_in_ms()
                return result
            case ArcaneEchoState.CAST_SKILL_TO_COPY:
                result = yield from self.original_skill_to_copy.execute(state)
                return result
            case ArcaneEchoState.CAST_COPIED_SKILL:
                result = yield from self.new_copied_instance.execute(state)
                return result
            case ArcaneEchoState.IDLE:
                return BehaviorResult.ACTION_SKIPPED

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"internal state : {self._get_arcane_echo_state(current_state)}")
        PyImGui.bullet_text(f"remaining duration : {self.echo_remaining_duration}")
