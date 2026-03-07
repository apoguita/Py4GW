from ctypes import Structure, c_float, c_uint32, c_void_p

from ...internals.types import GamePos, Vec2f
from .constants import AGENT_ARRAY_MAX_SIZE

class AgentSHMemStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("ptr", c_void_p),
        ("agent_id", c_uint32),

    ]
    
    ptr: int | None
    agent_id: int



class AgentRefSHMemStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("index", c_uint32),
    ]

    agent_id: int
    index: int

class AgentRefArraySHMemStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("count", c_uint32),
        ("entries", AgentRefSHMemStruct * AGENT_ARRAY_MAX_SIZE),
    ]
    
    count : int
    entries: list[AgentRefSHMemStruct]
    
    def to_list(self) -> list[int]:
        result = []
        count:int = min(self.count, AGENT_ARRAY_MAX_SIZE)
        entries: list[AgentRefSHMemStruct] = self.entries
        
        for i in range(min(count, AGENT_ARRAY_MAX_SIZE)):
            ref:AgentRefSHMemStruct = entries[i]
            agent_id = int(ref.agent_id)
            if agent_id == 0:
                continue
            result.append(ref.agent_id)
        return result



class AgentArraySHMemStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("max_size", c_uint32),
        ("AgentArrayCount", c_uint32),
        ("AgentArray", AgentSHMemStruct * AGENT_ARRAY_MAX_SIZE),
        ("AllArray", AgentRefArraySHMemStruct),
        ("AllyArray", AgentRefArraySHMemStruct),
        ("NeutralArray", AgentRefArraySHMemStruct),
        ("EnemyArray", AgentRefArraySHMemStruct),
        ("SpiritPetArray", AgentRefArraySHMemStruct),
        ("MinionArray", AgentRefArraySHMemStruct),
        ("NPCMinipetArray", AgentRefArraySHMemStruct),
        ("LivingArray", AgentRefArraySHMemStruct),
        ("ItemArray", AgentRefArraySHMemStruct),
        ("OwnedItemArray", AgentRefArraySHMemStruct),
        ("GadgetArray", AgentRefArraySHMemStruct),
        ("DeadAllyArray", AgentRefArraySHMemStruct),
        ("DeadEnemyArray", AgentRefArraySHMemStruct),
    ]
    
    max_size: int
    AgentArrayCount: int
    AgentArray: list[AgentSHMemStruct]
    AllArray: AgentRefArraySHMemStruct
    AllyArray: AgentRefArraySHMemStruct
    NeutralArray: AgentRefArraySHMemStruct
    EnemyArray: AgentRefArraySHMemStruct
    SpiritPetArray: AgentRefArraySHMemStruct
    MinionArray: AgentRefArraySHMemStruct
    NPCMinipetArray: AgentRefArraySHMemStruct
    LivingArray: AgentRefArraySHMemStruct
    ItemArray: AgentRefArraySHMemStruct
    OwnedItemArray: AgentRefArraySHMemStruct
    GadgetArray: AgentRefArraySHMemStruct
    DeadAllyArray: AgentRefArraySHMemStruct
    DeadEnemyArray: AgentRefArraySHMemStruct
    
    


class AgentArraySHMemWrapper:
    def __init__(self, raw: AgentArraySHMemStruct):
        self._raw = raw
        self._agents_dict: dict[int, AgentSHMemStruct] | None = None
        
    def _build_agents_dict(self):
        if self._agents_dict is None:
            self._agents_dict = {}
            for i in range(min(self._raw.AgentArrayCount, AGENT_ARRAY_MAX_SIZE)):
                agent = self._raw.AgentArray[i]
                agent_id = int(agent.agent_id)
                if agent_id == 0:
                    continue
                self._agents_dict[agent_id] = agent
           
    def get_agent_by_id(self, agent_id: int) -> AgentSHMemStruct | None:
        self._build_agents_dict()
        if self._agents_dict is None:
            return None
        return self._agents_dict.get(agent_id, None)
    
    def to_dict(self) -> dict[int, AgentSHMemStruct]:
        self._build_agents_dict()
        return self._agents_dict if self._agents_dict is not None else {}
    
    def to_list(self) -> list[AgentSHMemStruct]:
        return list(self.to_dict().values())
    
    def to_int_list(self) -> list[int]:
        return list(self.to_dict().keys())

    def get_all_array(self) -> list[int]:
        return self._raw.AllArray.to_list()
    
    def get_ally_array(self) -> list[int]:
        return self._raw.AllyArray.to_list()
    
    def get_neutral_array(self) -> list[int]:
        return self._raw.NeutralArray.to_list()
    
    def get_enemy_array(self) -> list[int]:
        return self._raw.EnemyArray.to_list()
    
    def get_spirit_pet_array(self) -> list[int]:
        return self._raw.SpiritPetArray.to_list()
    
    def get_minion_array(self) -> list[int]:
        return self._raw.MinionArray.to_list()
    
    def get_npc_minipet_array(self) -> list[int]:
        return self._raw.NPCMinipetArray.to_list()
    
    def get_living_array(self) -> list[int]:
        return self._raw.LivingArray.to_list()
    
    def get_item_array(self) -> list[int]:
        return self._raw.ItemArray.to_list()
    
    def get_owned_item_array(self) -> list[int]:
        return self._raw.OwnedItemArray.to_list()
    
    def get_gadget_array(self) -> list[int]:
        return self._raw.GadgetArray.to_list()
    
    def get_dead_ally_array(self) -> list[int]:
        return self._raw.DeadAllyArray.to_list()
    
    def get_dead_enemy_array(self) -> list[int]:
        return self._raw.DeadEnemyArray.to_list()
    
