
from collections.abc import Generator
from enum import Enum
from typing import Any, Callable
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import ProfessionConfiguration, BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_email import BuffConfigurationPerPlayerEmail, BuffEmailEntry
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

class CustomBuffTargetMode(Enum):
    PER_PROFESSION = 0
    PER_EMAIL = 1

class CustomBuffMultipleTarget():
    def __init__(self,
                event_bus: EventBus, 
                custom_skill: CustomSkill, 
                buff_mode: CustomBuffTargetMode = CustomBuffTargetMode.PER_PROFESSION, 
                buff_configuration_per_profession: list[ProfessionConfiguration] | None = None, 
                buff_configuration_per_email: dict[str, BuffEmailEntry] | None = None):
        
        self.custom_skill: CustomSkill = custom_skill
        self.buff_mode = buff_mode
        self.event_bus = event_bus

        if buff_mode == CustomBuffTargetMode.PER_PROFESSION:
            self.buff_configuration_per_profession: BuffConfigurationPerProfession = BuffConfigurationPerProfession(self.custom_skill, buff_configuration_per_profession)
            self.buff_configuration_per_email = BuffConfigurationPerPlayerEmail(self.custom_skill)
        elif buff_mode == CustomBuffTargetMode.PER_EMAIL:
            self.buff_configuration_per_profession = BuffConfigurationPerProfession(self.custom_skill)
            self.buff_configuration_per_email: BuffConfigurationPerPlayerEmail = BuffConfigurationPerPlayerEmail(self.custom_skill, buff_configuration_per_email)
        else:
            raise Exception(f"Unknown buff mode: {buff_mode}")

        self.event_bus.subscribe(EventType.MAP_CHANGED, self.map_changed, subscriber_name= "CustomBuffMultipleTarget_" + self.custom_skill.skill_name)

    @classmethod
    def from_profession_config(cls, event_bus: EventBus, custom_skill: CustomSkill, buff_configuration: list[ProfessionConfiguration]) -> "CustomBuffMultipleTarget":
        """Alternative constructor for profession-based configuration."""
        return cls(event_bus, custom_skill, CustomBuffTargetMode.PER_PROFESSION, buff_configuration)

    @classmethod
    def from_email_config(cls, event_bus: EventBus, custom_skill: CustomSkill, buff_configuration: dict[str, BuffEmailEntry]) -> "CustomBuffMultipleTarget":
        """Alternative constructor for email-based configuration."""
        return cls(event_bus, custom_skill, CustomBuffTargetMode.PER_EMAIL, None, buff_configuration)

    def serialize_to_string(self) -> str:
        if self.buff_mode == CustomBuffTargetMode.PER_PROFESSION:
            return "PER_PROFESSION;" + self.buff_configuration_per_profession.serialize_to_string()
        elif self.buff_mode == CustomBuffTargetMode.PER_EMAIL:
            return "PER_EMAIL;" + self.buff_configuration_per_email.serialize_to_string()
        else:
            raise Exception(f"Unknown buff mode: {self.buff_mode}")
        
    @staticmethod
    def instanciate_from_string(event_bus: EventBus, custom_skill: CustomSkill, serialized_string: str) -> "CustomBuffMultipleTarget":
        buff_mode_str, serialized_configuration = serialized_string.split(";", 1)

        # Parse buff_mode from either enum name or integer value
        if buff_mode_str == "PER_PROFESSION":
            buff_mode = CustomBuffTargetMode.PER_PROFESSION
        elif buff_mode_str == "PER_EMAIL":
            buff_mode = CustomBuffTargetMode.PER_EMAIL
        else:
            raise Exception(f"Unknown buff mode: {buff_mode_str}")

        if buff_mode == CustomBuffTargetMode.PER_PROFESSION:
            buff_configuration_per_profession: list[ProfessionConfiguration] = BuffConfigurationPerProfession.instanciate_from_string(serialized_configuration)
            return CustomBuffMultipleTarget.from_profession_config(event_bus, custom_skill, buff_configuration=buff_configuration_per_profession)
        
        elif buff_mode == CustomBuffTargetMode.PER_EMAIL:
            buff_configuration_per_email: dict[str, BuffEmailEntry] = BuffConfigurationPerPlayerEmail.instanciate_from_string(serialized_configuration)
            return CustomBuffMultipleTarget.from_email_config(event_bus, custom_skill, buff_configuration=buff_configuration_per_email)
        else:
            raise Exception(f"Unknown buff mode: {buff_mode}")

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

    def render_buff_configuration(self):
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
            self.buff_configuration_per_profession.render_buff_configuration()
        elif self.buff_mode == CustomBuffTargetMode.PER_EMAIL:
            self.buff_configuration_per_email.render_buff_configuration()
        else:
            raise Exception(f"Unknown buff mode: {self.buff_mode}")
        PyImGui.new_line()
