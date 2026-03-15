from abc import abstractmethod
import traceback
from collections.abc import Callable, Generator
from typing import Any
import time

from Py4GWCoreLib import IniManager, Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers

from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target import CustomBuffTarget
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_nature import CustomSkillNature
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class CustomSkillUtilityBase:
    def __init__(self, 
                event_bus: EventBus,
                skill: CustomSkill,
                in_game_build: list[CustomSkill],
                score_definition: ScoreDefinition,
                mana_required_to_cast: float = 0,
                allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
                utility_skill_typology: UtilitySkillTypology = UtilitySkillTypology.COMBAT,
                execution_strategy = UtilitySkillExecutionStrategy.EXECUTE_THROUGH_THE_END
                ):

        self.event_bus: EventBus = event_bus
        self.custom_skill: CustomSkill = skill
        self.utility_skill_typology: UtilitySkillTypology = utility_skill_typology
        self.in_game_build: list[CustomSkill] = in_game_build
        self.allowed_states: list[BehaviorState] | None = allowed_states
        self.mana_required_to_cast: float = mana_required_to_cast
        self.is_enabled: bool = True
        self.execution_strategy: UtilitySkillExecutionStrategy = execution_strategy
        self.score_definition: ScoreDefinition = score_definition

    @abstractmethod
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False

        if self.allowed_states is not None and current_state not in self.allowed_states:
            if constants.DEBUG:
                print(f'PreCheck Reject - Wrong State {self.custom_skill.skill_name}')
            return False
        if custom_behavior_helpers.Resources.get_player_absolute_energy() < self.mana_required_to_cast:
            if constants.DEBUG:
                print(f'PreCheck Reject - Energy Requirement for Utility {self.custom_skill.skill_name}')
            return False
        if not Routines.Checks.Skills.IsSkillSlotReady(self.custom_skill.skill_slot):
            if constants.DEBUG:
                print(f"custom_skill.skill_slot: {self.custom_skill.skill_slot}")
                print(f'PreCheck Reject - IsSkillSlotReady {self.custom_skill.skill_name}')
            return False
        if not custom_behavior_helpers.Resources.has_enough_resources(self.custom_skill):
            if constants.DEBUG:
                print(f'PreCheck Reject - Resources Requirement for Ability {self.custom_skill.skill_name}')
            return False
        return True
    
    @abstractmethod
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        pass

    @abstractmethod
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        pass

    def evaluate(self, current_state: BehaviorState, previously_attempted_skills:list[CustomSkill]) -> float | None:
        if not self.is_enabled:
            if constants.DEBUG: print(f'I Am Not Enabled {self.custom_skill.skill_name}')
            return None
        if self.custom_skill.skill_slot == 0 and self.custom_skill.skill_id != 0:
            print(f'PreCheck Reject {self.custom_skill.skill_name} was missing its skill slot, reloading.')
            self.custom_skill.skill_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.custom_skill.skill_id) if self.custom_skill.skill_id != 0 else 0

        if not self.are_common_pre_checks_valid(current_state):
            if constants.DEBUG:
                if self.utility_skill_typology == UtilitySkillTypology.COMBAT and current_state == BehaviorState.IN_AGGRO and current_state in self.allowed_states:
                    print(f'PreCheck Reject {self.custom_skill.skill_name}')
            return None

        if self.utility_skill_typology == UtilitySkillTypology.COMBAT and not CustomBehaviorParty().get_party_is_combat_enabled():
            if constants.DEBUG: print(f'Reject Combat Not Enabled {self.custom_skill.skill_name}')
            return None
        if self.utility_skill_typology == UtilitySkillTypology.FOLLOWING and not CustomBehaviorParty().get_party_is_following_enabled():
            if constants.DEBUG: print(f'Reject Combat Not Enabled {self.custom_skill.skill_name}')
            return None
        if self.utility_skill_typology == UtilitySkillTypology.LOOTING and not CustomBehaviorParty().get_party_is_looting_enabled():
            if constants.DEBUG: print(f'Reject Combat Not Enabled {self.custom_skill.skill_name}')
            return None
        if self.utility_skill_typology == UtilitySkillTypology.CHESTING and not CustomBehaviorParty().get_party_is_chesting_enabled():
            if constants.DEBUG: print(f'Reject Combat Not Enabled {self.custom_skill.skill_name}')
            return None
        if self.utility_skill_typology == UtilitySkillTypology.BLESSING and not CustomBehaviorParty().get_party_is_blessing_enabled():
            if constants.DEBUG: print(f'Reject Combat Not Enabled {self.custom_skill.skill_name}')
            return None
        if self.utility_skill_typology == UtilitySkillTypology.INVENTORY and not CustomBehaviorParty().get_party_is_inventory_enabled():
            if constants.DEBUG: print(f'Reject Combat Not Enabled {self.custom_skill.skill_name}')
            return None
        if current_state == BehaviorState.IDLE:
            if (self.utility_skill_typology != UtilitySkillTypology.BOTTING
                and self.utility_skill_typology != UtilitySkillTypology.DAEMON
                and self.utility_skill_typology != UtilitySkillTypology.INVENTORY):
                raise Exception("only botting & daemon utility_skill_typology can perform stuff in IDLE")

        try:
            score:float | None = self._evaluate(current_state, previously_attempted_skills)

            if score is None:
                if constants.DEBUG:
                    if self.utility_skill_typology == UtilitySkillTypology.COMBAT and current_state == BehaviorState.IN_AGGRO and current_state in self.allowed_states: print(f'Evaluate Reject {self.custom_skill.skill_name}')
                return None
            if 0 > score > 100: raise Exception(f"{self.custom_skill.skill_name} : score must be between 0 and 100, calculated {score}.")

            if constants.DEBUG:
                if self.utility_skill_typology == UtilitySkillTypology.COMBAT: print(f'Score {score} for {self.custom_skill.skill_name}')

            return score
        except Exception as e:
            # actually log the errors in evaluate, as mind wracks errors in base were just getting ignored
            print(f'Evaluate Exception {self.custom_skill.skill_name}: {e}')
            print(traceback.format_exc())
            return None

    def execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        if constants.DEBUG: print(f"Executing {self.custom_skill.skill_name}")

        try:
            gen:Generator[Any | None, Any | None, BehaviorResult] = self._execute(state)
            result:BehaviorResult = yield from gen
        except Exception as e:
            print(f'execute Exception {self.custom_skill.skill_name}: {e}')
            print(traceback.format_exc())
            return BehaviorResult.ACTION_SKIPPED

        return result

    def nature_has_been_attempted_last(self, previously_attempted_skills: list[CustomSkill]) -> bool:
        if len(previously_attempted_skills) == 0: return False
        last_value = previously_attempted_skills[-1]
        is_nature_has_been_attempted_last = last_value.skill_nature == self.custom_skill.skill_nature
        return is_nature_has_been_attempted_last

    def is_another_interrupt_ready(self) -> bool:
        for skill in self.in_game_build:
            if skill.skill_nature == CustomSkillNature.Interrupt and skill.skill_id != self.custom_skill.skill_id:
                if Routines.Checks.Skills.IsSkillIDReady(skill.skill_id):
                    return True
        return False

    @abstractmethod
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        """
        This method is used to display the debug UI for the skill.
        Can be overridden by the skill itself to display additional information.
        """
        pass

    @abstractmethod
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        '''
        This method is used to get the buff configuration for the skill.
        Can be overridden by the skill itself to return the buff configuration.
        If the skill does not use buffs, return None.
        '''
        pass

    @abstractmethod
    def has_persistence(self) -> bool:
        return False
    
    @abstractmethod
    def delete_persisted_configuration(self):
        '''
        for ui button
        '''
        pass

    @abstractmethod
    def persist_configuration_as_global(self):
        '''
        for ui button
        '''
        pass

    @abstractmethod
    def persist_configuration_for_account(self):
        '''
        for ui button
        '''
        pass