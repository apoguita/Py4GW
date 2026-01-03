import math
from tkinter.constants import N
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, Agent, Party, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, LootConfig, ThrottledTimer, Utils
from Py4GWCoreLib.enums_src.Model_enums import ModelID

from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
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
from Widgets.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class OpenNearChestUtility(CustomSkillUtilityBase):

    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill]) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("open_near_chest_utility"), 
            in_game_build=current_build, 
            score_definition=ScoreStaticDefinition(CommonScore.LOOT.value), 
            allowed_states=[BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.CHESTING,
            execution_strategy=UtilitySkillExecutionStrategy.STOP_EXECUTION_ONCE_SCORE_NOT_HIGHEST)

        self.score_definition: ScoreStaticDefinition =ScoreStaticDefinition(CommonScore.LOOT.value + 0.001)
        self.opened_chest_agent_ids: set[int] = set()
        self.cooldown_execution = ThrottledTimer(1000)

        self.event_bus.subscribe(EventType.MAP_CHANGED, self.map_changed, subscriber_name=self.custom_skill.skill_name)

    def map_changed(self, message: EventMessage)-> Generator[Any, Any, Any]:
        self.opened_chest_agent_ids = set()
        yield
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1: return None #"No free slots in inventory, halting."
        if GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Lockpick.value) < 1: return None #"No lockpicks in inventory, halting."
        chest_agent_id = custom_behavior_helpers.Resources.get_nearest_locked_chest(700)
        if chest_agent_id in self.opened_chest_agent_ids: return None
        if chest_agent_id is None or chest_agent_id == 0: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        if not self.cooldown_execution.IsExpired():
            yield
            return BehaviorResult.ACTION_SKIPPED

        self.cooldown_execution.Reset()

        chest_agent_id = custom_behavior_helpers.Resources.get_nearest_locked_chest(700)
        if chest_agent_id is None or chest_agent_id == 0: 
            yield
            return BehaviorResult.ACTION_SKIPPED

        # print(f"open_near_chest_utility_ STARTING")

        chest_x, chest_y = Agent.GetXY(chest_agent_id)
        lock_key = f"open_near_chest_utility_{chest_agent_id}"

        result = yield from Routines.Yield.Movement.FollowPath(
            path_points=[(chest_x, chest_y)],
            timeout=10_000)

        if result == False:
            # print(f"open_near_chest_utility_ FAIL FollowPath")
            yield
            return BehaviorResult.ACTION_SKIPPED

        if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key) == False:
            # print(f"open_near_chest_utility_ FAIL try_aquire_lock")
            yield
            return BehaviorResult.ACTION_SKIPPED

        # Use try-finally to ensure lock is always released
        try:
            # print(f"open_near_chest_utility_ LOCK AQUIRED")
            yield from custom_behavior_helpers.Helpers.wait_for(1000) # we must wait until the chest closing animation is finalized
            ActionQueueManager().ResetAllQueues()
            GLOBAL_CACHE.Player.Interact(chest_agent_id, call_target=False)
            yield from custom_behavior_helpers.Helpers.wait_for(1000)
            GLOBAL_CACHE.Player.SendDialog(2)
            yield from custom_behavior_helpers.Helpers.wait_for(1000)
            # print("CHEST_OPENED")
            # Only mark chest as opened and publish the event upon successful interaction
            # print(f"RELEASE Lock key {lock_key}")
            # print(f"self.opened_chest_agent_ids {self.opened_chest_agent_ids}")
            self.opened_chest_agent_ids.add(chest_agent_id)
            yield from self.event_bus.publish(EventType.CHEST_OPENED, state, data=chest_agent_id)
            CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
            return BehaviorResult.ACTION_PERFORMED

        except Exception as e:
            # print(f"ERROR in OpenNearChestUtility._execute: {type(e).__name__}: {e}")
            # print(f"Lock key: {lock_key}, Chest agent ID: {chest_agent_id}")
            import traceback
            traceback.print_exc()
            return BehaviorResult.ACTION_SKIPPED
        finally:
            # Always release the lock, even if an exception occurs
            CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
            pass

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"get_nearest_locked_chest : {custom_behavior_helpers.Resources.get_nearest_locked_chest(700)}")
        PyImGui.bullet_text(f"opened_chest_agent_ids : {self.opened_chest_agent_ids}")
        return
        # debug mode
        gadget_array = AgentArray.GetGadgetArray()
        gadget_array = AgentArray.Filter.ByDistance(gadget_array, GLOBAL_CACHE.Player.GetXY(), 100)
        for agent_id in gadget_array:
            gadget_id = Agent.GetGadgetID(agent_id)
            PyImGui.bullet_text(f"gadget_id close to my position : {gadget_id}")
