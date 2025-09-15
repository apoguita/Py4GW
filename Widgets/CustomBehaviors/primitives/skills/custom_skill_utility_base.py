from abc import abstractmethod
from collections.abc import Generator
from typing import Any

from Py4GWCoreLib import Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers

from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.skills.bonds.per_type.custom_buff_target import BuffConfigurationPerProfession
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

from Widgets.CustomBehaviors.primitives.skills.custom_skill_nature import CustomSkillNature
from Widgets.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class CustomSkillUtilityBase:
    def __init__(self, skill: CustomSkill,
                in_game_build: list[CustomSkill],
                score_definition:ScoreDefinition,
                mana_required_to_cast:float=0,
                allowed_states:list[BehaviorState]=[BehaviorState.IN_AGGRO],
                utility_skill_typology: UtilitySkillTypology = UtilitySkillTypology.COMBAT,
                execution_strategy = UtilitySkillExecutionStrategy.EXECUTE_THROUGH_THE_END
                ):

        self.custom_skill: CustomSkill = skill
        self.utility_skill_typology: UtilitySkillTypology = utility_skill_typology
        self.in_game_build: list[CustomSkill] = in_game_build
        self.allowed_states: list[BehaviorState] | None = allowed_states
        self.mana_required_to_cast: float = mana_required_to_cast
        self.is_enabled:bool = True
        self.execution_strategy:UtilitySkillExecutionStrategy = execution_strategy

    @abstractmethod
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if custom_behavior_helpers.Resources.get_player_absolute_energy() < self.mana_required_to_cast: return False
        if not Routines.Checks.Skills.IsSkillSlotReady(self.custom_skill.skill_slot): return False
        if not custom_behavior_helpers.Resources.has_enough_resources(self.custom_skill): return False
        return True
    
    @abstractmethod
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        pass

    @abstractmethod
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        pass

    def evaluate(self, current_state: BehaviorState, previously_attempted_skills:list[CustomSkill]) -> float | None:
        # print(f'Evaluating {self.custom_skill.skill_name}')
        if not self.is_enabled: return None
        if not self.are_common_pre_checks_valid(current_state): return None
        if self.utility_skill_typology == UtilitySkillTypology.COMBAT and not CustomBehaviorParty().get_party_is_combat_enabled(): return None
        if self.utility_skill_typology == UtilitySkillTypology.FOLLOWING and not CustomBehaviorParty().get_party_is_following_enabled(): return None
        if self.utility_skill_typology == UtilitySkillTypology.LOOTING and not CustomBehaviorParty().get_party_is_looting_enabled(): return None
        if self.utility_skill_typology == UtilitySkillTypology.CHESTING and not CustomBehaviorParty().get_party_is_chesting_enabled(): return None
        if self.utility_skill_typology == UtilitySkillTypology.BLESSING and not CustomBehaviorParty().get_party_is_blessing_enabled(): return None
        if self.utility_skill_typology == UtilitySkillTypology.INVENTORY and not CustomBehaviorParty().get_party_is_inventory_enabled(): return None
        if current_state == BehaviorState.IDLE:
            if (self.utility_skill_typology != UtilitySkillTypology.BOTTING 
                and self.utility_skill_typology != UtilitySkillTypology.DAEMON 
                and self.utility_skill_typology != UtilitySkillTypology.INVENTORY): 
                print(self.utility_skill_typology)
                raise Exception("only botting & daemon utility_skill_typology can perform stuff in IDLE")

        score:float | None = self._evaluate(current_state, previously_attempted_skills)
        if score is None: return None
        if 0 > score > 100: raise Exception(f"{self.custom_skill.skill_name} : score must be between 0 and 100, calculated {score}.")

        return score

    def execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        if constants.DEBUG: print(f"Executing {self.custom_skill.skill_name}")
        gen:Generator[Any | None, Any | None, BehaviorResult] = self._execute(state)
        result:BehaviorResult = yield from gen
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
    def get_buff_configuration(self) -> BuffConfigurationPerProfession | None:
        '''
        This method is used to get the buff configuration for the skill.
        Can be overridden by the skill itself to return the buff configuration.
        If the skill does not use buffs, return None.
        '''
        pass