from abc import abstractmethod
from typing import Callable

from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_plugin import UtilitySkillPlugin

class UtilitySkillTargetingModifier(UtilitySkillPlugin):
    '''
    A targeting modifier is a plugin that modifies the targeting of the skill.
    It allows to add extra conditions on top of the skill's default targeting.
    '''

    def __init__(self, parent_skill: CustomSkill, capability_name: str):
        super().__init__(parent_skill, capability_name)

    @property
    @abstractmethod
    def data(self) -> str:
        raise NotImplementedError("Subclasses should implement this.")
    
    @abstractmethod
    def get_agent_id_filtering_predicate(self) -> Callable[[int], bool]:
        raise NotImplementedError("Subclasses should implement this.")

    @abstractmethod
    def get_agent_id_ordering_predicate(self) -> Callable[[int], int]:
        raise NotImplementedError("Subclasses should implement this.")