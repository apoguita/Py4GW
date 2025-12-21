from typing import Optional
from ctypes import Structure
from ..internals.types import Vec2f
from ..internals.gw_array import GW_Array

class LoginCharacter(Structure):
    unk0: int
    character_name: str

class PreGameContextStruct(Structure):
    frame_id: int
    
    h0004: list[int]
    chosen_character_index: int
    """
    h0128: list[int]
    index_1: int
    index_2: int
    
    chars: GW_Array
    """
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