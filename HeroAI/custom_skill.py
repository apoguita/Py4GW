
from .custom_skill_src.skill_types import CustomSkill

from .custom_skill_src.warrior import WarriorSkills
from .custom_skill_src.ranger import RangerSkills
from .custom_skill_src.monk import MonkSkills
from .custom_skill_src.necromancer import NecromancerSkills
from .custom_skill_src.mesmer import MesmerSkills
from .custom_skill_src.elementalist import ElementalistSkills
from .custom_skill_src.assassin import AssassinSkills
from .custom_skill_src.ritualist import RitualistSkills
from .custom_skill_src.paragon import ParagonSkills
from .custom_skill_src.dervish import DervishSkills
from .custom_skill_src.pve import PVESkills


class CustomSkillClass:
    # Constants1
    MaxSkillData = 3433

    def __init__(self):
        self.skill_data = [CustomSkill() for _ in range(self.MaxSkillData)]
        self.Warrior_Skills = WarriorSkills(self.skill_data)  # Initialize WarriorSkills instance
        self.Ranger_Skills = RangerSkills(self.skill_data)  # Initialize RangerSkills instance
        self.Monk_Skills = MonkSkills(self.skill_data) # Initialize MonkSkills instance
        self.Necromancer_Skills = NecromancerSkills(self.skill_data)  # Initialize NecromancerSkills instance
        self.Mesmer_Skills = MesmerSkills(self.skill_data)  # Initialize MesmerSkills instance
        self.Elementalist_Skills = ElementalistSkills(self.skill_data)  # Initialize ElementalistSkills instance
        self.Assassin_Skills = AssassinSkills(self.skill_data)  # Initialize AssassinSkills instance
        self.Ritualist_Skills = RitualistSkills(self.skill_data)  # Initialize RitualistSkills instance
        self.Paragon_Skills = ParagonSkills(self.skill_data)  # Initialize ParagonSkills instance
        self.Dervish_Skills = DervishSkills(self.skill_data)  # Initialize DervishSkills instance
        self.PVE_Skills = PVESkills(self.skill_data)
        

    def get_skill(self, skill_id) -> CustomSkill:
        """Fetch skill by ID."""
        if 0 <= skill_id < self.MaxSkillData:
            return self.skill_data[skill_id]
        raise ValueError(f"Invalid SkillID: {skill_id}")

    def set_skill(self, skill_id, skill):
        """Update a skill."""
        if 0 <= skill_id < self.MaxSkillData:
            self.skill_data[skill_id] = skill
        else:
            raise ValueError(f"Invalid SkillID: {skill_id}")

    def is_empty_skill(self, skill_id):
        """Check if the slot is empty."""
        return self.skill_data[skill_id].SkillID == 0

    def load_skills(self):
        """Populate skill data using hardcoded definitions."""
        pass

        

       