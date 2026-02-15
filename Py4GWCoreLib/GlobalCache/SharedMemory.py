import Py4GW
import PyQuest
from PyParty import HeroPartyMember, PetInfo
from PyEffects import BuffType, EffectType
from typing import Optional, Tuple, List
from Py4GWCoreLib import ConsoleLog, Map, Party, Player, Agent, Effects, SharedCommandType, Skill, ThrottledTimer
from Py4GWCoreLib.enums import FactionType
from ctypes import Array, Structure, addressof, c_int, c_uint, c_float, c_bool, c_wchar, memmove
from multiprocessing import shared_memory
import ctypes
from ctypes import sizeof
from datetime import datetime, timezone
from ..native_src.context.AgentContext import AgentStruct
from ..native_src.context.WorldContext import TitleStruct as NAtiveTitleStruct
from ..native_src.internals.helpers import encoded_wstr_to_str

from Py4GWCoreLib.Skillbar import SkillBar
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.enums_src.GameData_enums import Attribute
from Py4GWCoreLib.py4gwcorelib_src import Utils
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from ..native_src.internals.helpers import encoded_wstr_to_str

SHMEM_MAX_NUM_PLAYERS = 64
SHMEM_MAX_EMAIL_LEN = 64
SHMEM_MAX_CHAR_LEN = 30
SHMEM_MAX_AVAILABLE_CHARS = 20
SHMEM_MAX_NUMBER_OF_BUFFS = 240
SMM_MODULE_NAME = "Py4GW - Shared Memory"
SHMEM_SHARED_MEMORY_FILE_NAME = "Py4GW_Shared_Mem"
SHMEM_ZERO_EPOCH = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
SHMEM_SUBSCRIBE_TIMEOUT_MILLISECONDS = 500 # milliseconds

SHMEM_NUMBER_OF_SKILLS = 8
SHMEM_NUMBER_OF_ATTRIBUTES = len(Attribute) #5 primary + 3 secondary + 1 from of Profession Mod

INT32_MAX = 2**31 - 1
INT32_MIN = -2**31
UINT32_MAX = 2**32 - 1
FLOAT32_MAX = 3.4028235e+38
FLOAT32_MIN = 1.17549435e-38

MISSION_FLAG_ENTRIES = 25 #each entry is a bitmap of a mission flags (32 bits each)
SKILL_FLAG_ENTRIES = 108 #each entry is a bitmap of a skill flags (32 bits each)


#region rework
from typing import Optional, cast
from ctypes import Array, Structure, addressof, c_int, c_uint, c_float, c_bool, c_wchar, memmove, c_uint64, sizeof
import ctypes
from multiprocessing import shared_memory
from PyParty import HeroPartyMember, PetInfo
from PyEffects import BuffType, EffectType
from Py4GWCoreLib import SharedCommandType
from ..native_src.internals.types import Vec2f, Vec3f
import Py4GW
import PyQuest
#import ctypes
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
)

from .shared_memory_src.RankStruct import RankStruct
from .shared_memory_src.FactionStruct import FactionStruct
from .shared_memory_src.TitlesStruct import TitlesStruct
from .shared_memory_src.QuestLogStruct import QuestLogStruct
from .shared_memory_src.ExperienceStruct import ExperienceStruct
from .shared_memory_src.MissionDataStruct import MissionDataStruct
from .shared_memory_src.UnlockedSkillsStruct import UnlockedSkillsStruct
from .shared_memory_src.AvailableCharacterStruct import AvailableCharacterStruct, AvailableCharacterUnitStruct
from .shared_memory_src.SharedMessageStruct import SharedMessageStruct
from .shared_memory_src.HeroAIOptionStruct import HeroAIOptionStruct
from .shared_memory_src.AttributesStruct import AttributesStruct, AttributeUnitStruct
from .shared_memory_src.BuffStruct import BuffStruct, BuffUnitStruct
from .shared_memory_src.SkillbarStruct import SkillbarStruct
from .shared_memory_src.KeyStruct import KeyStruct
from .shared_memory_src.AgentPartyStruct import AgentPartyStruct
from .shared_memory_src.MapStruct import MapStruct
from .shared_memory_src.EnergyStruct import EnergyStruct
from .shared_memory_src.HealthStruct import HealthStruct


#region AgentData
class AgentDataStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Map", MapStruct),
        ("Skillbar", SkillbarStruct),
        ("Attributes", AttributesStruct),
        ("BuffData", BuffStruct),
        
        
        ("UUID", c_uint * 4),  # 128-bit UUID
        ("AgentID", c_uint),
        ("OwnerID", c_uint),
        ("TargetID", c_uint),
        ("ObservingID", c_uint),
        ("PlayerNumber", c_uint),
        ("Profession", c_uint * 2),  # Primary and Secondary Profession
        ("Level", c_uint),
        ("Energy", c_float),
        ("MaxEnergy", c_float),
        ("EnergyPips", c_int),
        ("Health", c_float),
        ("MaxHealth", c_float),
        ("HealthPips", c_int),
        ("LoginNumber", c_uint),
        ("DaggerStatus", c_uint),
        ("WeaponType", c_uint),
        ("WeaponItemType", c_uint),
        ("OffhandItemType", c_uint),
        ("Overcast", c_float),
        ("WeaponAttackSpeed", c_float),
        ("AttackSpeedModifier", c_float),
        ("EffectsMask", c_uint),  #mask of active effects
        ("VisualEffectsMask", c_uint),  #mask of active visual effects
        ("TypeMap", c_uint),  #mask of type and subtype flags
        ("ModelState", c_uint),
        ("AnimationSpeed", c_float),
        ("AnimationCode", c_uint),
        ("AnimationID", c_uint),
        ("XYZ", c_float * 3),
        ("ZPlane", c_int),
        ("RotationAngle", c_float),
        ("VelocityVector", c_float * 2),  
        
    ]
    
    # Type hints for IntelliSense
    Map: MapStruct
    Skillbar: SkillbarStruct
    Attributes: AttributesStruct
    BuffData: BuffStruct
    
    UUID: list[int]
    AgentID: int
    OwnerID: int
    TargetID: int
    ObservingID: int
    PlayerNumber: int
    Profession: list[int]
    Level: int
    Energy: float
    MaxEnergy: float
    EnergyPips: int
    Health: float
    MaxHealth: float
    HealthPips: int
    LoginNumber: int
    DaggerStatus: int
    WeaponType: int
    WeaponItemType: int
    OffhandItemType: int
    Overcast: float
    WeaponAttackSpeed: float
    AttackSpeedModifier: float
    EffectsMask: int
    VisualEffectsMask: int
    TypeMap: int
    ModelState: int
    AnimationSpeed: float
    AnimationCode: int
    AnimationID: int
    XYZ: list[float]
    ZPlane: int
    RotationAngle: float
    VelocityVector: list[float]

    @property
    def Is_Bleeding(self) -> bool:
        return (self.EffectsMask & 0x0001) != 0
    @property
    def Is_Conditioned(self) -> bool:
        return (self.EffectsMask & 0x0002) != 0
    @property
    def Is_Crippled(self) -> bool:
        return (self.EffectsMask & 0x000A) == 0xA
    @property
    def Is_Dead(self) -> bool:
        return (self.EffectsMask & 0x0010) != 0
    @property
    def Is_DeepWounded(self) -> bool:
        return (self.EffectsMask & 0x0020) != 0
    @property
    def Is_Poisoned(self) -> bool:
        return (self.EffectsMask & 0x0040) != 0
    @property
    def Is_Enchanted(self) -> bool:
        return (self.EffectsMask & 0x0080) != 0
    @property
    def Is_DegenHexed(self) -> bool:
        return (self.EffectsMask & 0x0400) != 0
    @property
    def Is_Hexed(self) -> bool:
        return (self.EffectsMask & 0x0800) != 0
    @property
    def Is_WeaponSpelled(self) -> bool:
        return (self.EffectsMask & 0x8000) != 0
    @property
    def Is_InCombatStance(self) -> bool:
        return (self.TypeMap & 0x000001) != 0
    @property
    def Has_Quest(self) -> bool:
        return (self.TypeMap & 0x000002) != 0
    @property
    def Is_DeadByTypeMap(self) -> bool:
        return (self.TypeMap & 0x000008) != 0
    @property
    def Is_Female(self) -> bool:
        return (self.TypeMap & 0x000200) != 0
    @property
    def Has_BossGlow(self) -> bool:
        return (self.TypeMap & 0x000400) != 0
    @property
    def Is_HidingCape(self) -> bool:
        return (self.TypeMap & 0x001000) != 0 
    @property
    def Can_Be_Viewed_In_Party_Window(self) -> bool:
        return (self.TypeMap & 0x20000) != 0
    @property
    def Is_Spawned(self) -> bool:   
        return (self.TypeMap & 0x040000) != 0
    @property
    def Is_Being_Observed(self) -> bool:
        return (self.TypeMap & 0x400000) != 0
    @property
    def Is_Knocked_Down(self) -> bool:
        return (self.ModelState == 1104)
    @property
    def Is_Moving(self) -> bool:
        return (self.ModelState == 12 or self.ModelState == 76 or self.ModelState == 204)
    @property
    def Is_Attacking(self) -> bool:
        return (self.ModelState == 96 or self.ModelState == 1088 or self.ModelState == 1120)
    @property
    def Is_Casting(self) -> bool:
        return (self.ModelState == 65 or self.ModelState == 581)
    @property
    def Is_Idle(self) -> bool:
        return (self.ModelState == 68 or self.ModelState == 64 or self.ModelState == 100)
    @property
    def Is_Alive(self) -> bool:
        return not self.Is_Dead and self.Health > 0.0
    @property 
    def Is_Player(self) -> bool:
        return self.LoginNumber != 0
    @property
    def Is_NPC(self) -> bool:
        return self.LoginNumber == 0  
    
    def reset(self) -> None:
        """Reset all fields to zero or default values."""
        for i in range(4):
            self.UUID[i] = 0
        self.AgentID = 0
        self.OwnerID = 0
        self.TargetID = 0
        self.ObservingID = 0
        self.PlayerNumber = 0
        for i in range(2):
            self.Profession[i] = 0
        self.Level = 0
        self.Energy = 0.0
        self.MaxEnergy = 0.0
        self.EnergyPips = 0
        self.Health = 0.0
        self.MaxHealth = 0.0
        self.HealthPips = 0
        self.LoginNumber = 0
        self.DaggerStatus = 0
        self.WeaponType = 0
        self.WeaponItemType = 0
        self.OffhandItemType = 0
        self.Overcast = 0.0
        self.WeaponAttackSpeed = 0.0
        self.AttackSpeedModifier = 0.0
        self.EffectsMask = 0
        self.VisualEffectsMask = 0
        self.TypeMap = 0
        self.ModelState = 0
        self.AnimationSpeed = 1.0
        self.AnimationCode = 0
        self.AnimationID = 0
        for i in range(3):
            self.XYZ[i] = 0.0
        self.ZPlane = 0
        self.RotationAngle = 0.0
        for i in range(2):
            self.VelocityVector[i] = 0.0  
    
#region AccountData

class AccountStruct(Structure):
    _pack_ = 1
    _fields_ = [

        ("CharacterName", c_wchar*SHMEM_MAX_CHAR_LEN),

        ("OwnerPlayerID", c_uint),
        ("HeroID", c_uint),
        ("MapID", c_uint),
        ("MapRegion", c_int),
        ("MapDistrict", c_uint),
        ("MapLanguage", c_int),
        ("PlayerID", c_uint),
        ("PlayerLevel", c_uint),
        ("PlayerProfession", c_uint * 2),  # Primary and Secondary Profession        
        ("PlayerMorale", c_uint),
        ("PlayerHP", c_float),
        ("PlayerMaxHP", c_float),
        ("PlayerHealthRegen", c_float),
        ("PlayerEnergy", c_float),
        ("PlayerMaxEnergy", c_float),
        ("PlayerEnergyRegen", c_float),
        ("PlayerPosX", c_float),
        ("PlayerPosY", c_float),
        ("PlayerPosZ", c_float),
        ("PlayerFacingAngle", c_float),
        ("PlayerTargetID", c_uint),
        ("PlayerLoginNumber", c_uint),
        ("PlayerIsTicked", c_bool),
        ("PartyID", c_uint),
        ("PartyPosition", c_uint),
        ("PlayerIsPartyLeader", c_bool),   
        ("PlayerBuffs", BuffUnitStruct * SHMEM_MAX_NUMBER_OF_BUFFS),  # Buff IDs 

        #Restructure Structures
        #--------------------
        ("Key", KeyStruct),  # KeyStruct for each player slot
        ("AccountEmail", c_wchar*SHMEM_MAX_EMAIL_LEN),
        ("AccountName", c_wchar*SHMEM_MAX_CHAR_LEN),
        
        ("AgentData", AgentDataStruct),
        ("AgentPartyData", AgentPartyStruct),
        ("RankData", RankStruct),
        ("FactionData", FactionStruct),
        ("TitlesData", TitlesStruct),
        ("QuestLog", QuestLogStruct),
        ("ExperienceData", ExperienceStruct),
        ("MissionData", MissionDataStruct),
        ("UnlockedSkills", UnlockedSkillsStruct),
        ("AvailableCharacters", AvailableCharacterStruct),    
        
        ("SlotNumber", c_uint),  # Slot number for the player
        ("IsSlotActive", c_bool),
        ("IsAccount", c_bool),
        ("IsHero", c_bool),
        ("IsPet", c_bool),
        ("IsNPC", c_bool),

        ("LastUpdated", c_uint),
    ]
    
    # Type hints for IntelliSense
    CharacterName: str

    OwnerPlayerID: int
    HeroID: int
    MapID: int
    MapRegion: int
    MapDistrict: int
    MapLanguage : int
    PlayerID: int
    PlayerLevel: int
    PlayerProfession: tuple[int, int]
    PlayerMorale: int
    PlayerHP: float
    PlayerMaxHP: float
    PlayerHealthRegen: float
    PlayerEnergy: float
    PlayerMaxEnergy: float
    PlayerEnergyRegen: float
    PlayerPosX: float
    PlayerPosY: float
    PlayerPosZ: float
    PlayerFacingAngle: float
    PlayerTargetID: int
    PlayerLoginNumber: int
    PlayerIsTicked: bool
    PartyID: int
    PartyPosition: int
    PlayerIsPartyLeader: bool
    
    PlayerBuffs: list[BuffUnitStruct]    
    
    #--------------------
    Key: KeyStruct
    AccountEmail: str
    AccountName: str
    
    AgentData: AgentDataStruct
    AgentPartyData: AgentPartyStruct
    
    RankData: RankStruct
    FactionData: FactionStruct
    TitlesData: TitlesStruct
    QuestLog: QuestLogStruct
    ExperienceData: ExperienceStruct
    MissionData: MissionDataStruct
    UnlockedSkills: UnlockedSkillsStruct
    AvailableCharacters: AvailableCharacterStruct
    
    SlotNumber: int
    IsSlotActive: bool
    IsAccount: bool
    IsHero: bool
    IsPet: bool
    IsNPC: bool

    LastUpdated: int
    
    def reset(self) -> None:
        """Reset all fields to zero or default values."""
        self.CharacterName = ""
        self.OwnerPlayerID = 0
        self.HeroID = 0
        self.MapID = 0
        self.MapRegion = 0
        self.MapDistrict = 0
        self.MapLanguage = 0
        self.PlayerID = 0
        self.PlayerLevel = 0
        self.PlayerProfession = (0, 0)
        self.PlayerMorale = 0
        self.PlayerHP = 0.0
        self.PlayerMaxHP = 0.0
        self.PlayerHealthRegen = 0.0
        self.PlayerEnergy = 0.0
        self.PlayerMaxEnergy = 0.0
        self.PlayerEnergyRegen = 0.0
        self.PlayerPosX = 0.0
        self.PlayerPosY = 0.0
        self.PlayerPosZ = 0.0
        self.PlayerFacingAngle = 0.0
        self.PlayerTargetID = 0
        self.PlayerLoginNumber = 0
        self.PlayerIsTicked = False
        self.PartyID = 0
        self.PartyPosition = 0
        self.PlayerIsPartyLeader = False
        
   
        for i in range(SHMEM_MAX_NUMBER_OF_BUFFS):
            self.PlayerBuffs[i].reset()
        
        
        #--------------------
        self.Key.reset()
        self.AccountEmail = ""
        self.AccountName = ""
        
        self.AgentData.reset()
        self.AgentPartyData.reset()
        
        self.RankData.reset()
        self.FactionData.reset()
        self.TitlesData.reset()
        self.QuestLog.reset()
        self.ExperienceData.reset()
        self.MissionData.reset()
        self.UnlockedSkills.reset()
        self.AvailableCharacters.reset()
        
        self.SlotNumber = 0
        self.IsSlotActive = False
        self.IsAccount = False
        self.IsHero = False
        self.IsPet = False
        self.IsNPC = False

        self.LastUpdated = 0
        
        

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
    
    
#region SharedMemoryManager    
class Py4GWSharedMemoryManager:
    _instance = None  # Singleton instance
    def __new__(cls, name=SHMEM_SHARED_MEMORY_FILE_NAME, num_players=SHMEM_MAX_NUM_PLAYERS):
        if cls._instance is None:
            cls._instance = super(Py4GWSharedMemoryManager, cls).__new__(cls)
            cls._instance._initialized = False  # Ensure __init__ runs only once
        return cls._instance
    
    def __init__(self, name=SHMEM_SHARED_MEMORY_FILE_NAME, max_num_players=SHMEM_MAX_NUM_PLAYERS):
        if not self._initialized:
            self.shm_name = name
            self.max_num_players = max_num_players
            self.size = sizeof(AllAccounts)
            self.party_instance = None #Party.party_instance()
            self.agent_instance: AgentStruct | None = None
            self.effects_instance = None
            self._title_instances: dict[int, NAtiveTitleStruct] = {}
            self.quest_instance = None
            self._quest_instances: dict[int, PyQuest.PyQuest] = {}
            self.throttle_timer_150 = ThrottledTimer(150)
            self.throttle_timer_63 = ThrottledTimer(63) # 4 frames at 15 FPS
        
        # Create or attach shared memory
        try:
            self.shm = shared_memory.SharedMemory(name=self.shm_name)
            ConsoleLog(SMM_MODULE_NAME, "Attached to existing shared memory.", Py4GW.Console.MessageType.Info)
            
        except FileNotFoundError:
            self.shm = shared_memory.SharedMemory(name=self.shm_name, create=True, size=self.size)
            self.ResetAllData()  # Initialize all player data
            
            ConsoleLog(SMM_MODULE_NAME, "Shared memory area created.", Py4GW.Console.MessageType.Success)
            
        except BufferError:
            ConsoleLog(SMM_MODULE_NAME, "Shared memory area already exists but could not be attached.", Py4GW.Console.MessageType.Error)
            raise

        # Attach the shared memory structure
        #self.game_struct = AllAccounts.from_buffer(self.shm.buf)
        
        self._initialized = True
    
    def GetAllAccounts(self) -> AllAccounts:
        if self.shm.buf is None:
            raise RuntimeError("Shared memory is not initialized.")
        return AllAccounts.from_buffer(self.shm.buf)
    
    def GetAccountData(self, index: int) -> AccountStruct:
        if index < 0 or index >= self.max_num_players:
            raise IndexError(f"Index {index} is out of bounds for max players {self.max_num_players}.")
        return self.GetAllAccounts().AccountData[index]
    
        
    def GetBaseTimestamp(self):
        # Return milliseconds since ZERO_EPOCH
        #return int((time.time() - SHMEM_ZERO_EPOCH) * 1000)
        return Utils.GetBaseTimestamp()
        
    def _str_to_c_wchar_array(self,value: str, maxlen: int) -> ctypes.Array:
        import ctypes as ct
        """Convert Python string to c_wchar array with maxlen (including terminator)."""
        arr = (ct.c_wchar * maxlen)()
        if value:
            s = value[:maxlen - 1]  # leave room for terminator
            for i, ch in enumerate(s):
                arr[i] = ch
            arr[len(s)] = '\0'
        return arr

    def _c_wchar_array_to_str(self,arr: ctypes.Array) -> str:
        """Convert c_wchar array back to Python str, stopping at null terminator."""
        return "".join(ch for ch in arr if ch != '\0').rstrip()

    def _get_account_email(self) -> str:
        if not Player.IsPlayerLoaded():
            return ""
        return Player.GetAccountEmail()
 
    def _pack_extra_data_for_sendmessage(self, extra_tuple, maxlen=128):
        out = []
        for i in range(4):
            val = extra_tuple[i] if i < len(extra_tuple) else ""
            out.append(self._str_to_c_wchar_array(str(val), maxlen))
        return tuple(out)
    
    def _is_slot_active(self, index: int) -> bool:
        """Check if the slot at the given index is active."""
        slot_active = self.GetAccountData(index).IsSlotActive    
        last_updated = self.GetAccountData(index).LastUpdated
        
        base_timestamp = self.GetBaseTimestamp()
        if slot_active and (base_timestamp - last_updated) < SHMEM_SUBSCRIBE_TIMEOUT_MILLISECONDS:
            return True
        return False

    #region Find and Get Slot Methods
    def FindAccount(self, account_email: str) -> int:
        if not account_email:
            return -1
        
        """Find the index of the account with the given email."""
        for i in range(self.max_num_players):
            if not self._is_slot_active(i):
                continue
            
            player = self.GetAllAccounts().AccountData[i]
            if self.GetAllAccounts().AccountData[i].AccountEmail == account_email and player.IsAccount:
                return i
            
        return -1
    
    def FindHero(self, hero_data:HeroPartyMember) -> int:
        """Find the index of the hero with the given ID."""
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            #if not player.IsSlotActive:
            if not self._is_slot_active(i):
                continue
            if player.IsHero and player.HeroID == hero_data.hero_id.GetID() and player.OwnerPlayerID == Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id):
                return i
        return -1
    
    def FindPet(self, pet_data:PetInfo) -> int:
        """Find the index of the pet with the given ID."""
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            #if not player.IsSlotActive:
            if not self._is_slot_active(i):
                continue
            if player.IsPet and player.PlayerID == pet_data.agent_id and player.OwnerPlayerID == pet_data.owner_agent_id:
                return i
        return -1

    def FindEmptySlot(self) -> int:
        """Find the first empty slot in shared memory."""        
        for clean_slot in [True, False]:
            for i in range(self.max_num_players):
                if not self._is_slot_active(i) and (not clean_slot or not self.GetAllAccounts().AccountData[i].IsAccount):
                    if not clean_slot:
                        ConsoleLog(SMM_MODULE_NAME, f"Reusing occupied slot {i} for new data.", Py4GW.Console.MessageType.Warning)
                    return i
            
        return -1
    
    def FindExistingAccountSlot(self, account_email: str = "") -> Optional[int]:
        """Find the first empty slot in shared memory."""
        if not account_email:
            return None
                    
        for i in range(self.max_num_players):
            existing_email = self.GetAllAccounts().AccountData[i].AccountEmail
            is_account = self.GetAllAccounts().AccountData[i].IsAccount
            
            if (existing_email == account_email and is_account):
                return i
            
        return None
    
    def GetAccountSlot(self, account_email: str) -> int:
        """Get the slot index for the account with the given email."""
        if not account_email:
            return -1
        
        index = self.FindAccount(account_email)
        
        if index == -1:
            existing_index = self.FindExistingAccountSlot(account_email)
            index = existing_index if existing_index is not None else self.FindEmptySlot()
            #ConsoleLog(SMM_MODULE_NAME, f"No active slot found for account email '{account_email}'." +
            #           (f"Reusing previously used slot {index}." if existing_index is not None else f"Using empty slot {index}."), Py4GW.Console.MessageType.Info)
            player = self.GetAccountData(index)
            player.IsSlotActive = True
            player.AccountEmail = account_email
            player.LastUpdated = self.GetBaseTimestamp()
        
        return index
    
    def GetHeroSlot(self, hero_data:HeroPartyMember) -> int:
        """Get the slot index for the hero with the given owner ID and hero ID."""
        index = self.FindHero(hero_data)
        if index == -1:
            index = self.FindEmptySlot()
            hero = self.GetAccountData(index)
            hero.IsSlotActive = True
            hero.IsHero = True
            hero.OwnerPlayerID = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
            hero.HeroID = hero_data.hero_id.GetID()
            hero.LastUpdated = self.GetBaseTimestamp()
        return index
    
    def GetPetSlot(self, pet_data:PetInfo) -> int:
        """Get the slot index for the pet with the given owner ID and agent ID."""
        index = self.FindPet(pet_data)
        if index == -1:
            index = self.FindEmptySlot()
            pet = self.GetAccountData(index)
            pet.IsSlotActive = True
            pet.IsPet = True
            pet.OwnerPlayerID = pet_data.owner_agent_id
            pet.PlayerID = pet_data.agent_id
            pet.LastUpdated = self.GetBaseTimestamp()
        return index
    
    #region Update Cache
    def _updatechache(self):
        """Update the shared memory cache."""
        if (Map.IsMapLoading() or 
            Map.IsInCinematic()):
            if self.party_instance is not None:
                self.party_instance.GetContext()
                
            self.agent_instance = None
            self.effects_instance = None
            
            return

            
        if self.party_instance is None:
            self.party_instance = Party.party_instance()
            
        if (self.agent_instance is not None):
            living_agent = self.agent_instance.GetAsAgentLiving()
            if (living_agent is None or
                living_agent.agent_id != Player.GetAgentID()):
                self.agent_instance = None
            
      
        if self.agent_instance is None:
            self.agent_instance = Agent.GetAgentByID(Player.GetAgentID())
            
        
        self.effects_instance = Effects.get_instance(Player.GetAgentID())
            
        if self.quest_instance is None and Player.IsPlayerLoaded():
            self.quest_instance = PyQuest.PyQuest()
            
        if self.throttle_timer_150.IsExpired():   
            self.throttle_timer_150.Reset()
            self.party_instance.GetContext()

            
            title_array = Player.GetTitleArray()
            for title_id in title_array:
                if title_id in self._title_instances:
                    continue
                title = Player.GetTitle(title_id)
                if title:
                    self._title_instances[title_id] = title

        if self.throttle_timer_63.IsExpired():
            self.throttle_timer_63.Reset()
            if self.agent_instance is not None:
                self.agent_instance = Agent.GetAgentByID(Player.GetAgentID())

    def GetLoginNumber(self):
        players = self.party_instance.players if self.party_instance else []
        agent_id = Player.GetAgentID() if Player.IsPlayerLoaded() else 0
        if len(players) > 0:
            for player in players:
                Pagent_id = self.party_instance.GetAgentIDByLoginNumber(player.login_number) if self.party_instance else 0
                if agent_id == Pagent_id:
                    return player.login_number
        return 0   

    def GetPartyNumber(self):
        login_number = self.GetLoginNumber()
        players = self.party_instance.players if self.party_instance else []

        for index, player in enumerate(players):
            if player.login_number == login_number:
                return index

        return -1
    
    #region Reset    
    def ResetAllData(self):
        """Reset all player data in shared memory."""
        for i in range(self.max_num_players):
            self.ResetPlayerData(i)
            self.ResetHeroAIData(i)
        
    def ResetPlayerData(self, index):
        """Reset data for a specific player."""
        if 0 <= index < self.max_num_players:
            player : AccountStruct = self.GetAccountData(index)
            player.reset()  # Reset all player fields to default values
            player.LastUpdated = self.GetBaseTimestamp()
           
    #region ResetHeroAIData 
    def ResetHeroAIData(self, index): 
            option:HeroAIOptionStruct = self.GetAllAccounts().HeroAIOptions[index]
            option.Following = True
            option.Avoidance = True
            option.Looting = True
            option.Targeting = True
            option.Combat = True
            for i in range(SHMEM_NUMBER_OF_SKILLS):
                option.Skills[i] = True 
            option.IsFlagged = False
            option.FlagPosX = 0.0
            option.FlagPosY = 0.0
            option.FlagFacingAngle = 0.0
       
    #region Set Player Data 
    def SetPlayerData(self, account_email: str):
        """Set player data for the account with the given email."""  
        def _set_buff_data(index):
            player : AccountStruct = self.GetAccountData(index)
            if self.effects_instance is None:
                return
            buffs = self.effects_instance.GetEffects() + self.effects_instance.GetBuffs()
            for j in range(SHMEM_MAX_NUMBER_OF_BUFFS):
                buff = buffs[j] if j < len(buffs) else None
                effect = buff if isinstance(buff, EffectType) else None
                upkeep = buff if isinstance(buff, BuffType) else None
                
                player.PlayerBuffs[j].SkillId = buff.skill_id if buff else 0
                player.PlayerBuffs[j].Type = 2 if effect else (1 if upkeep else 0)
                player.PlayerBuffs[j].Duration = effect.duration if effect else 0.0
                player.PlayerBuffs[j].TargetAgentID = upkeep.target_agent_id if upkeep else 0
                player.PlayerBuffs[j].Remaining = effect.time_remaining if effect else 0.0
                
                player.PlayerBuffs[j].SkillId = buff.skill_id if buff else 0
                player.PlayerBuffs[j].Type = 2 if effect else (1 if upkeep else 0)
                player.PlayerBuffs[j].Duration = effect.duration if effect else 0.0
                player.PlayerBuffs[j].TargetAgentID = upkeep.target_agent_id if upkeep else 0
                player.PlayerBuffs[j].Remaining = effect.time_remaining if effect else 0.0
                

        def _set_agent_data(index):
            agent_data : AgentDataStruct = self.GetAccountData(index).AgentData
            if self.agent_instance is None:
                return
            
            uuid = Player.GetPlayerUUID() if Player.IsPlayerLoaded() else (0,0,0,0)
            for i in range(4):
                agent_data.UUID[i] = uuid[i]
            
            agent_id = self.agent_instance.agent_id if self.agent_instance else 0
            agent_data.AgentID = agent_id
            agent_data.OwnerID = Agent.GetOwnerID(agent_id)
            agent_data.TargetID = Player.GetTargetID() if Player.IsPlayerLoaded() else 0
            agent_data.ObservingID = Player.GetObservingID() if Player.IsPlayerLoaded() else 0
            agent_data.PlayerNumber = Agent.GetPlayerNumber(agent_id)
            agent_data.Profession[0] = Agent.GetProfessionIDs(agent_id)[0]
            agent_data.Profession[1] = Agent.GetProfessionIDs(agent_id)[1]
            agent_data.Level = Agent.GetLevel(agent_id)
            agent_data.Energy = Agent.GetEnergy(agent_id)
            max_energy = Agent.GetMaxEnergy(agent_id)
            agent_data.MaxEnergy = max_energy
            energy_regen = Agent.GetEnergyRegen(agent_id)
            agent_data.EnergyPips = Utils.calculate_energy_pips(max_energy, energy_regen)
            health = Agent.GetHealth(agent_id)
            max_health = Agent.GetMaxHealth(agent_id)
            agent_data.Health = health
            agent_data.MaxHealth = max_health
            health_regen = Agent.GetHealthRegen(agent_id)
            agent_data.HealthPips = Utils.calculate_health_pips(max_health, health_regen)
            agent_data.LoginNumber = Agent.GetLoginNumber(agent_id)
            agent_data.DaggerStatus = Agent.GetDaggerStatus(agent_id)
            agent_data.WeaponType = Agent.GetWeaponType(agent_id)[0]
            agent_data.WeaponItemType = Agent.GetWeaponItemType(agent_id)
            agent_data.OffhandItemType = Agent.GetOffhandItemType(agent_id)
            agent_data.Overcast = Agent.GetOvercast(agent_id)
            agent_data.WeaponAttackSpeed = Agent.GetWeaponAttackSpeed(agent_id)
            agent_data.AttackSpeedModifier = Agent.GetAttackSpeedModifier(agent_id)
            agent_data.EffectsMask = Agent.GetAgentEffects(agent_id)
            agent_data.VisualEffectsMask = Agent.GetVisualEffects(agent_id)
            agent_data.TypeMap = Agent.GetTypeMap(agent_id)
            agent_data.ModelState = Agent.GetModelState(agent_id)
            agent_data.AnimationSpeed = Agent.GetAnimationSpeed(agent_id)
            agent_data.AnimationCode = Agent.GetAnimationCode(agent_id)
            agent_data.AnimationID = Agent.GetAnimationID(agent_id)
            agent_data.XYZ[0] = Agent.GetXYZ(agent_id)[0]
            agent_data.XYZ[1] = Agent.GetXYZ(agent_id)[1]
            agent_data.XYZ[2] = Agent.GetXYZ(agent_id)[2]
            agent_data.ZPlane = Agent.GetZPlane(agent_id)
            agent_data.RotationAngle = Agent.GetRotationAngle(agent_id)
            agent_data.VelocityVector[0] = Agent.GetVelocityXY(agent_id)[0]
            agent_data.VelocityVector[1] = Agent.GetVelocityXY(agent_id)[1]

        def _set_account_data(index):
            player : AccountStruct = self.GetAccountData(index)
            player.AccountName = Player.GetAccountName() if Player.IsPlayerLoaded() else ""
            player.CharacterName =self.party_instance.GetPlayerNameByLoginNumber(self.GetLoginNumber()) if self.party_instance else ""
            player.IsHero = False
            player.IsPet = False
            player.IsNPC = False
            player.OwnerPlayerID = 0
            player.HeroID = 0
            
        def _set_map_data(index):
            player : AccountStruct = self.GetAccountData(index)
            player.MapID = Map.GetMapID()
            player.MapRegion = Map.GetRegion()[0]
            player.MapDistrict = Map.GetDistrict()
            player.MapLanguage = Map.GetLanguage()[0]
            
        def _set_player_data(index):
            player : AccountStruct = self.GetAccountData(index)
            if not Player.IsPlayerLoaded():
                return

            if not self.party_instance:
                return
            
            login_number = self.GetLoginNumber()
            party_number = self.GetPartyNumber()
            playerx, playery, playerz = Agent.GetXYZ(Player.GetAgentID())

            player.PlayerID = Player.GetAgentID()
            
            player.PlayerLevel = Player.GetLevel()
            player.PlayerProfession = Agent.GetProfessionIDs(Player.GetAgentID())
            player.PlayerMorale = Player.GetMorale()
            player.PlayerHP = Agent.GetHealth(Player.GetAgentID())
            player.PlayerMaxHP = Agent.GetMaxHealth(Player.GetAgentID())
            player.PlayerHealthRegen = Agent.GetHealthRegen(Player.GetAgentID())
            player.PlayerEnergy = Agent.GetEnergy(Player.GetAgentID())
            player.PlayerMaxEnergy = Agent.GetMaxEnergy(Player.GetAgentID())
            player.PlayerEnergyRegen = Agent.GetEnergyRegen(Player.GetAgentID())
            player.PlayerPosX = playerx
            player.PlayerPosY = playery
            player.PlayerPosZ = playerz
            player.PlayerFacingAngle = Agent.GetRotationAngle(Player.GetAgentID())
            player.PlayerTargetID = Player.GetTargetID()
            player.PlayerLoginNumber = Agent.GetLoginNumber(Player.GetAgentID())
            player.PlayerIsTicked = self.party_instance.GetIsPlayerTicked(party_number)
            player.PartyID = self.party_instance.party_id
            player.PartyPosition = party_number
            player.PlayerIsPartyLeader = self.party_instance.is_party_leader

        if not account_email:
            return    
        index = self.GetAccountSlot(account_email)
        if index != -1:
            self._updatechache()
            player = self.GetAccountData(index)
            player.SlotNumber = index
            player.IsSlotActive = True
            player.IsAccount = True
            player.AccountEmail = account_email
            player.LastUpdated = self.GetBaseTimestamp()
            
            if Map.IsMapLoading():
                return
            
            if (self.party_instance is None or 
                not Player.IsPlayerLoaded()):
                return
            
            if not Map.IsMapReady():
                return
            if not self.party_instance.is_party_loaded:
                return
            if Map.IsInCinematic():
                return
            
            _set_account_data(index)
            _set_player_data(index)
            _set_map_data(index)
            _set_buff_data(index)  
            self.GetAccountData(index).AgentData.Attributes.from_context(self.agent_instance.agent_id if self.agent_instance else 0)   
            self.GetAccountData(index).AgentData.Skillbar.from_context()
            self.GetAccountData(index).RankData.from_context()
            self.GetAccountData(index).FactionData.from_context()
            self.GetAccountData(index).TitlesData.from_context()
            self.GetAccountData(index).QuestLog.from_context()
            self.GetAccountData(index).ExperienceData.from_context()
            _set_agent_data(index)
            self.GetAccountData(index).AvailableCharacters.from_context()
            self.GetAccountData(index).MissionData.from_context()
            self.GetAccountData(index).UnlockedSkills.from_context()

        else:
            ConsoleLog(SMM_MODULE_NAME, "No empty slot available for new player data.", Py4GW.Console.MessageType.Error)
            
    #region Set Hero Data
    def SetHeroData(self,hero_data:HeroPartyMember):
        """Set player data for the account with the given email."""     
        def _set_agent_data(index):
            agent_data : AgentDataStruct = self.GetAccountData(index).AgentData
            if self.agent_instance is None:
                return
            
            uuid = Player.GetPlayerUUID() if Player.IsPlayerLoaded() else (0,0,0,0)
            for i in range(4):
                agent_data.UUID[i] = uuid[i]
            agent_id = self.agent_instance.agent_id if self.agent_instance else 0
            agent_data.AgentID = agent_id
            agent_data.OwnerID = Agent.GetOwnerID(agent_id)
            agent_data.TargetID = 0
            agent_data.ObservingID = 0
            agent_data.PlayerNumber = Agent.GetPlayerNumber(agent_id)
            agent_data.Profession[0] = Agent.GetProfessionIDs(agent_id)[0]
            agent_data.Profession[1] = Agent.GetProfessionIDs(agent_id)[1]
            agent_data.Level = Agent.GetLevel(agent_id)
            agent_data.Energy = Agent.GetEnergy(agent_id)
            max_energy = Agent.GetMaxEnergy(agent_id)
            agent_data.MaxEnergy = max_energy
            energy_regen = Agent.GetEnergyRegen(agent_id)
            agent_data.EnergyPips = Utils.calculate_energy_pips(max_energy, energy_regen)
            health = Agent.GetHealth(agent_id)
            max_health = Agent.GetMaxHealth(agent_id)
            agent_data.Health = health
            agent_data.MaxHealth = max_health
            health_regen = Agent.GetHealthRegen(agent_id)
            agent_data.HealthPips = Utils.calculate_health_pips(max_health, health_regen)
            agent_data.LoginNumber = Agent.GetLoginNumber(agent_id)
            agent_data.DaggerStatus = Agent.GetDaggerStatus(agent_id)
            agent_data.WeaponType = Agent.GetWeaponType(agent_id)[0]
            agent_data.WeaponItemType = Agent.GetWeaponItemType(agent_id)
            agent_data.OffhandItemType = Agent.GetOffhandItemType(agent_id)
            agent_data.Overcast = Agent.GetOvercast(agent_id)
            agent_data.WeaponAttackSpeed = Agent.GetWeaponAttackSpeed(agent_id)
            agent_data.AttackSpeedModifier = Agent.GetAttackSpeedModifier(agent_id)
            agent_data.EffectsMask = Agent.GetAgentEffects(agent_id)
            agent_data.VisualEffectsMask = Agent.GetVisualEffects(agent_id)
            agent_data.TypeMap = Agent.GetTypeMap(agent_id)
            agent_data.ModelState = Agent.GetModelState(agent_id)
            agent_data.AnimationSpeed = Agent.GetAnimationSpeed(agent_id)
            agent_data.AnimationCode = Agent.GetAnimationCode(agent_id)
            agent_data.AnimationID = Agent.GetAnimationID(agent_id)
            agent_data.XYZ[0] = Agent.GetXYZ(agent_id)[0]
            agent_data.XYZ[1] = Agent.GetXYZ(agent_id)[1]
            agent_data.XYZ[2] = Agent.GetXYZ(agent_id)[2]
            agent_data.ZPlane = Agent.GetZPlane(agent_id)
            agent_data.RotationAngle = Agent.GetRotationAngle(agent_id)
            agent_data.VelocityVector[0] = Agent.GetVelocityXY(agent_id)[0]
            agent_data.VelocityVector[1] = Agent.GetVelocityXY(agent_id)[1]

        index = self.GetHeroSlot(hero_data)
        if index != -1:
            hero = self.GetAccountData(index)
            hero.SlotNumber = index
            hero.IsSlotActive = True
            hero.IsAccount = False
            hero.LastUpdated = self.GetBaseTimestamp()
            
            if Map.IsMapLoading():
                return
            
            if (self.party_instance is None or 
                not Player.IsPlayerLoaded()):
                return
            
            if not Map.IsMapReady():
                return
            if not self.party_instance.is_party_loaded:
                return
            if Map.IsInCinematic():
                return
            
            hero.AccountEmail = self._get_account_email()
            agent_id = hero_data.agent_id
            map_region = Map.GetRegion()[0]
            
            if not Agent.IsValid(agent_id):
                return
            hero_agent_instance = Agent.GetAgentByID(agent_id)
            if hero_agent_instance is None:
                return
            
            playerx, playery, playerz = hero_agent_instance.pos.x, hero_agent_instance.pos.y, hero_agent_instance.z
            
            hero.AccountName = Player.GetAccountName()
            hero.CharacterName = hero_data.hero_id.GetName()
            
            hero.IsHero = True
            hero.IsPet = False
            hero.IsNPC = False
            hero.OwnerPlayerID = self.party_instance.GetAgentIDByLoginNumber(hero_data.owner_player_id)
            hero.HeroID = hero_data.hero_id.GetID()
            hero.MapID = Map.GetMapID()
            hero.MapRegion = map_region
            hero.MapDistrict = Map.GetDistrict()
            hero.MapLanguage = Map.GetLanguage()[0]
            hero.PlayerID = agent_id
            hero.PlayerLevel = Agent.GetLevel(agent_id)
            hero.PlayerProfession = (Agent.GetProfessionIDs(agent_id)[0], Agent.GetProfessionIDs(agent_id)[1])
            hero.PlayerMorale = 0
            hero.PlayerHP = Agent.GetHealth(agent_id)
            hero.PlayerMaxHP = Agent.GetMaxHealth(agent_id)
            hero.PlayerHealthRegen = Agent.GetHealthRegen(agent_id)
            hero.PlayerEnergy = Agent.GetEnergy(agent_id)
            hero.PlayerMaxEnergy = Agent.GetMaxEnergy(agent_id)
            hero.PlayerEnergyRegen = Agent.GetEnergyRegen(agent_id)
            hero.PlayerPosX = playerx
            hero.PlayerPosY = playery
            hero.PlayerPosZ = playerz
            hero.PlayerFacingAngle = hero_agent_instance.rotation_angle
            hero.PlayerTargetID = 0
            hero.PlayerLoginNumber = 0
            hero.PlayerIsTicked = False
            hero.PartyID = self.party_instance.party_id
            hero.PartyPosition = 0
            hero.PlayerIsPartyLeader = False
            effects_instance = Effects.get_instance(agent_id)
            
            buffs = effects_instance.GetEffects() + effects_instance.GetBuffs()
            for j in range(SHMEM_MAX_NUMBER_OF_BUFFS):
                buff = buffs[j] if j < len(buffs) else None
                effect = buff if isinstance(buff, EffectType) else None
                upkeep = buff if isinstance(buff, BuffType) else None
                
                hero.PlayerBuffs[j].SkillId = buff.skill_id if buff else 0
                hero.PlayerBuffs[j].Type = 2 if effect else (1 if upkeep else 0)
                hero.PlayerBuffs[j].Duration = effect.duration if effect else 0.0
                hero.PlayerBuffs[j].TargetAgentID = upkeep.target_agent_id if upkeep else 0
                hero.PlayerBuffs[j].Remaining = effect.time_remaining if effect else 0.0
                
                hero.PlayerBuffs[j].SkillId = buff.skill_id if buff else 0
                hero.PlayerBuffs[j].Type = 2 if effect else (1 if upkeep else 0)
                hero.PlayerBuffs[j].Duration = effect.duration if effect else 0.0
                hero.PlayerBuffs[j].TargetAgentID = upkeep.target_agent_id if upkeep else 0
                hero.PlayerBuffs[j].Remaining = effect.time_remaining if effect else 0.0
                
            # Attributes
            attributes = Agent.GetAttributes(agent_id)
            for attribute_id in range(SHMEM_NUMBER_OF_ATTRIBUTES):
                attribute = next((attr for attr in attributes if int(attr.attribute_id) == attribute_id), None)
                hero.AgentData.Attributes.Attributes[attribute_id].Id = attribute_id if attribute else 0
                hero.AgentData.Attributes.Attributes[attribute_id].Value = attribute.level if attribute else 0
                hero.AgentData.Attributes.Attributes[attribute_id].BaseValue = attribute.level_base if attribute else 0
                
            # Skills   
            hero.AgentData.Skillbar.from_hero_context(hero.SlotNumber, agent_id)                

            _set_agent_data(index)
            
                     
        else:
            ConsoleLog(SMM_MODULE_NAME, "No empty slot available for new hero data.", Py4GW.Console.MessageType.Error)
      
    #region Set Pet Data      
    def SetPetData(self):
        def _set_agent_data(index):
            agent_data : AgentDataStruct = self.GetAccountData(index).AgentData
            if self.agent_instance is None:
                return
            
            uuid = Player.GetPlayerUUID() if Player.IsPlayerLoaded() else (0,0,0,0)
            for i in range(4):
                agent_data.UUID[i] = uuid[i]
                
            agent_id = self.agent_instance.agent_id if self.agent_instance else 0
            agent_data.AgentID = agent_id
            agent_data.OwnerID = Agent.GetOwnerID(agent_id)
            agent_data.TargetID = 0
            agent_data.ObservingID = 0
            agent_data.PlayerNumber = Agent.GetPlayerNumber(agent_id)
            agent_data.Profession[0] = Agent.GetProfessionIDs(agent_id)[0]
            agent_data.Profession[1] = Agent.GetProfessionIDs(agent_id)[1]
            agent_data.Level = Agent.GetLevel(agent_id)
            agent_data.Energy = Agent.GetEnergy(agent_id)
            max_energy = Agent.GetMaxEnergy(agent_id)
            agent_data.MaxEnergy = max_energy
            energy_regen = Agent.GetEnergyRegen(agent_id)
            agent_data.EnergyPips = Utils.calculate_energy_pips(max_energy, energy_regen)
            health = Agent.GetHealth(agent_id)
            max_health = Agent.GetMaxHealth(agent_id)
            agent_data.Health = health
            agent_data.MaxHealth = max_health
            health_regen = Agent.GetHealthRegen(agent_id)
            agent_data.HealthPips = Utils.calculate_health_pips(max_health, health_regen)
            agent_data.LoginNumber = Agent.GetLoginNumber(agent_id)
            agent_data.DaggerStatus = Agent.GetDaggerStatus(agent_id)
            agent_data.WeaponType = Agent.GetWeaponType(agent_id)[0]
            agent_data.WeaponItemType = Agent.GetWeaponItemType(agent_id)
            agent_data.OffhandItemType = Agent.GetOffhandItemType(agent_id)
            agent_data.Overcast = Agent.GetOvercast(agent_id)
            agent_data.WeaponAttackSpeed = Agent.GetWeaponAttackSpeed(agent_id)
            agent_data.AttackSpeedModifier = Agent.GetAttackSpeedModifier(agent_id)
            agent_data.EffectsMask = Agent.GetAgentEffects(agent_id)
            agent_data.VisualEffectsMask = Agent.GetVisualEffects(agent_id)
            agent_data.TypeMap = Agent.GetTypeMap(agent_id)
            agent_data.ModelState = Agent.GetModelState(agent_id)
            agent_data.AnimationSpeed = Agent.GetAnimationSpeed(agent_id)
            agent_data.AnimationCode = Agent.GetAnimationCode(agent_id)
            agent_data.AnimationID = Agent.GetAnimationID(agent_id)
            agent_data.XYZ[0] = Agent.GetXYZ(agent_id)[0]
            agent_data.XYZ[1] = Agent.GetXYZ(agent_id)[1]
            agent_data.XYZ[2] = Agent.GetXYZ(agent_id)[2]
            agent_data.ZPlane = Agent.GetZPlane(agent_id)
            agent_data.RotationAngle = Agent.GetRotationAngle(agent_id)
            agent_data.VelocityVector[0] = Agent.GetVelocityXY(agent_id)[0]
            agent_data.VelocityVector[1] = Agent.GetVelocityXY(agent_id)[1]

                
                
        owner_agent_id = Player.GetAgentID()
        
        pet_info = self.party_instance.GetPetInfo(owner_agent_id) if self.party_instance else None
        # if not pet_info or pet_info.agent_id == 102298104:
        if not pet_info or not self.party_instance or (not pet_info.agent_id in self.party_instance.others):
            return
        
        index = self.GetPetSlot(pet_info)
        if index != -1:
            pet = self.GetAccountData(index)
            pet.SlotNumber = index
            pet.IsSlotActive = True
            pet.IsPet = True
            pet.OwnerPlayerID = pet_info.owner_agent_id
            pet.HeroID = 0
            pet.IsAccount = False
            pet.LastUpdated = self.GetBaseTimestamp()
            
            if Map.IsMapLoading():
                return
            
            if (self.party_instance is None or 
                not Player.IsPlayerLoaded()):
                return
            
            if not Map.IsMapReady():
                return
            if not self.party_instance.is_party_loaded:
                return
            if Map.IsInCinematic():
                return
            
            agent_id = pet_info.agent_id
            if not Agent.IsValid(agent_id):
                return
            agent_instance = Agent.GetAgentByID(agent_id)
            if agent_instance is None:
                return
            map_region = Map.GetRegion()[0]
            playerx, playery, playerz = agent_instance.pos.x, agent_instance.pos.y, agent_instance.z
            
            pet.AccountEmail = self._get_account_email()
            pet.AccountName = Player.GetAccountName()
            pet.CharacterName = f"Agent {pet_info.owner_agent_id} Pet"
            pet.IsHero = False
            pet.IsNPC = False
            pet.MapID = Map.GetMapID()
            pet.MapRegion = map_region
            pet.MapDistrict = Map.GetDistrict()
            pet.MapLanguage = Map.GetLanguage()[0]
            pet.PlayerID = agent_id
            pet.PartyID = self.party_instance.party_id
            pet.PartyPosition = 0
            pet.PlayerIsPartyLeader = False  
            pet.PlayerLoginNumber = 0 
            if Map.IsOutpost():
                return
            pet.PlayerMorale = 0
            pet.PlayerHP = Agent.GetHealth(agent_id)
            pet.PlayerMaxHP = Agent.GetMaxHealth(agent_id)
            pet.PlayerHealthRegen = Agent.GetHealthRegen(agent_id)
            pet.PlayerEnergy = Agent.GetEnergy(agent_id)
            pet.PlayerMaxEnergy = Agent.GetMaxEnergy(agent_id)
            pet.PlayerEnergyRegen = Agent.GetEnergyRegen(agent_id)
            pet.PlayerPosX = playerx
            pet.PlayerPosY = playery
            pet.PlayerPosZ = playerz
            pet.PlayerFacingAngle = agent_instance.rotation_angle
            pet.PlayerTargetID = pet_info.locked_target_id
            
            effects_instance = Effects.get_instance(agent_id)
            buffs = effects_instance.GetEffects() + effects_instance.GetBuffs()
            for j in range(SHMEM_MAX_NUMBER_OF_BUFFS):
                buff = buffs[j] if j < len(buffs) else None
                effect = buff if isinstance(buff, EffectType) else None
                upkeep = buff if isinstance(buff, BuffType) else None
                
                pet.PlayerBuffs[j].SkillId = buff.skill_id if buff else 0
                pet.PlayerBuffs[j].Type = 2 if effect else (1 if upkeep else 0)
                pet.PlayerBuffs[j].Duration = effect.duration if effect else 0.0
                pet.PlayerBuffs[j].TargetAgentID = upkeep.target_agent_id if upkeep else 0
                pet.PlayerBuffs[j].Remaining = effect.time_remaining if effect else 0.0
                
                pet.PlayerBuffs[j].SkillId = buff.skill_id if buff else 0
                pet.PlayerBuffs[j].Type = 2 if effect else (1 if upkeep else 0)
                pet.PlayerBuffs[j].Duration = effect.duration if effect else 0.0
                pet.PlayerBuffs[j].TargetAgentID = upkeep.target_agent_id if upkeep else 0
                pet.PlayerBuffs[j].Remaining = effect.time_remaining if effect else 0.0
                
            # Attributes
            attributes = Agent.GetAttributes(agent_id)
            for attribute_id in range(SHMEM_NUMBER_OF_ATTRIBUTES):
                attribute = next((attr for attr in attributes if int(attr.attribute_id) == attribute_id), None)
                pet.AgentData.Attributes.Attributes[attribute_id].Id = attribute_id if attribute else 0
                pet.AgentData.Attributes.Attributes[attribute_id].Value = attribute.level if attribute else 0
                pet.AgentData.Attributes.Attributes[attribute_id].BaseValue = attribute.level_base if attribute else 0
                
            # Skills   
            pet.AgentData.Skillbar.reset()
                
            _set_agent_data(index)
                
        else:
            ConsoleLog(SMM_MODULE_NAME, "No empty slot available for new Pet data.", Py4GW.Console.MessageType.Error)
        
        
    def SetHeroesData(self):
        """Set data for all heroes in the given list."""
        owner_id = Player.GetAgentID()
        for hero_data in self.party_instance.heroes if self.party_instance else []:
            agent_from_login = self.party_instance.GetAgentIDByLoginNumber(hero_data.owner_player_id) if self.party_instance else 0
            if agent_from_login != owner_id:
                continue
            self.SetHeroData(hero_data)
         
    #region GetAllActivePlayers   
    def GetAllActivePlayers(self) -> list[AccountStruct]:
        """Get all active players in shared memory."""
        players : list[AccountStruct] = []
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self._is_slot_active(i) and player.IsAccount:
                players.append(player)
        return players
    
    def GetNumActivePlayers(self) -> int:
        """Get the number of active players in shared memory."""
        count = 0
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self._is_slot_active(i) and player.IsAccount:
                count += 1
        return count
    
    def GetNumActiveSlots(self) -> int:
        """Get the number of active slots in shared memory."""
        count = 0
        for i in range(self.max_num_players):
            if self._is_slot_active(i):
                count += 1
        return count
        
    def GetAllActiveSlotsData(self) -> list[AccountStruct]:
        """Get all active slot data, ordered by PartyID, PartyPosition, PlayerLoginNumber, CharacterName."""
        accs : list[AccountStruct] = []
        for i in range(self.max_num_players):
            acc = self.GetAllAccounts().AccountData[i]
            if self._is_slot_active(i):
                accs.append(acc)

        # Sort by PartyID, then PartyPosition, then PlayerLoginNumber, then CharacterName
        accs.sort(key=lambda p: (
            p.MapID,
            p.MapRegion,
            p.MapDistrict,
            p.MapLanguage,
            p.PartyID,
            p.PartyPosition,
            p.PlayerLoginNumber,
            p.CharacterName
        ))

        return accs
    
    def GetAllAccountData(self) -> list[AccountStruct]:
        """Get all player data, ordered by PartyID, PartyPosition, PlayerLoginNumber, CharacterName."""
        players : list[AccountStruct] = []
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self._is_slot_active(i) and player.IsAccount:
                players.append(player)

        # Sort by PartyID, then PartyPosition, then PlayerLoginNumber, then CharacterName
        players.sort(key=lambda p: (
            p.MapID,
            p.MapRegion,
            p.MapDistrict,
            p.MapLanguage,
            p.PartyID,
            p.PartyPosition,
            p.PlayerLoginNumber,
            p.CharacterName
        ))

        return players
    
    def GetAccountDataFromEmail(self, account_email: str, log : bool = False) -> AccountStruct | None:
        """Get player data for the account with the given email."""
        if not account_email:
            return None
        index = self.FindAccount(account_email)
        if index != -1:
            return self.GetAccountData(index)
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
            return None
     
    def GetAccountDataFromPartyNumber(self, party_number: int, log : bool = False) -> AccountStruct | None:
        """Get player data for the account with the given party number."""
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self._is_slot_active(i) and player.PartyPosition == party_number:
                return player
        
        ConsoleLog(SMM_MODULE_NAME, f"Party number {party_number} not found.", Py4GW.Console.MessageType.Error, log = False)
        return None
    
    def HasEffect(self, account_email: str, effect_id: int) -> bool:
        """Check if the account with the given email has the specified effect."""
        if effect_id == 0:
            return False
        
        player = self.GetAccountDataFromEmail(account_email)
        if player:
            for buff in player.PlayerBuffs:
                if buff.SkillId == effect_id:
                    return True
        return False
    
    def GetAllAccountHeroAIOptions(self) -> list[HeroAIOptionStruct]:
        """Get HeroAI options for all accounts."""
        options = []
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self._is_slot_active(i) and player.IsAccount:
                options.append(self.GetAllAccounts().HeroAIOptions[i])
        return options
        
    def GetHeroAIOptions(self, account_email: str) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given email."""
        if not account_email:
            return None
        index = self.FindAccount(account_email)
        if index != -1:
            return self.GetAllAccounts().HeroAIOptions[index]
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
            return None
        
    def GetGerHeroAIOptionsByPartyNumber(self, party_number: int) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given party number."""
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self._is_slot_active(i) and player.PartyPosition == party_number:
                return self.GetAllAccounts().HeroAIOptions[i]
        return None    
        
        
    def SetHeroAIOptions(self, account_email: str, options: HeroAIOptionStruct):
        """Set HeroAI options for the account with the given email."""
        if not account_email:
            return
        index = self.FindAccount(account_email)
        if index != -1:
            self.GetAllAccounts().HeroAIOptions[index] = options
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
    
    def SetHeroAIProperty(self, account_email: str, property_name: str, value):
        """Set a specific HeroAI property for the account with the given email."""
        if not account_email:
            return
        index = self.FindAccount(account_email)
        if index != -1:
            options = self.GetAllAccounts().HeroAIOptions[index]
            
            if property_name.startswith("Skill_"):
                skill_index = int(property_name.split("_")[1])
                if 0 <= skill_index < SHMEM_NUMBER_OF_SKILLS:
                    options.Skills[skill_index] = value
                else:
                    ConsoleLog(SMM_MODULE_NAME, f"Invalid skill index: {skill_index}.", Py4GW.Console.MessageType.Error)
                return
            
            if hasattr(options, property_name):
                setattr(options, property_name, value)
            else:
                ConsoleLog(SMM_MODULE_NAME, f"Property {property_name} does not exist in HeroAIOptions.", Py4GW.Console.MessageType.Error)
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
    
    def GetMapsFromPlayers(self):
        """Get a list of unique maps from all active players."""
        maps = set()
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if self._is_slot_active(i) and player.IsAccount:
                maps.add((player.MapID, player.MapRegion, player.MapDistrict, player.MapLanguage))
        return list(maps)
    
    def GetPartiesFromMaps(self, map_id: int, map_region: int, map_district: int, map_language: int):
        """
        Get a list of unique PartyIDs for players in the specified map/region/district.
        """
        parties = set()
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if (self._is_slot_active(i) and player.IsAccount and
                player.MapID == map_id and
                player.MapRegion == map_region and
                player.MapDistrict == map_district and
                player.MapLanguage == map_language):
                parties.add(player.PartyID)
        return list(parties)

    
    def GetPlayersFromParty(self, party_id: int, map_id: int, map_region: int, map_district: int, map_language: int):
        """Get a list of players in a specific party on a specific map."""
        players = []
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if (self._is_slot_active(i) and player.IsAccount and
                player.MapID == map_id and
                player.MapRegion == map_region and
                player.MapDistrict == map_district and
                player.MapLanguage == map_language and
                player.PartyID == party_id):
                players.append(player)
        return players
    
    def GetHeroesFromPlayers(self, owner_player_id: int) -> list[AccountStruct]:
        """Get a list of heroes owned by the specified player."""
        heroes : list[AccountStruct] = []
        for i in range(self.max_num_players):
            player = self.GetAllAccounts().AccountData[i]
            if (self._is_slot_active(i) and player.IsHero and
                player.OwnerPlayerID == owner_player_id):
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
            if (self._is_slot_active(i) and player.IsPet and
                player.OwnerPlayerID == owner_agent_id):
                pets.append(player)
        return pets
    
    def GetNumPetsFromPlayers(self, owner_agent_id: int) -> int:
        """Get the number of pets owned by the specified player."""
        return self.GetPetsFromPlayers(owner_agent_id).__len__()
    
    def UpdateTimeouts(self):
        return

    #("ExtraData", c_wchar * 4 * SHMEM_MAX_CHAR_LEN),
    
    def SendMessage(self, sender_email: str, receiver_email: str, command: SharedCommandType, params: tuple = (0.0, 0.0, 0.0, 0.0), ExtraData: tuple = ()) -> int:
        """Send a message to another player. Returns the message index or -1 on failure."""
        
        import ctypes as ct
        index = self.FindAccount(receiver_email)
        
        if index == -1:
            ConsoleLog(SMM_MODULE_NAME, f"Receiver account {receiver_email} not found.", Py4GW.Console.MessageType.Error)
            return -1
        
        if not receiver_email:
            ConsoleLog(SMM_MODULE_NAME, "Receiver email is empty.", Py4GW.Console.MessageType.Error)
            return -1
        
        if not sender_email:
            ConsoleLog(SMM_MODULE_NAME, "Sender email is empty.", Py4GW.Console.MessageType.Error)
            return -1
        
        for i in range(self.max_num_players):
            message = self.GetAllAccounts().Inbox[i]
            if message.Active:
                continue  # Find the first unfinished message slot
            
            message.SenderEmail = sender_email
            message.ReceiverEmail = receiver_email
            message.Command = command.value
            message.Params = (c_float * 4)(*params)
            # Pack 4 strings into 4 arrays of c_wchar[SHMEM_MAX_CHAR_LEN]
            arr_type = ct.c_wchar * SHMEM_MAX_CHAR_LEN
            packed = [self._str_to_c_wchar_array(
                        ExtraData[j] if j < len(ExtraData) else "",
                        SHMEM_MAX_CHAR_LEN)
                    for j in range(4)]
            message.ExtraData = (arr_type * 4)(*packed)
            message.Active = True
            message.Running = False
            message.Timestamp = self.GetBaseTimestamp()
            return i

        return -1

    def GetNextMessage(self, account_email: str) -> tuple[int, SharedMessageStruct | None]:
        """Read the next message for the given account.
        Returns the raw SharedMessage. Use self._c_wchar_array_to_str() to read ExtraData safely.
        """
        for index in range(self.max_num_players):
            message = self.GetAllAccounts().Inbox[index]
            if message.ReceiverEmail == account_email and message.Active and not message.Running:
                return index, message
        return -1, None


    
    def PreviewNextMessage(self, account_email: str, include_running: bool = True) -> tuple[int, SharedMessageStruct | None]:
        """Preview the next message for the given account.
        If include_running is True, will also return a running message.
        Ensures ExtraData is returned as tuple[str] using existing helpers.
        """
        for index in range(self.max_num_players):
            message = self.GetAllAccounts().Inbox[index]
            if message.ReceiverEmail != account_email or not message.Active:
                continue
            if not message.Running or include_running:
                return index, message
        return -1, None


    
    def MarkMessageAsRunning(self, account_email: str, message_index: int):
        """Mark a specific message as running."""
        if 0 <= message_index < self.max_num_players:
            message = self.GetAllAccounts().Inbox[message_index]
            if message.ReceiverEmail == account_email:
                message.Running = True
                message.Active = True
                message.Timestamp = self.GetBaseTimestamp()
            else:
                ConsoleLog(SMM_MODULE_NAME, f"Message at index {message_index} does not belong to {account_email}.", Py4GW.Console.MessageType.Error)
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Invalid message index: {message_index}.", Py4GW.Console.MessageType.Error)
            
    def MarkMessageAsFinished(self, account_email: str, message_index: int):
        """Mark a specific message as finished."""
        import ctypes as ct
        if 0 <= message_index < self.max_num_players:
            message = self.GetAllAccounts().Inbox[message_index]
            if message.ReceiverEmail == account_email:
                message.SenderEmail = ""
                message.ReceiverEmail = ""
                message.Command = SharedCommandType.NoCommand
                message.Params = (c_float * 4)(0.0, 0.0, 0.0, 0.0)

                # Reset ExtraData to 4 empty wide-char arrays
                arr_type = ct.c_wchar * SHMEM_MAX_CHAR_LEN
                empty = [self._str_to_c_wchar_array("", SHMEM_MAX_CHAR_LEN) for _ in range(4)]
                message.ExtraData = (arr_type * 4)(*empty)

                message.Timestamp = self.GetBaseTimestamp()
                message.Running = False
                message.Active = False
            else:
                ConsoleLog(
                    SMM_MODULE_NAME,
                    f"Message at index {message_index} does not belong to {account_email}.",
                    Py4GW.Console.MessageType.Error
                )
        else:
            ConsoleLog(
                SMM_MODULE_NAME,
                f"Invalid message index: {message_index}.",
                Py4GW.Console.MessageType.Error
            )

            
    def GetAllMessages(self) -> list[tuple[int, SharedMessageStruct]]:
        """Get all messages in shared memory with their index."""
        messages = []
        for index in range(self.max_num_players):
            message = self.GetAllAccounts().Inbox[index]
            if message.Active:
                messages.append((index, message))  # Add index and message
        return messages