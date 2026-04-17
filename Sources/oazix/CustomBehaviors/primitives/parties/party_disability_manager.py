from dataclasses import dataclass
import inspect
import importlib

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.shared_memory_src.AccountStruct import AccountStruct
from Py4GWCoreLib.GlobalCache.shared_memory_src.BuffStruct import BuffUnitStruct
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.parties.party_teambuild_manager import PartyTeamBuildManager
from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.hex_prioritiy import HexPriority
from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.condition_priority import ConditionPriority

@dataclass
class AgentDisabilityStaticData:
    account_email: str # KEY
    skillbar_name: str
    hex_priorities: list[HexPriority]
    condition_priorities: list[ConditionPriority]
    
@dataclass
class AgentDisabilityLiveData:
    agent_id: int | None # KEY
    account_email: str
    skillbar_name: str

    hex_priorities: list[HexPriority]
    hex_score: int # RESULT
    
    condition_priorities: list[ConditionPriority]
    condition_score: int # RESULT

class PartyDisabilityManager():
    """
    Singleton class that aggregates disability priorities (hexes and conditions) from all party members' using custom behavior skillbars.
    """
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PartyDisabilityManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._skillbar_static_data_by_skillbar_name: dict[str, AgentDisabilityStaticData] = {}
            self._skillbar_live_data_by_agent_id: dict[int, AgentDisabilityLiveData] = {}

            self._initialized = True   
        
    def _gather_hexes(self, static_data: AgentDisabilityStaticData, buffs: list[BuffUnitStruct]) -> int:
        score:int = 0
        buff_by_id: dict[int, BuffUnitStruct] = {buff.SkillId: buff for buff in buffs}

        for hex_priority in static_data.hex_priorities:
            if hex_priority.hex_skill_id not in buff_by_id: continue
            score += hex_priority.priority.value
        return score

    def _gather_conditions(self, static_data: AgentDisabilityStaticData, buffs: list[BuffUnitStruct]) -> int:
        score:int = 0
        buff_by_id: dict[int, BuffUnitStruct] = {buff.SkillId: buff for buff in buffs}

        for condition_priority in static_data.condition_priorities:
            if condition_priority.condition_skill_id not in buff_by_id: continue
            score += condition_priority.priority.value
        return score

    def _refresh_live_data(self):
        accounts:list[AccountStruct] = GLOBAL_CACHE.ShMem.GetAllAccountData()
        self._skillbar_live_data_by_agent_id = {}

        for account in accounts:
            email = account.AccountEmail
            skillbar_name = PartyTeamBuildManager().get_custom_behavior_skillbar_used_for_account(email)
            if skillbar_name is None: continue
        
            static_data : AgentDisabilityStaticData | None = self._skillbar_static_data_by_skillbar_name.get(skillbar_name)
            if static_data is None: continue

            live_data: AgentDisabilityLiveData = AgentDisabilityLiveData(
                agent_id=account.AgentData.AgentID,
                account_email=email,
                skillbar_name=skillbar_name,

                hex_priorities=static_data.hex_priorities,
                hex_score=self._gather_hexes(static_data, account.AgentData.Buffs.Buffs),

                condition_priorities=static_data.condition_priorities,
                condition_score=self._gather_conditions(static_data, account.AgentData.Buffs.Buffs),
            )

            self._skillbar_live_data_by_agent_id[account.AgentData.AgentID] = live_data

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

    def _load_static_data(self) -> dict[str, AgentDisabilityStaticData]:

        from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader

        candidates = CustomBehaviorLoader().get_all_custom_behavior_candidates()
        if candidates is None: return {}

        result: dict[str, AgentDisabilityStaticData] = {}

        for candidate in candidates:

            skillbar_name = candidate.instance.__class__.__name__
            hex_priorities = candidate.instance.hexes_to_dispell_extra_priority()
            condition_priorities = candidate.instance.conditions_to_dispell_extra_priority()

            result[skillbar_name] = AgentDisabilityStaticData(
                account_email="",
                skillbar_name=skillbar_name,
                hex_priorities=hex_priorities,
                condition_priorities=condition_priorities,
            )

        return result
    
    def act(self):
        if self._skillbar_static_data_by_skillbar_name == {}:
            if constants.DEBUG: print(f"PartyDisabilityManager / Loading static data...")
            self._skillbar_static_data_by_skillbar_name = self._load_static_data()
        
        self._refresh_live_data() # real time data, fresh each frame

    def get_debug_data(self) -> tuple[dict[str, AgentDisabilityStaticData], dict[int, AgentDisabilityLiveData]]:
        # for UI
        return self._skillbar_static_data_by_skillbar_name, self._skillbar_live_data_by_agent_id

    def get_hex_score(self, agent_id: int) -> int:
        live_data: AgentDisabilityLiveData | None = self._skillbar_live_data_by_agent_id.get(agent_id)
        if live_data is None: return 0
        return live_data.hex_score

    def get_condition_score(self, agent_id: int) -> int:
        live_data: AgentDisabilityLiveData | None = self._skillbar_live_data_by_agent_id.get(agent_id)
        if live_data is None: return 0
        return live_data.condition_score