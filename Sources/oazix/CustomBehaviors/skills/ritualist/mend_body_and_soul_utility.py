from typing import Any, Generator, override

from Py4GWCoreLib import Range, Agent
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.lock_key_helper import LockKeyHelper
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.plugins.targeting_modifiers.buff_configurator import BuffConfigurator

class MendBodyAndSoulUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerHealthGravityDefinition = ScorePerHealthGravityDefinition(7),
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Mend_Body_and_Soul"),
            in_game_build=current_build,
            score_definition=score_definition,
            allowed_states=allowed_states)

        self.score_definition: ScorePerHealthGravityDefinition = score_definition
        self.add_plugin_targetting_modifier(lambda x: BuffConfigurator(event_bus, self.custom_skill, buff_configuration_per_profession= BuffConfigurationPerProfession.BUFF_CONFIGURATION_ALL))
    
    def _get_lock_key(self, agent_id: int) -> str:
        return LockKeyHelper.condition_removal(agent_id)
    
    def _get_target(self, can_dismiss_condition: bool = False) -> custom_behavior_helpers.SortableAgentData | None:

        targets: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,
            condition=lambda agent_id: self.get_plugin_targeting_modifiers_filtering_predicate()(agent_id) and Agent.GetHealth(agent_id) < 0.75,
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC))
            
        targets_conditionned: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,
            condition=lambda agent_id: self.get_plugin_targeting_modifiers_filtering_predicate()(agent_id) and Agent.IsConditioned(agent_id),
            sort_key=(TargetingOrder.CONDITION_PRIORITY_LEVEL_DESC, TargetingOrder.MELEE_THEN_CASTER, TargetingOrder.HP_ASC))

        if len(targets) > 0: return targets[0]
        if can_dismiss_condition and len(targets_conditionned) > 0: return targets_conditionned[0]
        return None

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        is_spirit_exist:bool = custom_behavior_helpers.Resources.is_spirit_exist(within_range=Range.Earshot)
        target = self._get_target(can_dismiss_condition=is_spirit_exist)
        if target is None: return None
        
        if target.hp < 0.40: return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY)
        if target.hp < 0.75: return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED)
        if Agent.IsConditioned(target.agent_id): 
            lock_key = self._get_lock_key(target.agent_id)
            if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key): return None
            return self.score_definition.get_score(HealingScore.MEMBER_CONDITIONED)

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        target = self._get_target()
        if target is None: return BehaviorResult.ACTION_SKIPPED

        # skill used for healing. we dont care about the condition - it's a bonus
        if target.hp < 0.75:
            result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
            return result

        # skill used for conditions
        lock_key = self._get_lock_key(target.agent_id)
        if Agent.IsConditioned(target.agent_id):
            if not CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key):
                yield
                return BehaviorResult.ACTION_SKIPPED
            try:
                result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
            finally:
                CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
            return result
        
        return BehaviorResult.ACTION_SKIPPED
