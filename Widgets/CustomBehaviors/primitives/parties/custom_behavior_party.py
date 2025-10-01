import inspect
import importlib
import pkgutil
from typing import Callable, Generator, Any, List

from Py4GWCoreLib import Routines
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.bus.event_bus import EVENT_BUS
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetData, CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.parties.shared_lock_manager import SharedLockManager
from Widgets.CustomBehaviors.primitives.parties.command_handler import CommandHandler
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology


class CustomBehaviorParty:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CustomBehaviorParty, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._generator_handle = self._handle()
            
            self.command_handler = CommandHandler()
            self.throttler = ThrottledTimer(50)

    def _handle(self) -> Generator[Any | None, Any | None, None]:
        while True:
            self.command_handler.execute_next_step()
            yield
    
    def act(self):
        if not self.throttler.IsExpired(): return
        self.throttler.Reset()
        
        if not Routines.Checks.Map.MapValid(): return

        try:
            next(self._generator_handle)
        except StopIteration:
            print(f"CustomBehaviorParty.act is not expected to StopIteration.")
        except Exception as e:
            print(f"CustomBehaviorParty.act is not expected to exit : {e}")

    def schedule_action(self, action_gen: Callable[[], Generator]) -> bool:
        """Schedule a generator action. Returns True if accepted, False if busy."""
        return self.command_handler.schedule_action(action_gen)

    def is_ready_for_action(self) -> bool:
        """Check if it's safe to schedule another action."""
        return self.command_handler.is_ready_for_action()

    #---

    def get_shared_lock_manager(self) -> SharedLockManager:
        return CustomBehaviorWidgetMemoryManager().GetSharedLockManager()

    def get_typology_is_enabled(self, skill_typology:UtilitySkillTypology):
        if skill_typology == UtilitySkillTypology.COMBAT:
            return self.get_party_is_combat_enabled()
        if skill_typology == UtilitySkillTypology.CHESTING:
            return self.get_party_is_chesting_enabled()
        if skill_typology == UtilitySkillTypology.FOLLOWING:
            return self.get_party_is_following_enabled()
        if skill_typology == UtilitySkillTypology.LOOTING :
            return self.get_party_is_looting_enabled()
        if skill_typology == UtilitySkillTypology.BLESSING :
            return self.get_party_is_blessing_enabled()
        if skill_typology == UtilitySkillTypology.INVENTORY :
            return self.get_party_is_inventory_enabled()
        return True

    #---

    def get_party_is_enabled(self) -> bool:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.is_enabled

    def set_party_is_enabled(self, is_enabled: bool):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            is_enabled=is_enabled, 
            is_combat_enabled=shared_data.is_combat_enabled, 
            is_looting_enabled=shared_data.is_looting_enabled, 
            is_chesting_enabled=shared_data.is_chesting_enabled, 
            is_following_enabled=shared_data.is_following_enabled, 
            is_blessing_enabled=shared_data.is_blessing_enabled, 
            is_inventory_enabled=shared_data.is_inventory_enabled,
            party_target_id=shared_data.party_target_id, 
            party_forced_state=shared_data.party_forced_state)

    #---

    def get_party_is_combat_enabled(self) -> bool:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.is_combat_enabled

    def set_party_is_combat_enabled(self, is_combat_enabled: bool):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            is_enabled=shared_data.is_enabled, 
            is_combat_enabled=is_combat_enabled, 
            is_looting_enabled=shared_data.is_looting_enabled, 
            is_chesting_enabled=shared_data.is_chesting_enabled, 
            is_following_enabled=shared_data.is_following_enabled, 
            is_blessing_enabled=shared_data.is_blessing_enabled, 
            is_inventory_enabled=shared_data.is_inventory_enabled,
            party_target_id=shared_data.party_target_id,
            party_forced_state=shared_data.party_forced_state)

    #---

    def get_party_is_looting_enabled(self) -> bool:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.is_looting_enabled

    def set_party_is_looting_enabled(self, is_looting_enabled: bool):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            is_enabled=shared_data.is_enabled, 
            is_combat_enabled=shared_data.is_combat_enabled, 
            is_looting_enabled=is_looting_enabled, 
            is_chesting_enabled=shared_data.is_chesting_enabled, 
            is_following_enabled=shared_data.is_following_enabled, 
            is_blessing_enabled=shared_data.is_blessing_enabled, 
            is_inventory_enabled=shared_data.is_inventory_enabled,
            party_target_id=shared_data.party_target_id,
            party_forced_state=shared_data.party_forced_state)

    #---

    def get_party_is_chesting_enabled(self) -> bool:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.is_chesting_enabled

    def set_party_is_chesting_enabled(self, is_chesting_enabled: bool):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            is_enabled=shared_data.is_enabled, 
            is_combat_enabled=shared_data.is_combat_enabled, 
            is_looting_enabled=shared_data.is_looting_enabled, 
            is_chesting_enabled=is_chesting_enabled, 
            is_following_enabled=shared_data.is_following_enabled, 
            is_blessing_enabled=shared_data.is_blessing_enabled, 
            is_inventory_enabled=shared_data.is_inventory_enabled,
            party_target_id=shared_data.party_target_id,
            party_forced_state=shared_data.party_forced_state)

    #---
    
    def get_party_is_following_enabled(self) -> bool:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.is_following_enabled

    def set_party_is_following_enabled(self, is_following_enabled: bool):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            is_enabled=shared_data.is_enabled, 
            is_combat_enabled=shared_data.is_combat_enabled, 
            is_looting_enabled=shared_data.is_looting_enabled, 
            is_chesting_enabled=shared_data.is_chesting_enabled, 
            is_following_enabled=is_following_enabled, 
            is_blessing_enabled=shared_data.is_blessing_enabled, 
            is_inventory_enabled=shared_data.is_inventory_enabled,
            party_target_id=shared_data.party_target_id,
            party_forced_state=shared_data.party_forced_state)

    #---

    def get_party_is_blessing_enabled(self) -> bool:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.is_blessing_enabled

    def set_party_is_blessing_enabled(self, is_blessing_enabled: bool):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            is_enabled=shared_data.is_enabled, 
            is_combat_enabled=shared_data.is_combat_enabled, 
            is_looting_enabled=shared_data.is_looting_enabled, 
            is_chesting_enabled=shared_data.is_chesting_enabled, 
            is_following_enabled=shared_data.is_following_enabled, 
            is_blessing_enabled=is_blessing_enabled, 
            is_inventory_enabled=shared_data.is_inventory_enabled,
            party_target_id=shared_data.party_target_id,
            party_forced_state=shared_data.party_forced_state)

    #---

    def get_party_is_inventory_enabled(self) -> bool:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.is_inventory_enabled

    def set_party_is_inventory_enabled(self, is_inventory_enabled: bool):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            is_enabled=shared_data.is_enabled, 
            is_combat_enabled=shared_data.is_combat_enabled, 
            is_looting_enabled=shared_data.is_looting_enabled, 
            is_chesting_enabled=shared_data.is_chesting_enabled, 
            is_following_enabled=shared_data.is_following_enabled, 
            is_blessing_enabled=shared_data.is_blessing_enabled, 
            is_inventory_enabled=is_inventory_enabled,
            party_target_id=shared_data.party_target_id,
            party_forced_state=shared_data.party_forced_state)

    #---

    def get_party_forced_state(self) -> BehaviorState|None:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        result = BehaviorState(shared_data.party_forced_state) if shared_data.party_forced_state is not None else None
        return result

    def set_party_forced_state(self, state: BehaviorState | None):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            is_enabled=shared_data.is_enabled, 
            is_combat_enabled=shared_data.is_combat_enabled, 
            is_looting_enabled=shared_data.is_looting_enabled, 
            is_chesting_enabled=shared_data.is_chesting_enabled, 
            is_following_enabled=shared_data.is_following_enabled,
            is_blessing_enabled=shared_data.is_blessing_enabled, 
            is_inventory_enabled=shared_data.is_inventory_enabled,
            party_target_id=shared_data.party_target_id,
            party_forced_state=state.value if state is not None else None)

    #---

    def get_party_custom_target(self) -> int | None:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.party_target_id

    def set_party_custom_target(self, target: int | None):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            is_enabled=shared_data.is_enabled, 
            is_combat_enabled=shared_data.is_combat_enabled, 
            is_looting_enabled=shared_data.is_looting_enabled, 
            is_chesting_enabled=shared_data.is_chesting_enabled, 
            is_following_enabled=shared_data.is_following_enabled,
            is_blessing_enabled=shared_data.is_blessing_enabled, 
            is_inventory_enabled=shared_data.is_inventory_enabled,
            party_target_id=target,
            party_forced_state=shared_data.party_forced_state)
