from abc import abstractmethod
from typing import Callable

from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_plugin import UtilitySkillPlugin

class UtilitySkillPrecondition(UtilitySkillPlugin):
    '''
    A precondition is a plugin that must be satisfied for the skill to be considered.
    If the precondition is not satisfied, the skill will not be evaluated.
    '''

    def __init__(self, parent_skill: CustomSkill, capability_name: str):
        super().__init__(parent_skill, capability_name)

    @property
    @abstractmethod
    def data(self) -> str:
        raise NotImplementedError("Subclasses should implement this.")
    
    @abstractmethod
    def is_satisfied(self) -> bool:
        raise NotImplementedError("Subclasses should implement this.")