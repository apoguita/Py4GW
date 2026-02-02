import math
from tkinter.constants import N
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, Agent, Party, Routines, Range, Player
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, LootConfig, ThrottledTimer, Utils
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.enums_src.Model_enums import ModelID

from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.helpers.cooldown_timer import CooldownTimer
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

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

        self.window_open_timeout = ThrottledTimer(10_000)
        self.window_open_timeout.Stop()

        self.window_close_timeout = ThrottledTimer(10_000)
        self.window_close_timeout.Stop()

        self.dedicated_debug = False

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
        chest_agent_id = custom_behavior_helpers.Resources.get_nearest_locked_chest(1000)
        if chest_agent_id in self.opened_chest_agent_ids: return None
        if chest_agent_id is None or chest_agent_id == 0: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        if not self.cooldown_execution.IsExpired():
            yield
            return BehaviorResult.ACTION_SKIPPED

        self.cooldown_execution.Reset()

        chest_agent_id = custom_behavior_helpers.Resources.get_nearest_locked_chest(1000)
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
            yield from custom_behavior_helpers.Helpers.wait_for(1000) # we must wait until the chest closing animation is finalized
            # this must be done first, so beeing interrupted in that process is not an issue

            if self.dedicated_debug: print(f"open_near_chest_utility_ LOCK AQUIRED")
            ActionQueueManager().ResetAllQueues()

            # ----------- 1 WAIT FOR CHEST WINDOW TO OPEN PHASE ------------
            if self.dedicated_debug: print(f"open_near_chest_utility_ wait_for_chest_window_to_open")
            is_chest_window_opened = yield from self.wait_for_chest_window_to_open(chest_agent_id)
            print(f"open_near_chest_utility_ wait_for_chest_window_to_open is_successful:{is_chest_window_opened}")
            
            if is_chest_window_opened == False:
                self.opened_chest_agent_ids.add(chest_agent_id)
                yield
                return BehaviorResult.ACTION_SKIPPED
            
            # ----------- 2 SEND DIALOG AND WAIT FOR CHEST WINDOW TO CLOSE PHASE ------------
            if self.dedicated_debug: print(f"open_near_chest_utility_ wait_for_chest_window_to_close")
            is_chest_window_closed = yield from self.wait_for_chest_window_to_close()
            print(f"open_near_chest_utility_ wait_for_chest_window_to_close is_successful:{is_chest_window_closed}")

            # ----------- 3 SUCCESS ------------
            self.opened_chest_agent_ids.add(chest_agent_id)
            yield from self.event_bus.publish(EventType.CHEST_OPENED, state, data=chest_agent_id)
            print(f"open_near_chest_utility_ CHEST_OPENED")
            yield
            return BehaviorResult.ACTION_PERFORMED

        except Exception as e:
            print(f"ERROR in OpenNearChestUtility._execute: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            yield
            return BehaviorResult.ACTION_SKIPPED
        finally:
            # Always release the lock, even if an exception occurs
            CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)

    def wait_for_chest_window_to_open(self, chest_agent_id: int) -> Generator[Any, None, bool]:
        
        # 1) reset the timer if not running
        if self.window_open_timeout.IsStopped():
            self.window_open_timeout.Reset()

        # 2) now repeat those step until timeout

        while not self.window_open_timeout.IsExpired():

            # 2.a) interact with the chest
            if self.dedicated_debug: print(f"open_near_chest_utility_ Interact")
            Player.Interact(chest_agent_id, call_target=False)
            yield from custom_behavior_helpers.Helpers.wait_for(150)

            # 2.b) wait for the chest window to open
            if self.dedicated_debug: print(f"open_near_chest_utility_ wait_for_chest_window_to_open")
            if UIManager.IsLockedChestWindowVisible():
                self.window_open_timeout.Stop()
                return True
        
        # 3) timeout
        print(f"open_near_chest_utility_ TIMEOUT waiting for chest window to open (chest_agent_id={chest_agent_id})")
        self.window_open_timeout.Stop()
        return False

    def wait_for_chest_window_to_close(self) -> Generator[Any, None, bool]:

        # 1) reset the timer if not running
        if self.window_close_timeout.IsStopped():
            self.window_close_timeout.Reset()

        # 2) now repeat those step until timeout
        while not self.window_close_timeout.IsExpired():

            # 2.a) send dialog to close the chest window
            if self.dedicated_debug: print(f"open_near_chest_utility_ SendDialog")
            Player.SendDialog(2)
            yield from custom_behavior_helpers.Helpers.wait_for(150)

            # 2.b) check if the chest window is closed
            if self.dedicated_debug: print(f"open_near_chest_utility_ wait_for_chest_window_to_close")
            if not UIManager.IsLockedChestWindowVisible():
                self.window_close_timeout.Stop()
                return True

        # 3) timeout
        print(f"open_near_chest_utility_ TIMEOUT waiting for chest window to close")
        self.window_close_timeout.Stop()
        return False

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"get_nearest_locked_chest : {custom_behavior_helpers.Resources.get_nearest_locked_chest(700)}")
        PyImGui.bullet_text(f"opened_chest_agent_ids : {self.opened_chest_agent_ids}")
        return
        # debug mode
        gadget_array = AgentArray.GetGadgetArray()
        gadget_array = AgentArray.Filter.ByDistance(gadget_array, Player.GetXY(), 100)
        for agent_id in gadget_array:
            gadget_id = Agent.GetGadgetID(agent_id)
            PyImGui.bullet_text(f"gadget_id close to my position : {gadget_id}")
