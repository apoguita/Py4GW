from typing import override

import PyImGui

from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_precondition import UtilitySkillPrecondition
from Sources.oazix.CustomBehaviors.skills.warrior.save_yourselves_utility import SaveYourselvesUtility


class ShouldWaitForSaveYourselvesFinalizedOnAllies(UtilitySkillPrecondition):
    def __init__(self, 
                 parent_skill: CustomSkill,
                 default_value: bool = False):
        super().__init__(parent_skill, "should_wait_for_save_yourselves_cooldown")
        from_persistence = self.load_from_persistence(str(int(default_value)))

        self.should_wait_for_save_yourselves_cooldown: bool = bool(int(from_persistence))

    @override
    def render_debug_ui(self):
        hash_id = f"should_wait_for_save_yourselves_cooldown##wait_sy_cd_{self.parent_skill_name}"
        self.should_wait_for_save_yourselves_cooldown = PyImGui.checkbox(f"Wait for SY cooldown##{hash_id}", self.should_wait_for_save_yourselves_cooldown)

    @property
    @override
    def data(self) -> str:
        return str(int(self.should_wait_for_save_yourselves_cooldown))

    @override
    def is_satisfied(self) -> bool:
        
        if not self.should_wait_for_save_yourselves_cooldown:
            return True
        
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(SaveYourselvesUtility.LOCK_KEY):
            return False

        return True

