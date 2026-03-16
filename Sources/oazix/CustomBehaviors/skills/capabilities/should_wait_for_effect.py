from typing import override

import PyImGui

from Py4GWCoreLib import Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Player import Player
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_capability import UtilitySkillCapability

class ShouldWaitForEffect(UtilitySkillCapability):
    def __init__(self, parent_skill: CustomSkill, effect_skill: CustomSkill, default_value: bool = False):
        super().__init__(parent_skill, "should_wait_for_effect")
        from_persistence = self.load_from_persistence(str(int(default_value)))
        self.should_wait_for_effect = bool(int(from_persistence))
        self.effect_skill = effect_skill

    @property
    @override
    def data(self) -> str:
        return str(int(self.should_wait_for_effect))

    @override
    def render_debug_ui(self):
        PyImGui.text(f"Waiting for effect: {self.effect_skill.skill_name}")
        hash = f"should_wait_for_effect##should_wait_for_effect_{self.parent_skill_name}_{self.effect_skill.skill_name}"
        self.should_wait_for_effect = PyImGui.checkbox(f"should_wait_for_effect##{hash}", self.should_wait_for_effect)

    @override
    def is_satisfied(self) -> bool:

        # let's verify that the skill is in the skillbar first.
        if GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.effect_skill.skill_id) == 0:
            return True

        if self.should_wait_for_effect:
            return Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.effect_skill.skill_id)
        return True

    @override
    def get_targetting_agent_id_predicate(self):
        return lambda agent_id: True

