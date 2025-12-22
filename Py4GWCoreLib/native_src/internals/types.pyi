from typing import Optional
from ctypes import Structure

class Vec2f(Structure):
    x: float
    y: float
    
class GamePos(Structure):
    x: float
    y: float
    zplane: int