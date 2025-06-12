import PySkill
import PySkillbar

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
    def LoadHeroSkillTemplate (hero_index, skill_template):
        """
        Purpose: Load a Hero skill template by Hero index and Template.
        Args:
            hero_index: int, template_name (str): The name of the skill template to load.
        Returns: None
        """
        skillbar_instance = PySkillbar.Skillbar()
        skillbar_instance.LoadHeroSkillTemplate(hero_index, skill_template)

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
            skill_id (int): The ID of the skill to retrieve.
        Returns: dict: A dictionary containing skill details like ID, adrenaline, recharge, and event data.
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
