from typing import Any, Generator, override
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.enums import Profession, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.bonds.per_type.custom_buff_target import BuffConfigurationPerProfession
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class GreatDwarfWeaponUtility(CustomSkillUtilityBase):

    def __init__(self, 
        current_build: list[CustomSkill], 
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(30),
        mana_required_to_cast: int = 10,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
        ) -> None:

        super().__init__(
            skill=CustomSkill("Great_Dwarf_Weapon"), 
            in_game_build=current_build, 
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)
                
        self.score_definition: ScoreStaticDefinition = score_definition
        self.buff_configuration: BuffConfigurationPerProfession = BuffConfigurationPerProfession(self.custom_skill, BuffConfigurationPerProfession.BUFF_CONFIGURATION_MARTIAL)


    def _get_target(self) -> int | None:
        
        # Check if we have a valid target
        target = custom_behavior_helpers.Targets.get_first_or_default_from_allies_ordered_by_priority(
                within_range=Range.Spellcast,
                condition=lambda agent_id: 
                    agent_id != GLOBAL_CACHE.Player.GetAgentID() and 
                    self.buff_configuration.get_agent_id_predicate()(agent_id),
                sort_key=(TargetingOrder.DISTANCE_DESC, TargetingOrder.CASTER_THEN_MELEE),
                range_to_count_enemies=None,
                range_to_count_allies=None)
    
        return target

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        target = self._get_target()
        if target is None: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        target = self._get_target()
        if target is None: return BehaviorResult.ACTION_SKIPPED
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target)
        return result 

    @override
    def get_buff_configuration(self) -> BuffConfigurationPerProfession | None:
        return self.buff_configuration