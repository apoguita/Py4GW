from ...internals.types import Vec2f, GamePos
from ctypes import Structure

class AgentSHMemStruct(Structure):
    ptr: int
    Position: GamePos
    z: float
    rotation_angle: float
    velocity: Vec2f
    agent_type: int
    agent_id: int
    item_id: int
    owner_id: int
    player_number: int
    profession: list[int]
    level: int
    EnergyValues: list[float]
    HPValues: list[float]
    login_number: int
    allegiance: int
    effects: int
    type_map: int
    model_state: int
    casting_skill_id: int

class AgentRefSHMemStruct(Structure):
    agent_id: int
    index: int

class AgentRefArraySHMemStruct(Structure):
    count: int
    entries: list[AgentRefSHMemStruct]
    def to_dict(self, agents) -> dict[int, AgentSHMemStruct]: ...
    def to_list(self, agents) -> list[AgentSHMemStruct]: ...

class AgentArraySHMemStruct(Structure):
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
    def __init__(self, struct: AgentArraySHMemStruct):...
    def _build_agent_dict(self) -> dict[int, AgentSHMemStruct]: ...
    def get_agent_by_id(self, agent_id: int) -> AgentSHMemStruct | None: ...
    def to_dict(self) -> dict[int, AgentSHMemStruct]: ...
    def to_list(self) -> list[AgentSHMemStruct]: ...
    def get_ally_array(self) -> list[AgentSHMemStruct]:...
    def get_neutral_array(self) -> list[AgentSHMemStruct]:...
    def get_enemy_array(self) -> list[AgentSHMemStruct]:...
    def get_spirit_pet_array(self) -> list[AgentSHMemStruct]:...
    def get_minion_array(self) -> list[AgentSHMemStruct]:...
    def get_npc_minipet_array(self) -> list[AgentSHMemStruct]:...
    def get_living_array(self) -> list[AgentSHMemStruct]:...
    def get_item_array(self) -> list[AgentSHMemStruct]:...
    def get_owned_item_array(self) -> list[AgentSHMemStruct]:...
    def get_gadget_array(self) -> list[AgentSHMemStruct]:...
    def get_dead_ally_array(self) -> list[AgentSHMemStruct]:...
    def get_dead_enemy_array(self) -> list[AgentSHMemStruct]:...
        