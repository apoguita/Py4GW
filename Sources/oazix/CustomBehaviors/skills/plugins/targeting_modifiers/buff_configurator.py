from re import S
from typing import Callable, override

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget, CustomBuffTargetMode
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.profession_configuration import ProfessionConfiguration
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_targeting_modifier import UtilitySkillTargetingModifier


class BuffConfigurator(UtilitySkillTargetingModifier):

    def __init__(self, event_bus: EventBus, parent_skill: CustomSkill, buff_configuration_per_profession: list[ProfessionConfiguration] | None = BuffConfigurationPerProfession.BUFF_CONFIGURATION_ALL):
        super().__init__(parent_skill, "buff_configuration")
        from_persistence = self.load_from_persistence(default_value="")
        if from_persistence == "":
            self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget(event_bus, parent_skill, buff_mode=CustomBuffTargetMode.PER_PROFESSION, buff_configuration_per_profession=buff_configuration_per_profession)
        else:
            self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget.instanciate_from_string(event_bus, parent_skill, from_persistence)

    @property
    @override
    def data(self) -> str:
        return self.buff_configuration.serialize_to_string()

    @override
    def get_agent_id_filtering_predicate(self) -> Callable[[int], bool]:
        return self.buff_configuration.get_agent_id_predicate()

    @override
    def get_agent_id_ordering_predicate(self) -> Callable[[int], int]:
        return self.buff_configuration.get_agent_id_ordering_predicate()

    @override
    def render_debug_ui(self):
        self.buff_configuration.render_buff_configuration()
