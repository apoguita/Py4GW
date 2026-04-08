from typing import Any, Generator, override

from Py4GWCoreLib import Agent, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.specifics.underworld.dhuum_helpers import is_uw_chest_present, resolve_first_known_skill


class SpiritualHealingUtility(CustomSkillUtilityBase):
    """Heal the ally with the lowest HP that is currently below 70% health.

    Score: 90. Suppressed when the Underworld Chest is present (fight over).
    Targets are sorted by ascending HP first, then by ascending distance.
    """

    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill]):
        super().__init__(
            event_bus=event_bus,
            skill=resolve_first_known_skill("Spiritual_Healing", "Spiritual Healing"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(90),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if is_uw_chest_present():
            return False
        return super().are_common_pre_checks_valid(current_state)

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        return custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,
            condition=lambda agent_id: Agent.IsValid(agent_id) and Agent.GetHealth(agent_id) < 0.70,
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        return 90.0 if self._get_targets() else None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        targets = self._get_targets()
        if not targets:
            if False:
                yield None
            return BehaviorResult.ACTION_SKIPPED
        return (yield from custom_behavior_helpers.Actions.cast_skill_to_target(
            self.custom_skill,
            target_agent_id=targets[0].agent_id,
        ))

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        pass

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return None

    @override
    def has_persistence(self) -> bool:
        return False

    @override
    def delete_persisted_configuration(self):
        pass

    @override
    def persist_configuration_as_global(self):
        pass

    @override
    def persist_configuration_for_account(self):
        pass
