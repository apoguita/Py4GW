from abc import abstractmethod
from typing import Callable

from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

class UtilitySkillCapability:
    def __init__(self, parent_skill: CustomSkill, capability_name: str):
        self.parent_skill_name: str = parent_skill.skill_name
        self.capability_name: str = capability_name

    @property
    @abstractmethod
    def data(self) -> str:
        raise NotImplementedError("Subclasses should implement this.")
    
    @abstractmethod
    def is_satisfied(self) -> bool:
        raise NotImplementedError("Subclasses should implement this.")
    
    @abstractmethod
    def get_targetting_agent_id_predicate(self) -> Callable[[int], bool]:
        # most of the time, the capability does not impact targetting
        # so we just return True
        # but if it does, the capability can override this method to provide a custom predicate
        raise NotImplementedError("Subclasses should implement this.")
    
    @abstractmethod
    def render_debug_ui(self):
        pass
    
    def has_persistence(self) -> bool:
        return True
    
    def load_from_persistence(self, default_value: str) -> str:
        if not self.has_persistence(): return default_value
        if self.parent_skill_name is None: raise Exception("parent_skill_name is None")
        return PersistenceLocator().skills.read_or_default(self.parent_skill_name, self.capability_name, default_value)

    def persist_configuration_for_account(self):
        if not self.has_persistence(): return
        if self.parent_skill_name is None: raise Exception("parent_skill_name is None")
        PersistenceLocator().skills.write_for_account(str(self.parent_skill_name), self.capability_name, self.data)
        print(f"UtilitySkillCapability {self.__class__.__name__} saved for account.")

    def persist_configuration_as_global(self):
        if not self.has_persistence(): return
        if self.parent_skill_name is None: raise Exception("parent_skill_name is None")
        PersistenceLocator().skills.write_global(str(self.parent_skill_name), self.capability_name, self.data)
        print(f"UtilitySkillCapability {self.__class__.__name__} saved as global.")

    def delete_persisted_configuration(self):
        if not self.has_persistence(): return
        if self.parent_skill_name is None: raise Exception("parent_skill_name is None")
        PersistenceLocator().skills.delete(str(self.parent_skill_name), self.capability_name)
        print(f"UtilitySkillCapability {self.__class__.__name__} deleted.")
