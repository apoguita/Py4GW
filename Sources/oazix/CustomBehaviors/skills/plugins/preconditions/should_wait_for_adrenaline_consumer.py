from collections.abc import Callable
from typing import override

import PyImGui

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_precondition import UtilitySkillPrecondition

class ShouldWaitForAdrenalineConsumer(UtilitySkillPrecondition):
    """
    Precondition plugin that waits for adrenaline consumer skills to be ready
    before using adrenaline generating skills.
    
    This prevents wasting adrenaline when high-value consumer skills (like Save Yourselves)
    are about to be ready.
    """
    def __init__(self, 
                 parent_skill: CustomSkill, 
                 generated_strike_of_adrenaline: Callable[[], int],
                 adrenaline_consumers: list[CustomSkillUtilityBase], 
                 default_value: bool = False):
        super().__init__(parent_skill, "should_wait_for_adrenaline_consumer")
        from_persistence = self.load_from_persistence(str(int(default_value)))

        self.should_wait_for_adrenaline_consumer: bool = bool(int(from_persistence))
        self.generated_strike_of_adrenaline: Callable[[], int] = generated_strike_of_adrenaline
        self.adrenaline_consumers: list[CustomSkillUtilityBase] = adrenaline_consumers

    @override
    def render_debug_ui(self):
        
        PyImGui.text(f"Generated Strikes of Adrenaline: {self.generated_strike_of_adrenaline()}")
        # adrenaline generated is about 25 per strike
        PyImGui.text(f"Generated Adrenaline: {self.generated_strike_of_adrenaline() * 25}")

        for consumer in self.adrenaline_consumers:
            PyImGui.text(f"  -> {consumer.custom_skill.skill_name}")
            PyImGui.text(f"    - adrenaline required: {GLOBAL_CACHE.Skill.Data.GetAdrenaline(consumer.custom_skill.skill_id)}")
            PyImGui.text(f"    - adrenaline current: {self.get_current_adrenaline(consumer.custom_skill)}")
            PyImGui.text(f"    - is consumer ready to get adrenaline : {self.is_consumer_ready_to_get_adrenaline(consumer.custom_skill)}")
            
        # hash_id = f"should_wait_for_adrenaline_consumer##wait_adr_{self.parent_skill_name}"
        # self.should_wait_for_adrenaline_consumer = PyImGui.checkbox(f"should_wait_for_adrenaline_consumer##{hash_id}", self.should_wait_for_adrenaline_consumer)

    def get_current_adrenaline(self, consumer_skill: CustomSkill) -> int:
        slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(consumer_skill.skill_id)
        if slot == 0:
            return 0
        
        skillbar_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skillbar_data is None:
            return 0
        
        return skillbar_data.adrenaline_a if skillbar_data is not None else 0

    def is_consumer_ready_to_get_adrenaline(self, consumer_skill: CustomSkill) -> bool:
        slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(consumer_skill.skill_id)
        if slot == 0: return False
    
        consumer_adrenaline_level = self.get_current_adrenaline(consumer_skill)
        consumer_required_adrenaline = GLOBAL_CACHE.Skill.Data.GetAdrenaline(consumer_skill.skill_id)
        generated_adrenaline = self.generated_strike_of_adrenaline() * 25
        allowed_margin = 50 # 2 strike margin

        return consumer_adrenaline_level + generated_adrenaline - allowed_margin <= consumer_required_adrenaline

    @property
    @override
    def data(self) -> str:
        return str(int(self.should_wait_for_adrenaline_consumer))

    @override
    def is_satisfied(self) -> bool:
        """
        Check if we should wait for adrenaline consumers.
        
        Logic:
        - If disabled, always return True (skill can be used)
        - If enabled, check if any consumer skill is in the skillbar and almost ready
        - If a consumer is almost ready (within generated_adrenaline), wait (return False)
        - Otherwise, allow the generator to be used (return True)
        """
        if not self.should_wait_for_adrenaline_consumer:
            return True

        for consumer_utility in self.adrenaline_consumers:
            if self.is_consumer_ready_to_get_adrenaline(consumer_utility.custom_skill):
                return True
            
        return False

