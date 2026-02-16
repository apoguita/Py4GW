from ctypes import Structure

from .Globals import (
    SHMEM_MAX_PLAYERS,
)

from .SharedMessageStruct import SharedMessageStruct
from .HeroAIOptionStruct import HeroAIOptionStruct
from .AccountStruct import AccountStruct




#region AllAccounts 
class AllAccounts(Structure):
    _pack_ = 1
    _fields_ = [
        ("AccountData", AccountStruct * SHMEM_MAX_PLAYERS),
        ("Inbox", SharedMessageStruct * SHMEM_MAX_PLAYERS),  # Messages for each player
        ("HeroAIOptions", HeroAIOptionStruct * SHMEM_MAX_PLAYERS),  # Game options for HeroAI
    ]
    
    # Type hints for IntelliSense
    AccountData: list["AccountStruct"]
    Inbox: list["SharedMessageStruct"]
    HeroAIOptions: list[HeroAIOptionStruct]
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        for i in range(SHMEM_MAX_PLAYERS):
            self.AccountData[i].reset()
            self.Inbox[i].reset()
            self.HeroAIOptions[i].reset()