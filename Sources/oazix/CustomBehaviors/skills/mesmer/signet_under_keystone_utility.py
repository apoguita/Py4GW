from typing import Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Player
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class SignetUnderKeystoneUtility(CustomSkillUtilityBase):

    def __init__(self,
                event_bus: EventBus,
                skill: CustomSkill,

                current_build: list[CustomSkill],
                score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 2 else 40 if enemy_qte <= 2 else 0),

                condition: Callable[[int], bool] = lambda agent_id: True,
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition)
        
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition
        self.condition: Callable[[int], bool] = condition
        self.keystone_signet_skill: CustomSkill = CustomSkill("Keystone_Signet")
        
        # all signet must be forced cast before keystone effect ends

    def _get_lock_key(self, agent_id: int) -> str:
        return f"Interrupt_{agent_id}"

    def _get_targets(self, condition: Callable[[int], bool]) -> list[custom_behavior_helpers.SortableAgentData]:
        return custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
                within_range=Range.Spellcast,
                condition=lambda agent_id: condition(agent_id),
                sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.DISTANCE_ASC),
                range_to_count_enemies=Range.Adjacent.value) # keystone signet is doing dmg to adjacents
    
    def should_spam_all_signets(self) -> bool:

        has_keystone_signet_buff = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.keystone_signet_skill.skill_id)
        if not has_keystone_signet_buff: return False

        keystone_signet_buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(Player.GetAgentID(), self.keystone_signet_skill.skill_id)
        if keystone_signet_buff_time_remaining <= 4000: return True
        
        keystone_signet_recharge_time_remaining = custom_behavior_helpers.Resources.get_skill_recharge_time_remaining_in_milliseconds(self.keystone_signet_skill)
        if keystone_signet_recharge_time_remaining <= 4000: return True
        
        return False
        

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        has_keystone_signet_buff = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.keystone_signet_skill.skill_id)
        if not has_keystone_signet_buff: return None

        if self.should_spam_all_signets(): return self.score_definition.get_score(80)

        targets: list[custom_behavior_helpers.SortableAgentData] = self._get_targets(self.condition)
        if len(targets) == 0: return None

        lock_key = self._get_lock_key(targets[0].agent_id)
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key): return None #someone is already doing that

        return self.score_definition.get_score(targets[0].enemy_quantity_within_range + 1) # +1 is to count the current ennemy
        
    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:

        if self.should_spam_all_signets():
            target = custom_behavior_helpers.Targets.get_first_or_default_from_enemy_ordered_by_priority(
                within_range=Range.Spellcast,
                condition=lambda agent_id: True,
                sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.DISTANCE_ASC),
                range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id)
            )
            if target is None: return BehaviorResult.ACTION_SKIPPED
            result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target)
            return result
        
        enemies = self._get_targets(self.condition)
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = enemies[0]

        lock_key = self._get_lock_key(target.agent_id)
        if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key) == False: 
            return BehaviorResult.ACTION_SKIPPED 

        try:
            result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        finally:
            CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
        return result
