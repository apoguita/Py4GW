from tkinter.constants import N
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Agent, AgentArray, Routines, Range, Player
from Py4GWCoreLib.enums import Profession
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Widgets.CustomBehaviors.primitives.skills.bonds.custom_buff_target import CustomBuffTarget
from Widgets.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Widgets.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_email import BuffConfigurationPerPlayerEmail
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class BloodOfTheMasterUtility(CustomSkillUtilityBase):
    def __init__(self, 
        event_bus:EventBus,
        current_build: list[CustomSkill], 
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(30),
        sacrifice_life_limit_percent: float = 0.55,
        sacrifice_life_limit_absolute: int = 175,
        required_target_mana_lower_than_percent: float = 0.40,
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Blood_of_the_Master"), 
            in_game_build=current_build, 
            score_definition=score_definition, 
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition
        self.sacrifice_life_limit_percent: float = sacrifice_life_limit_percent
        self.sacrifice_life_limit_absolute: int = sacrifice_life_limit_absolute
        self.required_target_mana_lower_than_percent: float = required_target_mana_lower_than_percent

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        minion_array = AgentArray.GetMinionArray()
        minion_array = AgentArray.Filter.ByDistance(minion_array, Player.GetXY(), Range.Spellcast.value)
        minion_array = AgentArray.Filter.ByCondition(minion_array, lambda agent_id: Agent.IsAlive(agent_id))
        minion_array = AgentArray.Filter.ByCondition(minion_array, lambda agent_id: Agent.GetHealth(agent_id) < 0.50)

        minion_count = len(minion_array)
        if minion_count < 2: return None
        
        if not custom_behavior_helpers.Resources.player_can_sacrifice_health(minion_count * 2, self.sacrifice_life_limit_percent, self.sacrifice_life_limit_absolute):
            return None
        
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        return