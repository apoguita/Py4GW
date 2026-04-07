
from typing import override

import PyImGui

from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_option import UtilitySkillOption

class RawBooleanOption(UtilitySkillOption):

    def __init__(self, parent_skill: CustomSkill, capability_name: str, default_value: bool):
        super().__init__(parent_skill, capability_name)

        from_persistence = self.load_from_persistence(str(int(default_value)))
        self.option_value: bool = bool(int(from_persistence))

    @property
    @override
    def data(self) -> str:
        return str(int(self.option_value))

    @override
    def render_debug_ui(self):
        hash = f"{self.plugin_name}##{self.parent_skill_name}"
        self.option_value = PyImGui.checkbox(f"{self.plugin_name}##{hash}", self.option_value)
    
    