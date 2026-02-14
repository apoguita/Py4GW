from typing import Optional
from ctypes import Structure
from typing import Generic, TypeVar

T = TypeVar("T")

class CPointer(Generic[T]):
    contents: T
    
class Vec2f(Structure):
    x: float
    y: float
    
    def __init__(self, x: float = 0.0, y: float = 0.0): ...
    def to_tuple(self) -> tuple[float, float]: ...
    def to_list(self) -> list[float]: ...
    
class Vec3f(Structure):
    x: float
    y: float
    z: float
    
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0): ...
    def to_tuple(self) -> tuple[float, float, float]: ...
    def to_list(self) -> list[float]: ...
    
class GamePos(Structure):
    x: float
    y: float
    zplane: int
    
    def __init__(self, x: float = 0.0, y: float = 0.0, zplane: int = 0): ...
    def to_tuple(self) -> tuple[float, float, int]: ...