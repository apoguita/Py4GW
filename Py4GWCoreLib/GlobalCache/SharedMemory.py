
from Py4GWCoreLib import ConsoleLog, Party, Player, Agent, Effects, ThrottledTimer, Range
from ..native_src.context.WorldContext import TitleStruct as NAtiveTitleStruct

from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.py4gwcorelib_src import Utils
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from ..native_src.internals.types import Vec3f

#region rework
from typing import Optional
from ctypes import sizeof, c_float
import ctypes
import math
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
    SHMEM_INTENT_SWEEP_INTERVAL_MS,
)

from .shared_memory_src.SharedMessageStruct import SharedMessageStruct
from .shared_memory_src.HeroAIOptionStruct import HeroAIOptionStruct
from .shared_memory_src.AgentDataStruct import AgentDataStruct
from .shared_memory_src.AccountStruct import AccountStruct
from .shared_memory_src.AllAccounts import AllAccounts
from HeroAI.follow.leader_publish import FollowFormationPublisher
from ..py4gwcorelib_src.FrameCache import frame_cache


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
            self.follow_publisher = FollowFormationPublisher(self)
        
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
        self._intent_sweep_timer = ThrottledTimer(SHMEM_INTENT_SWEEP_INTERVAL_MS)
        self._initialized = True

    def PublishFormationFollowPoints(self):
        self.follow_publisher.publish()
        
    #Base Methods
    def GetBaseTimestamp(self):
        return Py4GW.Game.get_tick_count64()
    
    @frame_cache(category="SharedMemory", source_lib="GetAllAccounts")
    def GetAllAccounts(self) -> AllAccounts:
        if self.shm.buf is None:
            raise RuntimeError("Shared memory is not initialized.")

        return AllAccounts.from_buffer(self.shm.buf)

    
    @frame_cache(category="SharedMemory", source_lib="GetAccountData")
    def GetAccountData(self, index: int) -> AccountStruct:
        return self.GetAllAccounts().GetAccountData(index)
            
    #region Messaging
    @frame_cache(category="SharedMemory", source_lib="GetAllMessages")
    def GetAllMessages(self) -> list[tuple[int, SharedMessageStruct]]:
        """Get all messages in shared memory with their index."""
        return self.GetAllAccounts().GetAllMessages()
    
    @frame_cache(category="SharedMemory", source_lib="GetInbox")
    def GetInbox(self, index: int) -> SharedMessageStruct:
        return self.GetAllAccounts().GetInbox(index)


    #region Find and Get Slot Methods
    @frame_cache(category="SharedMemory", source_lib="GetSlotByEmail")
    def GetSlotByEmail(self, account_email: str) -> int:
        return self.GetAllAccounts().GetVisibleSlotByEmail(account_email)

    @frame_cache(category="SharedMemory", source_lib="IsAccountIsolated")
    def IsAccountIsolated(self, account_email: str) -> bool:
        return self.GetAllAccounts().IsAccountIsolated(account_email)

    def SetAccountIsolationByEmail(self, account_email: str, isolated: bool) -> bool:
        return self.GetAllAccounts().SetAccountIsolationByEmail(account_email, isolated)

    def SetAccountIsolatedByEmail(self, account_email: str) -> bool:
        return self.GetAllAccounts().SetAccountIsolatedByEmail(account_email)

    def RemoveAccountIsolationByEmail(self, account_email: str) -> bool:
        return self.GetAllAccounts().RemoveAccountIsolationByEmail(account_email)

    def SetAccountGroupByEmail(self, account_email: str, group_id: int) -> bool:
        return self.GetAllAccounts().SetAccountGroupByEmail(account_email, group_id)

    @frame_cache(category="SharedMemory", source_lib="GetAccountGroupByEmail")
    def GetAccountGroupByEmail(self, account_email: str) -> int:
        return self.GetAllAccounts().GetAccountGroupByEmail(account_email)

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
    @frame_cache(category="SharedMemory", source_lib="GetNumActiveSlots")
    def GetNumActiveSlots(self) -> int:
        """Get the number of active slots in shared memory."""
        return self.GetAllAccounts().GetNumActiveSlots()
        
    @frame_cache(category="SharedMemory", source_lib="GetAllActiveSlotsData")
    def GetAllActiveSlotsData(self) -> list[AccountStruct]:
        """Get all active slot data, ordered by PartyID, PartyPosition, PlayerLoginNumber, CharacterName."""
        return self.GetAllAccounts().GetAllActiveSlotsData()
    
    @frame_cache(category="SharedMemory", source_lib="GetAllActivePlayers")
    def GetAllAccountData(self, sort_results: bool = True, include_isolated: bool = False) -> list[AccountStruct]:
        """Get active account-player data. Sorted by default for backward compatibility."""
        return self.GetAllAccounts().GetAllActivePlayers(sort_results=sort_results, include_isolated=include_isolated)
    
    @frame_cache(category="SharedMemory", source_lib="GetNumActivePlayers")
    def GetNumActivePlayers(self) -> int:
        """Get the number of active players in shared memory."""
        return self.GetAllAccounts().GetNumActivePlayers()
    
    @frame_cache(category="SharedMemory", source_lib="GetAccountDataFromEmail")
    def GetAccountDataFromEmail(self, account_email: str, log : bool = False) -> AccountStruct | None:
        """Get player data for the account with the given email."""
        if not account_email: return None
        acc = self.GetAllAccounts().GetAccountDataFromEmail(account_email)
        if acc: return acc
        ConsoleLog(SHMEM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
        return None
     
    @frame_cache(category="SharedMemory", source_lib="GetAccountDataFromPartyNumber")
    def GetAccountDataFromPartyNumber(self, party_number: int, log : bool = False) -> AccountStruct | None:
        """Get player data for the account with the given party number."""
        acc = self.GetAllAccounts().GetAccountDataFromPartyNumber(party_number)
        if acc: return acc
        ConsoleLog(SHMEM_MODULE_NAME, f"Party number {party_number} not found.", Py4GW.Console.MessageType.Error, log = False)
        return None
    
    @frame_cache(category="SharedMemory", source_lib="AccountHasEffect")
    def AccountHasEffect(self, account_email: str, effect_id: int) -> bool:
        """Check if the account with the given email has the specified effect."""
        return self.GetAllAccounts().AccountHasEffect(account_email, effect_id)

    #region HeroAI
    @frame_cache(category="SharedMemory", source_lib="GetAllAccountHeroAIOptions")
    def GetAllAccountHeroAIOptions(self) -> list[HeroAIOptionStruct]:
        """Get HeroAI options for all accounts."""
        return self.GetAllAccounts().GetAllAccountHeroAIOptions()

    @frame_cache(category="SharedMemory", source_lib="GetAllActiveAccountHeroAIPairs")
    def GetAllActiveAccountHeroAIPairs(self, sort_results: bool = True) -> list[tuple[AccountStruct, HeroAIOptionStruct]]:
        """Get active account-player data and HeroAI options in one pass."""
        return self.GetAllAccounts().GetAllActiveAccountHeroAIPairs(sort_results=sort_results)
    
    @frame_cache(category="SharedMemory", source_lib="GetHeroAIOptionsFromEmail")
    def GetHeroAIOptionsFromEmail(self, account_email: str) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given email."""
        return self.GetAllAccounts().GetHeroAIOptionsFromEmail(account_email)
       
    @frame_cache(category="SharedMemory", source_lib="GetHeroAIOptionsByPartyNumber") 
    def GetHeroAIOptionsByPartyNumber(self, party_number: int) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given party number."""
        return self.GetAllAccounts().GetHeroAIOptionsByPartyNumber(party_number)
        
    def SetHeroAIOptionsByEmail(self, account_email: str, options: HeroAIOptionStruct):
        """Set HeroAI options for the account with the given email."""
        return self.GetAllAccounts().SetHeroAIOptionsByEmail(account_email, options)
    

    def SetHeroAIPropertyByEmail(self, account_email: str, property_name: str, value):
        """Set a specific HeroAI property for the account with the given email."""
        return self.GetAllAccounts().SetHeroAIPropertyByEmail(account_email, property_name, value)
    
    @frame_cache(category="SharedMemory", source_lib="GetMapsFromPlayers")
    def GetMapsFromPlayers(self):
        """Get a list of unique maps from all active players."""
        return self.GetAllAccounts().GetMapsFromPlayers()
    
    @frame_cache(category="SharedMemory", source_lib="GetPartiesFromMaps")
    def GetPartiesFromMaps(self, map_id: int, map_region: int, map_district: int, map_language: int):
        """
        Get a list of unique PartyIDs for players in the specified map/region/district.
        """
        return self.GetAllAccounts().GetPartiesFromMaps(map_id, map_region, map_district, map_language)

    @frame_cache(category="SharedMemory", source_lib="GetPlayersFromParty")
    def GetPlayersFromParty(self, party_id: int, map_id: int, map_region: int, map_district: int, map_language: int):
        """Get a list of players in a specific party on a specific map."""
        return self.GetAllAccounts().GetPlayersFromParty(party_id, map_id, map_region, map_district, map_language)
    
    @frame_cache(category="SharedMemory", source_lib="GetHeroesFromPlayers")
    def GetHeroesFromPlayers(self, owner_player_id: int) -> list[AccountStruct]:
        """Get a list of heroes owned by the specified player."""
        return self.GetAllAccounts().GetHeroesFromPlayers(owner_player_id)
    
    @frame_cache(category="SharedMemory", source_lib="GetNumHeroesFromPlayers")
    def GetNumHeroesFromPlayers(self, owner_player_id: int) -> int:
        """Get the number of heroes owned by the specified player."""
        return self.GetAllAccounts().GetNumHeroesFromPlayers(owner_player_id)
    
    @frame_cache(category="SharedMemory", source_lib="GetPetsFromPlayers")
    def GetPetsFromPlayers(self, owner_agent_id: int) -> list[AccountStruct]:
        """Get a list of pets owned by the specified player."""
        return self.GetAllAccounts().GetPetsFromPlayers(owner_agent_id)
    
    @frame_cache(category="SharedMemory", source_lib="GetNumPetsFromPlayers")
    def GetNumPetsFromPlayers(self, owner_agent_id: int) -> int:
        """Get the number of pets owned by the specified player."""
        return self.GetAllAccounts().GetNumPetsFromPlayers(owner_agent_id)

    #region Messaging
    def SendMessage(self, sender_email: str, receiver_email: str, command: SharedCommandType, params: tuple = (0.0, 0.0, 0.0, 0.0), ExtraData: tuple = ()) -> int:
        """Send a message to another player. Returns the message index or -1 on failure."""
        return self.GetAllAccounts().SendMessage(sender_email, receiver_email, command, params, ExtraData)

    @frame_cache(category="SharedMemory", source_lib="GetNextMessage")
    def GetNextMessage(self, account_email: str) -> tuple[int, SharedMessageStruct | None]:
        """Read the next message for the given account.
        Returns the raw SharedMessage.
        """
        return self.GetAllAccounts().GetNextMessage(account_email)

    @frame_cache(category="SharedMemory", source_lib="PreviewNextMessage")
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

    #region Whiteboard (cross-hero cast-intent)
    def PostIntent(
        self,
        owner_email: str,
        skill_id: int,
        target_agent_id: int,
        expires_at_tick: int,
        isolation_group_id: int | None = None,
    ) -> int:
        """Claim a (skill_id, target_agent_id) slot on the whiteboard."""
        return self.GetAllAccounts().PostIntent(
            owner_email, skill_id, target_agent_id, expires_at_tick, isolation_group_id
        )

    def PostLock(
        self,
        owner_email: str,
        kind_id: int,
        key_id: int,
        target_id: int,
        expires_at_tick: int,
        isolation_group_id: int | None = None,
        lock_mode: int = 1,
        max_holders: int = 1,
        reentry_policy: int = 1,
        claim_strength: int = 1,
    ) -> int:
        """Claim a generic expiring whiteboard lock slot."""
        return self.GetAllAccounts().PostLock(
            owner_email,
            kind_id,
            key_id,
            target_id,
            expires_at_tick,
            isolation_group_id,
            lock_mode,
            max_holders,
            reentry_policy,
            claim_strength,
        )

    def ClearIntentsByOwner(self, owner_email: str) -> int:
        """Zero every intent slot whose OwnerEmail matches."""
        return self.GetAllAccounts().ClearIntentsByOwner(owner_email)

    @frame_cache(category="SharedMemory", source_lib="IsIntentClaimed")
    def IsIntentClaimed(
        self,
        skill_id: int,
        target_agent_id: int,
        group_id: int,
        exclude_email: str,
        now_tick: int,
    ) -> bool:
        """True iff another account in the same group holds an unexpired claim."""
        return self.GetAllAccounts().IsIntentClaimed(
            skill_id, target_agent_id, group_id, exclude_email, now_tick
        )

    @frame_cache(category="SharedMemory", source_lib="IsLockBlocked")
    def IsLockBlocked(
        self,
        kind_id: int,
        key_id: int,
        target_id: int,
        group_id: int,
        exclude_email: str,
        now_tick: int,
        lock_mode: int = 1,
        max_holders: int = 1,
        reentry_policy: int = 1,
        claim_strength: int = 1,
    ) -> bool:
        """True when matching unexpired whiteboard locks should block this caller."""
        return self.GetAllAccounts().IsLockBlocked(
            kind_id,
            key_id,
            target_id,
            group_id,
            exclude_email,
            now_tick,
            lock_mode,
            max_holders,
            reentry_policy,
            claim_strength,
        )

    @frame_cache(category="SharedMemory", source_lib="CountLocks")
    def CountLocks(
        self,
        kind_id: int,
        key_id: int,
        target_id: int,
        group_id: int,
        exclude_email: str,
        now_tick: int,
        reentry_policy: int = 1,
        claim_strength: int = 1,
    ) -> int:
        """Count matching unexpired whiteboard locks."""
        return self.GetAllAccounts().CountLocks(
            kind_id,
            key_id,
            target_id,
            group_id,
            exclude_email,
            now_tick,
            reentry_policy,
            claim_strength,
        )

    @frame_cache(category="SharedMemory", source_lib="IsLockSatisfied")
    def IsLockSatisfied(
        self,
        kind_id: int,
        key_id: int,
        target_id: int,
        group_id: int,
        exclude_email: str,
        now_tick: int,
        required_holders: int,
        claim_strength: int = 1,
    ) -> bool:
        """Barrier helper: True when enough matching unexpired locks exist."""
        return self.GetAllAccounts().IsLockSatisfied(
            kind_id,
            key_id,
            target_id,
            group_id,
            exclude_email,
            now_tick,
            required_holders,
            claim_strength,
        )

    def SweepExpiredIntents(self, now_tick: int) -> int:
        """Compact pass — zero expired slots."""
        return self.GetAllAccounts().SweepExpiredIntents(now_tick)

    @frame_cache(category="SharedMemory", source_lib="GetAllIntents")
    def GetAllIntents(self):
        """Debug/probe helper: list of (index, IntentStruct) for active slots."""
        return self.GetAllAccounts().GetAllIntents()

    #region Callback
    def update_callback(self):
        """Callback function to update shared memory data."""
        self.SetPlayerData(Player.GetAccountEmail())
        self.PublishFormationFollowPoints()
        if self._hero_update_timer.IsExpired():
            self.SetHeroesData()
            self._hero_update_timer.Reset()
        if self._pet_update_timer.IsExpired():
            self.SetPetData()
            self._pet_update_timer.Reset()
        if self._intent_sweep_timer.IsExpired():
            self._intent_sweep_timer.Reset()
            now = Py4GW.Game.get_tick_count64()
            # Inline sweep; the ThrottledTimer above already rate-limits
            # and iterating 64 slots is cheap. Bypasses the WHITEBOARD_SWEEP
            # ActionQueue since no code in this repo drains named queues
            # automatically, which would dead-letter the sweep.
            self.SweepExpiredIntents(now)
        
        
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
