from typing import Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class WanderingEyeUtility(CustomSkillUtilityBase):
    """
    Wandering Eye utility that targets melee enemies in clusters.
    Combines melee order + cluster targeting.
    """
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 74 if enemy_qte >= 2 else 39 if enemy_qte <= 2 else 0),
        mana_required_to_cast: int = 10,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Wandering_Eye"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
                
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    def _get_lock_key(self, agent_id: int) -> str:
        return f"WanderingEye_{agent_id}"

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        """Get melee enemies ordered by cluster size."""
        return custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
                    within_range=Range.Spellcast,
                    condition=lambda agent_id: GLOBAL_CACHE.Agent.IsMelee(agent_id),
                    sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC,),
                    range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        
        targets = self._get_targets()
        if len(targets) == 0: return None
        lock_key = self._get_lock_key(targets[0].agent_id)
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key): return None

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

