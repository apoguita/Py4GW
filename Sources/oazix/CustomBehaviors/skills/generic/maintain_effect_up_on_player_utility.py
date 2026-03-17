from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Player
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class MaintainEffectUpOnPlayerUtility(CustomSkillUtilityBase):
    """
    Utility that maintains a specific effect/buff on the player character.
    
    This is similar to KeepSelfEffectUpUtility but uses a separate skill name
    for configuration purposes while maintaining a different effect.
    
    Example: Use skill "Maintain_Effect_Up_On_Player_1" to maintain "Spirit_Bond" on player.
    """

    def __init__(
        self,
        event_bus: EventBus,
        skill: CustomSkill,
        skill_to_maintain: CustomSkill,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition,
        mana_required_to_cast: int = 0,
        renew_before_expiration_in_milliseconds: int = 500,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition
        self.skill_to_maintain: CustomSkill = skill_to_maintain
        self.renew_before_expiration_in_milliseconds: int = renew_before_expiration_in_milliseconds

        self.enabled: bool = True
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if custom_behavior_helpers.Resources.get_player_absolute_energy() < self.mana_required_to_cast: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        
        if not self.enabled: return None
        if self.skill_to_maintain.skill_slot == 0: return None # Check if the skill to maintain is in the build
        if not Routines.Checks.Skills.IsSkillSlotReady(self.skill_to_maintain.skill_slot): return None
        if not custom_behavior_helpers.Resources.has_enough_resources(self.skill_to_maintain): return None
        
        player_agent = Player.GetAgentID()
        
        # Check if player has the buff
        has_buff = Routines.Checks.Effects.HasBuff(player_agent, self.skill_to_maintain.skill_id)
        if not has_buff:
            return self.score_definition.get_score()
        
        # Check if buff is about to expire
        buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent, self.skill_to_maintain.skill_id)
        if buff_time_remaining <= self.renew_before_expiration_in_milliseconds:
            return self.score_definition.get_score()
        
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.skill_to_maintain, target_agent_id=Player.GetAgentID())
        return result

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        # self.enabled = PyImGui.checkbox("is_enabled##is_enabled", self.enabled)

        PyImGui.text(f"Maintaining: {self.skill_to_maintain.skill_name}")
        self.renew_before_expiration_in_milliseconds = PyImGui.input_int("renew_before_expiration_ms##renew_before_expiration_ms", 
            self.renew_before_expiration_in_milliseconds)