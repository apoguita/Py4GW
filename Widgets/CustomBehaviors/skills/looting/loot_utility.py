import math
from tkinter.constants import N
from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, Party, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, LootConfig, ThrottledTimer, Utils
from Py4GWCoreLib.enums import SharedCommandType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
import time
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class LootUtility(CustomSkillUtilityBase):

    def __init__(
            self, 
            current_build: list[CustomSkill], 
            allowed_states: list[BehaviorState] = [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO] 
            # CLOSE_TO_AGGRO is required to avoid infinite-loop, if when approching an item to loot, player is aggroing.
            # otherwise once approching enemies, player will infinitely loop between loot & follow_party_leader
        ) -> None:
        
        super().__init__(
            skill=CustomSkill("loot"), 
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.LOOT.value), 
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.LOOTING,
            execution_strategy=UtilitySkillExecutionStrategy.STOP_EXECUTION_ONCE_SCORE_NOT_HIGHEST)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.LOOT.value)
        self.throttle_timer = ThrottledTimer(1_000)
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1: 
            return None

        if custom_behavior_helpers.Targets.is_party_leader_in_aggro(): 
            return None

        if custom_behavior_helpers.Targets.is_party_in_aggro(): 
            return None

        loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)
        # print(f"Loot array: {loot_array}")
        if len(loot_array) == 0: return None

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        if not self.throttle_timer.IsExpired():
            yield
            return BehaviorResult.ACTION_SKIPPED
        
        loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)
        if len(loot_array) == 0: 
            yield
            return BehaviorResult.ACTION_SKIPPED

        self.throttle_timer.Reset()

        while True:

            if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1: break
            loot_array:list[int] = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)
            if len(loot_array) == 0: break
            item_id = loot_array.pop(0)
            if item_id is None or item_id == 0: 
                yield from custom_behavior_helpers.Helpers.wait_for(100)
                continue
            if not GLOBAL_CACHE.Agent.IsValid(item_id): 
                yield from custom_behavior_helpers.Helpers.wait_for(100)
                continue
            
            # 1) try to loot
            pos = GLOBAL_CACHE.Agent.GetXY(item_id)
            follow_success = yield from Routines.Yield.Movement.FollowPath([pos], timeout=6_000)
            if not follow_success:
                print("Failed to follow path to loot item, halting.")
                real_item_id = GLOBAL_CACHE.Agent.GetItemAgent(item_id).item_id
                LootConfig().AddItemIDToBlacklist(real_item_id)
                yield from custom_behavior_helpers.Helpers.wait_for(100)
                continue
            
            GLOBAL_CACHE.Player.Interact(item_id, call_target=False)
            yield from custom_behavior_helpers.Helpers.wait_for(100)

            # 2) check if loot has been looted
            pickup_timer = ThrottledTimer(3_000)
            while not pickup_timer.IsExpired():
                loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)
                if item_id not in loot_array or len(loot_array) == 0:
                    break
                yield from custom_behavior_helpers.Helpers.wait_for(100)
            
            # 3) Check if we timed out and add to blacklist if so
            if pickup_timer.IsExpired():
                real_item_id = GLOBAL_CACHE.Agent.GetItemAgent(item_id).item_id
                LootConfig().AddItemIDToBlacklist(real_item_id)

        yield from custom_behavior_helpers.Helpers.wait_for(100)
        return BehaviorResult.ACTION_PERFORMED