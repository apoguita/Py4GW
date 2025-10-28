
from collections.abc import Generator
from enum import Enum
from typing import Any, Callable
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import ProfessionConfiguration, BuffConfigurationPerProfession
from Widgets.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_email import BuffConfigurationPerPlayerEmail
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

class CustomBuffTargetMode(Enum):
    PER_PROFESSION = 0
    PER_EMAIL = 1

class CustomBuffMultipleTarget():
    def __init__(self,
                event_bus: EventBus, 
                custom_skill: CustomSkill, 
                buff_mode: CustomBuffTargetMode = CustomBuffTargetMode.PER_PROFESSION, 
                buff_configuration_per_profession: list[ProfessionConfiguration] | None = None):
        
        self.custom_skill: CustomSkill = custom_skill
        self.buff_mode = buff_mode
        self.event_bus = event_bus

        buff_configuration = buff_configuration_per_profession if buff_configuration_per_profession is not None else BuffConfigurationPerProfession.BUFF_CONFIGURATION_ALL
        self.buff_configuration_per_profession: BuffConfigurationPerProfession = BuffConfigurationPerProfession(self.custom_skill, buff_configuration_per_profession)
        self.buff_configuration_per_email: BuffConfigurationPerPlayerEmail = BuffConfigurationPerPlayerEmail(self.custom_skill)

        self.event_bus.subscribe(EventType.MAP_CHANGED, self.map_changed, subscriber_name= "CustomBuffMultipleTarget_" + self.custom_skill.skill_name)

    def map_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:
        self.buff_configuration_per_email.reset()
        yield

    def get_agent_id_predicate(self) -> Callable[[int], bool]:
        if self.buff_mode == CustomBuffTargetMode.PER_PROFESSION:
            return self.buff_configuration_per_profession.get_agent_id_predicate()
        elif self.buff_mode == CustomBuffTargetMode.PER_EMAIL:
            return self.buff_configuration_per_email.get_agent_id_predicate()
        else:
            raise Exception(f"Unknown buff mode: {self.buff_mode}")

    def render_buff_configuration(self, py4gw_root_directory: str):
        # Dropdown to choose target mode (per profession or per email)
        import PyImGui

        items = ["Per profession", "Per email"]
        current_index = 0 if self.buff_mode == CustomBuffTargetMode.PER_PROFESSION else 1
        new_index = PyImGui.combo(f"Targeting mode##{self.custom_skill.skill_name}", current_index, items)
        if new_index != current_index:
            previous_mode = self.buff_mode
            self.buff_mode = CustomBuffTargetMode.PER_PROFESSION if new_index == 0 else CustomBuffTargetMode.PER_EMAIL
            # When switching into per-email mode, initialize email toggles from current per-profession settings
            if previous_mode == CustomBuffTargetMode.PER_PROFESSION and self.buff_mode == CustomBuffTargetMode.PER_EMAIL:
                try:
                    self.buff_configuration_per_email.initialize_buff_according_to_professions(self.buff_configuration_per_profession)
                except Exception:
                    pass

        # Render the configuration UI for the selected mode
        if self.buff_mode == CustomBuffTargetMode.PER_PROFESSION:
            self.buff_configuration_per_profession.render_buff_configuration(py4gw_root_directory)
        elif self.buff_mode == CustomBuffTargetMode.PER_EMAIL:
            self.buff_configuration_per_email.render_buff_configuration(py4gw_root_directory)
        else:
            raise Exception(f"Unknown buff mode: {self.buff_mode}")
