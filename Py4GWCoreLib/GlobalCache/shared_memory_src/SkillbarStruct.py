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
            
    def from_context(self) -> None:
        from ...Agent import Agent
        from ...Skillbar import SkillBar
        from ...Player import Player

        self.CastingSkillID = Agent.GetCastingSkillID(Player.GetAgentID())
        skillbar = SkillBar.GetSkillbar()
        
        for i, skill in enumerate(skillbar):        
            skill = SkillBar.GetSkillData(i + 1)
            
            if skill is None: continue
                        
            self.Skills[i].Id = skill.id.id
            self.Skills[i].Recharge = skill.get_recharge if skill.id.id != 0 else 0.0
            self.Skills[i].Adrenaline = skill.adrenaline_a if skill.id.id != 0 else 0.0  
        
        
    def from_hero_context(self, hero_index: int, agent_id: int) -> None:
        from ...Agent import Agent
        from ...Skillbar import SkillBar

        # Skills           
        self.CastingSkillID = Agent.GetCastingSkillID(agent_id) if agent_id is not None else 0
        skills = SkillBar.GetHeroSkillbar(hero_index) 
        
        for i, skill in enumerate(skills):                      
            self.Skills[i].Id = skill.id.id
            self.Skills[i].Recharge = skill.get_recharge if skill.id.id != 0 else 0.0
            self.Skills[i].Adrenaline = skill.adrenaline_a if skill.id.id != 0 else 0.0  

            

