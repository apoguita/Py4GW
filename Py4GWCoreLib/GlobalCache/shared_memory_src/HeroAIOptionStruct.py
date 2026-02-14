from ctypes import Structure, c_float, c_bool
from ...native_src.internals.types import Vec3f, Vec2f
from .Globals import (
    SHMEM_MAX_NUMBER_OF_SKILLS,
)

class HeroAIOptionStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Following", c_bool),
        ("Avoidance", c_bool), 
        ("Looting", c_bool), 
        ("Targeting", c_bool),
        ("Combat", c_bool),
        ("Skills", c_bool * SHMEM_MAX_NUMBER_OF_SKILLS),
        ("IsFlagged", c_bool),
        ("FlagPosX", c_float),
        ("FlagPosY", c_float),
        ("FlagFacingAngle", c_float),
        ("FollowPos", Vec2f),
        ("FlagPos", Vec2f),
        ("AllFlag", Vec2f),
    ] 
    
    
    # Type hints for IntelliSense
    Following : bool
    Avoidance : bool
    Looting : bool
    Targeting : bool
    Combat : bool
    Skills : list[bool]
    IsFlagged : bool
    FlagPosX : float
    FlagPosY : float
    FlagFacingAngle : float
    FollowPos : Vec2f
    FlagPos : Vec2f
    AllFlag : Vec2f
    
    def reset(self) -> None:
        """Reset all fields to zero or default values."""
        self.Following = True
        self.Avoidance = True
        self.Looting = True
        self.Targeting = True
        self.Combat = True
        for i in range(SHMEM_MAX_NUMBER_OF_SKILLS):
            self.Skills[i] = True
        self.IsFlagged = False
        self.FlagPosX = 0.0
        self.FlagPosY = 0.0
        self.FlagFacingAngle = 0.0
        self.FollowPos = Vec2f(0.0, 0.0)
        self.FlagPos = Vec2f(0.0, 0.0)
        self.AllFlag = Vec2f(0.0, 0.0)