import math
from tkinter.constants import N
from typing import Any, Generator, override

from HeroAI.cache_data import CacheData
from HeroAI.types import PlayerStruct
from Py4GWCoreLib import GLOBAL_CACHE, Inventory, Party, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, LootConfig, ThrottledTimer, Utils
from Py4GWCoreLib.routines_src.Yield import Yield
from Widgets.CustomBehaviors.primitives.bus.event_bus import EVENT_BUS
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
import time
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class OpenNearChestUtility(CustomSkillUtilityBase):

    def __init__(
            self, 
            current_build: list[CustomSkill], 
            allowed_states: list[BehaviorState] = [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:
        
        super().__init__(
            skill=CustomSkill("open_near_chest_utility"), 
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.LOOT.value + 0.001), 
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.CHESTING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.LOOT.value)
        self.throttle_timer = ThrottledTimer(1000)
        self.opened_chest_agent_ids: set[int] = set()
        EVENT_BUS.subscribe(EventType.MAP_CHANGED, self.map_changed)

    def map_changed(self, message: EventMessage):
        self.opened_chest_agent_ids = set()
        self.throttle_timer.Reset()
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if not self.throttle_timer.IsExpired(): return None 
        if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1: return None #"No free slots in inventory, halting."
        if GLOBAL_CACHE.Inventory.GetModelCount(22751) < 1: return None #"No lockpicks in inventory, halting."
        chest_agent_id = Routines.Agents.GetNearestChest(700)
        if chest_agent_id in self.opened_chest_agent_ids: return None
        if chest_agent_id is None or chest_agent_id == 0: return None

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        chest_agent_id = Routines.Agents.GetNearestChest(700)
        if chest_agent_id is None or chest_agent_id == 0: 
            yield
            self.throttle_timer.Reset()
            return BehaviorResult.ACTION_SKIPPED

        chest_x, chest_y = GLOBAL_CACHE.Agent.GetXY(chest_agent_id)
        lock_key = f"open_near_chest_utility_{chest_agent_id}"

        result = yield from Routines.Yield.Movement.FollowPath(
            path_points=[(chest_x, chest_y)],
            timeout=10_000)

        if result == False:
            yield
            self.throttle_timer.Reset()
            return BehaviorResult.ACTION_SKIPPED

        if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key) == False:
            yield
            self.throttle_timer.Reset()
            return BehaviorResult.ACTION_SKIPPED

        ActionQueueManager().ResetAllQueues()
        yield from Yield.Player.InteractAgent(chest_agent_id)
        yield from Yield.wait(1000)
        GLOBAL_CACHE.Player.SendDialog(2)
        yield from Yield.wait(1000)
        self.throttle_timer.Reset()
        print("CHEST_OPENED")
        self.opened_chest_agent_ids.add(chest_agent_id)
        EVENT_BUS.publish(EventType.CHEST_OPENED, chest_agent_id)

        CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)

        return BehaviorResult.ACTION_PERFORMED