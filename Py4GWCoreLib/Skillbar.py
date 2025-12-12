from PyAgent import AttributeClass
import PySkillbar

from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils

class SkillBar:   
    @staticmethod
    def LoadSkillTemplate(skill_template):
        """
        Purpose: Load a skill template by name.
        Args:
            template_name (str): The name of the skill template to load.
        Returns: None
        """
        skillbar_instance = PySkillbar.Skillbar()
        skillbar_instance.LoadSkillTemplate(skill_template)

    @staticmethod
    def LoadHeroSkillTemplate(hero_index, skill_template):
        """
        Purpose: Load a Hero skill template by party position.
        Args:
            hero_index (int): The 1-based party position of the hero (1 = first hero, 2 = second hero, etc.).
                             This is NOT the hero ID (e.g., Koss=6). To use hero IDs, use LoadHeroSkillTemplateByHeroID() instead.
            skill_template (str): The skill template code to load.
        Returns:
            bool: True if the template was loaded successfully, False otherwise.
        
        Example:
            # Load a template on the first hero in your party (regardless of which hero it is)
            SkillBar.LoadHeroSkillTemplate(1, "OQATEjpUjIACVAAAAAAAAAA")
            
            # Load on the second hero
            SkillBar.LoadHeroSkillTemplate(2, "OQASEDqEC1vcNABWAAAA")
        """
        skillbar_instance = PySkillbar.Skillbar()
        result = skillbar_instance.LoadHeroSkillTemplate(hero_index, skill_template)
        if not result:
            print(f"Warning: Failed to load skill template on hero at party position {hero_index}. "
                  f"Ensure a hero exists at that position and the template code is valid.")
        return result
    
    @staticmethod
    def LoadHeroSkillTemplateByHeroID(hero_id, skill_template):
        """
        Purpose: Load a Hero skill template by Hero ID (e.g., Koss=6, Norgu=1).
        Args:
            hero_id (int): The Hero ID (see PyParty.HeroType for values).
            skill_template (str): The skill template code to load.
        Returns:
            bool: True if the template was loaded successfully, False otherwise.
            
        Example:
            from PyParty import HeroType
            SkillBar.LoadHeroSkillTemplateByHeroID(HeroType.Koss, "OQATEjpUjIACVAAAAAAAAAA")
        """
        from Py4GWCoreLib.Party import Party
        
        # Find which party position this hero is in
        heroes = Party.GetHeroes()
        for idx, hero in enumerate(heroes):
            if hero.hero_id.GetID() == hero_id:
                hero_index = idx + 1  # 1-indexed
                return SkillBar.LoadHeroSkillTemplate(hero_index, skill_template)
        
        # Hero not found in party
        try:
            from PyParty import Hero
            hero_name = Hero(hero_id).GetName()
            print(f"Error: Hero '{hero_name}' (ID: {hero_id}) is not in your party.")
        except Exception:
            print(f"Error: Hero with ID {hero_id} is not in your party.")
        return False
    
    @staticmethod
    def LoadHeroSkillTemplateByName(hero_name, skill_template):
        """
        Purpose: Load a Hero skill template by hero name.
        Args:
            hero_name (str): The hero name (e.g., "Koss", "Norgu", etc.)
            skill_template (str): The skill template code to load.
        Returns:
            bool: True if the template was loaded successfully, False otherwise.
            
        Example:
            SkillBar.LoadHeroSkillTemplateByName("Koss", "OQATEjpUjIACVAAAAAAAAAA")
        """
        from Py4GWCoreLib.Party import Party
        from PyParty import Hero
        
        try:
            hero_id = Hero(hero_name).GetID()
            return SkillBar.LoadHeroSkillTemplateByHeroID(hero_id, skill_template)
        except Exception:
            print(f"Error: Could not find hero with name '{hero_name}'")
            return False

    @staticmethod
    def GetSkillbar():
        """
        Purpose: Retrieve the IDs of all 8 skills in the skill bar.
        Returns: list: A list containing the IDs of all 8 skills.
        """
        skill_ids = []
        for slot in range(1, 9):  # Loop through skill slots 1 to 8
            skill_id = SkillBar.GetSkillIDBySlot(slot)
            if skill_id != 0:
                skill_ids.append(skill_id)
        return skill_ids

    @staticmethod
    def GetZeroFilledSkillbar():
        skill_ids : dict[int, int] = {}
        for slot in range(1, 9):  # Loop through skill slots 1 to 8
            skill_ids[slot] = SkillBar.GetSkillIDBySlot(slot)

        return skill_ids
    
    @staticmethod
    def GetHeroSkillbar(hero_index):
        """
        Purpose: Retrieve the skill bar of a hero.
        Args:
            hero_index (int): The index of the hero to retrieve the skill bar from.
        Returns: list: A list of dictionaries containing skill details.
        """
        skillbar_instance = PySkillbar.Skillbar()
        hero_skillbar = skillbar_instance.GetHeroSkillbar(hero_index)
        return hero_skillbar

        
    @staticmethod
    def UseSkill(skill_slot, target_agent_id=0):
        """
        Purpose: Use a skill from the skill bar.
        Args:
            skill_slot (int): The slot number of the skill to use (1-8).
            target_agent_id (int, optional): The ID of the target agent. Default is 0.
        Returns: None
        """
        skillbar_instance = PySkillbar.Skillbar()
        skillbar_instance.UseSkill(skill_slot, target_agent_id)
        
    @staticmethod
    def UseSkillTargetless(skill_slot):
        """
        Purpose: Use a skill from the skill bar without a target.
        Args:
            skill_slot (int): The slot number of the skill to use (1-8).
        Returns: None
        """
        skillbar_instance = PySkillbar.Skillbar()
        skillbar_instance.UseSkillTargetless(skill_slot)

    @staticmethod
    def HeroUseSkill(target_agent_id, skill_number, hero_number):
        """
        Have a hero use a skill.
        Args:
            target_agent_id (int): The target agent ID.
            skill_number (int): The skill number (1-8)
            hero_number (int): The hero number (1-7)
        """
        skillbar_instance = PySkillbar.Skillbar()
        skillbar_instance.HeroUseSkill(target_agent_id, skill_number, hero_number)

    @staticmethod
    def ChangeHeroSecondary(hero_index, secondary_profession):
        """
        Purpose: Change the secondary profession of a hero.
        Args:
            hero_index (int): The index of the hero to change.
            secondary_profession (int): The ID of the secondary profession to change to.
        Returns: None
        """
        skillbar_instance = PySkillbar.Skillbar()
        skillbar_instance.ChangeHeroSecondary(hero_index, secondary_profession)

    @staticmethod
    def GetSkillIDBySlot(skill_slot):
        """
        Purpose: Retrieve the data of a skill by its slot number.
        Args:
            skill_slot (int): The slot number of the skill to retrieve (1-8).
        Returns: dict: A dictionary containing skill details retrieved by slot.
        """
        skillbar_instance = PySkillbar.Skillbar()
        skill = skillbar_instance.GetSkill(skill_slot)
        return skill.id.id

    #get the slot by skillid
    @staticmethod
    def GetSlotBySkillID(skill_id):
        """
        Purpose: Retrieve the slot number of a skill by its ID.
        Args:
            skill_id (int): The ID of the skill to retrieve.
        Returns: int: The slot number of the skill.
        """
        #search for all slots until skill found and return it
        for i in range(1, 9):
            if SkillBar.GetSkillIDBySlot(i) == skill_id:
                return i

        return 0
    
    @staticmethod
    def GetSkillData(slot):
        """
        Purpose: Retrieve the data of a skill by its ID.
        Args:
            slot (int): The slot number of the skill to retrieve (1-8).
        Returns: dict: A SkillbarSkill object containing skill details.
        """
        skill_instance = PySkillbar.Skillbar()
        return skill_instance.GetSkill(slot)

    @staticmethod
    def GetHoveredSkillID():
        """
        Purpose: Retrieve the ID of the skill that is currently hovered.
        Args: None
        Returns: int: The ID of the skill that is currently hovered.
        """
        skillbar_instance = PySkillbar.Skillbar()
        hovered_skill_id = skillbar_instance.GetHoveredSkill()
        return hovered_skill_id

    @staticmethod
    def IsSkillUnlocked(skill_id):
        """
        Purpose: Check if a skill is unlocked.
        Args:
            skill_id (int): The ID of the skill to check.
        Returns: bool: True if the skill is unlocked, False otherwise.
        """
        skillbar_instance = PySkillbar.Skillbar()
        return skillbar_instance.IsSkillUnlocked(skill_id)

    @staticmethod
    def IsSkillLearnt(skill_id):
        """
        Purpose: Check if a skill is learnt.
        Args:
            skill_id (int): The ID of the skill to check.
        Returns: bool: True if the skill is learnt, False otherwise.
        """
        skillbar_instance = PySkillbar.Skillbar()
        return skillbar_instance.IsSkillLearnt(skill_id)

    @staticmethod
    def GetAgentID():
        """
        Purpose: Retrieve the agent ID of the skill bar owner.
        Args: None
        Returns: int: The agent ID of the skill bar owner.
        """
        skillbar_instance = PySkillbar.Skillbar()
        return skillbar_instance.agent_id

    @staticmethod
    def GetDisabled():
        """
        Purpose: Check if the skill bar is disabled.
        Args: None
        Returns: bool: True if the skill bar is disabled, False otherwise.
        """
        skillbar_instance = PySkillbar.Skillbar()
        return skillbar_instance.disabled

    @staticmethod
    def GetCasting():
        """
        Purpose: Check if the skill bar is currently casting.
        Args: None
        Returns: bool: True if the skill bar is currently casting, False otherwise.
        """
        skillbar_instance = PySkillbar.Skillbar()
        return skillbar_instance.casting
