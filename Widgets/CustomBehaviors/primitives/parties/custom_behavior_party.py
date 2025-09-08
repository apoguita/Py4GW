import inspect
import importlib
import pkgutil
from typing import Generator, Any, List

from Py4GWCoreLib import GLOBAL_CACHE, Routines
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetData, CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.parties.shared_lock_manager import SharedLockManager
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
        return True

    #---

    def get_party_is_enabled(self) -> bool:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.is_enabled

    def set_party_is_enabled(self, is_enabled: bool):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            is_enabled, 
            shared_data.is_combat_enabled, 
            shared_data.is_looting_enabled, 
            shared_data.is_chesting_enabled, 
            shared_data.is_following_enabled, 
            shared_data.party_target_id, 
            shared_data.party_forced_state)

    #---

    def get_party_is_combat_enabled(self) -> bool:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.is_combat_enabled

    def set_party_is_combat_enabled(self, is_combat_enabled: bool):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            shared_data.is_enabled, 
            is_combat_enabled, 
            shared_data.is_looting_enabled, 
            shared_data.is_chesting_enabled, 
            shared_data.is_following_enabled, 
            shared_data.party_target_id,
            shared_data.party_forced_state)

    #---

    def get_party_is_looting_enabled(self) -> bool:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.is_looting_enabled

    def set_party_is_looting_enabled(self, is_looting_enabled: bool):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            shared_data.is_enabled, 
            shared_data.is_combat_enabled, 
            is_looting_enabled, 
            shared_data.is_chesting_enabled, 
            shared_data.is_following_enabled, 
            shared_data.party_target_id,
            shared_data.party_forced_state)

    #---

    def get_party_is_chesting_enabled(self) -> bool:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.is_chesting_enabled

    def set_party_is_chesting_enabled(self, is_chesting_enabled: bool):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            shared_data.is_enabled, 
            shared_data.is_combat_enabled, 
            shared_data.is_looting_enabled, 
            is_chesting_enabled, 
            shared_data.is_following_enabled, 
            shared_data.party_target_id,
            shared_data.party_forced_state)

    #---
    
    def get_party_is_following_enabled(self) -> bool:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.is_following_enabled

    def set_party_is_following_enabled(self, is_following_enabled: bool):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            shared_data.is_enabled, 
            shared_data.is_combat_enabled, 
            shared_data.is_looting_enabled, 
            shared_data.is_chesting_enabled, 
            is_following_enabled, 
            shared_data.party_target_id,
            shared_data.party_forced_state)

    #---

    def get_party_forced_state(self) -> BehaviorState|None:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        result = BehaviorState(shared_data.party_forced_state) if shared_data.party_forced_state is not None else None
        return result

    def set_party_forced_state(self, state: BehaviorState | None):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            shared_data.is_enabled, 
            shared_data.is_combat_enabled, 
            shared_data.is_looting_enabled, 
            shared_data.is_chesting_enabled, 
            shared_data.is_following_enabled,
            shared_data.party_target_id,
            state.value if state is not None else None)

    #---

    def get_party_custom_target(self) -> int | None:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.party_target_id

    def set_party_custom_target(self, target: int | None):
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        CustomBehaviorWidgetMemoryManager().SetCustomBehaviorWidgetData(
            shared_data.is_enabled, 
            shared_data.is_combat_enabled, 
            shared_data.is_looting_enabled, 
            shared_data.is_chesting_enabled, 
            shared_data.is_following_enabled,
            target,
            shared_data.party_forced_state)
