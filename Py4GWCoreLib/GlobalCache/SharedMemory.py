import Py4GW
import PyQuest
from PyParty import HeroPartyMember, PetInfo
from PyEffects import BuffType, EffectType
from typing import Optional, Tuple, List
from Py4GWCoreLib import ConsoleLog, Map, Party, Player, Agent, Effects, SharedCommandType, Skill, ThrottledTimer
from Py4GWCoreLib.Quest import Quest
from Py4GWCoreLib.enums import FactionType
from ctypes import Array, Structure, addressof, c_int, c_uint, c_float, c_bool, c_wchar, memmove
from multiprocessing import shared_memory
import ctypes
from ctypes import sizeof
from datetime import datetime, timezone
from ..native_src.context.AgentContext import AgentStruct, AgentLivingStruct, AgentItemStruct, AgentGadgetStruct
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

#region Structures
#region Rank
class RankStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Rank", c_uint),
        ("Rating", c_uint),
        ("QualifierPoints", c_uint),
        ("Wins", c_uint),
        ("Losses", c_uint),
        ("TournamentRewardPoints", c_uint),
    ]
    
    # Type hints for IntelliSense
    Rank: int
    Rating: int
    QualifierPoints: int
    Wins: int
    Losses: int
    TournamentRewardPoints: int
   
#region Factions 
class FactionStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("FactionType", c_uint),
        ("Current", c_uint),
        ("TotalEarned", c_uint),
        ("Max", c_uint),
    ]
    
    # Type hints for IntelliSense
    FactionType: int
    Current: int
    TotalEarned: int
    Max: int
    
class FactionsStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Factions", FactionStruct * 4),  # 4 factions
    ]
    
    # Type hints for IntelliSense
    Factions: list[FactionStruct]
  
#region Titles  
class TitleStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("TitleID", c_uint),
        ("CurrentPoints", c_uint),
    ]
    
    # Type hints for IntelliSense
    TitleID: int
    CurrentPoints: int

class TitlesStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("ActiveTitleID", c_uint),
        ("Titles", TitleStruct * 48),  # 48 titles
    ]
    
    # Type hints for IntelliSense
    ActiveTitleID: int
    Titles: list[TitleStruct]
  
#region Quests  
class QuestStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("QuestID", c_uint),
        ("IsCompleted", c_bool),
    ]
    
    # Type hints for IntelliSense
    QuestID: int
    IsCompleted: bool
    
class ActiveQuestStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("QuestID", c_uint),
        ("MarkerX", c_float),
        ("MarkerY", c_float),
        ("MapFrom", c_uint),
        ("MapTo", c_uint),
        ("IsCompleted", c_bool),
    ]
    
    # Type hints for IntelliSense
    QuestID: int
    MarkerX: float
    MarkerY: float
    MapFrom: int
    MapTo: int
    IsCompleted: bool
    
class QuestsStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("ActiveQuest", ActiveQuestStruct),
        ("Quests", QuestStruct * 100),  # 100 quests
    ]
    
    # Type hints for IntelliSense
    ActiveQuest : ActiveQuestStruct
    Quests: list[QuestStruct]
  
#region Experience  
class ExperienceStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Level", c_uint),
        ("Experience", c_uint),
        ("ProgressPct", c_float),
        ("CurrentSkillPoints", c_uint),
        ("TotalEarnedSkillPoints", c_uint),
    ]
    
    # Type hints for IntelliSense
    Level: int
    Experience: int
    ProgressPct: float
    CurrentSkillPoints: int
    TotalEarnedSkillPoints: int
 
#region SkillStruct   
class SkillStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Id", c_uint),
        ("Recharge", c_float),
        ("Adrenaline", c_float),
    ]
    
    # Type hints for IntelliSense
    Id: int
    Recharge: float
    Adrenaline: float
    
class SkillbarStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("CastingSkillID", c_uint),
        ("Skills", SkillStruct * SHMEM_NUMBER_OF_SKILLS),
        
    ]
    
    # Type hints for IntelliSense
    CastingSkillID: int
    Skills : list[SkillStruct]
 
#region Attributes   
class AttributeStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Id", c_uint),
        ("Value", c_uint),
        ("BaseValue", c_uint),
    ]
    
    # Type hints for IntelliSense
    Id: int
    Value: int
    BaseValue: int
  
#region BuffStruct  
class BuffStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("SkillId", c_uint),
        ("Duration", c_float),
        ("Remaining", c_float),
        ("TargetAgentID", c_uint),
        ("Type", c_int),
    ]
    
    # Type hints for IntelliSense
    SkillId: int
    Duration: float
    Remaining: float
    TargetAgentID: int
    Type: int

#region MissionData
class MissionDataStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("NormalModeCompleted", c_uint * MISSION_FLAG_ENTRIES),
        ("NormalModeBonus", c_uint * MISSION_FLAG_ENTRIES),
        ("HardModeCompleted", c_uint * MISSION_FLAG_ENTRIES),
        ("HardModeBonus", c_uint * MISSION_FLAG_ENTRIES),
    ]
    
    # Type hints for IntelliSense
    NormalModeCompleted: list[int]
    NormalModeBonus: list[int]
    HardModeCompleted: list[int]
    HardModeBonus: list[int]

#region AgentData
class AgentDataStruct(Structure):
    _pack_ = 1
    _fields_ = [
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
        ("ModelState", c_uint),
        ("AnimationSpeed", c_float),
        ("AnimationCode", c_uint),
        ("AnimationID", c_uint),
        ("XYZ", c_float * 3),
        ("ZPlane", c_int),
        ("RotationAngle", c_float),
        ("VelocityVector", c_float * 2),
        ("Is_Bleeding", c_bool),
        ("Is_Conditioned", c_bool),
        ("Is_Crippled", c_bool),
        ("Is_Dead", c_bool),
        ("Is_DeepWounded", c_bool),
        ("Is_Poisoned", c_bool),
        ("Is_Enchanted", c_bool),
        ("Is_DegenHexed", c_bool),
        ("Is_Hexed", c_bool),
        ("Is_WeaponSpelled", c_bool),
        ("Is_InCombatStance", c_bool),
        ('Is_Moving', c_bool),
        ("Is_Attacking", c_bool),
        ("Is_Casting", c_bool),
        ("Is_Idle", c_bool),
        ("Is_Alive", c_bool),
        
    ]
    
    # Type hints for IntelliSense
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
    VisualEffectsMask: int
    ModelState: int
    AnimationSpeed: float
    AnimationCode: int
    AnimationID: int
    XYZ: list[float]
    ZPlane: int
    RotationAngle: float
    VelocityVector: list[float]
    Is_Bleeding: bool
    Is_Conditioned: bool
    Is_Crippled: bool
    Is_Dead: bool
    Is_DeepWounded: bool
    Is_Poisoned: bool
    Is_Enchanted: bool
    Is_DegenHexed: bool
    Is_Hexed: bool
    Is_WeaponSpelled: bool
    Is_InCombatStance: bool
    Is_Moving: bool
    Is_Attacking: bool
    Is_Casting: bool
    Is_Idle: bool
    Is_Alive: bool
    
class AvailableCharacterStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Name", c_wchar * SHMEM_MAX_CHAR_LEN),
        ("Level", c_uint),
        ("IsPvP", c_bool),
        ("MapID", c_uint),
        ("Professions", c_uint * 2),  # Primary and Secondary Profession
        ("CampaignID", c_uint),  
    ]
    
    # Type hints for IntelliSense
    Name: str
    Level: int
    IsPvP: bool
    MapID: int
    Professions: tuple[int, int]
    CampaignID: int
    
    
#region Player  
class PlayerStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("RankData", RankStruct),
        ("FactionsData", FactionsStruct),
        ("TitlesData", TitlesStruct),
        ("QuestsData", QuestsStruct),
        ("ExperienceData", ExperienceStruct),
        ("SkillbarData", SkillbarStruct),
        ("AttributesData",  AttributeStruct * SHMEM_NUMBER_OF_ATTRIBUTES),
        ("BuffData", BuffStruct * SHMEM_MAX_NUMBER_OF_BUFFS),
        ("MissionData", MissionDataStruct),
        ("UnlockedSkills", c_uint * SKILL_FLAG_ENTRIES),  # Bitmap of unlocked skills\
        ("AgentData", AgentDataStruct),
        ("AvailableCharacters", AvailableCharacterStruct * SHMEM_MAX_AVAILABLE_CHARS),
        
    ]
    
    # Type hints for IntelliSense
    RankData: RankStruct
    FactionsData: FactionsStruct
    TitlesData: TitlesStruct
    QuestsData: QuestsStruct
    ExperienceData: ExperienceStruct
    SkillbarData: SkillbarStruct
    AttributesData: list[AttributeStruct]
    BuffData: list[BuffStruct]
    UnlockedSkills: list[int]
    MissionData: MissionDataStruct
    AgentData: AgentDataStruct
    AvailableCharacters: list[AvailableCharacterStruct]


#region old structures

class AccountData(Structure):
    _pack_ = 1
    _fields_ = [
        ("SlotNumber", c_uint),  # Slot number for the player
        ("IsSlotActive", c_bool),
        ("AccountEmail", c_wchar*SHMEM_MAX_EMAIL_LEN),
        ("AccountName", c_wchar*SHMEM_MAX_CHAR_LEN),
        ("CharacterName", c_wchar*SHMEM_MAX_CHAR_LEN),
        ("IsAccount", c_bool),
        ("IsHero", c_bool),
        ("IsPet", c_bool),
        ("IsNPC", c_bool),
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
        ("PlayerBuffs", BuffStruct * SHMEM_MAX_NUMBER_OF_BUFFS),  # Buff IDs 
              
        ("LastUpdated", c_uint),
        
        #Restructure Structures
        ("PlayerData", PlayerStruct),
    ]
    
    # Type hints for IntelliSense
    SlotNumber: int
    IsSlotActive: bool
    AccountEmail: str
    AccountName: str
    CharacterName: str
    IsAccount: bool
    IsHero: bool
    IsPet: bool
    IsNPC: bool
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
    
    PlayerBuffs: list[BuffStruct]    
    
    LastUpdated: int
    
    PlayerData: PlayerStruct
        
    def clone(self) -> "AccountData":
        """Return a deep copy of this AccountData as a real ctypes structure."""
        clone = type(self)()  # new AccountData()
        memmove(addressof(clone), addressof(self), sizeof(self))
        return clone
    
class SharedMessage(Structure):
    _pack_ = 1
    _fields_ = [
        ("SenderEmail", c_wchar * SHMEM_MAX_EMAIL_LEN),
        ("ReceiverEmail", c_wchar * SHMEM_MAX_EMAIL_LEN),
        ("Command", c_uint),
        ("Params", c_float * 4),
        ("ExtraData", (c_wchar * SHMEM_MAX_CHAR_LEN) * 4),
        ("Active", c_bool), 
        ("Running", c_bool),
        ("Timestamp", c_uint), 
    ]
    
    # Type hints for IntelliSense
    SenderEmail: str
    ReceiverEmail: str
    Command: int
    Params: Array[c_float]
    ExtraData: Array
    Active: bool
    Running: bool
    Timestamp: int
    
class HeroAIOptionStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Following", c_bool),
        ("Avoidance", c_bool), 
        ("Looting", c_bool), 
        ("Targeting", c_bool),
        ("Combat", c_bool),
        ("Skills", c_bool * SHMEM_NUMBER_OF_SKILLS),
        ("IsFlagged", c_bool),
        ("FlagPosX", c_float),
        ("FlagPosY", c_float),
        ("FlagFacingAngle", c_float),
    ] 
    
    # Type hints for IntelliSense
    Following : bool
    Avoidance : bool
    Looting : bool
    Targeting : bool
    Combat : bool
    Skills : list[bool]
    IsFlagged : bool
    FlagPosX : float
    FlagPosY : float
    FlagFacingAngle : float
    
class AllAccounts(Structure):
    _pack_ = 1
    _fields_ = [
        ("AccountData", AccountData * SHMEM_MAX_NUM_PLAYERS),
        ("SharedMessage", SharedMessage * SHMEM_MAX_NUM_PLAYERS),  # Messages for each player
        ("HeroAIOptions", HeroAIOptionStruct * SHMEM_MAX_NUM_PLAYERS),  # Game options for HeroAI
    ]
    
    # Type hints for IntelliSense
    AccountData: list["AccountData"]
    SharedMessage: list["SharedMessage"]
    HeroAIOptions: list[HeroAIOptionStruct]
    
    
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
    
    def GetStruct(self) -> AllAccounts:
        if self.shm.buf is None:
            raise RuntimeError("Shared memory is not initialized.")
        return AllAccounts.from_buffer(self.shm.buf)
        
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

    #region Reset
        
    def ResetAllData(self):
        """Reset all player data in shared memory."""
        for i in range(self.max_num_players):
            self.ResetPlayerData(i)
            self.ResetHeroAIData(i)
        
    def ResetPlayerData(self, index):
        """Reset data for a specific player."""
        def _reset_rank_data(index):
            rank_data: RankStruct = self.GetStruct().AccountData[index].PlayerData.RankData
            rank_data.Rank = 0
            rank_data.Rating = 0
            rank_data.QualifierPoints = 0
            rank_data.Wins = 0
            rank_data.Losses = 0
            rank_data.TournamentRewardPoints = 0
            
        def _reset_factions_data(index):
            factions_data: FactionsStruct = self.GetStruct().AccountData[index].PlayerData.FactionsData
            for index, faction in enumerate(factions_data.Factions):
                faction.FactionType = index
                faction.Current = 0
                faction.TotalEarned = 0
                faction.Max = 0
                
        def _reset_titles_data(index):
            titles_data: TitlesStruct = self.GetStruct().AccountData[index].PlayerData.TitlesData
            titles_data.ActiveTitleID = 0
            for index, title in enumerate(titles_data.Titles):
                title.TitleID = index
                title.CurrentPoints = 0
                
        def _reset_quests_data(index):
            quests_data: QuestsStruct = self.GetStruct().AccountData[index].PlayerData.QuestsData
            
            quests_data.ActiveQuest = ActiveQuestStruct()
            quests_data.ActiveQuest.QuestID = 0
            quests_data.ActiveQuest.MarkerX = 0.0
            quests_data.ActiveQuest.MarkerY = 0.0
            quests_data.ActiveQuest.IsCompleted = False
            
            for index, quest in enumerate(quests_data.Quests):
                quest.QuestID = 0
                quest.IsCompleted = False
                
        def _reset_experience_data(index):
            experience_data: ExperienceStruct = self.GetStruct().AccountData[index].PlayerData.ExperienceData
            experience_data.Level = 0
            experience_data.Experience = 0
            experience_data.ProgressPct = 0.0
            experience_data.CurrentSkillPoints = 0
            experience_data.TotalEarnedSkillPoints = 0
        
        def _reset_buff_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            for j in range(SHMEM_MAX_NUMBER_OF_BUFFS):
                player.PlayerData.BuffData[j].SkillId = 0
                player.PlayerData.BuffData[j].Type = 0
                player.PlayerData.BuffData[j].Duration = 0.0
                player.PlayerData.BuffData[j].TargetAgentID = 0
                player.PlayerData.BuffData[j].Remaining = 0.0
                
                player.PlayerBuffs[j].SkillId = 0
                player.PlayerBuffs[j].Type = 0
                player.PlayerBuffs[j].Duration = 0.0
                player.PlayerBuffs[j].TargetAgentID = 0
                player.PlayerBuffs[j].Remaining = 0.0
                
        def _reset_skill_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            player.PlayerData.SkillbarData.CastingSkillID = 0
            for slot in range(SHMEM_NUMBER_OF_SKILLS):
                player.PlayerData.SkillbarData.Skills[slot].Id = 0
                player.PlayerData.SkillbarData.Skills[slot].Recharge = 0.0
                player.PlayerData.SkillbarData.Skills[slot].Adrenaline = 0.0
                
        def _reset_attribute_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            for j in range(SHMEM_NUMBER_OF_ATTRIBUTES):
                player.PlayerData.AttributesData[j].Id = 0
                player.PlayerData.AttributesData[j].Value = 0
                player.PlayerData.AttributesData[j].BaseValue = 0
                
        def _reset_agent_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            agent_data : AgentDataStruct = player.PlayerData.AgentData
            for i in range(4):
                agent_data.UUID[i] = 0
            agent_data.AgentID = 0
            agent_data.OwnerID = 0
            agent_data.TargetID = 0
            agent_data.ObservingID = 0
            agent_data.PlayerNumber = 0
            agent_data.Profession[0] = 0
            agent_data.Profession[1] = 0
            agent_data.Level = 0
            agent_data.Energy = 0.0
            agent_data.MaxEnergy = 0.0
            agent_data.EnergyPips = 0
            agent_data.Health = 0.0
            agent_data.MaxHealth = 0.0
            agent_data.HealthPips = 0
            agent_data.LoginNumber = 0
            agent_data.DaggerStatus = 0
            agent_data.WeaponType = 0
            agent_data.WeaponItemType = 0
            agent_data.OffhandItemType = 0
            agent_data.Overcast = 0.0
            agent_data.WeaponAttackSpeed = 0.0
            agent_data.AttackSpeedModifier = 0.0
            agent_data.VisualEffectsMask = 0
            agent_data.ModelState = 0
            agent_data.AnimationSpeed = 0.0
            agent_data.AnimationCode = 0
            agent_data.AnimationID = 0
            for i in range(3):
                agent_data.XYZ[i] = 0.0
            agent_data.ZPlane = 0
            agent_data.RotationAngle = 0.0
            for i in range(2):
                agent_data.VelocityVector[i] = 0.0
                
            agent_data.Is_Bleeding = False
            agent_data.Is_Conditioned = False
            agent_data.Is_Crippled = False
            agent_data.Is_Dead = False
            agent_data.Is_DeepWounded = False
            agent_data.Is_Poisoned = False
            agent_data.Is_Enchanted = False
            agent_data.Is_DegenHexed = False
            agent_data.Is_Hexed = False
            agent_data.Is_WeaponSpelled = False
            agent_data.Is_InCombatStance = False
            agent_data.Is_Moving = False
            agent_data.Is_Attacking = False
            agent_data.Is_Casting = False
            agent_data.Is_Idle = False
            agent_data.Is_Alive = False
                
        def _reset_available_characters_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            for j in range(SHMEM_MAX_AVAILABLE_CHARS):
                char_data : AvailableCharacterStruct = player.PlayerData.AvailableCharacters[j]
                char_data.Name = ""
                char_data.Level = 0
                char_data.IsPvP = False
                char_data.MapID = 0 
                char_data.Professions = (0, 0)
                char_data.CampaignID = 0
                
        def _reset_account_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            player.AccountEmail = ""
            player.AccountName = ""
            player.CharacterName = ""
            player.IsAccount = False    
            
        def _reset_hero_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            player.IsHero = False
            player.HeroID = 0
            player.OwnerPlayerID = 0
            
        def _reset_pet_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            player.IsPet = False
            
        def _reset_npc_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            player.IsNPC = False
        
        def _reset_map_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            player.MapID = 0
            player.MapRegion = 0
            player.MapDistrict = 0
            player.MapLanguage = 0
            
        def _reset_player_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            player.PlayerID = 0
            player.PlayerLevel = 0
            player.PlayerProfession = (0, 0)
            player.PlayerMorale = 0
            player.PlayerHP = 0.0
            player.PlayerMaxHP = 0.0
            player.PlayerHealthRegen = 0.0
            player.PlayerEnergy = 0.0
            player.PlayerMaxEnergy = 0.0
            player.PlayerEnergyRegen = 0.0  
            player.PlayerPosX = 0.0
            player.PlayerPosY = 0.0
            player.PlayerPosZ = 0.0
            player.PlayerFacingAngle = 0.0
            player.PlayerTargetID = 0
            player.PlayerLoginNumber = 0
            player.PlayerIsTicked = False
            player.PartyID = 0
            player.PartyPosition = 0
            player.PlayerIsPartyLeader = False
            
            for j in range(SKILL_FLAG_ENTRIES):
                player.PlayerData.UnlockedSkills[j] = 0
                
            
            #mission data
            for j in range(MISSION_FLAG_ENTRIES):
                player.PlayerData.MissionData.NormalModeCompleted[j] = 0
                player.PlayerData.MissionData.NormalModeBonus[j] = 0
                player.PlayerData.MissionData.HardModeCompleted[j] = 0
                player.PlayerData.MissionData.HardModeBonus[j] = 0
            
            
            
        
        if 0 <= index < self.max_num_players:
            player : AccountData = self.GetStruct().AccountData[index]
            player.IsSlotActive = False
            _reset_account_data(index)
            _reset_hero_data(index)
            _reset_pet_data(index)
            _reset_npc_data(index)
            _reset_map_data(index)
            _reset_player_data(index)
            
            _reset_buff_data(index)
            _reset_skill_data(index)
            _reset_attribute_data(index)
            _reset_rank_data(index)
            _reset_factions_data(index)
            _reset_titles_data(index)
            _reset_quests_data(index)
            _reset_experience_data(index)
            _reset_agent_data(index)
            _reset_available_characters_data(index)
                
            player.LastUpdated = self.GetBaseTimestamp()
           
    #region ResetHeroAIData 
    def ResetHeroAIData(self, index): 
            option = self.GetStruct().HeroAIOptions[index]
            option.Following = True
            option.Avoidance = True
            option.Looting = True
            option.Targeting = True
            option.Combat = True
            for i in range(SHMEM_NUMBER_OF_SKILLS):
                option.Skills[i] = True 
            option.IsFlaged = False
            option.FlagPosX = 0.0
            option.FlagPosY = 0.0
            option.FlagFacingAngle = 0.0
       
    def _is_slot_active(self, index: int) -> bool:
        """Check if the slot at the given index is active."""
        slot_active = self.GetStruct().AccountData[index].IsSlotActive    
        last_updated = self.GetStruct().AccountData[index].LastUpdated
        
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
            
            player = self.GetStruct().AccountData[i]
            if self.GetStruct().AccountData[i].AccountEmail == account_email and player.IsAccount:
                return i
            
        return -1
    
    def FindHero(self, hero_data:HeroPartyMember) -> int:
        """Find the index of the hero with the given ID."""
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            #if not player.IsSlotActive:
            if not self._is_slot_active(i):
                continue
            if player.IsHero and player.HeroID == hero_data.hero_id.GetID() and player.OwnerPlayerID == Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id):
                return i
        return -1
    
    def FindPet(self, pet_data:PetInfo) -> int:
        """Find the index of the pet with the given ID."""
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
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
                if not self._is_slot_active(i) and (not clean_slot or not self.GetStruct().AccountData[i].IsAccount):
                    if not clean_slot:
                        ConsoleLog(SMM_MODULE_NAME, f"Reusing occupied slot {i} for new data.", Py4GW.Console.MessageType.Warning)
                    return i
            
        return -1
    
    def FindExistingAccountSlot(self, account_email: str = "") -> Optional[int]:
        """Find the first empty slot in shared memory."""
        if not account_email:
            return None
                    
        for i in range(self.max_num_players):
            existing_email = self.GetStruct().AccountData[i].AccountEmail
            is_account = self.GetStruct().AccountData[i].IsAccount
            
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
            player = self.GetStruct().AccountData[index]
            player.IsSlotActive = True
            player.AccountEmail = account_email
            player.LastUpdated = self.GetBaseTimestamp()
        
        return index
    
    def GetHeroSlot(self, hero_data:HeroPartyMember) -> int:
        """Get the slot index for the hero with the given owner ID and hero ID."""
        index = self.FindHero(hero_data)
        if index == -1:
            index = self.FindEmptySlot()
            hero = self.GetStruct().AccountData[index]
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
            pet = self.GetStruct().AccountData[index]
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
       
    #region Set Player Data 
    def SetPlayerData(self, account_email: str):
        """Set player data for the account with the given email."""  
        def _set_buff_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            if self.effects_instance is None:
                return
            buffs = self.effects_instance.GetEffects() + self.effects_instance.GetBuffs()
            for j in range(SHMEM_MAX_NUMBER_OF_BUFFS):
                buff = buffs[j] if j < len(buffs) else None
                effect = buff if isinstance(buff, EffectType) else None
                upkeep = buff if isinstance(buff, BuffType) else None
                
                player.PlayerData.BuffData[j].SkillId = buff.skill_id if buff else 0
                player.PlayerData.BuffData[j].Type = 2 if effect else (1 if upkeep else 0)
                player.PlayerData.BuffData[j].Duration = effect.duration if effect else 0.0
                player.PlayerData.BuffData[j].TargetAgentID = upkeep.target_agent_id if upkeep else 0
                player.PlayerData.BuffData[j].Remaining = effect.time_remaining if effect else 0.0
                
                player.PlayerBuffs[j].SkillId = buff.skill_id if buff else 0
                player.PlayerBuffs[j].Type = 2 if effect else (1 if upkeep else 0)
                player.PlayerBuffs[j].Duration = effect.duration if effect else 0.0
                player.PlayerBuffs[j].TargetAgentID = upkeep.target_agent_id if upkeep else 0
                player.PlayerBuffs[j].Remaining = effect.time_remaining if effect else 0.0
                
                
        
        def _set_attribute_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            if self.agent_instance is None:
                return
            attributes = Agent.GetAttributes(self.agent_instance.agent_id)
            for attribute_id in range(SHMEM_NUMBER_OF_ATTRIBUTES):
                attribute = next((attr for attr in attributes if int(attr.attribute_id) == attribute_id), None)
                player.PlayerData.AttributesData[attribute_id].Id = attribute_id if attribute else 0
                player.PlayerData.AttributesData[attribute_id].Value = attribute.level if attribute else 0
                player.PlayerData.AttributesData[attribute_id].BaseValue = attribute.level_base if attribute else 0
                
        def _set_skill_data(index):
            # Skills            
            for slot in range(SHMEM_NUMBER_OF_SKILLS):        
                skill = SkillBar.GetSkillData(slot + 1)
                
                if skill is None:
                    player.PlayerData.SkillbarData.Skills[slot].Id = 0
                    player.PlayerData.SkillbarData.Skills[slot].Recharge = 0.0
                    player.PlayerData.SkillbarData.Skills[slot].Adrenaline = 0.0
                    continue
                            
                player.PlayerData.SkillbarData.Skills[slot].Id = skill.id.id
                player.PlayerData.SkillbarData.Skills[slot].Recharge = skill.get_recharge if skill.id.id != 0 else 0.0
                player.PlayerData.SkillbarData.Skills[slot].Adrenaline = skill.adrenaline_a if skill.id.id != 0 else 0.0  
                        
            casting_skill_id = Agent.GetCastingSkillID(self.agent_instance.agent_id) if self.agent_instance else 0
            player.PlayerData.SkillbarData.CastingSkillID = casting_skill_id if casting_skill_id in [skill.Id for skill in player.PlayerData.SkillbarData.Skills] else 0
        
        def _set_rank_data(index):
            rank_data: RankStruct = self.GetStruct().AccountData[index].PlayerData.RankData
            if rank_data is None:
                return
            if not Player.IsPlayerLoaded():
                return
            rank_data.Rank = Player.GetRankData()[0]
            rank_data.Rating = Player.GetRankData()[1]
            rank_data.QualifierPoints = Player.GetRankData()[2]
            rank_data.Wins = Player.GetRankData()[3]
            rank_data.Losses = Player.GetRankData()[4]
            rank_data.TournamentRewardPoints = Player.GetTournamentRewardPoints()
            
        def _set_factions_data(index):
            factions_data: FactionsStruct = self.GetStruct().AccountData[index].PlayerData.FactionsData
            if factions_data is None:
                return
            if not Player.IsPlayerLoaded():
                return
            
            factions_data.Factions[FactionType.Kurzick.value].FactionType = FactionType.Kurzick.value
            factions_data.Factions[FactionType.Kurzick.value].Current = Player.GetKurzickData()[0]
            factions_data.Factions[FactionType.Kurzick.value].TotalEarned = Player.GetKurzickData()[1]
            factions_data.Factions[FactionType.Kurzick.value].Max = Player.GetKurzickData()[2]
            
            factions_data.Factions[FactionType.Luxon.value].FactionType = FactionType.Luxon.value
            factions_data.Factions[FactionType.Luxon.value].Current = Player.GetLuxonData()[0]
            factions_data.Factions[FactionType.Luxon.value].TotalEarned = Player.GetLuxonData()[1]
            factions_data.Factions[FactionType.Luxon.value].Max = Player.GetLuxonData()[2]
            
            factions_data.Factions[FactionType.Imperial.value].FactionType = FactionType.Imperial.value
            factions_data.Factions[FactionType.Imperial.value].Current = Player.GetImperialData()[0]
            factions_data.Factions[FactionType.Imperial.value].TotalEarned = Player.GetImperialData()[1]
            factions_data.Factions[FactionType.Imperial.value].Max = Player.GetImperialData()[2]
            
            factions_data.Factions[FactionType.Balthazar.value].FactionType = FactionType.Balthazar.value
            factions_data.Factions[FactionType.Balthazar.value].Current = Player.GetBalthazarData()[0]
            factions_data.Factions[FactionType.Balthazar.value].TotalEarned = Player.GetBalthazarData()[1]
            factions_data.Factions[FactionType.Balthazar.value].Max = Player.GetBalthazarData()[2]
            
        def _set_titles_data(index):
            titles_data: TitlesStruct = self.GetStruct().AccountData[index].PlayerData.TitlesData
            if titles_data is None:
                return
            if not Player.IsPlayerLoaded():
                return
            
            for title_id, title_instance in self._title_instances.items():
                if title_id < 0 or title_id >= 48:
                    continue
                titles_data.Titles[title_id].TitleID = title_id
                titles_data.Titles[title_id].CurrentPoints = title_instance.current_points

        def _set_quests_data(index):
            quests_data: QuestsStruct = self.GetStruct().AccountData[index].PlayerData.QuestsData
            if quests_data is None:
                return
            if not Player.IsPlayerLoaded():
                return
            
            active_quest = Quest.GetActiveQuest()
            quests_data.ActiveQuest.QuestID = active_quest
            if active_quest != 0 and self.quest_instance:
                
                active_quest_data = Quest.GetQuestData(active_quest)
                quests_data.ActiveQuest.MarkerX = active_quest_data.marker_x
                quests_data.ActiveQuest.MarkerY = active_quest_data.marker_y                
                quests_data.ActiveQuest.MapFrom = active_quest_data.map_from
                quests_data.ActiveQuest.MapTo = active_quest_data.map_to                
                quests_data.ActiveQuest.IsCompleted = active_quest_data.is_completed
            
            quest_log = self.quest_instance.get_quest_log_ids() if self.quest_instance else []
            for i, quest_id in enumerate(quest_log):
                quests_data.Quests[i].QuestID = quest_id
                quests_data.Quests[i].IsCompleted = self.quest_instance.is_quest_completed(quest_id) if self.quest_instance else False

        def _set_experience_data(index):
            experience_data: ExperienceStruct = self.GetStruct().AccountData[index].PlayerData.ExperienceData
            if experience_data is None:
                return
            if Player.IsPlayerLoaded() == False:
                return
            
            experience_data.Level = Player.GetLevel()
            experience_data.Experience = Player.GetExperience()
            experience_data.ProgressPct = Utils.GetExperienceProgression(Player.GetExperience())
            experience_data.CurrentSkillPoints = Player.GetSkillPointData()[0]
            experience_data.TotalEarnedSkillPoints = Player.GetSkillPointData()[1]
            
        def _set_agent_data(index):
            agent_data : AgentDataStruct = self.GetStruct().AccountData[index].PlayerData.AgentData
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
            agent_data.VisualEffectsMask = Agent.GetVisualEffects(agent_id)
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
            agent_data.Is_Bleeding = Agent.IsBleeding(agent_id)
            agent_data.Is_Conditioned = Agent.IsConditioned(agent_id)
            agent_data.Is_Crippled = Agent.IsCrippled(agent_id)
            agent_data.Is_Dead = Agent.IsDead(agent_id)
            agent_data.Is_DeepWounded = Agent.IsDeepWounded(agent_id)
            agent_data.Is_Poisoned = Agent.IsPoisoned(agent_id)
            agent_data.Is_Enchanted = Agent.IsEnchanted(agent_id)
            agent_data.Is_DegenHexed = Agent.IsDegenHexed(agent_id)
            agent_data.Is_Hexed = Agent.IsHexed(agent_id)
            agent_data.Is_WeaponSpelled = Agent.IsWeaponSpelled(agent_id)
            agent_data.Is_InCombatStance = Agent.IsInCombatStance(agent_id)
            agent_data.Is_Moving = Agent.IsMoving(agent_id)
            agent_data.Is_Attacking = Agent.IsAttacking(agent_id)
            agent_data.Is_Casting = Agent.IsCasting(agent_id)
            agent_data.Is_Idle = Agent.IsIdle(agent_id)
            agent_data.Is_Alive = Agent.IsAlive(agent_id)
            
        def _set_available_characters_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            if not Player.IsPlayerLoaded():
                return
            available_characters= Map.Pregame.GetAvailableCharacterList()
            for j in range(SHMEM_MAX_AVAILABLE_CHARS):
                char = available_characters[j] if j < len(available_characters) else None
                if char:
                    player.PlayerData.AvailableCharacters[j].Name = char.player_name
                    player.PlayerData.AvailableCharacters[j].Level = char.level
                    player.PlayerData.AvailableCharacters[j].IsPvP = char.is_pvp
                    player.PlayerData.AvailableCharacters[j].MapID = char.map_id
                    player.PlayerData.AvailableCharacters[j].Professions = (char.primary, char.secondary)
                    player.PlayerData.AvailableCharacters[j].CampaignID = char.campaign
                else:
                    player.PlayerData.AvailableCharacters[j].Name = ""
                    player.PlayerData.AvailableCharacters[j].Level = 0
                    player.PlayerData.AvailableCharacters[j].IsPvP = False
                    player.PlayerData.AvailableCharacters[j].MapID = 0 
                    player.PlayerData.AvailableCharacters[j].Professions = (0, 0)
                    player.PlayerData.AvailableCharacters[j].CampaignID = 0
            
        def _set_account_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            player.AccountName = Player.GetAccountName() if Player.IsPlayerLoaded() else ""
            player.CharacterName =self.party_instance.GetPlayerNameByLoginNumber(self.GetLoginNumber()) if self.party_instance else ""
            player.IsHero = False
            player.IsPet = False
            player.IsNPC = False
            player.OwnerPlayerID = 0
            player.HeroID = 0
            
        def _set_map_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
            player.MapID = Map.GetMapID()
            player.MapRegion = Map.GetRegion()[0]
            player.MapDistrict = Map.GetDistrict()
            player.MapLanguage = Map.GetLanguage()[0]
            
        def _set_player_data(index):
            player : AccountData = self.GetStruct().AccountData[index]
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
            
            for j in range(SKILL_FLAG_ENTRIES):
                unlocked_character_skills = Player.GetUnlockedCharacterSkills()
                player.PlayerData.UnlockedSkills[j] = unlocked_character_skills[j] if j < len(unlocked_character_skills) else 0
                
            missions_completed = Player.GetMissionsCompleted()
            missions_bonus = Player.GetMissionsBonusCompleted()
            missions_completed_hm = Player.GetMissionsCompletedHM()
            missions_bonus_hm = Player.GetMissionsBonusCompletedHM()
            
            for entry in range(MISSION_FLAG_ENTRIES):
                player.PlayerData.MissionData.NormalModeCompleted[entry] = missions_completed[entry] if entry < len(missions_completed) else 0
                player.PlayerData.MissionData.NormalModeBonus[entry] = missions_bonus[entry] if entry < len(missions_bonus) else 0
                player.PlayerData.MissionData.HardModeCompleted[entry] = missions_completed_hm[entry] if entry < len(missions_completed_hm) else 0
                player.PlayerData.MissionData.HardModeBonus[entry] = missions_bonus_hm[entry] if entry < len(missions_bonus_hm) else 0

        if not account_email:
            return    
        index = self.GetAccountSlot(account_email)
        if index != -1:
            self._updatechache()
            player = self.GetStruct().AccountData[index]
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
            _set_attribute_data(index)   
            _set_skill_data(index)
            _set_rank_data(index)
            _set_factions_data(index)
            _set_titles_data(index)
            _set_quests_data(index)
            _set_experience_data(index)
            _set_agent_data(index)
            _set_available_characters_data(index)
            

        else:
            ConsoleLog(SMM_MODULE_NAME, "No empty slot available for new player data.", Py4GW.Console.MessageType.Error)
            
    #region Set Hero Data
    def SetHeroData(self,hero_data:HeroPartyMember):
        """Set player data for the account with the given email."""     
        def _set_agent_data(index):
            agent_data : AgentDataStruct = self.GetStruct().AccountData[index].PlayerData.AgentData
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
            agent_data.VisualEffectsMask = Agent.GetVisualEffects(agent_id)
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
            agent_data.Is_Bleeding = Agent.IsBleeding(agent_id)
            agent_data.Is_Conditioned = Agent.IsConditioned(agent_id)
            agent_data.Is_Crippled = Agent.IsCrippled(agent_id)
            agent_data.Is_Dead = Agent.IsDead(agent_id)
            agent_data.Is_DeepWounded = Agent.IsDeepWounded(agent_id)
            agent_data.Is_Poisoned = Agent.IsPoisoned(agent_id)
            agent_data.Is_Enchanted = Agent.IsEnchanted(agent_id)
            agent_data.Is_DegenHexed = Agent.IsDegenHexed(agent_id)
            agent_data.Is_Hexed = Agent.IsHexed(agent_id)
            agent_data.Is_WeaponSpelled = Agent.IsWeaponSpelled(agent_id)
            agent_data.Is_InCombatStance = Agent.IsInCombatStance(agent_id)
            agent_data.Is_Moving = Agent.IsMoving(agent_id)
            agent_data.Is_Attacking = Agent.IsAttacking(agent_id)
            agent_data.Is_Casting = Agent.IsCasting(agent_id)
            agent_data.Is_Idle = Agent.IsIdle(agent_id)
            agent_data.Is_Alive = Agent.IsAlive(agent_id)
                
        index = self.GetHeroSlot(hero_data)
        if index != -1:
            hero = self.GetStruct().AccountData[index]
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
                
                hero.PlayerData.BuffData[j].SkillId = buff.skill_id if buff else 0
                hero.PlayerData.BuffData[j].Type = 2 if effect else (1 if upkeep else 0)
                hero.PlayerData.BuffData[j].Duration = effect.duration if effect else 0.0
                hero.PlayerData.BuffData[j].TargetAgentID = upkeep.target_agent_id if upkeep else 0
                hero.PlayerData.BuffData[j].Remaining = effect.time_remaining if effect else 0.0
                
                hero.PlayerBuffs[j].SkillId = buff.skill_id if buff else 0
                hero.PlayerBuffs[j].Type = 2 if effect else (1 if upkeep else 0)
                hero.PlayerBuffs[j].Duration = effect.duration if effect else 0.0
                hero.PlayerBuffs[j].TargetAgentID = upkeep.target_agent_id if upkeep else 0
                hero.PlayerBuffs[j].Remaining = effect.time_remaining if effect else 0.0
                
            # Attributes
            attributes = Agent.GetAttributes(agent_id)
            for attribute_id in range(SHMEM_NUMBER_OF_ATTRIBUTES):
                attribute = next((attr for attr in attributes if int(attr.attribute_id) == attribute_id), None)
                hero.PlayerData.AttributesData[attribute_id].Id = attribute_id if attribute else 0
                hero.PlayerData.AttributesData[attribute_id].Value = attribute.level if attribute else 0
                hero.PlayerData.AttributesData[attribute_id].BaseValue = attribute.level_base if attribute else 0
                
            # Skills                   
            skills = SkillBar.GetHeroSkillbar(hero.SlotNumber)       
            for slot in range(SHMEM_NUMBER_OF_SKILLS):        
                skill = skills[slot] if len(skills) > slot else None
                
                if skill is None:
                    hero.PlayerData.SkillbarData.Skills[slot].Id = 0
                    hero.PlayerData.SkillbarData.Skills[slot].Recharge = 0.0
                    hero.PlayerData.SkillbarData.Skills[slot].Adrenaline = 0.0
                    continue
                            
                hero.PlayerData.SkillbarData.Skills[slot].Id = skill.id.id
                hero.PlayerData.SkillbarData.Skills[slot].Recharge = skill.get_recharge if skill.id.id != 0 else 0.0
                hero.PlayerData.SkillbarData.Skills[slot].Adrenaline = skill.adrenaline_a if skill.id.id != 0 else 0.0  
                        
            casting_skill = Agent.GetCastingSkillID(agent_id)
            hero.PlayerData.SkillbarData.CastingSkillID = casting_skill if casting_skill in [skill.Id for skill in hero.PlayerData.SkillbarData.Skills] else 0
            
            _set_agent_data(index)
            
                     
        else:
            ConsoleLog(SMM_MODULE_NAME, "No empty slot available for new hero data.", Py4GW.Console.MessageType.Error)
      
    #region Set Pet Data      
    def SetPetData(self):
        def _set_agent_data(index):
            agent_data : AgentDataStruct = self.GetStruct().AccountData[index].PlayerData.AgentData
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
            agent_data.VisualEffectsMask = Agent.GetVisualEffects(agent_id)
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
            agent_data.Is_Bleeding = Agent.IsBleeding(agent_id)
            agent_data.Is_Conditioned = Agent.IsConditioned(agent_id)
            agent_data.Is_Crippled = Agent.IsCrippled(agent_id)
            agent_data.Is_Dead = Agent.IsDead(agent_id)
            agent_data.Is_DeepWounded = Agent.IsDeepWounded(agent_id)
            agent_data.Is_Poisoned = Agent.IsPoisoned(agent_id)
            agent_data.Is_Enchanted = Agent.IsEnchanted(agent_id)
            agent_data.Is_DegenHexed = Agent.IsDegenHexed(agent_id)
            agent_data.Is_Hexed = Agent.IsHexed(agent_id)
            agent_data.Is_WeaponSpelled = Agent.IsWeaponSpelled(agent_id)
            agent_data.Is_InCombatStance = Agent.IsInCombatStance(agent_id)
            agent_data.Is_Moving = Agent.IsMoving(agent_id)
            agent_data.Is_Attacking = Agent.IsAttacking(agent_id)
            agent_data.Is_Casting = Agent.IsCasting(agent_id)
            agent_data.Is_Idle = Agent.IsIdle(agent_id)
            agent_data.Is_Alive = Agent.IsAlive(agent_id)
                
                
        owner_agent_id = Player.GetAgentID()
        
        pet_info = self.party_instance.GetPetInfo(owner_agent_id) if self.party_instance else None
        # if not pet_info or pet_info.agent_id == 102298104:
        if not pet_info or not self.party_instance or (not pet_info.agent_id in self.party_instance.others):
            return
        
        index = self.GetPetSlot(pet_info)
        if index != -1:
            pet = self.GetStruct().AccountData[index]
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
                
                pet.PlayerData.BuffData[j].SkillId = buff.skill_id if buff else 0
                pet.PlayerData.BuffData[j].Type = 2 if effect else (1 if upkeep else 0)
                pet.PlayerData.BuffData[j].Duration = effect.duration if effect else 0.0
                pet.PlayerData.BuffData[j].TargetAgentID = upkeep.target_agent_id if upkeep else 0
                pet.PlayerData.BuffData[j].Remaining = effect.time_remaining if effect else 0.0
                
                pet.PlayerBuffs[j].SkillId = buff.skill_id if buff else 0
                pet.PlayerBuffs[j].Type = 2 if effect else (1 if upkeep else 0)
                pet.PlayerBuffs[j].Duration = effect.duration if effect else 0.0
                pet.PlayerBuffs[j].TargetAgentID = upkeep.target_agent_id if upkeep else 0
                pet.PlayerBuffs[j].Remaining = effect.time_remaining if effect else 0.0
                
            # Attributes
            attributes = Agent.GetAttributes(agent_id)
            for attribute_id in range(SHMEM_NUMBER_OF_ATTRIBUTES):
                attribute = next((attr for attr in attributes if int(attr.attribute_id) == attribute_id), None)
                pet.PlayerData.AttributesData[attribute_id].Id = attribute_id if attribute else 0
                pet.PlayerData.AttributesData[attribute_id].Value = attribute.level if attribute else 0
                pet.PlayerData.AttributesData[attribute_id].BaseValue = attribute.level_base if attribute else 0
                
            # Skills   
            pet.PlayerData.SkillbarData.CastingSkillID = 0             
            
            for slot in range(SHMEM_NUMBER_OF_SKILLS):
                pet.PlayerData.SkillbarData.Skills[slot].Id = 0
                pet.PlayerData.SkillbarData.Skills[slot].Recharge = 0.0
                pet.PlayerData.SkillbarData.Skills[slot].Adrenaline = 0.0   
                
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
    def GetAllActivePlayers(self) -> list[AccountData]:
        """Get all active players in shared memory."""
        players : list[AccountData] = []
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if self._is_slot_active(i) and player.IsAccount:
                players.append(player)
        return players
    
    def GetNumActivePlayers(self) -> int:
        """Get the number of active players in shared memory."""
        count = 0
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
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
        
    def GetAllActiveSlotsData(self) -> list[AccountData]:
        """Get all active slot data, ordered by PartyID, PartyPosition, PlayerLoginNumber, CharacterName."""
        accs : list[AccountData] = []
        for i in range(self.max_num_players):
            acc = self.GetStruct().AccountData[i]
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
    
    def GetAllAccountData(self) -> list[AccountData]:
        """Get all player data, ordered by PartyID, PartyPosition, PlayerLoginNumber, CharacterName."""
        players : list[AccountData] = []
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
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
    
    def GetAccountDataFromEmail(self, account_email: str, log : bool = False) -> AccountData | None:
        """Get player data for the account with the given email."""
        if not account_email:
            return None
        index = self.FindAccount(account_email)
        if index != -1:
            return self.GetStruct().AccountData[index]
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
            return None
     
    def GetAccountDataFromPartyNumber(self, party_number: int, log : bool = False) -> AccountData | None:
        """Get player data for the account with the given party number."""
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
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
            for buff in player.PlayerData.BuffData:
                if buff.SkillId == effect_id:
                    return True
        return False
    
    def GetAllAccountHeroAIOptions(self) -> list[HeroAIOptionStruct]:
        """Get HeroAI options for all accounts."""
        options = []
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if self._is_slot_active(i) and player.IsAccount:
                options.append(self.GetStruct().HeroAIOptions[i])
        return options
        
    def GetHeroAIOptions(self, account_email: str) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given email."""
        if not account_email:
            return None
        index = self.FindAccount(account_email)
        if index != -1:
            return self.GetStruct().HeroAIOptions[index]
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
            return None
        
    def GetGerHeroAIOptionsByPartyNumber(self, party_number: int) -> HeroAIOptionStruct | None:
        """Get HeroAI options for the account with the given party number."""
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if self._is_slot_active(i) and player.PartyPosition == party_number:
                return self.GetStruct().HeroAIOptions[i]
        return None    
        
        
    def SetHeroAIOptions(self, account_email: str, options: HeroAIOptionStruct):
        """Set HeroAI options for the account with the given email."""
        if not account_email:
            return
        index = self.FindAccount(account_email)
        if index != -1:
            self.GetStruct().HeroAIOptions[index] = options
        else:
            ConsoleLog(SMM_MODULE_NAME, f"Account {account_email} not found.", Py4GW.Console.MessageType.Error, log = False)
    
    def SetHeroAIProperty(self, account_email: str, property_name: str, value):
        """Set a specific HeroAI property for the account with the given email."""
        if not account_email:
            return
        index = self.FindAccount(account_email)
        if index != -1:
            options = self.GetStruct().HeroAIOptions[index]
            
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
            player = self.GetStruct().AccountData[i]
            if self._is_slot_active(i) and player.IsAccount:
                maps.add((player.MapID, player.MapRegion, player.MapDistrict, player.MapLanguage))
        return list(maps)
    
    def GetPartiesFromMaps(self, map_id: int, map_region: int, map_district: int, map_language: int):
        """
        Get a list of unique PartyIDs for players in the specified map/region/district.
        """
        parties = set()
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
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
            player = self.GetStruct().AccountData[i]
            if (self._is_slot_active(i) and player.IsAccount and
                player.MapID == map_id and
                player.MapRegion == map_region and
                player.MapDistrict == map_district and
                player.MapLanguage == map_language and
                player.PartyID == party_id):
                players.append(player)
        return players
    
    def GetHeroesFromPlayers(self, owner_player_id: int) -> list[AccountData]:
        """Get a list of heroes owned by the specified player."""
        heroes : list[AccountData] = []
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if (self._is_slot_active(i) and player.IsHero and
                player.OwnerPlayerID == owner_player_id):
                heroes.append(player)
        return heroes
    
    def GetNumHeroesFromPlayers(self, owner_player_id: int) -> int:
        """Get the number of heroes owned by the specified player."""
        return self.GetHeroesFromPlayers(owner_player_id).__len__()
    
    def GetPetsFromPlayers(self, owner_agent_id: int) -> list[AccountData]:
        """Get a list of pets owned by the specified player."""
        pets : list[AccountData] = []
        for i in range(self.max_num_players):
            player = self.GetStruct().AccountData[i]
            if (self._is_slot_active(i) and player.IsPet and
                player.OwnerPlayerID == owner_agent_id):
                pets.append(player)
        return pets
    
    def GetNumPetsFromPlayers(self, owner_agent_id: int) -> int:
        """Get the number of pets owned by the specified player."""
        return self.GetPetsFromPlayers(owner_agent_id).__len__()
    
    def UpdateTimeouts(self):
        return
        current_time = self.GetBaseTimestamp()

        for index in range(self.max_num_players):
            player = self.GetStruct().AccountData[index]

            if player.IsSlotActive:
                delta = current_time - player.LastUpdated
                if delta > SHMEM_SUBSCRIBE_TIMEOUT_MILLISECONDS:
                    #ConsoleLog(SMM_MODULE_NAME, f"Player {player.AccountEmail} has timed out after {delta} ms.", Py4GW.Console.MessageType.Warning)
                    self.ResetPlayerData(index)

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
            message = self.GetStruct().SharedMessage[i]
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

    def GetNextMessage(self, account_email: str) -> tuple[int, SharedMessage | None]:
        """Read the next message for the given account.
        Returns the raw SharedMessage. Use self._c_wchar_array_to_str() to read ExtraData safely.
        """
        for index in range(self.max_num_players):
            message = self.GetStruct().SharedMessage[index]
            if message.ReceiverEmail == account_email and message.Active and not message.Running:
                return index, message
        return -1, None


    
    def PreviewNextMessage(self, account_email: str, include_running: bool = True) -> tuple[int, SharedMessage | None]:
        """Preview the next message for the given account.
        If include_running is True, will also return a running message.
        Ensures ExtraData is returned as tuple[str] using existing helpers.
        """
        for index in range(self.max_num_players):
            message = self.GetStruct().SharedMessage[index]
            if message.ReceiverEmail != account_email or not message.Active:
                continue
            if not message.Running or include_running:
                return index, message
        return -1, None


    
    def MarkMessageAsRunning(self, account_email: str, message_index: int):
        """Mark a specific message as running."""
        if 0 <= message_index < self.max_num_players:
            message = self.GetStruct().SharedMessage[message_index]
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
            message = self.GetStruct().SharedMessage[message_index]
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

            
    def GetAllMessages(self) -> list[tuple[int, SharedMessage]]:
        """Get all messages in shared memory with their index."""
        messages = []
        for index in range(self.max_num_players):
            message = self.GetStruct().SharedMessage[index]
            if message.Active:
                messages.append((index, message))  # Add index and message
        return messages