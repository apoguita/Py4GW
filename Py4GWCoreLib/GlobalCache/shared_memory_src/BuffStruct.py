from ctypes import Structure, c_int, c_uint, c_float
from .Globals import (
    SHMEM_MAX_NUMBER_OF_BUFFS,
)

#region BuffStruct  
class BuffUnitStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("SkillId", c_uint),
        ("Duration", c_float),
        ("Remaining", c_float),
        ("TargetAgentID", c_uint),
        ("Type", c_int),
    ]
    
    # Type hints for IntelliSense
    SkillId: int
    Duration: float
    Remaining: float
    TargetAgentID: int
    Type: int
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        self.SkillId = 0
        self.Duration = 0.0
        self.Remaining = 0.0
        self.TargetAgentID = 0
        self.Type = 0

class BuffStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Buffs", BuffUnitStruct * SHMEM_MAX_NUMBER_OF_BUFFS),
    ]
    
    # Type hints for IntelliSense
    Buffs: list[BuffUnitStruct]
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        for i in range(SHMEM_MAX_NUMBER_OF_BUFFS):
            self.Buffs[i].reset()
            
    def from_context(self, agent_id: int) -> None:
        from ...Effect import Effects
        from PyEffects import BuffType, EffectType
        
        total_effects = Effects.GetBuffs(agent_id) + Effects.GetEffects(agent_id)
        for j in range(SHMEM_MAX_NUMBER_OF_BUFFS):
            buff = total_effects[j] if j < len(total_effects) else None
            effect = buff if isinstance(buff, EffectType) else None
            upkeep = buff if isinstance(buff, BuffType) else None
            
            self.Buffs[j].SkillId = effect.skill_id if effect else 0
            self.Buffs[j].Type = 2 if effect else (1 if upkeep else 0)
            self.Buffs[j].Duration = effect.duration if effect else 0.0
            self.Buffs[j].TargetAgentID = upkeep.target_agent_id if upkeep else 0
            self.Buffs[j].Remaining = effect.time_remaining if effect else 0.0
