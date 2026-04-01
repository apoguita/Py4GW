from typing import override

import PyImGui

from Py4GWCoreLib import Routines, GLOBAL_CACHE
from Py4GWCoreLib.Player import Player
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_precondition import UtilitySkillPrecondition

class ShouldWaitForHeroicRefrain(UtilitySkillPrecondition):
    def __init__(self, parent_skill: CustomSkill, default_value: bool = False):
        super().__init__(parent_skill, "should_wait_for_heroic_refrain")
        from_persistence = self.load_from_persistence(str(int(default_value)))
        self.should_wait_for_heroic_refrain : bool = bool(int(from_persistence))
        self.heroic_refrain_skill_id = GLOBAL_CACHE.Skill.GetID("Heroic_Refrain")
    
    @property
    @override
    def data(self) -> str:
        return str(int(self.should_wait_for_heroic_refrain))

    @override
    def render_debug_ui(self):
        hash = f"should_wait_for_heroic_refrain##should_wait_for_heroic_refrain_{self.parent_skill_name}"
        self.should_wait_for_heroic_refrain = PyImGui.checkbox(f"should_wait_for_heroic_refrain##{hash}", self.should_wait_for_heroic_refrain)

    @override
    def is_satisfied(self) -> bool:
        if self.should_wait_for_heroic_refrain:
            return Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.heroic_refrain_skill_id)
        return True