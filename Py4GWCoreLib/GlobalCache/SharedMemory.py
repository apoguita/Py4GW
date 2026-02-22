
from Py4GWCoreLib import ConsoleLog, Party, Player, Agent, Effects, ThrottledTimer
from ..native_src.context.WorldContext import TitleStruct as NAtiveTitleStruct

from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.py4gwcorelib_src import Utils
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from ..native_src.internals.types import Vec2f, Vec3f

#region rework
from typing import Optional
from ctypes import sizeof, c_float
import ctypes
from multiprocessing import shared_memory
from PyParty import HeroPartyMember, PetInfo
from Py4GWCoreLib import SharedCommandType
import Py4GW
import PyQuest
from .shared_memory_src.Globals import (
    SHMEM_MODULE_NAME, 
    SHMEM_SHARED_MEMORY_FILE_NAME,
    
    SHMEM_MAX_PLAYERS,
    SHMEM_MAX_EMAIL_LEN,
    SHMEM_MAX_CHAR_LEN,
    SHMEM_MAX_AVAILABLE_CHARS,
    SHMEM_MAX_NUMBER_OF_BUFFS,
    SHMEM_MAX_NUMBER_OF_SKILLS,
    SHMEM_MAX_NUMBER_OF_ATTRIBUTES,
    SHMEM_MAX_TITLES,
    SHMEM_MAX_QUESTS,

    MISSION_BITMAP_ENTRIES,
    SKILL_BITMAP_ENTRIES,
    SHMEM_SUBSCRIBE_TIMEOUT_MILLISECONDS,
    SHMEM_HERO_UPDATE_THROTTLE_MS,
    SHMEM_PET_UPDATE_THROTTLE_MS,
)

from .shared_memory_src.SharedMessageStruct import SharedMessageStruct
from .shared_memory_src.HeroAIOptionStruct import HeroAIOptionStruct
from .shared_memory_src.AgentDataStruct import AgentDataStruct
from .shared_memory_src.AccountStruct import AccountStruct
from .shared_memory_src.AllAccounts import AllAccounts

#region SharedMemoryManager    
class Py4GWSharedMemoryManager:
    _instance = None  # Singleton instance
    def __new__(cls, name=SHMEM_SHARED_MEMORY_FILE_NAME, num_players=SHMEM_MAX_PLAYERS):
        if cls._instance is None:
            cls._instance = super(Py4GWSharedMemoryManager, cls).__new__(cls)
            cls._instance._initialized = False  # Ensure __init__ runs only once
        return cls._instance
    
    def __init__(self, name=SHMEM_SHARED_MEMORY_FILE_NAME, max_num_players=SHMEM_MAX_PLAYERS):
        if not self._initialized:
            self.shm_name = name
            self.max_num_players = max_num_players
            self.size = sizeof(AllAccounts)
        
        # Create or attach shared memory
        try:
            self.shm = shared_memory.SharedMemory(name=self.shm_name)
            ConsoleLog(SHMEM_MODULE_NAME, "Attached to existing shared memory.", Py4GW.Console.MessageType.Info)
            
        except FileNotFoundError:
            self.shm = shared_memory.SharedMemory(name=self.shm_name, create=True, size=self.size)
            self.ResetAllData()  # Initialize all player data
            
            ConsoleLog(SHMEM_MODULE_NAME, "Shared memory area created.", Py4GW.Console.MessageType.Success)
            
        except BufferError:
            ConsoleLog(SHMEM_MODULE_NAME, "Shared memory area already exists but could not be attached.", Py4GW.Console.MessageType.Error)
            raise

        self._hero_update_timer = ThrottledTimer(SHMEM_HERO_UPDATE_THROTTLE_MS)
        self._pet_update_timer = ThrottledTimer(SHMEM_PET_UPDATE_THROTTLE_MS)
        self._initialized = True
        
    #Base Methods
    def GetBaseTimestamp(self):
        return Py4GW.Game.get_tick_count64()
    
    def GetAllAccounts(self) -> AllAccounts:
        if self.shm.buf is None:
            raise RuntimeError("Shared memory is not initialized.")

        return AllAccounts.from_buffer(self.shm.buf)

    
    def GetAccountData(self, index: int) -> AccountStruct:
        return self.GetAllAccounts().GetAccountData(index)
            
    #region Messaging
    def GetAllMessages(self) -> list[tuple[int, SharedMessageStruct]]:
        """Get all messages in shared memory with their index."""
        return self.GetAllAccounts().GetAllMessages()
    
    def GetInbox(self, index: int) -> SharedMessageStruct:
        return self.GetAllAccounts().GetInbox(index)


    #region Find and Get Slot Methods
    def GetSlotByEmail(self, account_email: str) -> int:
        return self.GetAllAccounts().GetSlotByEmail(account_email)
    
    def GetHeroSlotByHeroData(self, hero_data:HeroPartyMember) -> int:
        """Find the index of the hero with the given ID."""
        return self.GetAllAccounts().GetHeroSlotByHeroData(hero_data)
    
    def GetPetSlotByPetData(self, pet_data:PetInfo) -> int:
        """Find the index of the pet with the given ID."""
        return self.GetAllAccounts().GetPetSlotByPetData(pet_data)

    #region Reset    
    def ResetAllData(self):
        """Reset all player data in shared memory."""
        for i in range(self.max_num_players):
            self.ResetPlayerData(i)
            self.ResetHeroAIData(i)
    
    def ResetAllPlayersData(self):
        """Reset data for all player slots."""
        for i in range(self.max_num_players):
            self.ResetPlayerData(i)
            
    def ResetPlayerData(self, index):
        """Reset data for a specific player."""
        if 0 <= index < self.max_num_players:
            player : AccountStruct = self.GetAccountData(index)
            player.reset()  # Reset all player fields to default values
            player.LastUpdated = self.GetBaseTimestamp()
           
    def ResetHeroAIData(self, index): 
            option:HeroAIOptionStruct = self.GetAllAccounts().HeroAIOptions[index]
            option.reset()

       
    #region Set
    def SetPlayerData(self, account_email: str):
        """Set player data for the account with the given email."""  
        if not account_email:
            return    
        self.GetAllAccounts().SetPlayerData(account_email)


    #Hero Data
    def SetHeroesData(self):
        """Set data for all heroes in the given list."""
        self.GetAllAccounts().SetHeroesData()
            

 
    #Pet Data      
    def SetPetData(self):
        """Set data for all pets in the given list."""
        self.GetAllAccounts().SetPetData()

     
    #region GetAllActivePlayers   
    def GetNumActiveSlots(self) -> int:
        """Get the number of active slots in shared memory."""
        return self.GetAllAccounts().GetNumActiveSlots()
        
    def GetAllActiveSlotsData(self) -> list[AccountStruct]:
        """Get all active slot data, ordered by PartyID, PartyPosition, PlayerLoginNumber, CharacterName."""
        return self.GetAllAccounts().GetAllActiveSlotsData()
    
    def GetAllAccountData(self) -> list[AccountStruct]:
        """Get all player data, ordered by PartyID, PartyPosition, PlayerLoginNumber, CharacterName."""
        return self.GetAllAccounts().GetAllActivePlayers()
    
    def GetNumActivePlayers(self) -> int:
        """Get the number of active players in shared memory."""
        return self.GetAllAccounts().GetNumActivePlayers()
    
    def GetAccountDataFromEmail(self, account_email: str, log : bool = False) -> AccountStruct | None:
        """Get player data for the account with the given email."""
        if not account_email: return None
        acc = self.GetAllAccounts().GetAccountDataFromEmail(account_email)
        if acc: return acc
        ConsoleLog(SHMEM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
        return None
     
    def GetAccountDataFromPartyNumber(self, party_number: int, log : bool = False) -> AccountStruct | None:
        """Get player data for the account with the given party number."""
        acc = self.GetAllAccounts().GetAccountDataFromPartyNumber(party_number)
        if acc: return acc
        ConsoleLog(SHMEM_MODULE_NAME, f"Party number {party_number} not found.", Py4GW.Console.MessageType.Error, log = False)
        return None
    
    def AccountHasEffect(self, account_email: str, effect_id: int) -> bool:
        """Check if the account with the given email has the specified effect."""
        return self.GetAllAccounts().AccountHasEffect(account_email, effect_id)
    
    #region HeroAI
    def GetAllAccountHeroAIOptions(self) -> list[HeroAIOptionStruct]:
        """Get HeroAI options for all accounts."""
        return self.GetAllAccounts().GetAllAccountHeroAIOptions()
    
    def GetHeroAIOptionsFromEmail(self, account_email: str) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given email."""
        return self.GetAllAccounts().GetHeroAIOptionsFromEmail(account_email)
        
    def GetHeroAIOptionsByPartyNumber(self, party_number: int) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given party number."""
        return self.GetAllAccounts().GetHeroAIOptionsByPartyNumber(party_number)
        
    def SetHeroAIOptionsByEmail(self, account_email: str, options: HeroAIOptionStruct):
        """Set HeroAI options for the account with the given email."""
        return self.GetAllAccounts().SetHeroAIOptionsByEmail(account_email, options)
    
    def SetHeroAIPropertyByEmail(self, account_email: str, property_name: str, value):
        """Set a specific HeroAI property for the account with the given email."""
        return self.GetAllAccounts().SetHeroAIPropertyByEmail(account_email, property_name, value)
    
    def GetMapsFromPlayers(self):
        """Get a list of unique maps from all active players."""
        return self.GetAllAccounts().GetMapsFromPlayers()
    
    def GetPartiesFromMaps(self, map_id: int, map_region: int, map_district: int, map_language: int):
        """
        Get a list of unique PartyIDs for players in the specified map/region/district.
        """
        return self.GetAllAccounts().GetPartiesFromMaps(map_id, map_region, map_district, map_language)

    def GetPlayersFromParty(self, party_id: int, map_id: int, map_region: int, map_district: int, map_language: int):
        """Get a list of players in a specific party on a specific map."""
        return self.GetAllAccounts().GetPlayersFromParty(party_id, map_id, map_region, map_district, map_language)
    
    def GetHeroesFromPlayers(self, owner_player_id: int) -> list[AccountStruct]:
        """Get a list of heroes owned by the specified player."""
        return self.GetAllAccounts().GetHeroesFromPlayers(owner_player_id)
    
    def GetNumHeroesFromPlayers(self, owner_player_id: int) -> int:
        """Get the number of heroes owned by the specified player."""
        return self.GetAllAccounts().GetNumHeroesFromPlayers(owner_player_id)
    
    def GetPetsFromPlayers(self, owner_agent_id: int) -> list[AccountStruct]:
        """Get a list of pets owned by the specified player."""
        return self.GetAllAccounts().GetPetsFromPlayers(owner_agent_id)
    
    def GetNumPetsFromPlayers(self, owner_agent_id: int) -> int:
        """Get the number of pets owned by the specified player."""
        return self.GetAllAccounts().GetNumPetsFromPlayers(owner_agent_id)

    #region Messaging
    def SendMessage(self, sender_email: str, receiver_email: str, command: SharedCommandType, params: tuple = (0.0, 0.0, 0.0, 0.0), ExtraData: tuple = ()) -> int:
        """Send a message to another player. Returns the message index or -1 on failure."""
        return self.GetAllAccounts().SendMessage(sender_email, receiver_email, command, params, ExtraData)

    def GetNextMessage(self, account_email: str) -> tuple[int, SharedMessageStruct | None]:
        """Read the next message for the given account.
        Returns the raw SharedMessage.
        """
        return self.GetAllAccounts().GetNextMessage(account_email)

    def PreviewNextMessage(self, account_email: str, include_running: bool = True) -> tuple[int, SharedMessageStruct | None]:
        """Preview the next message for the given account.
        If include_running is True, will also return a running message.
        Ensures ExtraData is returned as tuple[str] using existing helpers.
        """
        return self.GetAllAccounts().PreviewNextMessage(account_email, include_running)

    def MarkMessageAsRunning(self, account_email: str, message_index: int):
        """Mark a specific message as running."""
        return self.GetAllAccounts().MarkMessageAsRunning(account_email, message_index)
            
    def MarkMessageAsFinished(self, account_email: str, message_index: int):
        """Mark a specific message as finished."""
        return self.GetAllAccounts().MarkMessageAsFinished(account_email, message_index)
    
    #region Callback
    def update_callback(self):
        """Callback function to update shared memory data."""
        self.SetPlayerData(Player.GetAccountEmail())
        if self._hero_update_timer.IsExpired():
            self.SetHeroesData()
            self._hero_update_timer.Reset()
        if self._pet_update_timer.IsExpired():
            self.SetPetData()
            self._pet_update_timer.Reset()
        
        
    @staticmethod
    def enable():
        import PyCallback
        Callback_name = "SharedMemory.Update"
        PyCallback.PyCallback.Register(
            Callback_name,
            PyCallback.Phase.Data,
            Py4GWSharedMemoryManager().update_callback,
            priority=99,
            context=PyCallback.Context.Draw
        )


Py4GWSharedMemoryManager.enable()
