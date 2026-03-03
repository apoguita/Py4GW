from ctypes import Structure, c_float, c_uint32, c_void_p

from ...internals.types import GamePos, Vec2f
from .constants import AGENT_ARRAY_MAX_SIZE

class AgentSHMemStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("ptr", c_void_p),
        ("Position", GamePos),
        ("z", c_float),
        ("rotation_angle", c_float),
        ("velocity", Vec2f),
        ("agent_type", c_uint32),
        ("agent_id", c_uint32),
        ("item_id", c_uint32),
        ("owner_id", c_uint32),
        ("player_number", c_uint32),
        ("profession", c_uint32 * 2),
        ("level", c_uint32),
        ("EnergyValues", c_float * 3),
        ("HPValues", c_float * 3),
        ("login_number", c_uint32),
        ("allegiance", c_uint32),
        ("effects", c_uint32),
        ("type_map", c_uint32),
        ("model_state", c_uint32),
        ("casting_skill_id", c_uint32),
    ]


class AgentRefSHMemStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("index", c_uint32),
    ]


class AgentRefArraySHMemStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("count", c_uint32),
        ("entries", AgentRefSHMemStruct * AGENT_ARRAY_MAX_SIZE),
    ]
    
    def to_list(self, agents_by_id: dict[int, AgentSHMemStruct] | None = None) -> list:
        result = []
        for i in range(min(self.count, AGENT_ARRAY_MAX_SIZE)):
            ref = self.entries[i]
            agent_id = int(ref.agent_id)
            if agent_id == 0:
                continue
            if agents_by_id is None:
                result.append(agent_id)
                continue
            agent = agents_by_id.get(agent_id)
            if agent is not None:
                result.append(agent)
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

    def get_all_array(self) -> list[AgentSHMemStruct]:
        return self._raw.AllArray.to_list(self.to_dict())
    
    def get_ally_array(self) -> list[AgentSHMemStruct]:
        return self._raw.AllyArray.to_list(self.to_dict())
    
    def get_neutral_array(self) -> list[AgentSHMemStruct]:
        return self._raw.NeutralArray.to_list(self.to_dict())
    
    def get_enemy_array(self) -> list[AgentSHMemStruct]:
        return self._raw.EnemyArray.to_list(self.to_dict())
    
    def get_spirit_pet_array(self) -> list[AgentSHMemStruct]:
        return self._raw.SpiritPetArray.to_list(self.to_dict())
    
    def get_minion_array(self) -> list[AgentSHMemStruct]:
        return self._raw.MinionArray.to_list(self.to_dict())
    
    def get_npc_minipet_array(self) -> list[AgentSHMemStruct]:
        return self._raw.NPCMinipetArray.to_list(self.to_dict())
    
    def get_living_array(self) -> list[AgentSHMemStruct]:
        return self._raw.LivingArray.to_list(self.to_dict())
    
    def get_item_array(self) -> list[AgentSHMemStruct]:
        return self._raw.ItemArray.to_list(self.to_dict())
    
    def get_owned_item_array(self) -> list[AgentSHMemStruct]:
        return self._raw.OwnedItemArray.to_list(self.to_dict())
    
    def get_gadget_array(self) -> list[AgentSHMemStruct]:
        return self._raw.GadgetArray.to_list(self.to_dict())
    
    def get_dead_ally_array(self) -> list[AgentSHMemStruct]:
        return self._raw.DeadAllyArray.to_list(self.to_dict())
    
    def get_dead_enemy_array(self) -> list[AgentSHMemStruct]:
        return self._raw.DeadEnemyArray.to_list(self.to_dict())
    
