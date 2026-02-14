from ctypes import Structure, c_uint, c_float
from .Globals import (
    SHMEM_MAX_NUMBER_OF_SKILLS,
)

class SkillStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Id", c_uint),
        ("Recharge", c_float),
        ("Adrenaline", c_float),
    ]
    
    # Type hints for IntelliSense
    Id: int
    Recharge: float
    Adrenaline: float
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        self.Id = 0
        self.Recharge = 0.0
        self.Adrenaline = 0.0
    
class SkillbarStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("CastingSkillID", c_uint),
        ("Skills", SkillStruct * SHMEM_MAX_NUMBER_OF_SKILLS),
        
    ]
    
    # Type hints for IntelliSense
    CastingSkillID: int
    Skills : list[SkillStruct]
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        self.CastingSkillID = 0
        for i in range(SHMEM_MAX_NUMBER_OF_SKILLS):
            self.Skills[i].reset()
            
    def from_context(self, SlotNumber:int | None = None, agent_id:int | None = None) -> None:
        from ...Agent import Agent
        from ...Skillbar import SkillBar
        from ...Player import Player
        if SlotNumber is None:
            self.CastingSkillID = Agent.GetCastingSkillID(Player.GetAgentID())
            for slot in range(SHMEM_MAX_NUMBER_OF_SKILLS):        
                skill = SkillBar.GetSkillData(slot + 1)
                
                if skill is None:
                    self.reset()  # If no skill data is available, reset the skillbar and exit
                    continue
                            
                self.Skills[slot].Id = skill.id.id
                self.Skills[slot].Recharge = skill.get_recharge if skill.id.id != 0 else 0.0
                self.Skills[slot].Adrenaline = skill.adrenaline_a if skill.id.id != 0 else 0.0  
        else:
            # Skills                   
            skills = SkillBar.GetHeroSkillbar(SlotNumber)       
            for slot in range(SHMEM_MAX_NUMBER_OF_SKILLS):        
                skill = skills[slot] if len(skills) > slot else None
                
                if skill is None:
                    self.reset()  # If no skill data is available, reset the skillbar and exit
                    continue
                            
                self.Skills[slot].Id = skill.id.id
                self.Skills[slot].Recharge = skill.get_recharge if skill.id.id != 0 else 0.0
                self.Skills[slot].Adrenaline = skill.adrenaline_a if skill.id.id != 0 else 0.0  

            self.CastingSkillID = Agent.GetCastingSkillID(agent_id) if agent_id is not None else 0

