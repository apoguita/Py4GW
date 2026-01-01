from typing import Optional
from ctypes import Structure
from ..internals.types import Vec2f
from ..internals.gw_array import GW_Array

class LoginCharacter(Structure):
    Unk00: int
    pvp_or_campaign: int
    UnkPvPData01: int
    UnkPvPData02: int
    UnkPvPData03: int
    UnkPvPData04: int
    Unk01: list[int]
    level: int
    current_map_id: int
    Unk02: list[int]
    character_name_enc: str
    
    @property
    def character_name_encoded_string(self) -> str | None:...
    
    @property
    def character_name(self) -> str | None:...

class PreGameContextStruct(Structure):
    frame_id: int
    Unk01: list[int]
    h0054: float
    h0058: float
    Unk02: list[int]
    h0060: float
    Unk03: list[int]
    h0068: float
    Unk04: int
    h0070: float
    Unk05: int
    h0078: float
    Unk06: list[int]
    h00a0: float
    h00a4: float
    h00a8: float
    Unk07: list[int]
    chosen_character_index: int
    Unk08: int  
    
    chars_array: GW_Array
    
    @property
    def chars_list(self) -> list[LoginCharacter]: ...
    
# ----------------------------------------------------------------------
# PreGameContext facade
# ----------------------------------------------------------------------
class PreGameContext:
    @staticmethod
    def get_ptr() -> int: ...

    @staticmethod
    def enable() -> None: ...

    @staticmethod
    def disable() -> None: ...

    @staticmethod
    def get_context() -> Optional[PreGameContextStruct]: ...