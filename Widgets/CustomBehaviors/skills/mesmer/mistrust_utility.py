from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class MistrustUtility(CustomSkillUtilityBase):
    def __init__(self, 
        current_build: list[CustomSkill], 
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 3 else 40 if enemy_qte <= 2 else 0),
        mana_required_to_cast: int = 18,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:

        super().__init__(
            skill=CustomSkill("Mistrust"), 
            in_game_build=current_build, 
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)
                
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    def _get_lock_key(self, agent_id: int) -> str:
        return f"Mistrust_{agent_id}"

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
                    within_range=Range.Spellcast,
                    condition=lambda agent_id: not GLOBAL_CACHE.Agent.IsHexed(agent_id),
                    sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_DESC),
                    range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        
        targets = self._get_targets()
        if len(targets) == 0: return None
        lock_key = self._get_lock_key(targets[0].agent_id)
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key): return None #someone is already doing that

        return self.score_definition.get_score(targets[0].enemy_quantity_within_range)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        enemies = self._get_targets()
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