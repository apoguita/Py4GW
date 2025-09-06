import math
from tkinter.constants import N
from typing import Any, Generator, override

from HeroAI.cache_data import CacheData
from HeroAI.types import PlayerStruct
from Py4GWCoreLib import GLOBAL_CACHE, Party, Routines, Range
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
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class LootUtility(CustomSkillUtilityBase):

    def __init__(
            self, 
            current_build: list[CustomSkill], 
            allowed_states: list[BehaviorState] = [BehaviorState.FAR_FROM_AGGRO]
        ) -> None:
        
        super().__init__(
            skill=CustomSkill("loot"), 
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.LOOT.value), 
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.LOOTING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.LOOT.value)
        self.throttle_timer = ThrottledTimer(1_000)
        self.__loot_cooldown_timer = ThrottledTimer(60_000)
        self.__loot_cooldown_active = False
        self.__loot_timeout_ms = 15_000
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        
        if not self.throttle_timer.IsExpired():
            return None

        # Respect cooldown to avoid getting stuck in repeated loot attempts
        if self.__loot_cooldown_active:
            if self.__loot_cooldown_timer.IsExpired():
                self.__loot_cooldown_active = False
            else:
                return None

        if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1: 
            return None

        if custom_behavior_helpers.Targets.is_party_leader_in_aggro(): 
            return None

        if custom_behavior_helpers.Targets.is_party_in_aggro(): 
            return None

        if self.IsLootingRoutineActive():
            return None

        loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)
        if len(loot_array) == 0: return None

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        self.throttle_timer.Reset()

        loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)
        if len(loot_array) == 0: return BehaviorResult.ACTION_SKIPPED

        account_email = GLOBAL_CACHE.Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        if self_account is not None:
            GLOBAL_CACHE.ShMem.SendMessage(
                self_account.AccountEmail,
                self_account.AccountEmail,
                SharedCommandType.PickUpLoot,
                (0, 0, 0, 0),
            )
        else:
            return BehaviorResult.ACTION_SKIPPED

        # Wait until looting ends or timeout elapses
        start_time = time.time()
        while self.IsLootingRoutineActive():
            if (time.time() - start_time) * 1000 >= self.__loot_timeout_ms:
                # Timeout reached: trigger cooldown to avoid being stuck
                self.__loot_cooldown_active = True
                self.__loot_cooldown_timer.Reset()
                return BehaviorResult.ACTION_SKIPPED
            yield from custom_behavior_helpers.Helpers.wait_for(200)

        # i don't know why but that stuff is not working
        # result:bool = yield from Routines.Yield.Items.LootItems(loot_array, log=True, progress_callback=lambda progress: print(f"LootItems: progress: {progress}"))
        # if result: return BehaviorResult.ACTION_PERFORMED
        return BehaviorResult.ACTION_PERFORMED

    def IsLootingRoutineActive(self):
        account_email = GLOBAL_CACHE.Player.GetAccountEmail()
        index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)

        if index == -1 or message is None:
            return False

        if message.Command != SharedCommandType.PickUpLoot:
            return False
        return True