
from typing import override

import PyImGui

from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_option import UtilitySkillOption

class RawNumberOption(UtilitySkillOption):

    def __init__(self, parent_skill: CustomSkill, capability_name: str, default_value: float):
        super().__init__(parent_skill, capability_name)
        
        from_persistence = self.load_from_persistence(str(default_value))
        self.option_value: float = float(from_persistence)

    @property
    @override
    def data(self) -> str:
        return str(self.option_value)

    @override
    def render_debug_ui(self):
        hash = f"{self.plugin_name}##{self.parent_skill_name}"
        self.option_value = PyImGui.input_float(f"{self.plugin_name}##{hash}", self.option_value)
    

    
    