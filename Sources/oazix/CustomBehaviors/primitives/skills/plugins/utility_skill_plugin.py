from abc import abstractmethod
from typing import Callable

from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

class UtilitySkillPlugin:
    '''
    Core class for everything enriching a utility skill.
    A plugin can be a :
    - precondition : something that must be true for the skill to be considered.
    - extension : something that extends the behavior of the skill.
    - targeting modifier : something that modifies the targeting of the skill.

    This is very simple decorator pattern
    '''

    def __init__(self, parent_skill: CustomSkill, plugin_name: str):
        self.parent_skill_name: str = parent_skill.skill_name
        self.plugin_name: str = plugin_name

    @property
    @abstractmethod
    def data(self) -> str:
        raise NotImplementedError("Subclasses should implement this.")
    
    @abstractmethod
    def render_debug_ui(self):
        pass
    
    def has_persistence(self) -> bool:
        return True
    
    def load_from_persistence(self, default_value: str) -> str:
        if not self.has_persistence(): return default_value
        if self.parent_skill_name is None: raise Exception("parent_skill_name is None")
        return PersistenceLocator().skills.read_or_default(self.parent_skill_name, self.plugin_name, default_value)

    def persist_configuration_for_account(self):
        if not self.has_persistence(): return
        if self.parent_skill_name is None: raise Exception("parent_skill_name is None")
        PersistenceLocator().skills.write_for_account(str(self.parent_skill_name), self.plugin_name, self.data)
        print(f"UtilitySkillCapability {self.__class__.__name__} saved for account.")

    def persist_configuration_as_global(self):
        if not self.has_persistence(): return
        if self.parent_skill_name is None: raise Exception("parent_skill_name is None")
        PersistenceLocator().skills.write_global(str(self.parent_skill_name), self.plugin_name, self.data)
        print(f"UtilitySkillCapability {self.__class__.__name__} saved as global.")

    def delete_persisted_configuration(self):
        if not self.has_persistence(): return
        if self.parent_skill_name is None: raise Exception("parent_skill_name is None")
        PersistenceLocator().skills.delete(str(self.parent_skill_name), self.plugin_name)
        print(f"UtilitySkillCapability {self.__class__.__name__} deleted.")