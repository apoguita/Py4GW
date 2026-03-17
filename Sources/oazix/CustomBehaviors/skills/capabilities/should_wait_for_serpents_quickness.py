from typing import override

import PyImGui

from Py4GWCoreLib import Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Player import Player
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_capability import UtilitySkillCapability

class ShouldWaitForSerpentsQuickness(UtilitySkillCapability):
    def __init__(self, parent_skill: CustomSkill, default_value: bool = False):
        super().__init__(parent_skill, "should_wait_for_serpents_quickness")
        from_persistence = self.load_from_persistence(str(int(default_value)))
        self.should_wait_for_serpents_quickness = bool(int(from_persistence))
        self.serpents_quickness_skill_id = GLOBAL_CACHE.Skill.GetID("Serpents_Quickness")

    @override
    def render_debug_ui(self):
        PyImGui.text(f"Waiting for Serpents Quickness")
        hash = f"should_wait_for_serpents_quickness##should_wait_for_serpents_quickness_{self.parent_skill_name}"
        self.should_wait_for_serpents_quickness = PyImGui.checkbox(f"should_wait_for_serpents_quickness##{hash}", self.should_wait_for_serpents_quickness)
    
    @property
    @override
    def data(self) -> str:
        return str(int(self.should_wait_for_serpents_quickness))
    
    @override
    def is_satisfied(self) -> bool:
        # let's verify that the skill is in the skillbar first.
        if GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.serpents_quickness_skill_id) == 0:
            return True

        if self.should_wait_for_serpents_quickness:
            return Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.serpents_quickness_skill_id)
        return True