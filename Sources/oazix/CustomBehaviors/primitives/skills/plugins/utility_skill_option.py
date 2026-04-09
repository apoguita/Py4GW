from abc import abstractmethod
from typing import Callable

from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_plugin import UtilitySkillPlugin

class UtilitySkillOption(UtilitySkillPlugin):
    '''
    An option is a shell that is there to simple store some data.
    '''

    def __init__(self, parent_skill: CustomSkill, capability_name: str):
        super().__init__(parent_skill, capability_name)

    @property
    @abstractmethod
    def data(self) -> str:
        raise NotImplementedError("Subclasses should implement this.")
    