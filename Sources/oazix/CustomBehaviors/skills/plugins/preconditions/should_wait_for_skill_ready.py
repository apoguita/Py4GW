from typing import override

import PyImGui

from Py4GWCoreLib import Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_precondition import UtilitySkillPrecondition

class ShouldWaitForSkillReady(UtilitySkillPrecondition):
    def __init__(self, parent_skill: CustomSkill, wait_for_skill: CustomSkill, default_value: bool = False):
        super().__init__(parent_skill, "should_wait_for_skill_ready")
        from_persistence = self.load_from_persistence(str(int(default_value)))
        self.should_wait_for_skill_ready = bool(int(from_persistence))
        self.wait_for_skill = wait_for_skill

    @override
    def render_debug_ui(self):
        hash = f"should_wait_for_skill_ready##should_wait_for_skill_ready_{self.parent_skill_name}_{self.wait_for_skill.skill_name}"
        self.should_wait_for_skill_ready = PyImGui.checkbox(f"should_wait_for_skill_ready##{hash}", self.should_wait_for_skill_ready)

    @property
    @override
    def data(self) -> str:
        return str(int(self.should_wait_for_skill_ready))

    @override
    def is_satisfied(self) -> bool:

        # let's verify that the skill is in the skillbar first.
        if GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.wait_for_skill.skill_id) == 0:
            return True

        if self.should_wait_for_skill_ready:
            return Routines.Checks.Skills.IsSkillIDReady(self.wait_for_skill.skill_id)
        return True