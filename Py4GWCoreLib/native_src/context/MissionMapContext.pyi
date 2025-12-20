from typing import Optional
from ctypes import Structure
from ..internals.types import Vec2f
from ..internals.gw_array import GW_Array

    
    
# ----------------------------------------------------------------------
# Mission map structs
# ----------------------------------------------------------------------

class MissionMapSubContext(Structure):
    h0000: list[int]


class MissionMapSubContext2(Structure):
    h0000: int
    player_mission_map_pos: Vec2f
    h000c: int
    mission_map_size: Vec2f
    unk: float
    mission_map_pan_offset: Vec2f
    mission_map_pan_offset2: Vec2f
    unk2: list[float]
    unk3: list[int]


class MissionMapContextStruct(Structure):
    size: Vec2f
    h0008: int
    last_mouse_location: Vec2f
    frame_id: int
    player_mission_map_pos: Vec2f
    h0020: GW_Array
    h0030: int
    h0034: int
    h0038: int
    h003c: Optional[MissionMapSubContext2]
    h0040: int
    h0044: int
    
# ----------------------------------------------------------------------
# MissionMapContext facade
# ----------------------------------------------------------------------

class MissionMapContext:
    @staticmethod
    def get_ptr() -> int: ...

    @staticmethod
    def enable() -> None: ...

    @staticmethod
    def disable() -> None: ...

    @staticmethod
    def get_context() -> Optional[MissionMapContextStruct]: ...