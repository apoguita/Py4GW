from ctypes import Array, Structure, addressof, c_int, c_uint, c_float, c_bool, c_wchar, memmove

from .Globals import (
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

from .RankStruct import RankStruct
from .FactionStruct import FactionStruct
from .TitlesStruct import TitlesStruct
from .QuestLogStruct import QuestLogStruct
from .ExperienceStruct import ExperienceStruct
from .MissionDataStruct import MissionDataStruct
from .UnlockedSkillsStruct import UnlockedSkillsStruct
from .AvailableCharacterStruct import AvailableCharacterStruct, AvailableCharacterUnitStruct
from .SharedMessageStruct import SharedMessageStruct
from .HeroAIOptionStruct import HeroAIOptionStruct
from .AttributesStruct import AttributesStruct, AttributeUnitStruct
from .BuffStruct import BuffStruct, BuffUnitStruct
from .SkillbarStruct import SkillbarStruct
from .KeyStruct import KeyStruct
from .AgentPartyStruct import AgentPartyStruct
from .MapStruct import MapStruct
from .EnergyStruct import EnergyStruct
from .HealthStruct import HealthStruct
from .AgentDataStruct import AgentDataStruct



class AccountStruct(Structure):
    _pack_ = 1
    _fields_ = [      
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
        
        
