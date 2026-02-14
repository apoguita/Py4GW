import ctypes
from dataclasses import dataclass
import inspect
import importlib
import pkgutil
from typing import Callable, Generator, Any, List

from PyAgent import AttributeClass

from Py4GWCoreLib import Routines, Map, Agent, Player
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountStruct
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer


from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives import constants

from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetData, CustomBehaviorWidgetMemoryManager
from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants
from Sources.oazix.CustomBehaviors.primitives.parties.party_command_handler_manager import PartyCommandHandlerManager
from Sources.oazix.CustomBehaviors.primitives.parties.party_flagging_manager import PartyFlaggingManager
from Sources.oazix.CustomBehaviors.primitives.parties.party_following_manager import PartyFollowingManager
from Sources.oazix.CustomBehaviors.primitives.parties.shared_lock_manager import SharedLockManager
from Sources.oazix.CustomBehaviors.primitives.parties.party_teambuild_manager import PartyTeamBuildManager
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants

@dataclass
class PartyData:
    account_email: str
    skillbar_template: str
    
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
            
            self.party_command_handler_manager = PartyCommandHandlerManager()
            self.party_teambuild_manager = PartyTeamBuildManager()
            self.party_following_manager = PartyFollowingManager()
            self.party_shared_lock_manager = CustomBehaviorWidgetMemoryManager().GetSharedLockManager()
            self.party_flagging_manager = PartyFlaggingManager()

            # Rename GW windows to match custom behavior party names on load
            print("CustomBehaviorParty: Renaming GW windows")
            CustomBehaviorParty().schedule_action(PartyCommandConstants.rename_gw_windows)

            self.throttler = ThrottledTimer(50)

    def _handle(self) -> Generator[Any | None, Any | None, None]:
        while True:
            self.party_command_handler_manager.execute_next_step()
            self.__messaging_process()
            self.party_teambuild_manager.act()
            
            # # ------------------------------ Custom party target ------------------------------
            if custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader():
                if Map.IsExplorable():
                    current_party_target_id = self.get_party_custom_target()
                    if current_party_target_id is not None:
                        # if not Agent.IsValid(current_party_target_id): self.set_party_custom_target(None)
                        if not Agent.IsAlive(current_party_target_id): self.set_party_custom_target(None)
                    
                    players = GLOBAL_CACHE.Party.GetPlayers()
                    for player in players:
                        agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
                        if agent_id == Player.GetAgentID():
                            called_target_id = player.called_target_id
                            if called_target_id != 0:
                                self.set_party_custom_target(called_target_id)
                            break
                else:
                    self.set_party_custom_target(None)


            # # ------------------------------ Party leader email ------------------------------



                
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
        return self.party_command_handler_manager.schedule_action(action_gen)

    def is_ready_for_action(self) -> bool:
        """Check if it's safe to schedule another action."""
        return self.party_command_handler_manager.is_ready_for_action()

    #---

    def __messaging_process(self):

        account_email = Player.GetAccountEmail()
        index, message = GLOBAL_CACHE.ShMem.GetNextMessage(account_email)

        if index == -1 or message is None:
            return

        match message.Command:
            case SharedCommandType.CustomBehaviors:
                
                pass

    #---

    def get_shared_lock_manager(self) -> SharedLockManager:
        return self.party_shared_lock_manager
    
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
            party_leader_email=shared_data.party_leader_email,
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
            party_leader_email=shared_data.party_leader_email,
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
            party_leader_email=shared_data.party_leader_email,
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
            party_leader_email=shared_data.party_leader_email,
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
            party_leader_email=shared_data.party_leader_email,
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
            party_leader_email=shared_data.party_leader_email,
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
            party_leader_email=shared_data.party_leader_email,
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
            party_leader_email=shared_data.party_leader_email,
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
            party_leader_email=shared_data.party_leader_email,
            party_forced_state=shared_data.party_forced_state)

    #---

    @staticmethod
    def get_party_leader_email() -> str | None:
        shared_data:CustomBehaviorWidgetData = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
        return shared_data.party_leader_email

    def set_party_leader_email(self, leader_email: str | None):
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
            party_leader_email=leader_email,
            party_forced_state=shared_data.party_forced_state)