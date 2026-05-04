from typing import Optional
from ctypes import Structure
from typing import Generic, TypeAlias, TypeVar

T = TypeVar("T")

class CPointer(Generic[T]):
    contents: T
    
class Vec2f(Structure):
    x: float
    y: float
    
    def __init__(self, x: float = 0.0, y: float = 0.0): ...
    def to_tuple(self) -> tuple[float, float]: ...
    def to_list(self) -> list[float]: ...

Point2D = tuple[float, float]
PointOrPath: TypeAlias = Vec2f | Point2D | list[Vec2f] | list[Point2D]

class PointPath:
    Value: TypeAlias = PointOrPath

    @staticmethod
    def as_path(pos: PointOrPath) -> list[Vec2f]: ...
    @staticmethod
    def final_point(pos: PointOrPath) -> Vec2f | None: ...
    
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
