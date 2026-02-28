from ctypes import Structure, c_uint, c_bool, c_wchar
import Py4GW
from PyParty import HeroPartyMember, PetInfo
from Py4GWCoreLib import ThrottledTimer
from .Globals import (
    SHMEM_MAX_PLAYERS,
    SHMEM_MAX_EMAIL_LEN,
    SHMEM_MAX_CHAR_LEN,
    SHMEM_PLAYER_META_UPDATE_THROTTLE_MS,
    SHMEM_PLAYER_PROGRESS_UPDATE_THROTTLE_MS,
    SHMEM_PLAYER_STATIC_UPDATE_THROTTLE_MS,
    SHMEM_HERO_EXTRA_UPDATE_THROTTLE_MS,
    SHMEM_PET_EXTRA_UPDATE_THROTTLE_MS,
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


_player_meta_timers: dict[int, ThrottledTimer] = {}
_player_progress_timers: dict[int, ThrottledTimer] = {}
_player_static_timers: dict[int, ThrottledTimer] = {}
_player_meta_stage: dict[int, int] = {}
_player_progress_stage: dict[int, int] = {}
_player_static_stage: dict[int, int] = {}

_hero_meta_timers: dict[int, ThrottledTimer] = {}
_hero_progress_timers: dict[int, ThrottledTimer] = {}
_hero_static_timers: dict[int, ThrottledTimer] = {}
_hero_meta_stage: dict[int, int] = {}
_hero_progress_stage: dict[int, int] = {}
_hero_static_stage: dict[int, int] = {}

_pet_meta_timers: dict[int, ThrottledTimer] = {}
_pet_progress_timers: dict[int, ThrottledTimer] = {}
_pet_static_timers: dict[int, ThrottledTimer] = {}
_pet_meta_stage: dict[int, int] = {}
_pet_progress_stage: dict[int, int] = {}
_pet_static_stage: dict[int, int] = {}


def _get_slot_timer(timer_map: dict[int, ThrottledTimer], slot_index: int, throttle_ms: int) -> ThrottledTimer:
    timer = timer_map.get(slot_index)
    if timer is None:
        timer = ThrottledTimer(throttle_ms)
        timer_map[slot_index] = timer
    elif timer.throttle_time != throttle_ms:
        timer.SetThrottleTime(throttle_ms)
    return timer

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
        ("IsIsolated", c_bool),

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
    IsIsolated: bool

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
        self.IsIsolated = False

        self.LastUpdated = 0
        
    def from_context(self, account_email:str , slot_index: int) -> None:
        from ...Map import Map
        from ...Player import Player
        from ...Party import Party
        """Load data from the specified slot index in shared memory."""
        if slot_index < 0 or slot_index >= SHMEM_MAX_PLAYERS:
            raise ValueError(f"Invalid slot index: {slot_index}")
        
        force_full = (self.LastUpdated == 0)

        self.SlotNumber = slot_index
        self.IsSlotActive = True
        self.IsAccount = True
        self.AccountEmail = account_email
        self.IsHero = False
        self.IsPet = False
        self.IsNPC = False
        self.AgentData.OwnerAgentID = 0
        self.AgentData.HeroID = 0
        
        if Map.IsMapLoading(): return
        if not Player.IsPlayerLoaded(): return
        if not Map.IsMapReady(): return
        if not Party.IsPartyLoaded(): return
        if Map.IsInCinematic(): return
        
        if self.AccountName == "":
            self.AccountName = Player.GetAccountName() if Player.IsPlayerLoaded() else ""
        
        agent_id = Player.GetAgentID()
        self.AgentData.from_context(agent_id, throttle_key=slot_index)

        meta_timer = _get_slot_timer(_player_meta_timers, slot_index, SHMEM_PLAYER_META_UPDATE_THROTTLE_MS)
        if force_full or meta_timer.IsExpired():
            if force_full:
                self.AgentPartyData.from_context()
                self.RankData.from_context()
                self.FactionData.from_context()
                self.ExperienceData.from_context()
                _player_meta_stage[slot_index] = 0
            else:
                meta_stage = _player_meta_stage.get(slot_index, 0)
                if meta_stage == 0:
                    self.AgentPartyData.from_context()
                elif meta_stage == 1:
                    self.RankData.from_context()
                elif meta_stage == 2:
                    self.FactionData.from_context()
                else:
                    self.ExperienceData.from_context()
                _player_meta_stage[slot_index] = (meta_stage + 1) % 4
            meta_timer.Reset()

        progress_timer = _get_slot_timer(_player_progress_timers, slot_index, SHMEM_PLAYER_PROGRESS_UPDATE_THROTTLE_MS)
        if force_full or progress_timer.IsExpired():
            if force_full:
                self.TitlesData.from_context()
                self.QuestLog.from_context()
                _player_progress_stage[slot_index] = 0
            else:
                progress_stage = _player_progress_stage.get(slot_index, 0)
                if progress_stage == 0:
                    self.TitlesData.from_context()
                else:
                    self.QuestLog.from_context()
                _player_progress_stage[slot_index] = (progress_stage + 1) % 2
            
            progress_timer.Reset()

        static_timer = _get_slot_timer(_player_static_timers, slot_index, SHMEM_PLAYER_STATIC_UPDATE_THROTTLE_MS)
        if force_full or static_timer.IsExpired():
            if force_full:
                self.AvailableCharacters.from_context()
                self.UnlockedSkills.from_context()
                self.MissionData.from_context()
                _player_static_stage[slot_index] = 0
            else:
                static_stage = _player_static_stage.get(slot_index, 0)
                if static_stage == 0:
                    self.AvailableCharacters.from_context()
                elif static_stage == 1:
                    self.UnlockedSkills.from_context()
                else:
                    self.MissionData.from_context()
                _player_static_stage[slot_index] = (static_stage + 1) % 3
            static_timer.Reset()
        
        self.LastUpdated = Py4GW.Game.get_tick_count64()
        
    def from_hero_context(self, hero_data: HeroPartyMember, slot_index: int) -> None:
        from ...Map import Map
        from ...Player import Player
        from ...Party import Party
        """Load data from the specified slot index in shared memory."""
        if slot_index < 0 or slot_index >= SHMEM_MAX_PLAYERS:
            raise ValueError(f"Invalid slot index: {slot_index}")
        
        force_full = (self.LastUpdated == 0) or (not self.IsHero)
        
        self.SlotNumber = slot_index
        self.IsSlotActive = True
        self.IsAccount = False
        if self.AccountEmail == "":
            self.AccountEmail = Player.GetAccountEmail()
        self.IsHero = True
        self.IsPet = False
        self.IsNPC = False
        
        if Map.IsMapLoading(): return
        if not Player.IsPlayerLoaded(): return
        if not Map.IsMapReady(): return
        if not Party.IsPartyLoaded(): return
        if Map.IsInCinematic(): return
        
        if self.AccountName == "":
            self.AccountName = Player.GetAccountName() if Player.IsPlayerLoaded() else ""
        
        agent_id = hero_data.agent_id
        self.AgentData.from_context(agent_id, throttle_key=slot_index)
        self.AgentData.Morale = 100
        self.AgentData.TargetID = 0
        self.AgentData.LoginNumber = 0
        self.AgentData.AgentID = agent_id
        self.AgentData.CharacterName = hero_data.hero_id.GetName()
        if self.AgentData.OwnerAgentID == 0:
            self.AgentData.OwnerAgentID = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
        self.AgentData.HeroID = hero_data.hero_id.GetID()
        

        meta_timer = _get_slot_timer(_hero_meta_timers, slot_index, SHMEM_HERO_EXTRA_UPDATE_THROTTLE_MS)
        if force_full or meta_timer.IsExpired():
            if force_full:
                self.AgentData.Skillbar.from_hero_context(slot_index, agent_id)
                self.AgentPartyData.from_context()
                _hero_meta_stage[slot_index] = 0
            else:
                meta_stage = _hero_meta_stage.get(slot_index, 0)
                if meta_stage == 0:
                    self.AgentData.Skillbar.from_hero_context(slot_index, agent_id)
                else:
                    self.AgentPartyData.from_context()
                _hero_meta_stage[slot_index] = (meta_stage + 1) % 2
            meta_timer.Reset()
        self.AgentPartyData.IsPartyLeader = False

        progress_timer = _get_slot_timer(_hero_progress_timers, slot_index, SHMEM_PLAYER_PROGRESS_UPDATE_THROTTLE_MS)
        if force_full or progress_timer.IsExpired():
            if force_full:
                self.FactionData.reset()
                self.TitlesData.reset()
                self.QuestLog.reset()
                self.ExperienceData.reset()
                self.RankData.reset()
                _hero_progress_stage[slot_index] = 0
            else:
                progress_stage = _hero_progress_stage.get(slot_index, 0)
                if progress_stage == 0:
                    self.FactionData.reset()
                elif progress_stage == 1:
                    self.TitlesData.reset()
                elif progress_stage == 2:
                    self.QuestLog.reset()
                elif progress_stage == 3:
                    self.ExperienceData.reset()
                else:
                    self.RankData.reset()
                _hero_progress_stage[slot_index] = (progress_stage + 1) % 5
            progress_timer.Reset()

        static_timer = _get_slot_timer(_hero_static_timers, slot_index, SHMEM_PLAYER_STATIC_UPDATE_THROTTLE_MS)
        if force_full or static_timer.IsExpired():
            if force_full:
                self.AvailableCharacters.reset()
                self.MissionData.reset()
                self.UnlockedSkills.reset()
                _hero_static_stage[slot_index] = 0
            else:
                static_stage = _hero_static_stage.get(slot_index, 0)
                if static_stage == 0:
                    self.AvailableCharacters.reset()
                elif static_stage == 1:
                    self.MissionData.reset()
                else:
                    self.UnlockedSkills.reset()
                _hero_static_stage[slot_index] = (static_stage + 1) % 3
            static_timer.Reset()
        self.LastUpdated = Py4GW.Game.get_tick_count64()
        
    def from_pet_context(self, pet_data: PetInfo, slot_index: int) -> None:
        from ...Map import Map
        from ...Player import Player
        from ...Party import Party
        """Load data from the specified slot index in shared memory."""
        if slot_index < 0 or slot_index >= SHMEM_MAX_PLAYERS:
            raise ValueError(f"Invalid slot index: {slot_index}")
        
        force_full = (self.LastUpdated == 0) or (not self.IsPet)
        
        self.SlotNumber = slot_index
        self.IsSlotActive = True
        self.IsAccount = False
        if self.AccountEmail == "":
            self.AccountEmail = Player.GetAccountEmail()
        
        if Map.IsMapLoading(): return
        if not Player.IsPlayerLoaded(): return
        if not Map.IsMapReady(): return
        if not Party.IsPartyLoaded(): return
        if Map.IsInCinematic(): return
        
        if self.AccountName == "":
            self.AccountName = Player.GetAccountName() if Player.IsPlayerLoaded() else ""
        self.IsHero = False
        self.IsPet = True
        self.IsNPC = False
        
        agent_id = pet_data.agent_id
        self.AgentData.from_context(agent_id, throttle_key=slot_index)
        self.AgentData.AgentID = agent_id
        self.AgentData.CharacterName = pet_data.pet_name or f"PET {pet_data.owner_agent_id}s Pet"
        self.AgentData.OwnerAgentID = pet_data.owner_agent_id
        self.AgentData.HeroID = 0
        self.AgentData.Morale = 100
        self.AgentData.TargetID = pet_data.locked_target_id
        self.AgentData.LoginNumber = 0
        self.AgentPartyData.IsPartyLeader = False

        meta_timer = _get_slot_timer(_pet_meta_timers, slot_index, SHMEM_PET_EXTRA_UPDATE_THROTTLE_MS)
        if force_full or meta_timer.IsExpired():
            if force_full:
                self.AgentData.Skillbar.reset()
                self.AgentPartyData.reset()
                self.RankData.reset()
                _pet_meta_stage[slot_index] = 0
            else:
                meta_stage = _pet_meta_stage.get(slot_index, 0)
                if meta_stage == 0:
                    self.AgentData.Skillbar.reset()
                elif meta_stage == 1:
                    self.AgentPartyData.reset()
                else:
                    self.RankData.reset()
                _pet_meta_stage[slot_index] = (meta_stage + 1) % 3
            meta_timer.Reset()
        self.AgentPartyData.IsPartyLeader = False

        progress_timer = _get_slot_timer(_pet_progress_timers, slot_index, SHMEM_PLAYER_PROGRESS_UPDATE_THROTTLE_MS)
        if force_full or progress_timer.IsExpired():
            if force_full:
                self.FactionData.reset()
                self.TitlesData.reset()
                self.QuestLog.reset()
                self.ExperienceData.reset()
                _pet_progress_stage[slot_index] = 0
            else:
                progress_stage = _pet_progress_stage.get(slot_index, 0)
                if progress_stage == 0:
                    self.FactionData.reset()
                elif progress_stage == 1:
                    self.TitlesData.reset()
                elif progress_stage == 2:
                    self.QuestLog.reset()
                else:
                    self.ExperienceData.reset()
                _pet_progress_stage[slot_index] = (progress_stage + 1) % 4
            progress_timer.Reset()

        static_timer = _get_slot_timer(_pet_static_timers, slot_index, SHMEM_PLAYER_STATIC_UPDATE_THROTTLE_MS)
        if force_full or static_timer.IsExpired():
            if force_full:
                self.AvailableCharacters.reset()
                self.MissionData.reset()
                self.UnlockedSkills.reset()
                _pet_static_stage[slot_index] = 0
            else:
                static_stage = _pet_static_stage.get(slot_index, 0)
                if static_stage == 0:
                    self.AvailableCharacters.reset()
                elif static_stage == 1:
                    self.MissionData.reset()
                else:
                    self.UnlockedSkills.reset()
                _pet_static_stage[slot_index] = (static_stage + 1) % 3
            static_timer.Reset()
        self.LastUpdated = Py4GW.Game.get_tick_count64()
        
