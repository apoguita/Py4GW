from dataclasses import dataclass
from enum import IntEnum
from typing import Callable
from HeroAI.custom_skill import CustomSkillClass
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.enums import Profession, Range
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill


@dataclass
class BuffConfiguration:
    def __init__(self, bond_target_profession: Profession, is_activated: bool):
        self.bond_target_profession: Profession = bond_target_profession
        self.is_activated: bool = is_activated

class BuffConfigurationPerProfession:
    BUFF_CONFIGURATION_CASTERS: list[BuffConfiguration] = [BuffConfiguration(Profession.Monk, True), BuffConfiguration(Profession.Ritualist, True), BuffConfiguration(Profession.Elementalist, True), BuffConfiguration(Profession.Mesmer, True), BuffConfiguration(Profession.Necromancer, True)]
    BUFF_CONFIGURATION_MARTIAL: list[BuffConfiguration] = [BuffConfiguration(Profession.Warrior, True), BuffConfiguration(Profession.Assassin, True), BuffConfiguration(Profession.Dervish, True), BuffConfiguration(Profession.Paragon, True), BuffConfiguration(Profession.Ranger, True)]
    BUFF_CONFIGURATION_ALL: list[BuffConfiguration] = [BuffConfiguration(Profession.Monk, True), BuffConfiguration(Profession.Ritualist, True), BuffConfiguration(Profession.Elementalist, True), BuffConfiguration(Profession.Mesmer, True), BuffConfiguration(Profession.Necromancer, True), BuffConfiguration(Profession.Warrior, True), BuffConfiguration(Profession.Assassin, True), BuffConfiguration(Profession.Dervish, True), BuffConfiguration(Profession.Paragon, True), BuffConfiguration(Profession.Ranger, True)]
    ALL_PROFESSIONS = [Profession.Assassin, Profession.Warrior, Profession.Ranger, Profession.Monk, Profession.Necromancer, Profession.Mesmer, Profession.Elementalist, Profession.Ritualist, Profession.Paragon, Profession.Dervish]

    def __init__(self, custom_skill: CustomSkill, custom_configuration: list[BuffConfiguration] | None = None):

        self.__target_configurations : list[BuffConfiguration] = []
        
        if custom_configuration is None:  # if no custom configuration is provided, use the default one
            self.__target_configurations = [BuffConfiguration(bond_target_profession, True) for bond_target_profession in self.ALL_PROFESSIONS]
        else:
            # Copy existing configurations and add missing ones
            existing_professions = [configuration.bond_target_profession for configuration in custom_configuration]
            
            # First, copy all existing configurations
            for config in custom_configuration:
                self.__target_configurations.append(config)
            
            # Then add any missing professions
            for profession in self.ALL_PROFESSIONS:
                if profession not in existing_professions:
                    self.__target_configurations.append(BuffConfiguration(profession, False))

        self.custom_skill: CustomSkill = custom_skill

    def get_by_profession(self, profession: Profession) -> BuffConfiguration:
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

    def get_agent_id_predicate(self) -> Callable[[int], bool]:
        return lambda agent_id: self.__should_apply_effect(agent_id)

    def __should_apply_effect(self, agent_id: int) -> bool:
        for target_configuration in self.__target_configurations:
            if target_configuration.is_activated:
                if self.__should_apply_effect_on_agent_id(agent_id, target_configuration.bond_target_profession):
                    return True
        return False

    def __should_apply_effect_on_agent_id(self, agent_id: int, profession: Profession) -> bool:
        from HeroAI.utils import CheckForEffect
        profession_id: int = GLOBAL_CACHE.Agent.GetProfessionIDs(agent_id)[0]

        if profession_id != profession.value:
            return False

        if agent_id == GLOBAL_CACHE.Player.GetAgentID() :
            # if target is the player, check if the player has the effect
            has_buff: bool = Routines.Checks.Effects.HasBuff(GLOBAL_CACHE.Player.GetAgentID(), self.custom_skill.skill_id)
            return not has_buff
        else:
            # else check if the party target has the effect
            # not sure pet are in heroAI...
            has_effect: bool = CheckForEffect(agent_id, self.custom_skill.skill_id)
            return not has_effect



    