from typing import Optional
from ctypes import Structure
    
# ----------------------------------------------------------------------
# GameplayContextStruct
# ----------------------------------------------------------------------

class GameplayContextStruct(Structure):
    h0000: list[int]
    mission_map_zoom: float
    unk: list[int]


class GameplayContext:
    @staticmethod
    def get_ptr() -> int: ...

    @staticmethod
    def enable() -> None: ...

    @staticmethod
    def disable() -> None: ...

    @staticmethod
    def get_context() -> Optional[GameplayContextStruct]: ...