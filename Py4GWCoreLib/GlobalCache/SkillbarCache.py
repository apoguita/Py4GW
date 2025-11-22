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
        
    def LoadHeroSkillTemplate(self, hero_index, skill_template):
        """Load a hero skill template by party position (1-based index).
        
        Note: This uses an action queue and executes asynchronously.
        
        Args:
            hero_index (int): The 1-based party position of the hero (1 = first hero, 2 = second hero, etc.)
            skill_template (str): The skill template code to load.
        """
        self._action_queue_manager.AddAction("ACTION", self._skillbar_instance.LoadHeroSkillTemplate, hero_index, skill_template)
    
    def LoadHeroSkillTemplateByHeroID(self, hero_id, skill_template):
        """Load a hero skill template by Hero ID.
        
        Note: This uses an action queue and executes asynchronously.
        
        Args:
            hero_id (int): The Hero ID (e.g., HeroType.Koss = 6)
            skill_template (str): The skill template code to load.
        """
        from Py4GWCoreLib.Party import Party
        
        # Find which party position this hero is in
        heroes = Party.GetHeroes()
        for idx, hero in enumerate(heroes):
            if hero.hero_id.GetID() == hero_id:
                hero_index = idx + 1  # 1-indexed
                self.LoadHeroSkillTemplate(hero_index, skill_template)
                return
        
        print(f"Error: Hero with ID {hero_id} is not in your party.")
    
    def LoadHeroSkillTemplateByName(self, hero_name, skill_template):
        """Load a hero skill template by hero name.
        
        Note: This uses an action queue and executes asynchronously.
        
        Args:
            hero_name (str): The hero name (e.g., "Koss")
            skill_template (str): The skill template code to load.
        """
        from PyParty import Hero
        
        try:
            hero_id = Hero(hero_name).GetID()
            self.LoadHeroSkillTemplateByHeroID(hero_id, skill_template)
        except Exception:
            print(f"Error: Could not find hero with name '{hero_name}'")
        
    def GetSkillBySlot(self, slot):
        return self._skillbar_instance.GetSkill(slot)
    
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
    
    
    
    
    
    
    
    
    
    
    
    