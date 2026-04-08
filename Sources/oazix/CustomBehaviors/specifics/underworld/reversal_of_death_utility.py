from typing import Any, Generator, override

from Py4GWCoreLib import Agent, Player, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.specifics.underworld.dhuum_helpers import (
    count_spirit_form_accounts,
    get_morale_by_agent_id,
    get_spirit_form_agent_ids,
    is_uw_chest_present,
    resolve_first_known_skill,
)


# Minimum number of same-party accounts with Spirit Form before this skill fires.
_SPIRIT_FORM_MIN_COUNT = 1


class ReversalOfDeathUtility(CustomSkillUtilityBase):
    """Cast Reversal of Death on the ally with the highest death penalty.

    Death penalty is derived from shared-memory morale data
    (morale < 100  ⇒  death_penalty = 100 − morale).

    Activation is gated on the Spirit Form phase:
      - Requires at least _SPIRIT_FORM_MIN_COUNT accounts to have Spirit Form
        before any cast attempt is made.
      - When ≤2 accounts have Spirit Form, only those soul-split allies are
        targeted (they are accumulating the rez-death penalty).
      - Once >2 accounts carry Spirit Form, any ally with a death penalty is
        a valid target.

    Score: 94. Suppressed when the Underworld Chest is present.
    """

    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill]):
        super().__init__(
            event_bus=event_bus,
            skill=resolve_first_known_skill("Reversal_of_Death", "Reversal of Death"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(94),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if is_uw_chest_present():
            return False
        if count_spirit_form_accounts() < _SPIRIT_FORM_MIN_COUNT:
            return False
        return super().are_common_pre_checks_valid(current_state)

    def _get_best_target(self) -> custom_behavior_helpers.SortableAgentData | None:
        """Return the in-range ally with the largest death penalty, or None."""
        spirit_form_count = count_spirit_form_accounts()
        spirit_form_ids   = get_spirit_form_agent_ids()
        restrict_to_spirit_form = spirit_form_count <= 2
        my_id = int(Player.GetAgentID())

        def _condition(agent_id: int) -> bool:
            if not Agent.IsValid(agent_id):
                return False
            if int(agent_id) == my_id:
                return False
            if restrict_to_spirit_form and int(agent_id) not in spirit_form_ids:
                return False
            return True

        allies = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,
            condition=_condition,
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
            is_alive=True,
        )
        if not allies:
            return None

        morale_map = get_morale_by_agent_id()
        if not morale_map:
            return None

        best_target = None
        best_penalty = 0
        for ally in allies:
            morale  = int(morale_map.get(int(ally.agent_id), 100))
            penalty = max(0, 100 - morale)
            if penalty <= 0:
                continue
            if best_target is None or penalty > best_penalty:
                best_target  = ally
                best_penalty = penalty
        return best_target

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        return 94.0 if self._get_best_target() is not None else None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        target = self._get_best_target()
        if target is None:
            if False:
                yield None
            return BehaviorResult.ACTION_SKIPPED
        return (yield from custom_behavior_helpers.Actions.cast_skill_to_target(
            self.custom_skill,
            target_agent_id=target.agent_id,
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
