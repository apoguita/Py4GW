from typing import Optional
from ctypes import Structure
from typing import Generic, TypeVar

T = TypeVar("T")

class CPointer(Generic[T]):
    contents: T
    
class Vec2f(Structure):
    x: float
    y: float
    
class Vec3f(Structure):
    x: float
    y: float
    z: float
    
class GamePos(Structure):
    x: float
    y: float
    zplane: int