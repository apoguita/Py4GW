from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.sortable_agent_data import SortableAgentData
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class OverloadUtility(CustomSkillUtilityBase):

    def __init__(self,
                event_bus: EventBus,
                current_build: list[CustomSkill],
                interrupt_score_definition: ScoreStaticDefinition = ScoreStaticDefinition(88),
                hex_spread_score_definition: ScoreStaticDefinition = ScoreStaticDefinition(55),
                mana_required_to_cast: int = 5,
                allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Overload"),
            in_game_build=current_build,
            score_definition=interrupt_score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.interrupt_score_definition: ScoreStaticDefinition = interrupt_score_definition
        self.hex_spread_score_definition: ScoreStaticDefinition = hex_spread_score_definition

    def _get_lock_key(self, agent_id: int) -> str:
        return f"Overload_{agent_id}"

    def _get_first_unlocked_target(self, targets: list[SortableAgentData]) -> SortableAgentData | None:
        lock_manager = CustomBehaviorParty().get_shared_lock_manager()
        for target in targets:
            if not lock_manager.is_lock_taken(self._get_lock_key(target.agent_id)):
                return target
        return None

    def detect_casting_enemies(self) -> list[SortableAgentData]:
        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            condition=lambda agent_id:
                Agent.IsCasting(agent_id) and
                GLOBAL_CACHE.Skill.Data.GetActivation(Agent.GetCastingSkillID(agent_id)) >= 0.250,
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.CASTER_THEN_MELEE),
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id)
        )
        return targets

    def get_hex_spread_targets(self) -> list[SortableAgentData]:
        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            condition=lambda agent_id: not Agent.IsHexed(agent_id),
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_DESC),
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id)
        )
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        casting_target = self._get_first_unlocked_target(self.detect_casting_enemies())
        if casting_target is not None:
            return self.interrupt_score_definition.get_score()

        hex_target = self._get_first_unlocked_target(self.get_hex_spread_targets())
        if hex_target is not None:
            return self.hex_spread_score_definition.get_score()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        lock_manager = CustomBehaviorParty().get_shared_lock_manager()

        casting_target = self._get_first_unlocked_target(self.detect_casting_enemies())
        if casting_target is not None:
            lock_key = self._get_lock_key(casting_target.agent_id)
            if not lock_manager.try_aquire_lock(lock_key):
                return BehaviorResult.ACTION_SKIPPED
            try:
                result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=casting_target.agent_id)
            finally:
                lock_manager.release_lock(lock_key)
            return result

        hex_target = self._get_first_unlocked_target(self.get_hex_spread_targets())
        if hex_target is not None:
            lock_key = self._get_lock_key(hex_target.agent_id)
            if not lock_manager.try_aquire_lock(lock_key):
                return BehaviorResult.ACTION_SKIPPED
            try:
                result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=hex_target.agent_id)
            finally:
                lock_manager.release_lock(lock_key)
            return result

        return BehaviorResult.ACTION_SKIPPED
