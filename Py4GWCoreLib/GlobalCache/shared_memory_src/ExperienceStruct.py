from ctypes import Structure,  c_uint, c_float
#region Experience  
class ExperienceStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Level", c_uint),
        ("Experience", c_uint),
        ("ProgressPct", c_float),
        ("CurrentSkillPoints", c_uint),
        ("TotalEarnedSkillPoints", c_uint),
    ]
    
    # Type hints for IntelliSense
    Level: int
    Experience: int
    ProgressPct: float
    CurrentSkillPoints: int
    TotalEarnedSkillPoints: int
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        self.Level = 0
        self.Experience = 0
        self.ProgressPct = 0.0
        self.CurrentSkillPoints = 0
        self.TotalEarnedSkillPoints = 0
        
    def from_context(self) -> None:
        from ...Player import Player
        from ...py4gwcorelib_src.Utils import Utils
        self.Level = Player.GetLevel()
        self.Experience = Player.GetExperience()
        self.ProgressPct = Utils.GetExperienceProgression(Player.GetExperience())
        skillpoints_data = Player.GetSkillPointData()
        self.CurrentSkillPoints = skillpoints_data[0]
        self.TotalEarnedSkillPoints = skillpoints_data[1]
 