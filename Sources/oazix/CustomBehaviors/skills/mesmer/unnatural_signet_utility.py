from typing import List, Any, Generator, Callable, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class UnnaturalSignetUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        should_fallback_if_no_target_found: bool = False,
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 3 else 40 if enemy_qte <= 2 else 0),
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Unnatural_Signet"),
            in_game_build=current_build,
            score_definition=score_definition,
            allowed_states=allowed_states)

        self.score_definition: ScorePerAgentQuantityDefinition = score_definition
        self.should_fallback_if_no_target_found = bool(int(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "should_fallback_if_no_target_found", str(int(should_fallback_if_no_target_found)))))

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        
        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
                    within_range=Range.Spellcast,
                    condition=lambda agent_id: Agent.IsHexed(agent_id) or Agent.IsEnchanted(agent_id),
                    sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_DESC),
                    range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))
        if len(targets) == 0:
            targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
                    within_range=Range.Spellcast,
                    sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_DESC),
                    range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        targets = self._get_targets()
        if len(targets) == 0: return None
        return self.score_definition.get_score(targets[0].enemy_quantity_within_range)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        enemies = self._get_targets()
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = enemies[0]
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        return result

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"should_fallback_if_no_target_found :")
        self.should_fallback_if_no_target_found = PyImGui.checkbox("##should_fallback_if_no_target_found", self.should_fallback_if_no_target_found)

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "should_fallback_if_no_target_found", str(int(self.should_fallback_if_no_target_found)))
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "should_fallback_if_no_target_found", str(int(self.should_fallback_if_no_target_found)))
        print("configuration saved as global")

    @override
    def delete_persisted_configuration(self):
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "should_fallback_if_no_target_found")
        print("configuration deleted")