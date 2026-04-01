from abc import abstractmethod
from collections.abc import Generator
from typing import Any, Callable

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_plugin import UtilitySkillPlugin

class UtilitySkillWatchdog(UtilitySkillPlugin):
    '''
    An extension is a plugin that live aside of the skill's normal behavior.
    Something like a mini-skill daemon.
    '''

    def __init__(self, parent_skill: CustomSkill, capability_name: str):
        super().__init__(parent_skill, capability_name)

    @property
    @abstractmethod
    def data(self) -> str:
        raise NotImplementedError("Subclasses should implement this.")
    
    @abstractmethod
    def act(self) -> Generator[Any | None, Any | None, None]:
        raise NotImplementedError("Subclasses should implement this.")