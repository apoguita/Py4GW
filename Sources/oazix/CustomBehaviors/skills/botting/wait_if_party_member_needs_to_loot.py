from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Range
from Py4GWCoreLib.Py4GWcorelib import LootConfig, ThrottledTimer
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
import time
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class WaitIfPartyMemberNeedsToLootUtility(CustomSkillUtilityBase):
    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("wait_if_party_member_needs_to_loot"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.LOOT.value - 0.0001), # this cannot pass before my own loot
            allowed_states= [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.BOTTING,
            execution_strategy= UtilitySkillExecutionStrategy.STOP_EXECUTION_ONCE_SCORE_NOT_HIGHEST)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.LOOT.value - 0.0001)
        self._timeout = ThrottledTimer(30_000)
        self._cooldown_after_timeout = ThrottledTimer(25_000)
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if not CustomBehaviorParty().get_party_is_looting_enabled(): return False
        # maybe the other player is not able to reach the loot, so we must have a cooldown
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        
        # Check if we're in cooldown period after timeout
        if not self._cooldown_after_timeout.IsExpired():
            return None
        
        # Reset timeout if cooldown has expired
        if self._cooldown_after_timeout.IsExpired():
            self._timeout.Reset()
            self._cooldown_after_timeout.Reset()

        # we choose a bigger range on purpose, allies are not exactly at our position.
        loot_array = LootConfig().GetfilteredLootArray(Range.Spellcast.value, multibox_loot=True, allow_unasigned_loot=True)
        if len(loot_array) > 1:
            return self.score_definition.get_score()
        
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        # Reset timeout at the start of execution
        self._timeout.Reset()
        
        # Wait for party members to loot, with timeout
        while not self._timeout.IsExpired():
            # Check if there's still loot available for party members
            loot_array = LootConfig().GetfilteredLootArray(Range.Spellcast.value, multibox_loot=True, allow_unasigned_loot=True)
            if len(loot_array) <= 1:  # No more loot for party members
                break
            yield from custom_behavior_helpers.Helpers.wait_for(300)

        # Start cooldown period after timeout
        self._cooldown_after_timeout.Reset()
        
        return BehaviorResult.ACTION_PERFORMED