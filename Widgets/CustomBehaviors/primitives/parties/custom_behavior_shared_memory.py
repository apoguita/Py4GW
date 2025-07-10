from ctypes import Structure, c_uint, c_float, c_bool, c_wchar
from multiprocessing import shared_memory
from ctypes import sizeof
from datetime import datetime, timezone
from datetime import datetime, timezone
import time
from threading import Lock

from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.constants import DEBUG

class CustomBehaviorWidgetStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("IsEnabled", c_bool),
        ("PartyTargetId", c_uint),
        ("PartyForcedState", c_uint),
    ]

class CustomBehaviorWidgetData:
    def __init__(self, is_enabled: bool, party_target_id: int | None, party_forced_state: int | None):
        self.is_enabled: bool = is_enabled
        self.party_target_id: int | None = party_target_id
        self.party_forced_state: int | None = party_forced_state

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
            except FileNotFoundError:
                self.shm = shared_memory.SharedMemory(name=self.shm_name, create=True, size=self.size)
                if DEBUG: print(f"Shared memory area '{self.shm_name}' created.")

            # Attach the shared memory structure
            # self.game_struct = AllAccounts.from_buffer(self.shm.buf)
            self.__reset_all_data()  # Initialize all player data

            self._initialized = True

    def __get_struct(self) -> CustomBehaviorWidgetStruct:
        return CustomBehaviorWidgetStruct.from_buffer(self.shm.buf)

    def __reset_all_data(self):
        mem = self.__get_struct()
        mem.IsEnabled = True
        mem.PartyTargetId = 0
        mem.PartyForcedState = 0

    def GetCustomBehaviorWidgetData(self) -> CustomBehaviorWidgetData:
        mem = self.__get_struct()
        result = CustomBehaviorWidgetData(
            is_enabled= mem.IsEnabled if hasattr(mem, "IsEnabled") else True,
            party_target_id= mem.PartyTargetId if hasattr(mem, "PartyTargetId") and mem.PartyTargetId != 0 else None,
            party_forced_state= mem.PartyForcedState if hasattr(mem, "PartyForcedState") and mem.PartyForcedState != 0 else None
        )
        # print(f"GetCustomBehaviorWidgetData: {result.is_enabled} {result.party_target_id} {result.party_forced_state}")

        return result

    def SetCustomBehaviorWidgetData(self, is_enabled:bool, party_target_id:int|None, party_forced_state:int|None):
        # print(f"SetCustomBehaviorWidgetData: {is_enabled}, {party_target_id}, {party_forced_state}")
        mem = self.__get_struct()
        mem.IsEnabled = is_enabled
        mem.PartyTargetId = party_target_id if party_target_id is not None else 0
        mem.PartyForcedState = party_forced_state if party_forced_state is not None else 0