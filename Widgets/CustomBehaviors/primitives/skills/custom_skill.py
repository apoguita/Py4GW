import pathlib
from HeroAI.custom_skill import CustomSkillClass
from Py4GWCoreLib import GLOBAL_CACHE
from Widgets.CustomBehaviors.primitives.skills.custom_skill_nature import CustomSkillNature

class CustomSkill:

    custom_skill_class = CustomSkillClass()
    
    def __init__(self, skill_name: str):
        self.skill_name: str = skill_name
        self.skill_id: int = GLOBAL_CACHE.Skill.GetID(skill_name)
        nature_value:int = CustomSkill.custom_skill_class.get_skill(self.skill_id).Nature
        self.skill_nature:CustomSkillNature = CustomSkillNature(nature_value)
        self.skill_slot:int = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.skill_id) if self.skill_id != 0 else 0

    def get_texture(self) -> str:

        current_path = pathlib.Path.cwd()
        # path is c:\git\py4gw if launched from widget-manager
        # path is c:\git\py4gw\Widgets if the root python file is called manually by the console

        texture_file = ''
        if self.skill_id is not None and self.skill_id > 0:

            prefix = ""
            if "Widgets" in str(current_path):
                prefix = "..\\"

            texture_file = prefix + GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(self.skill_id)
        else:

            prefix = ""
            if "Widgets" not in str(current_path):
                prefix = "Widgets\\"

            texture_file = prefix + f"CustomBehaviors\\gui\\textures\\{self.skill_name}.png"

        return texture_file

            