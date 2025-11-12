from PyAgent import AttributeClass
import PySkillbar

from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils

class SkillBar:
    @staticmethod
    def encode_skill_template(prof_primary, prof_secondary, attributes, skills):
        """Encode skill template data into template string"""
        binary_data = ''

        # Template type (4 bits) - 14 for skill template
        binary_data += Utils.dec_to_bin64(14, 4)

        # Version number (4 bits) - 0
        binary_data += Utils.dec_to_bin64(0, 4)

        # Determine profession bits needed
        max_prof = max(prof_primary, prof_secondary)
        if max_prof <= 15:  # 4 bits
            prof_bits_code = 0
            prof_bits = 4
        elif max_prof <= 63:  # 6 bits
            prof_bits_code = 1
            prof_bits = 6
        elif max_prof <= 255:  # 8 bits
            prof_bits_code = 2
            prof_bits = 8
        else:  # 10 bits
            prof_bits_code = 3
            prof_bits = 10

        # Profession bits code (2 bits)
        binary_data += Utils.dec_to_bin64(prof_bits_code, 2)

        # Primary profession
        binary_data += Utils.dec_to_bin64(prof_primary, prof_bits)

        # Secondary profession
        binary_data += Utils.dec_to_bin64(prof_secondary, prof_bits)

        # Attributes count (4 bits)
        binary_data += Utils.dec_to_bin64(len(attributes), 4)

        # Determine attribute bits needed
        max_attr = max(attributes.keys()) if attributes else 0
        if max_attr <= 15:  # 4 bits
            attr_bits_code = 0
            attr_bits = 4
        elif max_attr <= 31:  # 5 bits
            attr_bits_code = 1
            attr_bits = 5
        elif max_attr <= 63:  # 6 bits
            attr_bits_code = 2
            attr_bits = 6
        elif max_attr <= 127:  # 7 bits
            attr_bits_code = 3
            attr_bits = 7
        elif max_attr <= 255:  # 8 bits
            attr_bits_code = 4
            attr_bits = 8
        else:  # More bits as needed
            attr_bits_code = min(15, max_attr.bit_length() - 4)
            attr_bits = attr_bits_code + 4

        # Attribute bits code (4 bits)
        binary_data += Utils.dec_to_bin64(attr_bits_code, 4)

        # Attributes
        for attr_id, attr_value in attributes.items():
            binary_data += Utils.dec_to_bin64(attr_id, attr_bits)
            binary_data += Utils.dec_to_bin64(attr_value, 4)

        # Determine skill bits needed
        max_skill = max(skills) if skills else 0
        if max_skill <= 255:  # 8 bits
            skill_bits_code = 0
            skill_bits = 8
        elif max_skill <= 511:  # 9 bits
            skill_bits_code = 1
            skill_bits = 9
        elif max_skill <= 1023:  # 10 bits
            skill_bits_code = 2
            skill_bits = 10
        elif max_skill <= 2047:  # 11 bits
            skill_bits_code = 3
            skill_bits = 11
        elif max_skill <= 4095:  # 12 bits
            skill_bits_code = 4
            skill_bits = 12
        else:  # More bits as needed
            skill_bits_code = min(15, max_skill.bit_length() - 8)
            skill_bits = skill_bits_code + 8

        # Skill bits code (4 bits)
        binary_data += Utils.dec_to_bin64(skill_bits_code, 4)

        # Skills (8 skills)
        for skill in skills:
            binary_data += Utils.dec_to_bin64(skill, skill_bits)

        # Tail (1 bit) - always 0
        binary_data += '0'

        # Convert binary to base64
        return Utils.bin64_to_base64(binary_data)

    @staticmethod
    def GenerateSkillbarTemplateFrom(prof_primary, prof_secondary, attributes, skills) -> str:
        """
        Purpose: Generate template code for a specified skillbar from given data
        Args:
            prof_primary (int): The primary profession ID.
            prof_secondary (int): The secondary profession ID.
            attributes (dict): A dictionary of attribute IDs and levels.
            skills (list): A list of skill IDs.
        """
        try:
            # Encode template
            template = SkillBar.encode_skill_template(prof_primary, prof_secondary, attributes, skills)
            return template

        except Exception as e:
            # Return empty string if encoding fails
            print(f"Failed to encode skillbar template: {e}")
            return ""
            
    @staticmethod
    def GenerateSkillbarTemplate() -> str:
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
        
        """
        Purpose: Generate template code for player's skillbar
        Args: None
        Returns: str: The current skillbar template.
        """
        try:
            # Get skill IDs for all 8 slots
            skills = []
            for slot in range(1, 9):  # Slots 1-8
                skill_id = SkillBar.GetSkillIDBySlot(slot)
                skills.append(skill_id if skill_id else 0)

            # Get profession IDs
            prof_primary, prof_secondary = GLOBAL_CACHE.Agent.GetProfessionIDs(GLOBAL_CACHE.Player.GetAgentID())
            
            # Get attributes
            attributes_raw:list[AttributeClass] = GLOBAL_CACHE.Agent.GetAttributes(GLOBAL_CACHE.Player.GetAgentID())
            attributes = {}

            # Convert attributes to dictionary format
            for attr in attributes_raw:
                attr_id = int(attr.attribute_id)  # Convert enum to integer
                attr_level = attr.level_base  # Get attribute level
                if attr_level > 0:  # Only include attributes with points
                    attributes[attr_id] = attr_level

            # Encode template
            template = SkillBar.encode_skill_template(prof_primary, prof_secondary, attributes, skills)
            return template

        except Exception as e:
            # Return empty string if encoding fails
            print(f"Failed to encode skillbar template: {e}")
            return ""

    @staticmethod
    def ParseSkillbarTemplate(template:str) -> tuple[int, int, dict, list]:
        '''
        Purpose: Parse a skillbar template into its components.
        Args:
            template (str): The skillbar template to parse.
        Returns:
            prof_primary (int): The primary profession ID.
            prof_secondary (int): The secondary profession ID.
            attributes (dict): A dictionary of attribute IDs and levels.
            skills (list): A list of skill IDs.
        '''

        
        enc_template = ''

        for char in template:
            enc_template = f'{enc_template}{Utils.base64_to_bin64(char)}'
    
        template_type = Utils.bin64_to_dec(enc_template[:4])
        # if template_type != 14:
        #     return (None, None, None, None)
        enc_template = enc_template[4:]

        version_number = Utils.bin64_to_dec(enc_template[:4])
        enc_template = enc_template[4:]

        prof_bits = Utils.bin64_to_dec(enc_template[:2]) * 2 + 4
        enc_template = enc_template[2:]

        prof_primary = Utils.bin64_to_dec(enc_template[:prof_bits])
        enc_template = enc_template[prof_bits:]

        prof_secondary = Utils.bin64_to_dec(enc_template[:prof_bits])
        enc_template = enc_template[prof_bits:]

        attributes_count = Utils.bin64_to_dec(enc_template[:4])
        enc_template = enc_template[4:]

        attributes_bits = Utils.bin64_to_dec(enc_template[:4]) + 4
        enc_template = enc_template[4:]
        
        attributes = {}
        for i in range(attributes_count):
            attr = Utils.bin64_to_dec(enc_template[:attributes_bits])
            enc_template = enc_template[attributes_bits:]
            value = Utils.bin64_to_dec(enc_template[:4])
            enc_template = enc_template[4:]
            attributes[attr] = value
        
        skill_bits = Utils.bin64_to_dec(enc_template[:4]) + 8
        enc_template = enc_template[4:]

        skills = []
        for i in range(8):
            skill = Utils.bin64_to_dec(enc_template[:skill_bits])
            enc_template = enc_template[skill_bits:]
            skills.append(skill)

        return (prof_primary, prof_secondary, attributes, skills)


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