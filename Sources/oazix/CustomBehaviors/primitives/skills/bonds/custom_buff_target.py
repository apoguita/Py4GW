from abc import abstractmethod
from enum import Enum
from typing import Callable
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import ProfessionConfiguration
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

class CustomBuffTarget:

    def __init__(self, custom_skill: CustomSkill, buff_configuration: list[ProfessionConfiguration]):
        self.custom_skill: CustomSkill = custom_skill

    @abstractmethod
    def get_agent_id_predicate(self) -> Callable[[int], bool]:
        pass

    @abstractmethod
    def render_buff_configuration(self):
        pass
