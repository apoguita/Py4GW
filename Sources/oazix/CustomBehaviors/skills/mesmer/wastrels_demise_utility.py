from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.sortable_agent_data import SortableAgentData
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class WastrelsDemiseUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        mana_required_to_cast: int = 0,
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 3 else 40 if enemy_qte <= 2 else 0),
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Wastrels_Demise"),
            in_game_build=current_build,
            mana_required_to_cast=mana_required_to_cast,
            score_definition=score_definition,
            allowed_states=allowed_states)

        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    def _get_lock_key(self, agent_id: int) -> str:
        return f"Wastrels_Demise_{agent_id}"

    def _get_first_unlocked_target(self, targets: list[SortableAgentData]) -> SortableAgentData | None:
        lock_manager = CustomBehaviorParty().get_shared_lock_manager()
        for target in targets:
            if not lock_manager.is_lock_taken(self._get_lock_key(target.agent_id)):
                return target
        return None

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:

        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
                    within_range=Range.Spellcast,
                    condition=lambda agent_id: not Agent.IsHexed(agent_id) and not Agent.IsSpirit(agent_id),
                    sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_DESC),
                    range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        targets = self._get_targets()
        if len(targets) == 0: return None
        target = self._get_first_unlocked_target(targets)
        if target is None: return None
        return self.score_definition.get_score(target.enemy_quantity_within_range)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        lock_manager = CustomBehaviorParty().get_shared_lock_manager()

        enemies = self._get_targets()
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = self._get_first_unlocked_target(enemies)
        if target is None: return BehaviorResult.ACTION_SKIPPED

        lock_key = self._get_lock_key(target.agent_id)
        if not lock_manager.try_aquire_lock(lock_key):
            return BehaviorResult.ACTION_SKIPPED

        try:
            result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        finally:
            lock_manager.release_lock(lock_key)
        return result