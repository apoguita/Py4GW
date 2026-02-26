
from Py4GWCoreLib import ConsoleLog, Party, Player, Agent, Effects, ThrottledTimer, Range
from Py4GWCoreLib.IniManager import IniManager
from ..native_src.context.WorldContext import TitleStruct as NAtiveTitleStruct

from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.py4gwcorelib_src import Utils
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from ..native_src.internals.types import Vec2f, Vec3f

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
            self._follow_formations_ini_key = ""
            self._follow_settings_ini_key = ""
            self._follow_runtime_ini_key = ""
            self._follow_ini_reload_timer = ThrottledTimer(1000)
            self._follow_ini_vars_registered = False
            self._follow_selected_id_cache = ""
            self._follow_points_cache: list[tuple[float, float]] = []
            self._follow_move_threshold_default = float(Range.Area.value)
            self._follow_move_threshold_combat = float(Range.Touch.value)
            self._follow_move_threshold_flagged = 0.0
            self._follow_map_signature = None
            self._follow_hold_until_leader_moves = False
            self._follow_leader_entry_pos: tuple[float, float] | None = None
        
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

    #region Follow Formation Publisher (leader-side shared-memory producer)
    def _ensure_global_ini_key_strict(self, path: str, filename: str) -> str:
        im = IniManager()
        key = im.ensure_global_key(path, filename)
        if not key:
            return ""
        try:
            node = im._get_node(key)
            if node and getattr(node, "is_global", False):
                return key
            if hasattr(im, "_handlers") and key in im._handlers:
                del im._handlers[key]
            key = im.ensure_global_key(path, filename)
        except Exception:
            pass
        return key

    def _ensure_follow_ini_keys(self):
        if not self._follow_formations_ini_key:
            self._follow_formations_ini_key = self._ensure_global_ini_key_strict("HeroAI", "FollowModule_Formations.ini")
        if not self._follow_settings_ini_key:
            self._follow_settings_ini_key = self._ensure_global_ini_key_strict("HeroAI", "FollowModule_Settings.ini")
        if not self._follow_runtime_ini_key:
            self._follow_runtime_ini_key = self._ensure_global_ini_key_strict("HeroAI", "FollowRuntime.ini")
        if self._follow_ini_vars_registered:
            return
        im = IniManager()
        if self._follow_settings_ini_key:
            im.add_str(self._follow_settings_ini_key, "selected_id", "Formations", "selected_id", "")
            im.add_str(self._follow_settings_ini_key, "selected", "Formations", "selected", "")
        if self._follow_formations_ini_key:
            im.add_int(self._follow_formations_ini_key, "formation_count", "Formations", "count", 0)
            # Pre-register point readers for any possible selected formation ID section.
            # We register lazily per active section below; this just marks setup complete.
        if self._follow_runtime_ini_key:
            im.add_float(self._follow_runtime_ini_key, "follow_move_threshold_default", "FollowRuntime", "follow_move_threshold_default", float(Range.Area.value))
            im.add_float(self._follow_runtime_ini_key, "follow_move_threshold_combat", "FollowRuntime", "follow_move_threshold_combat", float(Range.Touch.value))
            im.add_float(self._follow_runtime_ini_key, "follow_move_threshold_flagged", "FollowRuntime", "follow_move_threshold_flagged", 0.0)
        self._follow_ini_vars_registered = True

    def _ini_reload_vars(self, key: str):
        if not key:
            return
        im = IniManager()
        try:
            im.reload(key)
            node = im._get_node(key)
            if node:
                node.vars_loaded = False
            im.load_once(key)
        except Exception:
            pass

    def _ensure_follow_section_var_defs(self, section: str):
        if not self._follow_formations_ini_key or not section:
            return
        im = IniManager()
        sec_tag = section.replace(":", "_")
        im.add_int(self._follow_formations_ini_key, f"{sec_tag}_point_count", section, "point_count", 0)
        for i in range(11):
            im.add_float(self._follow_formations_ini_key, f"{sec_tag}_p{i}_x", section, f"p{i}_x", 0.0)
            im.add_float(self._follow_formations_ini_key, f"{sec_tag}_p{i}_y", section, f"p{i}_y", 0.0)

    def _reload_follow_points_from_ini(self):
        self._ensure_follow_ini_keys()
        if not self._follow_formations_ini_key or not self._follow_settings_ini_key:
            return

        im = IniManager()
        self._ini_reload_vars(self._follow_settings_ini_key)
        self._ini_reload_vars(self._follow_formations_ini_key)
        self._ini_reload_vars(self._follow_runtime_ini_key)
        if self._follow_runtime_ini_key:
            self._follow_move_threshold_default = max(
                0.0,
                float(im.getFloat(self._follow_runtime_ini_key, "follow_move_threshold_default", float(Range.Area.value), section="FollowRuntime"))
            )
            self._follow_move_threshold_combat = max(
                0.0,
                float(im.getFloat(self._follow_runtime_ini_key, "follow_move_threshold_combat", float(Range.Touch.value), section="FollowRuntime"))
            )
            self._follow_move_threshold_flagged = max(
                0.0,
                float(im.getFloat(self._follow_runtime_ini_key, "follow_move_threshold_flagged", 0.0, section="FollowRuntime"))
            )

        sec_formations = "Formations"
        selected_id = str(im.getStr(self._follow_settings_ini_key, "selected_id", "", section=sec_formations) or "").strip()
        if not selected_id:
            selected_name = str(im.getStr(self._follow_settings_ini_key, "selected", "", section=sec_formations) or "").strip()
            count = max(0, im.getInt(self._follow_formations_ini_key, "formation_count", 0, section=sec_formations))
            for i in range(count):
                if str(im.read_key(self._follow_formations_ini_key, sec_formations, f"name_{i}", "") or "").strip() == selected_name:
                    selected_id = str(im.read_key(self._follow_formations_ini_key, sec_formations, f"id_{i}", "") or "").strip()
                    break

        if not selected_id:
            self._follow_selected_id_cache = ""
            self._follow_points_cache = []
            return

        sec = f"FormationId:{selected_id}"
        if not im.read_key(self._follow_formations_ini_key, sec, "name", ""):
            # Backward compatibility with name-keyed sections if needed.
            count = max(0, im.read_int(self._follow_formations_ini_key, sec_formations, "count", 0))
            for i in range(count):
                fid = str(im.read_key(self._follow_formations_ini_key, sec_formations, f"id_{i}", "") or "").strip()
                if fid == selected_id:
                    name = str(im.read_key(self._follow_formations_ini_key, sec_formations, f"name_{i}", "") or "").strip()
                    if name:
                        sec = f"Formation:{name}"
                    break

        self._ensure_follow_section_var_defs(sec)
        self._ini_reload_vars(self._follow_formations_ini_key)
        sec_tag = sec.replace(":", "_")
        point_count = max(0, min(11, im.getInt(self._follow_formations_ini_key, f"{sec_tag}_point_count", 0, section=sec)))
        pts: list[tuple[float, float]] = []
        for i in range(point_count):
            x = float(im.getFloat(self._follow_formations_ini_key, f"{sec_tag}_p{i}_x", 0.0, section=sec))
            y = float(im.getFloat(self._follow_formations_ini_key, f"{sec_tag}_p{i}_y", 0.0, section=sec))
            pts.append((x, y))

        self._follow_selected_id_cache = selected_id
        self._follow_points_cache = pts

    def _get_follow_points(self) -> list[tuple[float, float]]:
        if self._follow_ini_reload_timer.IsExpired():
            self._reload_follow_points_from_ini()
            self._follow_ini_reload_timer.Reset()
        return self._follow_points_cache

    @staticmethod
    def _rotate_local_to_world(local_x: float, local_y: float, facing_angle: float) -> tuple[float, float]:
        # Match FollowingModule 3D preview / original local-coordinate convention.
        angle = float(facing_angle) - (math.pi / 2.0)
        c = -math.cos(angle)
        s = -math.sin(angle)
        rx = (local_x * c) - (local_y * s)
        ry = (local_x * s) + (local_y * c)
        return (rx, ry)

    @staticmethod
    def _same_party_and_map(a: AccountStruct, b: AccountStruct) -> bool:
        return (
            a.AgentPartyData.PartyID == b.AgentPartyData.PartyID and
            a.AgentData.Map.MapID == b.AgentData.Map.MapID and
            a.AgentData.Map.Region == b.AgentData.Map.Region and
            a.AgentData.Map.District == b.AgentData.Map.District and
            a.AgentData.Map.Language == b.AgentData.Map.Language
        )

    @staticmethod
    def _is_nonzero_vec2(v: Vec2f) -> bool:
        return abs(float(v.x)) > 0.001 or abs(float(v.y)) > 0.001

    def PublishFormationFollowPoints(self):
        # Producer runs only on leader client; followers consume FollowPos in HeroAI runtime.
        try:
            if not Party.IsPartyLoaded():
                return
            leader_agent_id = Party.GetPartyLeaderID()
            if not Agent.IsValid(leader_agent_id):
                return
            if Player.GetAgentID() != leader_agent_id:
                return
        except Exception:
            return

        account_email = Player.GetAccountEmail()
        if not account_email:
            return

        all_accounts = self.GetAllAccounts()
        leader_index = all_accounts.GetSlotByEmail(account_email)
        if leader_index < 0:
            return

        leader_account = all_accounts.AccountData[leader_index]
        leader_options = all_accounts.HeroAIOptions[leader_index]
        if not leader_account.IsSlotActive or not leader_account.IsAccount:
            return

        # Never publish active follow coordinates in outposts/loading screens.
        if (not Map.IsMapReady()) or Map.IsMapLoading() or (not Map.IsExplorable()):
            self._follow_map_signature = None
            self._follow_hold_until_leader_moves = False
            self._follow_leader_entry_pos = None
            for i in range(self.max_num_players):
                acc = all_accounts.AccountData[i]
                if not (acc.IsSlotActive and acc.IsAccount):
                    continue
                if not self._same_party_and_map(leader_account, acc):
                    continue
                opts = all_accounts.HeroAIOptions[i]
                opts.FollowPos.x = 0.0
                opts.FollowPos.y = 0.0
                opts.FollowPos.z = 0.0
                opts.FollowOffset.x = 0.0
                opts.FollowOffset.y = 0.0
                opts.FollowMoveThreshold = -1.0
                opts.FollowMoveThresholdCombat = -1.0
            return

        points = self._get_follow_points()
        leader_x, leader_y = Player.GetXY()
        leader_zplane = int(Agent.GetZPlane(leader_agent_id))
        leader_facing = Agent.GetRotationAngle(leader_agent_id)

        map_signature = (
            int(leader_account.AgentData.Map.MapID),
            int(leader_account.AgentData.Map.Region),
            int(leader_account.AgentData.Map.District),
            int(leader_account.AgentData.Map.Language),
            int(leader_account.AgentPartyData.PartyID),
        )
        if self._follow_map_signature != map_signature:
            self._follow_map_signature = map_signature
            self._follow_hold_until_leader_moves = True
            self._follow_leader_entry_pos = (float(leader_x), float(leader_y))

        if self._follow_hold_until_leader_moves and self._follow_leader_entry_pos is not None:
            entry_x, entry_y = self._follow_leader_entry_pos
            if Utils.Distance((leader_x, leader_y), (entry_x, entry_y)) > 1.0:
                self._follow_hold_until_leader_moves = False

        for i in range(self.max_num_players):
            acc = all_accounts.AccountData[i]
            if not (acc.IsSlotActive and acc.IsAccount):
                continue
            if not self._same_party_and_map(leader_account, acc):
                continue

            party_pos = int(acc.AgentPartyData.PartyPosition)
            opts = all_accounts.HeroAIOptions[i]

            # Skip leader slot but clear stale local offset for consistency.
            if party_pos <= 0:
                opts.FollowOffset.x = 0.0
                opts.FollowOffset.y = 0.0
                opts.FollowMoveThreshold = -1.0
                opts.FollowMoveThresholdCombat = -1.0
                continue

            slot_index = party_pos - 1
            if slot_index < 0 or slot_index >= len(points):
                opts.FollowOffset.x = 0.0
                opts.FollowOffset.y = 0.0
                if self._follow_hold_until_leader_moves:
                    opts.FollowPos.x = float(acc.AgentData.Pos.x)
                    opts.FollowPos.y = float(acc.AgentData.Pos.y)
                    opts.FollowPos.z = float(leader_zplane)
                else:
                    opts.FollowPos.x = 0.0
                    opts.FollowPos.y = 0.0
                    opts.FollowPos.z = 0.0
                opts.FollowMoveThreshold = -1.0
                opts.FollowMoveThresholdCombat = -1.0
                continue

            local_x, local_y = points[slot_index]
            opts.FollowOffset.x = float(local_x)
            opts.FollowOffset.y = float(local_y)
            opts.FollowMoveThreshold = float(self._follow_move_threshold_default)
            opts.FollowMoveThresholdCombat = float(self._follow_move_threshold_combat)

            if self._follow_hold_until_leader_moves:
                opts.FollowPos.x = float(acc.AgentData.Pos.x)
                opts.FollowPos.y = float(acc.AgentData.Pos.y)
                opts.FollowPos.z = float(leader_zplane)
                # Hold in place until the leader actually moves after map load.
                continue

            # Precedence: personal flag -> all-flag -> leader follow anchor.
            if bool(opts.IsFlagged) and self._is_nonzero_vec2(opts.FlagPos):
                opts.FollowPos.x = float(opts.FlagPos.x)
                opts.FollowPos.y = float(opts.FlagPos.y)
                opts.FollowPos.z = float(leader_zplane)
                opts.FollowMoveThreshold = float(self._follow_move_threshold_flagged)
                opts.FollowMoveThresholdCombat = float(self._follow_move_threshold_flagged)
                continue

            if bool(leader_options.IsFlagged) and self._is_nonzero_vec2(leader_options.AllFlag):
                anchor_x = float(leader_options.AllFlag.x)
                anchor_y = float(leader_options.AllFlag.y)
                facing = float(leader_options.FlagFacingAngle)
                opts.FollowMoveThreshold = float(self._follow_move_threshold_flagged)
                opts.FollowMoveThresholdCombat = float(self._follow_move_threshold_flagged)
            else:
                anchor_x = float(leader_x)
                anchor_y = float(leader_y)
                facing = float(leader_facing)

            rx, ry = self._rotate_local_to_world(local_x, local_y, facing)
            opts.FollowPos.x = anchor_x + rx
            opts.FollowPos.y = anchor_y + ry
            opts.FollowPos.z = float(leader_zplane)
        
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
    
    def GetAllAccountData(self, sort_results: bool = True) -> list[AccountStruct]:
        """Get active account-player data. Sorted by default for backward compatibility."""
        return self.GetAllAccounts().GetAllActivePlayers(sort_results=sort_results)
    
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

    def GetAllActiveAccountHeroAIPairs(self, sort_results: bool = True) -> list[tuple[AccountStruct, HeroAIOptionStruct]]:
        """Get active account-player data and HeroAI options in one pass."""
        return self.GetAllAccounts().GetAllActiveAccountHeroAIPairs(sort_results=sort_results)
    
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
        self.PublishFormationFollowPoints()
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
