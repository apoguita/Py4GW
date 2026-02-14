from ctypes import Structure, c_uint
from .Globals import (
    MISSION_BITMAP_ENTRIES,
)
#region MissionData
class MissionDataStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("NormalModeCompleted", c_uint * MISSION_BITMAP_ENTRIES),
        ("NormalModeBonus", c_uint * MISSION_BITMAP_ENTRIES),
        ("HardModeCompleted", c_uint * MISSION_BITMAP_ENTRIES),
        ("HardModeBonus", c_uint * MISSION_BITMAP_ENTRIES),
    ]
    
    # Type hints for IntelliSense
    NormalModeCompleted: list[int]
    NormalModeBonus: list[int]
    HardModeCompleted: list[int]
    HardModeBonus: list[int]
    
    def reset(self) -> None:
        """Reset all fields to zero (in-place)."""

        for i in range(MISSION_BITMAP_ENTRIES):
            self.NormalModeCompleted[i] = 0
            self.NormalModeBonus[i] = 0
            self.HardModeCompleted[i] = 0
            self.HardModeBonus[i] = 0

        
    def from_context(self) -> None:
        from ...Player import Player
        missions_completed = Player.GetMissionsCompleted()
        missions_bonus = Player.GetMissionsBonusCompleted()
        missions_completed_hm = Player.GetMissionsCompletedHM()
        missions_bonus_hm = Player.GetMissionsBonusCompletedHM()
        
        for entry in range(MISSION_BITMAP_ENTRIES):
            self.NormalModeCompleted[entry] = missions_completed[entry] if entry < len(missions_completed) else 0
            self.NormalModeBonus[entry] = missions_bonus[entry] if entry < len(missions_bonus) else 0
            self.HardModeCompleted[entry] = missions_completed_hm[entry] if entry < len(missions_completed_hm) else 0
            self.HardModeBonus[entry] = missions_bonus_hm[entry] if entry < len(missions_bonus_hm) else 0    


