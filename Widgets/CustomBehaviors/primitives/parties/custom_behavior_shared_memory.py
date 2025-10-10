from ctypes import Structure, c_uint, c_float, c_bool, c_wchar
from multiprocessing import shared_memory
from ctypes import sizeof
from datetime import datetime, timezone
from datetime import datetime, timezone
import time
from threading import Lock
from typing import Generator

from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.parties.shared_lock_manager import (
    SharedLockEntry,
    SharedLockEntryStruct,
    SharedLockHistoryStruct,
    SharedLockManager,
    MAX_LOCKS,
    MAX_LOCK_KEY_LEN,
    MAX_LOCK_HISTORY,
)


class PartyFollowingConfigStruct(Structure):
    """Struct for party following configuration stored in shared memory"""
    _pack_ = 1
    _fields_ = [
        # Combat parameters (IN_AGGRO)
        ("CombatFollowDistance", c_float),
        ("CombatSpreadThreshold", c_float),
        ("CombatRepulsionWeight", c_float),
        # Non-combat parameters (CLOSE_TO_AGGRO, FAR_FROM_AGGRO)
        ("NoncombatFollowDistance", c_float),
        ("NoncombatSpreadThreshold", c_float),
        ("NoncombatRepulsionWeight", c_float),
        # Common parameters
        ("FollowDistanceTolerance", c_float),
        ("MaxMoveDistance", c_float),
        ("MinMoveThreshold", c_float),
        # Debug
        ("EnableDebugOverlay", c_bool),
    ]


class CustomBehaviorWidgetStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("IsEnabled", c_bool),
        ("IsCombatEnabled", c_bool),
        ("IsFollowingEnabled", c_bool),
        ("IsLootingEnabled", c_bool),
        ("IsChestingEnabled", c_bool),
        ("IsBlessingEnabled", c_bool),
        ("IsInventoryEnabled", c_bool),
        ("PartyTargetId", c_uint),
        ("PartyForcedState", c_uint),
        ("LockEntries", SharedLockEntryStruct * MAX_LOCKS),
        ("LockHistoryEntries", SharedLockHistoryStruct * MAX_LOCK_HISTORY),
        ("LockHistoryIdx", c_uint),
        ("FollowingConfig", PartyFollowingConfigStruct),
    ]

class CustomBehaviorWidgetData:
    def __init__(self, is_enabled: bool, is_combat_enabled:bool, is_looting_enabled:bool, is_chesting_enabled:bool, is_following_enabled:bool, is_blessing_enabled:bool,is_inventory_enabled:bool, party_target_id: int | None, party_forced_state: int | None):
        self.is_enabled: bool = is_enabled
        self.is_combat_enabled: bool = is_combat_enabled
        self.is_looting_enabled: bool = is_looting_enabled
        self.is_chesting_enabled: bool = is_chesting_enabled
        self.is_following_enabled: bool = is_following_enabled
        self.is_blessing_enabled: bool = is_blessing_enabled
        self.is_inventory_enabled: bool = is_inventory_enabled
        self.party_target_id: int | None = party_target_id
        self.party_forced_state: int | None = party_forced_state

    # In-memory cooperative lock helpers (delegates to the singleton manager)
    def get_shared_lock_manager(self, key: str, timeout_seconds: int = 20) -> SharedLockManager:
        return CustomBehaviorWidgetMemoryManager().__shared_lock
    

SHMEM_SHARED_MEMORY_FILE_NAME = "CustomBehaviorWidgetMemoryManager"
DEBUG = True

class CustomBehaviorWidgetMemoryManager:
    _instance = None  # Singleton instance

    def __new__(cls, name=SHMEM_SHARED_MEMORY_FILE_NAME):
        if cls._instance is None:
            cls._instance = super(CustomBehaviorWidgetMemoryManager, cls).__new__(cls)
            cls._instance._initialized = False  # Ensure __init__ runs only once

        return cls._instance

    def __init__(self, name=SHMEM_SHARED_MEMORY_FILE_NAME):
        if not self._initialized:
            self.shm_name = name
            self.size = sizeof(CustomBehaviorWidgetStruct)

            # Create or attach shared memory
            try:
                self.shm = shared_memory.SharedMemory(name=self.shm_name)
                if DEBUG: print(f"Shared memory area '{self.shm_name}' attached.")
                # we keep current.
            except FileNotFoundError:
                self.shm = shared_memory.SharedMemory(name=self.shm_name, create=True, size=self.size)
                if DEBUG: print(f"Shared memory area '{self.shm_name}' created.")
                self.__reset_all_data()  # Initialize all player data

            # Attach the shared memory structure
            self.__shared_lock = SharedLockManager(self._get_struct)
            self._initialized = True

    def _get_struct(self) -> CustomBehaviorWidgetStruct:
        return CustomBehaviorWidgetStruct.from_buffer(self.shm.buf)

    def __reset_all_data(self):
        mem = self._get_struct()
        mem.PartyTargetId = 0
        mem.PartyForcedState = 0
        mem.IsEnabled = True
        mem.IsCombatEnabled = True
        mem.IsFollowingEnabled = True
        mem.IsLootingEnabled = True
        mem.IsChestingEnabled = False # we deactivate chesting by-default.
        mem.IsBlessingEnabled = False # we deactivate blessing by-default (there is often wrong-positive).
        mem.IsInventoryEnabled = False # we deactivate invoentory by-default.

        # Initialize following config with defaults
        mem.FollowingConfig.CombatFollowDistance = 150.0
        mem.FollowingConfig.CombatSpreadThreshold = 150.0
        mem.FollowingConfig.CombatRepulsionWeight = 150.0
        mem.FollowingConfig.NoncombatFollowDistance = 200.0
        mem.FollowingConfig.NoncombatSpreadThreshold = 100.0
        mem.FollowingConfig.NoncombatRepulsionWeight = 150.0
        mem.FollowingConfig.FollowDistanceTolerance = 50.0
        mem.FollowingConfig.MaxMoveDistance = 250.0
        mem.FollowingConfig.MinMoveThreshold = 0.5
        mem.FollowingConfig.EnableDebugOverlay = True

        for i in range(MAX_LOCKS):
            mem.LockEntries[i].Key = ""
            mem.LockEntries[i].AcquiredAt = 0
            if hasattr(mem.LockEntries[i], "ReleasedAt"):
                mem.LockEntries[i].ReleasedAt = 0
            if hasattr(mem.LockEntries[i], "SenderEmail"):
                mem.LockEntries[i].SenderEmail = ""
        mem.LockHistoryIdx = 0
        for i in range(MAX_LOCK_HISTORY):
            mem.LockHistoryEntries[i].Key = ""
            mem.LockHistoryEntries[i].SenderEmail = ""
            mem.LockHistoryEntries[i].AcquiredAt = 0
            mem.LockHistoryEntries[i].ReleasedAt = 0

    def GetCustomBehaviorWidgetData(self) -> CustomBehaviorWidgetData:
        mem = self._get_struct()
        result = CustomBehaviorWidgetData(
            is_enabled= mem.IsEnabled if hasattr(mem, "IsEnabled") else True,
            is_looting_enabled= mem.IsLootingEnabled if hasattr(mem, "IsLootingEnabled") else True,
            is_chesting_enabled= mem.IsChestingEnabled if hasattr(mem, "IsChestingEnabled") else True,
            is_following_enabled= mem.IsFollowingEnabled if hasattr(mem, "IsFollowingEnabled") else True,
            is_blessing_enabled= mem.IsBlessingEnabled if hasattr(mem, "IsBlessingEnabled") else True,
            is_inventory_enabled= mem.IsInventoryEnabled if hasattr(mem, "IsInventoryEnabled") else True,
            is_combat_enabled= mem.IsCombatEnabled if hasattr(mem, "IsCombatEnabled") else True,
            party_target_id= mem.PartyTargetId if hasattr(mem, "PartyTargetId") and mem.PartyTargetId != 0 else None,
            party_forced_state= mem.PartyForcedState if hasattr(mem, "PartyForcedState") and mem.PartyForcedState != 0 else None
        )
        # print(f"GetCustomBehaviorWidgetData: {result.is_enabled} {result.party_target_id} {result.party_forced_state}")

        return result

    def SetCustomBehaviorWidgetData(self, is_enabled:bool, is_combat_enabled:bool, is_looting_enabled:bool, is_chesting_enabled:bool, is_following_enabled:bool, is_blessing_enabled:bool, is_inventory_enabled:bool, party_target_id:int|None, party_forced_state:int|None):
        # print(f"SetCustomBehaviorWidgetData: {is_enabled}, {party_target_id}, {party_forced_state}")
        mem = self._get_struct()
        mem.IsEnabled = is_enabled
        mem.IsLootingEnabled = is_looting_enabled
        mem.IsChestingEnabled = is_chesting_enabled
        mem.IsFollowingEnabled = is_following_enabled
        mem.IsBlessingEnabled = is_blessing_enabled
        mem.IsInventoryEnabled = is_inventory_enabled
        mem.IsCombatEnabled = is_combat_enabled
        mem.PartyTargetId = party_target_id if party_target_id is not None else 0
        mem.PartyForcedState = party_forced_state if party_forced_state is not None else 0

    # --- Backwards-compatible delegates to shared_lock ---
    def GetSharedLockManager(self) -> SharedLockManager:
        return self.__shared_lock

    # --- Party Following Config Methods ---
    def GetFollowingConfig(self) -> PartyFollowingConfigStruct:
        """Get the party following configuration from shared memory"""
        mem = self._get_struct()
        return mem.FollowingConfig

    def SetFollowingConfig(self, config: PartyFollowingConfigStruct):
        """Set the party following configuration in shared memory"""
        mem = self._get_struct()
        mem.FollowingConfig = config