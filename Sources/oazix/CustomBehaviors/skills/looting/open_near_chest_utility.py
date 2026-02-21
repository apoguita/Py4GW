import math
from tkinter.constants import N
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, Agent, Party, Routines, Range, Player, Map
from Py4GWCoreLib.enums_src.UI_enums import ChatChannel as Channel
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, LootConfig, ThrottledTimer, Utils
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.enums_src.Model_enums import ModelID, GadgetModelID

from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives import constants
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
            allowed_states=[BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO, BehaviorState.IDLE, BehaviorState.IN_AGGRO],
            utility_skill_typology=UtilitySkillTypology.DAEMON,
            execution_strategy=UtilitySkillExecutionStrategy.STOP_EXECUTION_ONCE_SCORE_NOT_HIGHEST)

        self.score_definition: ScoreStaticDefinition =ScoreStaticDefinition(CommonScore.LOOT.value + 0.001)
        self.opened_chest_agent_ids: set[int] = set()
        self.my_slot_index: int = -1
        self.cooldown_execution = ThrottledTimer(1000)

        self.window_open_timeout = ThrottledTimer(10_000)
        self.window_open_timeout.Stop()

        self.window_close_timeout = ThrottledTimer(10_000)
        self.window_close_timeout.Stop()

        self.throttle_debug_log = ThrottledTimer(5000)
        self.dedicated_debug = False # Disable debug prints
        self.is_active = False # Flag to indicate critical section
        self.is_reporting = False # Flag to prevent combat interrupt during reporting

        self.event_bus.subscribe(EventType.MAP_CHANGED, self.map_changed, subscriber_name=self.custom_skill.skill_name)

    def map_changed(self, message: EventMessage)-> Generator[Any, Any, Any]:
        # if self.dedicated_debug: print(f"open_near_chest_utility_ Map Changed, clearing cache")
        self.opened_chest_agent_ids = set()
        self.my_slot_index = -1
        yield
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if self.is_active: return True # Don't interrupt if critical section

        # Only run in explorable areas, never in outposts
        if not Map.IsExplorable(): return False

        # Check Global and Chesting flags
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
        try:
            widget_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
            if not widget_data.is_enabled: return False
            if not widget_data.is_chesting_enabled: return False
        except Exception as e:
            if self.dedicated_debug: print(f"open_near_chest_utility_ Error checking enabled state: {e}")
            return False

        if self.allowed_states is not None and current_state not in self.allowed_states: 
            if self.throttle_debug_log.IsExpired():
                self.throttle_debug_log.Reset()
                print(f"open_near_chest_utility_ BLOCKED by State: {current_state} (Allowed: {self.allowed_states})")
            return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if self.is_active:
            # Check for enemies - if present, YIELD to combat behaviors
            enemies = AgentArray.GetEnemyArray()
            enemies = AgentArray.Filter.ByCondition(enemies, lambda e: Agent.IsAlive(e))
            player_pos = Player.GetXY()
            enemies_in_range = AgentArray.Filter.ByDistance(enemies, player_pos, Range.Earshot.value)
            if len(enemies_in_range) > 0:
                if self.dedicated_debug: print(f"COMBAT INTERRUPT ({len(enemies_in_range)} enemies) - yielding to combat")
                self.is_active = False  # Let behavior tree pick combat
                return None
            return 10000.0 # Force priority to finish sequence
        
        if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1: 
             return None

        if GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Lockpick.value) < 1: 
             return None

        # Leader synchronization logic
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
        # Get DIRECT reference to shared memory
        mem = CustomBehaviorWidgetMemoryManager()._get_struct()
        config = mem.ChestOpeningConfig
        is_leader = custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader()
        
        target_id = config.ChestAgentID
        
        # 1. LEADER LOGIC: Set/Reset Shared Target
        if is_leader:
            current_target = config.ChestAgentID
            
            # Need to search if:
            # A) No target set (0)
            # B) Current target is already opened by me (Leader)
            # C) Current target is invalid
            need_new_target = (current_target == 0) or \
                              (current_target in self.opened_chest_agent_ids) or \
                              (not Agent.IsValid(current_target))

            if need_new_target:
                # Scan for NEAREST locked chest
                new_target = custom_behavior_helpers.Resources.get_nearest_locked_chest(300)
                
                if new_target is not None and new_target != 0:
                     if new_target not in self.opened_chest_agent_ids:
                         # FOUND NEW CHEST! Reset everything directly in shared memory.
                         config.ChestAgentID = new_target
                         config.ChestReported = False
                         for i in range(12):
                             config.ChestStatus[i] = 0
                         # No SetChestOpeningConfig needed - wrote directly to shared memory
                         # Reset my own tracking for the new chest
                         self.my_slot_index = -1
                         if self.dedicated_debug: print(f"LEADER FOUND NEW CHEST: {new_target}")
                         Player.SendChat('#', f"Unlocking chest...")
                else:
                    # No new chest found, nothing to do
                    return None

        # 2. Universal Logic: Check shared memory for target
        # Re-read config directly from shared memory
        mem = CustomBehaviorWidgetMemoryManager()._get_struct()
        config = mem.ChestOpeningConfig
        chest_agent_id = config.ChestAgentID
        
        # Guard: Check if I already finished this specific chest
        if self.my_slot_index != -1 and config.ChestStatus[self.my_slot_index] == 1:
             if chest_agent_id in self.opened_chest_agent_ids:
                 return 0.0

        if chest_agent_id in self.opened_chest_agent_ids: 
             return 0.0
        
        if chest_agent_id is None or chest_agent_id == 0: 
             return None
        
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        if not self.cooldown_execution.IsExpired():
            yield
            return BehaviorResult.ACTION_SKIPPED

        if self.dedicated_debug: print(f"EXECUTE CALLED")

        self.cooldown_execution.Reset()

        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
        mem = CustomBehaviorWidgetMemoryManager()._get_struct()
        config = mem.ChestOpeningConfig
        chest_agent_id = config.ChestAgentID
        
        # EARLY EXIT: If already done
        if chest_agent_id in self.opened_chest_agent_ids:
             yield
             return BehaviorResult.ACTION_PERFORMED

        if self.my_slot_index != -1 and config.ChestStatus[self.my_slot_index] == 1:
             self.opened_chest_agent_ids.add(chest_agent_id)
             yield
             return BehaviorResult.ACTION_PERFORMED

        if chest_agent_id == 0:
            if custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader():
                chest_agent_id = custom_behavior_helpers.Resources.get_nearest_locked_chest(300)
        
        if chest_agent_id is None or chest_agent_id == 0: 
            yield
            return BehaviorResult.ACTION_SKIPPED
            
        # Protect entire sequence
        self.is_active = True
        lock_key = f"chest_{chest_agent_id}"
        
        try:
            # 1. Register and Start
            self.my_slot_index = self._register_self_for_reporting()
            my_slot_index = self.my_slot_index
            
            # PROTECT SUCCESS STATUS: Don't downgrade if we already succeeded
            if config.ChestStatus[my_slot_index] == 1:
                self.opened_chest_agent_ids.add(chest_agent_id)
                yield
                return BehaviorResult.ACTION_PERFORMED
            
            self._update_chest_status(chest_agent_id, 99) # Started

            # 2. APPROACH FIRST: Walk near the chest so everyone is gathered
            chest_x, chest_y = Agent.GetXY(chest_agent_id)
            result = yield from Routines.Yield.Movement.FollowPath(
                path_points=[(chest_x, chest_y)],
                timeout=15_000)

            if result == False:
                self._update_chest_status(chest_agent_id, 3) # Failed: Pathing
                yield
                return BehaviorResult.ACTION_SKIPPED

            # 3. ACQUIRE LOCK (while near the chest)
            lock_acquired = False
            loop_count = 0
            max_lock_wait = 2000 # 200 seconds max
            while loop_count < max_lock_wait:
                # Combat check: if enemies appear, bail out and let combat AI handle
                enemies = AgentArray.GetEnemyArray()
                enemies = AgentArray.Filter.ByCondition(enemies, lambda e: Agent.IsAlive(e))
                player_pos = Player.GetXY()
                enemies_in_range = AgentArray.Filter.ByDistance(enemies, player_pos, Range.Earshot.value)
                if len(enemies_in_range) > 0:
                    if self.dedicated_debug: print(f"COMBAT during lock wait, aborting")
                    self._update_chest_status(chest_agent_id, 0) # Reset status so we can retry
                    yield
                    return BehaviorResult.ACTION_SKIPPED

                self._update_chest_status(chest_agent_id, 97) # Waiting Lock
                if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key):
                    lock_acquired = True
                    break
                yield from custom_behavior_helpers.Helpers.wait_for(100)
                loop_count += 1
                if loop_count % 50 == 0:
                    if self.dedicated_debug: print(f"waiting for lock at slot {my_slot_index}")

            if not lock_acquired:
                self._update_chest_status(chest_agent_id, 4) # Failed: Lock Timeout
                yield
                return BehaviorResult.ACTION_SKIPPED

            # Use try-finally to ensure lock is always released
            # self.is_active = True # Already Active
            try:
                # Wait a bit after acquiring lock to ensure previous user is fully clear/synced? 
                yield from custom_behavior_helpers.Helpers.wait_for(500) 

                if self.dedicated_debug: print(f"open_near_chest_utility_ LOCK AQUIRED")
                ActionQueueManager().ResetAllQueues()

                # ----------- 1 WAIT FOR CHEST WINDOW TO OPEN PHASE ------------
                is_chest_window_opened = yield from self.wait_for_chest_window_to_open(chest_agent_id)
                
                if is_chest_window_opened == False:
                    self.opened_chest_agent_ids.add(chest_agent_id)
                    self._update_chest_status(chest_agent_id, 5) # Failed: Window Open Timeout
                    if constants.DEBUG: print(f"Failed to open/close chest window, adding to blacklist: {chest_agent_id}")
                    yield
                    return BehaviorResult.ACTION_SKIPPED
                
                # ----------- 2 SEND DIALOG AND WAIT FOR CHEST WINDOW TO CLOSE PHASE ------------
                is_chest_window_closed = yield from self.wait_for_chest_window_to_close()

                if is_chest_window_closed == False:
                    self.opened_chest_agent_ids.add(chest_agent_id)
                    self._update_chest_status(chest_agent_id, 6) # Failed: Window Close Timeout
                    if constants.DEBUG: print(f"Failed to close chest window, adding to blacklist: {chest_agent_id}")
                    yield
                    return BehaviorResult.ACTION_SKIPPED

                self.opened_chest_agent_ids.add(chest_agent_id) # LOCAL EXCLUSION
                yield from custom_behavior_helpers.Helpers.wait_for(1000) # Wait for drop animation
                
                # Scan for loot in a small radius (500 units) to ensure it's ours
                loot_array = LootConfig().GetfilteredLootArray(500, multibox_loot=True)
                for item_agent_id in loot_array:
                    if Agent.IsValid(item_agent_id):
                        pos = Agent.GetXY(item_agent_id)
                        yield from Routines.Yield.Movement.FollowPath([pos], timeout=2000)
                        Player.Interact(item_agent_id, call_target=False)
                        
                        # Wait for it to disappear
                        p_timer = ThrottledTimer(2000)
                        while not p_timer.IsExpired():
                            if not Agent.IsValid(item_agent_id): break
                            yield from custom_behavior_helpers.Helpers.wait_for(100)

                # B) COMBAT CHECK: If enemies in range, abort and let combat AI handle
                enemies = AgentArray.GetEnemyArray()
                enemies = AgentArray.Filter.ByCondition(enemies, lambda e: Agent.IsAlive(e))
                player_pos = Player.GetXY()
                enemies_in_range = AgentArray.Filter.ByDistance(enemies, player_pos, Range.Earshot.value)
                yield from custom_behavior_helpers.Helpers.wait_for(2000)

                # D) FINALIZE: Mark success to signal NEXT person
                self._update_chest_status(chest_agent_id, 1) # Success
                yield from self.event_bus.publish(EventType.CHEST_OPENED, state, data=chest_agent_id)
                
                # RELEASE LOCK NOW so others can go
                if 'lock_acquired' in locals() and lock_acquired:
                    CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
                    lock_acquired = False # Prevent double release in finally

                yield
                return BehaviorResult.ACTION_PERFORMED

            except Exception as e:
                # Inner try/catch for lock handling?
                # Actually, pass it up to outer catch?
                # No, just let it bubble up to outer catch
                raise e
        except Exception as e:
            print(f"ERROR in OpenNearChestUtility._execute: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self.opened_chest_agent_ids.add(chest_agent_id) # Add to blacklist on error
            self._update_chest_status(chest_agent_id, 7) # Failed: Exception
            yield
            return BehaviorResult.ACTION_SKIPPED
        finally:
            self.is_active = False
            # Always release the lock, even if an exception occurs
            if 'lock_acquired' in locals() and lock_acquired:
                CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)

    def _initialize_reporting(self, chest_agent_id: int):
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
        # Get DIRECT reference to shared memory
        mem = CustomBehaviorWidgetMemoryManager()._get_struct()
        config = mem.ChestOpeningConfig
        
        # If new chest ID, reset status
        if config.ChestAgentID != chest_agent_id:
            config.ChestAgentID = chest_agent_id
            for i in range(len(config.ChestStatus)):
                config.ChestStatus[i] = 0
            config.ChestReported = False # Reset reported flag

    def _register_self_for_reporting(self) -> int:
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
        # Get DIRECT reference to shared memory (not a copy)
        mem = CustomBehaviorWidgetMemoryManager()._get_struct()
        config = mem.ChestOpeningConfig
        my_email = Player.GetName()
        
        # 0. LEADER PRIORITY
        if custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader():
            if config.SlotEmails[0].value != my_email:
                config.SlotEmails[0].value = my_email
                # No SetChestOpeningConfig needed - we wrote directly to shared memory
            return 0

        # 1. Find existing slot
        for i in range(12):
            if config.SlotEmails[i].value == my_email:
                return i
        
        # 2. Claim new slot (followers start from 1)
        for i in range(1, 12):
            val = config.SlotEmails[i].value
            if not val or len(val) == 0:
                config.SlotEmails[i].value = my_email
                # No SetChestOpeningConfig needed - we wrote directly to shared memory
                return i
        
        return 11 # Fallback

    def _update_chest_status(self, chest_agent_id: int, status: int):
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
        # Get DIRECT reference to shared memory (not a copy)
        mem = CustomBehaviorWidgetMemoryManager()._get_struct()
        config = mem.ChestOpeningConfig
        
        if config.ChestAgentID == chest_agent_id:
            my_slot_index = self._register_self_for_reporting() # Find my stable slot
            
            # PROTECT SUCCESS STATUS: Don't downgrade if we already succeeded
            current_status = config.ChestStatus[my_slot_index]
            if current_status == 1 and status != 1:
                return 
            
            # Write directly to shared memory - no full struct copy!
            config.ChestStatus[my_slot_index] = status



    def wait_for_chest_window_to_open(self, chest_agent_id: int) -> Generator[Any, None, bool]:
        
        # 1) reset the timer if not running
        if self.window_open_timeout.IsStopped():
            self.window_open_timeout.Reset()

        # Key mapping
        chest_model_id = Agent.GetGadgetID(chest_agent_id)
        key_model_id = None
        
        if chest_model_id == GadgetModelID.CHEST_KRYTAN: key_model_id = ModelID.Krytan_Key
        elif chest_model_id == GadgetModelID.CHEST_MAGUUMA: key_model_id = ModelID.Maguuma_Key
        elif chest_model_id == GadgetModelID.CHEST_ASCALONIAN: key_model_id = ModelID.Ascalonian_Key
        elif chest_model_id == GadgetModelID.CHEST_SHING_JEA: key_model_id = ModelID.Shing_Jea_Key
        elif chest_model_id == GadgetModelID.CHEST_KOURNAN: key_model_id = ModelID.Kournan_Key
        elif chest_model_id == GadgetModelID.CHEST_DARKSTONE: key_model_id = ModelID.Darkstone_Key
        # elif chest_model_id == GadgetModelID.CHEST_VABBIAN: key_model_id = ModelID.Vabbian_Key # Vabbian chest ID not in enum yet?

        # Force Lockpick (134) to ignore keys as requested
        dialog_id_to_send = 134

        # 2) now repeat those step until timeout
        while not self.window_open_timeout.IsExpired():

            # 2.a) interact with the chest
            if self.dedicated_debug: print(f"Interact")
            Player.Interact(chest_agent_id, call_target=False)
            yield from custom_behavior_helpers.Helpers.wait_for(150)

            # 2.b) Send dialog if window not yet open (or to force it)
            # We assume the interaction triggers a dialog.
            # 2.b) Send dialog if window not yet open (or to force it)
            # REMOVED: Don't send dialog while opening, it might cancel/close the window!
            pass

            # 2.c) wait for the chest window to open
            if self.dedicated_debug: print(f"wait_for_chest_window_to_open")
            if UIManager.IsLockedChestWindowVisible():
                self.window_open_timeout.Stop()
                return True
            
            # Fallback: Locked chests often use the generic Dialog window ID 1 (0x1) 
            # If IsLockedChestWindowVisible fails (bad offsets?), check for Frame 1
            if UIManager.FrameExists(1): 
                 self.window_open_timeout.Stop()
                 return True

        # 3) timeout
        print(f"TIMEOUT waiting for chest window to open (chest_agent_id={chest_agent_id})")
        self.window_open_timeout.Stop()
        return False

    def wait_for_chest_window_to_close(self) -> Generator[Any, None, bool]:

        # 1) reset the timer if not running
        if self.window_close_timeout.IsStopped():
            self.window_close_timeout.Reset()

        # 2) Matching HeroAI OpenChest pattern: SendDialog(2) while window is visible
        while not self.window_close_timeout.IsExpired():

            # Already closed? Done.
            if not UIManager.IsLockedChestWindowVisible():
                self.window_close_timeout.Stop()
                return True

            # Send dialog 2 (Use Lockpick) - matches HeroAI Messaging.py OpenChest logic
            Player.SendDialog(2)
            yield from custom_behavior_helpers.Helpers.wait_for(1500)

        # 3) timeout
        print(f"TIMEOUT waiting for chest window to close")
        self.window_close_timeout.Stop()
        return False

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"get_nearest_locked_chest : {custom_behavior_helpers.Resources.get_nearest_locked_chest(1500)}")
        PyImGui.bullet_text(f"opened_chest_agent_ids : {self.opened_chest_agent_ids}")
        return
        # debug mode
        gadget_array = AgentArray.GetGadgetArray()
        gadget_array = AgentArray.Filter.ByDistance(gadget_array, Player.GetXY(), 100)
        for agent_id in gadget_array:
            gadget_id = Agent.GetGadgetID(agent_id)
            PyImGui.bullet_text(f"gadget_id close to my position : {gadget_id}")

