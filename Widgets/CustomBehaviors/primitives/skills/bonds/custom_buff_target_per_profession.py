from dataclasses import dataclass
from enum import IntEnum
from typing import Callable, override

import PyImGui
from Py4GWCoreLib import GLOBAL_CACHE, ImGui
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.enums import Profession, Range
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.skills.bonds.profession_configuration import ProfessionConfiguration
from Widgets.CustomBehaviors.primitives.skills.bonds.custom_buff_target import CustomBuffTarget
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

class BuffConfigurationPerProfession(CustomBuffTarget):
    BUFF_CONFIGURATION_CASTERS: list[ProfessionConfiguration] = [ProfessionConfiguration(Profession.Monk, True), ProfessionConfiguration(Profession.Ritualist, True), ProfessionConfiguration(Profession.Elementalist, True), ProfessionConfiguration(Profession.Mesmer, True), ProfessionConfiguration(Profession.Necromancer, True)]
    BUFF_CONFIGURATION_MARTIAL: list[ProfessionConfiguration] = [ProfessionConfiguration(Profession.Warrior, True), ProfessionConfiguration(Profession.Assassin, True), ProfessionConfiguration(Profession.Dervish, True), ProfessionConfiguration(Profession.Paragon, True), ProfessionConfiguration(Profession.Ranger, True)]
    BUFF_CONFIGURATION_ALL: list[ProfessionConfiguration] = [ProfessionConfiguration(Profession.Monk, True), ProfessionConfiguration(Profession.Ritualist, True), ProfessionConfiguration(Profession.Elementalist, True), ProfessionConfiguration(Profession.Mesmer, True), ProfessionConfiguration(Profession.Necromancer, True), ProfessionConfiguration(Profession.Warrior, True), ProfessionConfiguration(Profession.Assassin, True), ProfessionConfiguration(Profession.Dervish, True), ProfessionConfiguration(Profession.Paragon, True), ProfessionConfiguration(Profession.Ranger, True)]
    ALL_PROFESSIONS = [Profession.Assassin, Profession.Warrior, Profession.Ranger, Profession.Monk, Profession.Necromancer, Profession.Mesmer, Profession.Elementalist, Profession.Ritualist, Profession.Paragon, Profession.Dervish]

    def __init__(self, custom_skill: CustomSkill, custom_configuration: list[ProfessionConfiguration] | None = None):

        self.__target_configurations : list[ProfessionConfiguration] = []

        if custom_configuration is None:  # if no custom configuration is provided, use the default one
            self.__target_configurations = [ProfessionConfiguration(bond_target_profession, True) for bond_target_profession in self.ALL_PROFESSIONS]
        else:
            # Copy existing configurations and add missing ones
            existing_professions = [configuration.bond_target_profession for configuration in custom_configuration]

            # First, copy all existing configurations
            for config in custom_configuration:
                self.__target_configurations.append(config)

            # Then add any missing professions
            for profession in self.ALL_PROFESSIONS:
                if profession not in existing_professions:
                    self.__target_configurations.append(ProfessionConfiguration(profession, False))

        self.custom_skill: CustomSkill = custom_skill

    def get_by_profession(self, profession: Profession) -> ProfessionConfiguration:
        for configuration in self.__target_configurations:
            if configuration.bond_target_profession.value == profession.value:
                return configuration
        raise Exception(f"BuffConfigurationPerProfession: {profession} not found")

    def is_activated(self, profession: Profession) -> bool:
        return any(configuration.bond_target_profession == profession and configuration.is_activated for configuration in self.__target_configurations)

    def activate(self, profession: Profession) -> None:
        for configuration in self.__target_configurations:
            if configuration.bond_target_profession.value == profession.value:
                configuration.is_activated = True

    def deactivate(self, profession: Profession) -> None:
        for configuration in self.__target_configurations:
            if configuration.bond_target_profession.value == profession.value:
                configuration.is_activated = False

    @override
    def get_agent_id_predicate(self) -> Callable[[int], bool]:
        return lambda agent_id: self.__should_apply_effect(agent_id)

    def __should_apply_effect(self, agent_id: int) -> bool:
        for target_configuration in self.__target_configurations:
            if target_configuration.is_activated:
                if self.__should_apply_effect_on_agent_id(agent_id, target_configuration.bond_target_profession):
                    return True
        return False

    def __should_apply_effect_on_agent_id(self, agent_id: int, profession: Profession) -> bool:
        profession_id: int = GLOBAL_CACHE.Agent.GetProfessionIDs(agent_id)[0]

        if profession_id != profession.value:
            return False

        if agent_id == GLOBAL_CACHE.Player.GetAgentID() :
            # if target is the player, check if the player has the effect
            has_buff: bool = Routines.Checks.Effects.HasBuff(GLOBAL_CACHE.Player.GetAgentID(), self.custom_skill.skill_id)
            return not has_buff
        else:
            # else check if the party target has the effect
            # todo pets
            has_effect: bool = custom_behavior_helpers.Resources.is_ally_under_specific_effect(agent_id, self.custom_skill.skill_id)
            return not has_effect
        
    @override
    def render_buff_configuration(self, py4gw_root_directory: str):
        PyImGui.bullet_text(f"Buff configuration : ")
        for profession in BuffConfigurationPerProfession.ALL_PROFESSIONS:
            buff_configuration_per_profession = self.get_by_profession(profession)
            texture_path =  py4gw_root_directory + f"Textures\\Profession_Icons\\[{profession.value}] - {profession.name}.png"
            icon_size = 26
            if buff_configuration_per_profession.is_activated:
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)  # 1px border
                PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(3, 244, 60, 255)))
                if ImGui.ImageButton(f"deactivate_{self.custom_skill.skill_name}_{profession.name}", texture_path, icon_size, icon_size):
                    buff_configuration_per_profession.is_activated = False
                ImGui.show_tooltip(f"Deactivate buff for {profession.name}")
                PyImGui.pop_style_var(1)
                PyImGui.pop_style_color(1)
            else:
                if ImGui.ImageButton(f"activate_{self.custom_skill.skill_name}_{profession.name}", texture_path, icon_size, icon_size):
                    buff_configuration_per_profession.is_activated = True
                ImGui.show_tooltip(f"Activate buff for {profession.name}")
            PyImGui.same_line(0, 5)