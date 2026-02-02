from dataclasses import dataclass


@dataclass
class SortableAgentData:
    agent_id: int
    distance_from_player: float
    hp: float
    is_caster: bool
    is_melee: bool
    is_martial: bool
    enemy_quantity_within_range: int
    agent_quantity_within_range: int
    energy: float

