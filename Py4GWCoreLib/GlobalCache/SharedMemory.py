
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
    SHMEM_SUBSCRIBE_TIMEOUT_MILLISECONDS
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
        index = self.GetSlotByEmail(account_email)
        if index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, f"No slot found for account {account_email}.", Py4GW.Console.MessageType.Warning)
            return
        
        account = self.GetAccountData(index)
        account.from_context(account_email, index)


    #Hero Data
    def SetHeroesData(self):
        """Set data for all heroes in the given list."""
        owner_id = Player.GetAgentID()
        for hero_data in Party.GetHeroes():
            agent_from_login = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
            if agent_from_login != owner_id:
                continue
            self.SetHeroData(hero_data)
            
    def SetHeroData(self,hero_data:HeroPartyMember):
        """Set player data for the account with the given email."""     
      
        index = self.GetHeroSlotByHeroData(hero_data)
        if index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, f"No slot found for hero {hero_data.hero_id.GetName()} (ID: {hero_data.hero_id.GetID()}).", Py4GW.Console.MessageType.Warning)
            return
        
        account = self.GetAccountData(index)
        account.from_hero_context(hero_data, index)
         
 
    #Pet Data      
    def SetPetData(self):
        owner_agent_id = Player.GetAgentID()
        pet_info = Party.Pets.GetPetInfo(owner_agent_id)
        # if not pet_info or pet_info.agent_id == 102298104:
        if not pet_info or (not pet_info.agent_id in Party.GetOthers()):
            return
        
        index = self.GetPetSlotByPetData(pet_info)
        if index == -1:
            ConsoleLog(SHMEM_MODULE_NAME, f"No slot found for pet {pet_info.agent_id}.", Py4GW.Console.MessageType.Warning)
            return
        
        account = self.GetAccountData(index)
        account.from_pet_context(pet_info, index)

         
    #region GetAllActivePlayers   
    def GetAllActivePlayers(self) -> list[AccountStruct]:
        """Get all active players in shared memory."""
        players : list[AccountStruct] = []
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self.GetAllAccounts()._is_slot_active(i) and player.IsAccount:
                players.append(player)
        return players
    
    def GetNumActivePlayers(self) -> int:
        """Get the number of active players in shared memory."""
        count = 0
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self.GetAllAccounts()._is_slot_active(i) and player.IsAccount:
                count += 1
        return count
    
    def GetNumActiveSlots(self) -> int:
        """Get the number of active slots in shared memory."""
        count = 0
        for i in range(self.max_num_players):
            if self.GetAllAccounts()._is_slot_active(i):
                count += 1
        return count
        
    def GetAllActiveSlotsData(self) -> list[AccountStruct]:
        """Get all active slot data, ordered by PartyID, PartyPosition, PlayerLoginNumber, CharacterName."""
        accs : list[AccountStruct] = []
        for i in range(self.max_num_players):
            acc = self.GetAllAccounts().AccountData[i]
            if self.GetAllAccounts()._is_slot_active(i):
                accs.append(acc)

        # Sort by PartyID, then PartyPosition, then PlayerLoginNumber, then CharacterName
        accs.sort(key=lambda p: (
            p.AgentData.Map.MapID,
            p.AgentData.Map.Region,
            p.AgentData.Map.District,
            p.AgentData.Map.Language,
            p.AgentPartyData.PartyID,
            p.AgentPartyData.PartyPosition,
            p.AgentData.LoginNumber,
            p.AgentData.CharacterName
        ))

        return accs
    
    def GetAllAccountData(self) -> list[AccountStruct]:
        """Get all player data, ordered by PartyID, PartyPosition, PlayerLoginNumber, CharacterName."""
        players : list[AccountStruct] = []
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self.GetAllAccounts()._is_slot_active(i) and player.IsAccount:
                players.append(player)

        # Sort by PartyID, then PartyPosition, then PlayerLoginNumber, then CharacterName
        players.sort(key=lambda p: (
            p.AgentData.Map.MapID,
            p.AgentData.Map.Region,
            p.AgentData.Map.District,
            p.AgentData.Map.Language,
            p.AgentPartyData.PartyID,
            p.AgentPartyData.PartyPosition,
            p.AgentData.LoginNumber,
            p.AgentData.CharacterName
        ))

        return players
    
    def GetAccountDataFromEmail(self, account_email: str, log : bool = False) -> AccountStruct | None:
        """Get player data for the account with the given email."""
        if not account_email:
            return None
        index = self.GetSlotByEmail(account_email)
        if index != -1:
            return self.GetAccountData(index)
        else:
            ConsoleLog(SHMEM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
            return None
     
    def GetAccountDataFromPartyNumber(self, party_number: int, log : bool = False) -> AccountStruct | None:
        """Get player data for the account with the given party number."""
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self.GetAllAccounts()._is_slot_active(i) and player.AgentPartyData.PartyPosition == party_number:
                return player
        
        ConsoleLog(SHMEM_MODULE_NAME, f"Party number {party_number} not found.", Py4GW.Console.MessageType.Error, log = False)
        return None
    
    def HasEffect(self, account_email: str, effect_id: int) -> bool:
        """Check if the account with the given email has the specified effect."""
        if effect_id == 0:
            return False
        
        player = self.GetAccountDataFromEmail(account_email)
        if player:
            for buff in player.AgentData.Buffs.Buffs:
                if buff.SkillId == effect_id:
                    return True
        return False
    
    def GetAllAccountHeroAIOptions(self) -> list[HeroAIOptionStruct]:
        """Get HeroAI options for all accounts."""
        options = []
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self.GetAllAccounts()._is_slot_active(i) and player.IsAccount:
                options.append(self.GetAllAccounts().HeroAIOptions[i])
        return options
        
    def GetHeroAIOptions(self, account_email: str) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given email."""
        if not account_email:
            return None
        index = self.GetSlotByEmail(account_email)
        if index != -1:
            return self.GetAllAccounts().HeroAIOptions[index]
        else:
            ConsoleLog(SHMEM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
            return None
        
    def GetGerHeroAIOptionsByPartyNumber(self, party_number: int) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given party number."""
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self.GetAllAccounts()._is_slot_active(i) and player.AgentPartyData.PartyPosition == party_number:
                return self.GetAllAccounts().HeroAIOptions[i]
        return None    
        
        
    def SetHeroAIOptions(self, account_email: str, options: HeroAIOptionStruct):
        """Set HeroAI options for the account with the given email."""
        if not account_email:
            return
        index = self.GetSlotByEmail(account_email)
        if index != -1:
            self.GetAllAccounts().HeroAIOptions[index] = options
        else:
            ConsoleLog(SHMEM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
    
    def SetHeroAIProperty(self, account_email: str, property_name: str, value):
        """Set a specific HeroAI property for the account with the given email."""
        if not account_email:
            return
        index = self.GetSlotByEmail(account_email)
        if index != -1:
            options = self.GetAllAccounts().HeroAIOptions[index]
            
            if property_name.startswith("Skill_"):
                skill_index = int(property_name.split("_")[1])
                if 0 <= skill_index < SHMEM_MAX_NUMBER_OF_SKILLS:
                    options.Skills[skill_index] = value
                else:
                    ConsoleLog(SHMEM_MODULE_NAME, f"Invalid skill index: {skill_index}.", Py4GW.Console.MessageType.Error)
                return
            
            if hasattr(options, property_name):
                setattr(options, property_name, value)
            else:
                ConsoleLog(SHMEM_MODULE_NAME, f"Property {property_name} does not exist in HeroAIOptions.", Py4GW.Console.MessageType.Error)
        else:
            ConsoleLog(SHMEM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
    
    def GetMapsFromPlayers(self):
        """Get a list of unique maps from all active players."""
        maps = set()
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self.GetAllAccounts()._is_slot_active(i) and player.IsAccount:
                maps.add((player.AgentData.Map.MapID, player.AgentData.Map.Region, player.AgentData.Map.District, player.AgentData.Map.Language))
        return list(maps)
    
    def GetPartiesFromMaps(self, map_id: int, map_region: int, map_district: int, map_language: int):
        """
        Get a list of unique PartyIDs for players in the specified map/region/district.
        """
        parties = set()
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if (self.GetAllAccounts()._is_slot_active(i) and player.IsAccount and
                player.AgentData.Map.MapID == map_id and
                player.AgentData.Map.Region == map_region and
                player.AgentData.Map.District == map_district and
                player.AgentData.Map.Language == map_language):
                parties.add(player.AgentPartyData.PartyID)
        return list(parties)

    
    def GetPlayersFromParty(self, party_id: int, map_id: int, map_region: int, map_district: int, map_language: int):
        """Get a list of players in a specific party on a specific map."""
        players = []
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if (self.GetAllAccounts()._is_slot_active(i) and player.IsAccount and
                player.AgentData.Map.MapID == map_id and
                player.AgentData.Map.Region == map_region and
                player.AgentData.Map.District == map_district and
                player.AgentData.Map.Language == map_language and
                player.AgentPartyData.PartyID == party_id):
                players.append(player)
        return players
    
    def GetHeroesFromPlayers(self, owner_player_id: int) -> list[AccountStruct]:
        """Get a list of heroes owned by the specified player."""
        heroes : list[AccountStruct] = []
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if (self.GetAllAccounts()._is_slot_active(i) and player.IsHero and
                player.AgentData.OwnerAgentID == owner_player_id):
                heroes.append(player)
        return heroes
    
    def GetNumHeroesFromPlayers(self, owner_player_id: int) -> int:
        """Get the number of heroes owned by the specified player."""
        return self.GetHeroesFromPlayers(owner_player_id).__len__()
    
    def GetPetsFromPlayers(self, owner_agent_id: int) -> list[AccountStruct]:
        """Get a list of pets owned by the specified player."""
        pets : list[AccountStruct] = []
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if (self.GetAllAccounts()._is_slot_active(i) and player.IsPet and
                player.AgentData.OwnerAgentID == owner_agent_id):
                pets.append(player)
        return pets
    
    def GetNumPetsFromPlayers(self, owner_agent_id: int) -> int:
        """Get the number of pets owned by the specified player."""
        return self.GetPetsFromPlayers(owner_agent_id).__len__()

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

            
    