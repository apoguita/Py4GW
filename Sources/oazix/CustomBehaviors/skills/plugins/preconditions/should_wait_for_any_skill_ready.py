from typing import override

import PyImGui

from Py4GWCoreLib import Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_precondition import UtilitySkillPrecondition

class ShouldWaitForAnySkillReady(UtilitySkillPrecondition):
    def __init__(self, parent_skill: CustomSkill, wait_for_skills: list[CustomSkill], default_value: bool = False):
        super().__init__(parent_skill, "should_wait_for_any_skill_ready")
        from_persistence = self.load_from_persistence(str(int(default_value)))
        self.should_wait_for_any_skill_ready = bool(int(from_persistence))
        self.should_wait_for_any_skill_ready = True
        self.wait_for_skills = wait_for_skills

    @override
    def render_debug_ui(self):
        for skill in self.wait_for_skills:
            PyImGui.same_line(0,0)
            PyImGui.text(f"  - {skill.skill_name}")

        skills_names = [skill.skill_name for skill in self.wait_for_skills]
        hash = f"should_wait_for_any_skill_ready##should_wait_for_any_skill_ready_{self.parent_skill_name}_{'_'.join(skills_names)}"
        self.should_wait_for_any_skill_ready = PyImGui.checkbox(f"should_wait_for_any_skill_ready##{hash}", self.should_wait_for_any_skill_ready)

    @property
    @override
    def data(self) -> str:
        return str(int(self.should_wait_for_any_skill_ready))

    @override
    def is_satisfied(self) -> bool:
        if self.should_wait_for_any_skill_ready:
            for skill in self.wait_for_skills:
                # let's verify that the skill is in the skillbar first.
                if GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill.skill_id) == 0:
                    continue

                # At least one skill must be ready
                if Routines.Checks.Skills.IsSkillIDReady(skill.skill_id):
                    return True
            return False
        return True