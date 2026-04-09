from typing import Callable, override

import PyImGui
from Py4GWCoreLib import Agent

from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_targeting_modifier import UtilitySkillTargetingModifier


class ShouldTargetPetsWithWeaponSpell(UtilitySkillTargetingModifier):
    """
    A targeting modifier that allows targeting pets.
    When enabled, this modifier will filter to only include pets.
    When disabled, this modifier will not filter (allow all agents).
    """

    def __init__(self, parent_skill: CustomSkill, default_value: bool = False):
        super().__init__(parent_skill, "should_target_pets")
        
        self.parent_skill = parent_skill
        from_persistence = self.load_from_persistence(str(int(default_value)))
        self.should_target_pets: bool = bool(int(from_persistence))

    @property
    @override
    def data(self) -> str:
        return str(int(self.should_target_pets))
    
    def is_pet_under_effect(self, agent_id: int) -> bool:
        is_pet_under_effect = Agent.IsWeaponSpelled(agent_id)
        return is_pet_under_effect

    @override
    def get_agent_id_filtering_predicate(self) -> Callable[[int], bool]:
        """
        Returns a predicate that filters for pets if enabled.
        If disabled, allows all agents (returns True for all).
        """
        if self.should_target_pets:
            return lambda agent_id: Agent.IsPet(agent_id) and not self.is_pet_under_effect(agent_id)
        else:
            return lambda agent_id: False

    @override
    def get_agent_id_ordering_predicate(self) -> Callable[[int], int]:
        """
        Pets are always targeted last.
        """
        return lambda agent_id: -99

    @override
    def render_debug_ui(self):
        hash_value = f"{self.plugin_name}##{self.parent_skill_name}"
        self.should_target_pets = PyImGui.checkbox(f"Should Target Pets##{hash_value}", self.should_target_pets)
