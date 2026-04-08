from typing import Any, Generator, override

from Py4GWCoreLib import Range, Agent
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.lock_key_helper import LockKeyHelper
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class PeaceAndHarmonyUtility(CustomSkillUtilityBase):
    """
    Peace and Harmony utility that heals and removes both a hex and a condition from an ally.
    Targets allies that have hexes or conditions, ordered by lowest health first.
    """
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(50),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Peace_and_Harmony"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
                
        self.score_definition: ScoreStaticDefinition = score_definition

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        """Get allies that are hexed or conditioned, ordered by lowest health first."""
        targets: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,
            condition=lambda agent_id: Agent.IsHexed(agent_id) or Agent.IsConditioned(agent_id),
            sort_key=(TargetingOrder.HEX_PRIORITY_LEVEL_DESC, TargetingOrder.CONDITION_PRIORITY_LEVEL_DESC, ))
        return targets

    def _get_lock_keys(self, agent_id: int) -> list[str]:
        return [LockKeyHelper.hex_removal(agent_id), 
                LockKeyHelper.condition_removal(agent_id)]

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        targets = self._get_targets()
        if len(targets) == 0: return None

        for lock_key in self._get_lock_keys(targets[0].agent_id):
            if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key): return None

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        targets = self._get_targets()
        if len(targets) == 0: return BehaviorResult.ACTION_SKIPPED
        target = targets[0]

        lock_keys = self._get_lock_keys(target.agent_id)
        for lock_key in lock_keys:
            if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key) == False:
                yield
                for lock_key in lock_keys:
                    CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
                return BehaviorResult.ACTION_SKIPPED

        try:
            result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        finally:
            for lock_key in lock_keys:
                CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
        return result


