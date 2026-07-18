from ctypes import Structure, c_uint
from .Globals import (
    SKILL_BITMAP_ENTRIES,
)

class UnlockedSkillsStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Skills", c_uint * SKILL_BITMAP_ENTRIES),
    ]
    
    # Type hints for IntelliSense
    Skills: list[int]
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        for i in range(SKILL_BITMAP_ENTRIES):
            self.Skills[i] = 0
            
    def from_context(self) -> None:
        from ...Player import Player
        unlocked_skills = Player.GetUnlockedCharacterSkills()
        
        for entry in range(SKILL_BITMAP_ENTRIES):
            self.Skills[entry] = unlocked_skills[entry] if entry < len(unlocked_skills) else 0
    