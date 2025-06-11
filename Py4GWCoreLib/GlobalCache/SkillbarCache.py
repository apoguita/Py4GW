import PySkillbar
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager

class SkillbarCache:
    def __init__(self, action_queue_manager):
        self._skillbar_instance = PySkillbar.Skillbar()
        self._action_queue_manager:ActionQueueManager = action_queue_manager
        
    def _update_cache(self):
        self._skillbar_instance.GetContext()
        
    def LoadSkillTemplate(self, skill_template):
        self._action_queue_manager.AddAction("ACTION", self._skillbar_instance.LoadSkillTemplate, skill_template)
        
    def LoadHeroSkillTemplate (self, hero_index, skill_template):
        self._action_queue_manager.AddAction("ACTION", self._skillbar_instance.LoadHeroSkillTemplate, hero_index, skill_template)
        
    def GetSkillIDBySlot(self, slot):
        return self._skillbar_instance.GetSkill(slot).id.id
    
    def GetSkillbar(self):
        skill_ids = []
        for slot in range(1, 9):  # Loop through skill slots 1 to 8
            skill_id = self.GetSkillIDBySlot(slot)
            if skill_id != 0:
                skill_ids.append(skill_id)
                
        return skill_ids
    
    def GetHeroSkillbar(self, hero_index):
        hero_skillbar = self._skillbar_instance.GetHeroSkillbar(hero_index)
        return hero_skillbar
    
    def UseSkill(self, skill_slot, target_agent_id=0, aftercast_delay=0):
        self._action_queue_manager.AddActionWithDelay("ACTION",aftercast_delay, self._skillbar_instance.UseSkill, skill_slot, target_agent_id)
     
    def UseSkillTargetless(self, skill_slot, aftercast_delay=0):
        self._action_queue_manager.AddActionWithDelay("ACTION",aftercast_delay, self._skillbar_instance.UseSkillTargetless, skill_slot)
        
    def HeroUseSkill(self, target_agent_id, skill_number, hero_number):
        self._action_queue_manager.AddAction("ACTION", self._skillbar_instance.HeroUseSkill, target_agent_id, skill_number, hero_number)
      
    def ChangeHeroSecondary(self, hero_index, secondary_profession):
        self._action_queue_manager.AddAction("ACTION", self._skillbar_instance.ChangeHeroSecondary, hero_index, secondary_profession)  
        
    def GetSlotBySkillID(self, skill_id):
        for slot in range(1, 9):
            if self.GetSkillIDBySlot(slot) == skill_id:
                return slot    
        return 0
    
    def GetSkillData(self, slot):
        return self._skillbar_instance.GetSkill(slot)
        
    def GetHoveredSkillID(self):
        return self._skillbar_instance.GetHoveredSkill()
    
    def IsSkillUnlocked(self, skill_id):
        return self._skillbar_instance.IsSkillUnlocked(skill_id)
    
    def IsSkillLearnt(self, skill_id):
        return self._skillbar_instance.IsSkillLearnt(skill_id)
    
    def GetAgentID(self):
        return self._skillbar_instance.agent_id
    
    def GetDisabled(self):
        return self._skillbar_instance.disabled
    
    def GetCasting(self):
        return self._skillbar_instance.casting
    
    
    
    
    
    
    
    
    
    
    
    