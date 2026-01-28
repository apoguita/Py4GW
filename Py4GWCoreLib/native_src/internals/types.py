import ctypes
from ctypes import Structure, c_uint32, c_uint8, c_float, sizeof

from typing import Generic, TypeVar


class DyeInfoStruct(Structure):
    """Dye information for items (3 bytes)."""
    _pack_ = 1
    _fields_ = [
        ("dye_tint", c_uint8),        # 0x00
        ("dye1", c_uint8, 4),         # 0x01 low nibble
        ("dye2", c_uint8, 4),         # 0x01 high nibble
        ("dye3", c_uint8, 4),         # 0x02 low nibble
        ("dye4", c_uint8, 4),         # 0x02 high nibble
    ]


class Vec2f(Structure):
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
    ]
    
    def __init__(self, x: float = 0.0, y: float = 0.0):
        super().__init__()   # keep ctypes initialization intact
        self.x = x
        self.y = y
        
    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)
        
        
class Vec3f(Structure):
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
        ("z", c_float),
    ]  
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        super().__init__()   # keep ctypes initialization intact
        self.x = x
        self.y = y
        self.z = z
        
    def to_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)

class GamePos(Structure):
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
        ("zplane", c_uint32),
    ]
    
    def __init__(self, x: float = 0.0, y: float = 0.0, zplane: int = 0):
        super().__init__()   # keep ctypes initialization intact
        self.x = x
        self.y = y
        self.zplane = zplane
        
    def to_tuple(self) -> tuple[float, float, int]:
        return (self.x, self.y, self.zplane)
    

