import ctypes
from ctypes import Structure, c_uint32, c_float, sizeof

from typing import Generic, TypeVar

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
    
    def to_list(self) -> list[float]:
        return [self.x, self.y]
    
    #operators
    def __add__(self, other):
        if isinstance(other, Vec2f):
            return Vec2f(self.x + other.x, self.y + other.y)
        return NotImplemented
    
    def __sub__(self, other):
        if isinstance(other, Vec2f):
            return Vec2f(self.x - other.x, self.y - other.y)
        return NotImplemented
    
    def __mul__(self, scalar: float):
        return Vec2f(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar: float):
        if scalar != 0:
            return Vec2f(self.x / scalar, self.y / scalar)
        raise ValueError("Cannot divide by zero")
    
    def __repr__(self):
        return f"Vec2f(x={self.x}, y={self.y})"
    
    def __eq__(self, value):
        return super().__eq__(value)
        
        
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

    def to_list(self) -> list[float]:
        return [self.x, self.y, self.z]

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
    

