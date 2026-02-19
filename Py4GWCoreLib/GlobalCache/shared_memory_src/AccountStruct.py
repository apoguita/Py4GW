from ctypes import Structure, c_uint, c_bool, c_wchar
import Py4GW
from PyParty import HeroPartyMember, PetInfo
from .Globals import (
    SHMEM_MAX_PLAYERS,
    SHMEM_MAX_EMAIL_LEN,
    SHMEM_MAX_CHAR_LEN,
)

from .RankStruct import RankStruct
from .FactionStruct import FactionStruct
from .TitlesStruct import TitlesStruct
from .QuestLogStruct import QuestLogStruct
from .ExperienceStruct import ExperienceStruct
from .MissionDataStruct import MissionDataStruct
from .UnlockedSkillsStruct import UnlockedSkillsStruct
from .AvailableCharacterStruct import AvailableCharacterStruct
from .KeyStruct import KeyStruct
from .AgentPartyStruct import AgentPartyStruct
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
        
    def from_context(self, account_email:str , slot_index: int) -> None:
        from ...Map import Map
        from ...Player import Player
        from ...Party import Party
        """Load data from the specified slot index in shared memory."""
        if slot_index < 0 or slot_index >= SHMEM_MAX_PLAYERS:
            raise ValueError(f"Invalid slot index: {slot_index}")
        
        self.SlotNumber = slot_index
        self.IsSlotActive = True
        self.IsAccount = True
        self.AccountEmail = account_email
        self.IsHero = False
        self.IsPet = False
        self.IsNPC = False
        
        if Map.IsMapLoading(): return
        if not Player.IsPlayerLoaded(): return
        if not Map.IsMapReady(): return
        if not Party.IsPartyLoaded(): return
        if Map.IsInCinematic(): return
        
        self.AccountName = Player.GetAccountName() if Player.IsPlayerLoaded() else ""
        
        agent_id = Player.GetAgentID()
        self.AgentData.from_context(agent_id)
        self.AgentData.OwnerAgentID = 0
        self.AgentData.HeroID = 0
        
        self.AgentPartyData.from_context()
        self.RankData.from_context()
        self.FactionData.from_context()
        self.TitlesData.from_context()
        self.QuestLog.from_context()
        self.ExperienceData.from_context()
        self.AvailableCharacters.from_context()
        self.MissionData.from_context()
        self.UnlockedSkills.from_context()
        
        self.LastUpdated = Py4GW.Game.get_tick_count64()
        
    def from_hero_context(self, hero_data: HeroPartyMember, slot_index: int) -> None:
        from ...Map import Map
        from ...Player import Player
        from ...Party import Party
        """Load data from the specified slot index in shared memory."""
        if slot_index < 0 or slot_index >= SHMEM_MAX_PLAYERS:
            raise ValueError(f"Invalid slot index: {slot_index}")
        
        self.SlotNumber = slot_index
        self.IsSlotActive = True
        self.IsAccount = False
        self.AccountEmail = Player.GetAccountEmail()
        self.IsHero = True
        self.IsPet = False
        self.IsNPC = False
        
        if Map.IsMapLoading(): return
        if not Player.IsPlayerLoaded(): return
        if not Map.IsMapReady(): return
        if not Party.IsPartyLoaded(): return
        if Map.IsInCinematic(): return
        
        self.AccountName = Player.GetAccountName() if Player.IsPlayerLoaded() else ""
        
        agent_id = hero_data.agent_id
        self.AgentData.from_context(agent_id)
        self.AgentData.AgentID = agent_id
        self.AgentData.CharacterName = hero_data.hero_id.GetName()
        self.AgentData.OwnerAgentID = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
        self.AgentData.HeroID = hero_data.hero_id.GetID()
        self.AgentData.Morale = 100
        self.AgentData.TargetID = 0
        self.AgentData.LoginNumber = 0
        self.AgentData.Skillbar.from_hero_context(slot_index, agent_id) 
        
        self.AgentPartyData.from_context()
        self.AgentPartyData.IsPartyLeader = False
        self.RankData.from_context()
        self.FactionData.reset()
        self.TitlesData.reset()
        self.QuestLog.reset()
        self.ExperienceData.reset()
        self.AvailableCharacters.reset()
        self.MissionData.reset()
        self.UnlockedSkills.reset()
        self.LastUpdated = Py4GW.Game.get_tick_count64()
        
    def from_pet_context(self, pet_data: PetInfo, slot_index: int) -> None:
        from ...Map import Map
        from ...Player import Player
        from ...Party import Party
        """Load data from the specified slot index in shared memory."""
        if slot_index < 0 or slot_index >= SHMEM_MAX_PLAYERS:
            raise ValueError(f"Invalid slot index: {slot_index}")
        
        self.SlotNumber = slot_index
        self.IsSlotActive = True
        self.IsAccount = False
        self.AccountEmail = Player.GetAccountEmail()
        
        if Map.IsMapLoading(): return
        if not Player.IsPlayerLoaded(): return
        if not Map.IsMapReady(): return
        if not Party.IsPartyLoaded(): return
        if Map.IsInCinematic(): return
        
        self.AccountName = Player.GetAccountName() if Player.IsPlayerLoaded() else ""
        self.IsHero = False
        self.IsPet = True
        self.IsNPC = False
        
        agent_id = pet_data.agent_id
        self.AgentData.from_context(agent_id)
        self.AgentData.AgentID = agent_id
        self.AgentData.CharacterName = pet_data.pet_name or f"PET {pet_data.owner_agent_id}s Pet"
        self.AgentData.OwnerAgentID = pet_data.owner_agent_id
        self.AgentData.HeroID = 0
        self.AgentData.Morale = 100
        self.AgentData.TargetID = pet_data.locked_target_id
        self.AgentData.LoginNumber = 0
        self.AgentData.Skillbar.reset()
        
        self.AgentPartyData.from_context()
        self.AgentPartyData.IsPartyLeader = False
        self.RankData.from_context()
        self.FactionData.reset()
        self.TitlesData.reset()
        self.QuestLog.reset()
        self.ExperienceData.reset()
        self.AvailableCharacters.reset()
        self.MissionData.reset()
        self.UnlockedSkills.reset()
        self.LastUpdated = Py4GW.Game.get_tick_count64()
        