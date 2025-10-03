from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.enums import SpiritModelID
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState

from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class ProtectiveSpiritUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        skill: CustomSkill,
        current_build: list[CustomSkill],
        owned_spirit_model_id: SpiritModelID,
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(60),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)
                
        self.score_definition: ScoreStaticDefinition = score_definition
        self.soul_twisting_skill = CustomSkill("Soul_Twisting")
        self.owned_spirit_model_id: SpiritModelID = owned_spirit_model_id

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        # Check if we have Soul Twisting active
        has_soul_twisting = Routines.Checks.Effects.HasBuff(GLOBAL_CACHE.Player.GetAgentID(), self.soul_twisting_skill.skill_id)
        if not has_soul_twisting:
            return None  # Don't cast without Soul Twisting

        buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(GLOBAL_CACHE.Player.GetAgentID(), self.soul_twisting_skill.skill_id)

        if buff_time_remaining <= 1200:  # Don't cast if Soul Twisting is about to expire
            return None

        if buff_time_remaining <= 5000:  # if less than 5 seconds, let's try to exhaust charges by force casting spirits

            if custom_behavior_helpers.Resources.is_spirit_exist(
                    within_range=Range.Spellcast,
                    associated_to_skill=self.custom_skill,
                    condition=lambda agent_id: GLOBAL_CACHE.Agent.GetHealth(agent_id) < 0.80): # we only refresh low life spirits
                return self.score_definition.get_score()

        # Check if we need to cast the spirit
        if not custom_behavior_helpers.Resources.is_spirit_exist(
                within_range=Range.Spellcast,
                associated_to_skill=self.custom_skill,
                condition=lambda agent_id: GLOBAL_CACHE.Agent.GetHealth(agent_id) > 0.3):
            return self.score_definition.get_score()  # High priority if spirit doesn't exist or is low health
            
        return None  # No need to cast if spirit exists and is healthy

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        if result == BehaviorResult.ACTION_PERFORMED:
            yield from self.event_bus.publish(EventType.SPIRIT_CREATED, state, data=self.owned_spirit_model_id)
        
        return result