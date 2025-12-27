from typing import Optional
from ctypes import Structure
from ..internals.types import Vec2f

class WorldMapContextStruct(Structure):
    frame_id: int
    h0004: int
    h0008: int
    h000c: float
    h0010: float
    h0014: int
    h0018: float
    h001c: float
    h0020: float
    h0024: float
    h0028: float
    h002c: float
    h0030: float
    h0034: float
    zoom: float
    top_left: Vec2f
    bottom_right: Vec2f
    h004c: list[int]
    h0068: float
    h006c: float
    params: list[int]


class WorldMapContext:
    @staticmethod
    def get_ptr() -> int:...
    @staticmethod
    def _update_ptr():...
    @staticmethod
    def enable():...
    @staticmethod
    def disable():...
    @staticmethod
    def get_context() -> Optional[WorldMapContextStruct]: ...
