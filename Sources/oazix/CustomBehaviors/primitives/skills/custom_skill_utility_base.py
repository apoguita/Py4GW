from abc import abstractmethod
import traceback
from collections.abc import Callable, Generator
from typing import Any

from Py4GWCoreLib import Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers

from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_nature import CustomSkillNature
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_option import UtilitySkillOption
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_watchdog import UtilitySkillWatchdog
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_plugin import UtilitySkillPlugin
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_precondition import UtilitySkillPrecondition
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_targeting_modifier import UtilitySkillTargetingModifier
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
                execution_strategy = UtilitySkillExecutionStrategy.EXECUTE_THROUGH_THE_END,
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

        self._utility_skill_plugins: list[UtilitySkillPlugin] = []

    # Plugin management ------------------

    def add_plugin_precondition(self, precondition: Callable[['CustomSkillUtilityBase'], UtilitySkillPrecondition] ) -> 'CustomSkillUtilityBase':
        plugin_instance: UtilitySkillPlugin = precondition(self)
        if plugin_instance.plugin_name in [capability.plugin_name for capability in self._utility_skill_plugins]: 
            raise Exception(f"Precondition {plugin_instance.plugin_name} already added to {self.custom_skill.skill_name}")
        self._utility_skill_plugins.append(plugin_instance)
        return self
    
    def add_plugin_watchdog(self, extension: Callable[['CustomSkillUtilityBase'], UtilitySkillWatchdog] ) -> 'CustomSkillUtilityBase':
        plugin_instance: UtilitySkillPlugin = extension(self)
        if plugin_instance.plugin_name in [capability.plugin_name for capability in self._utility_skill_plugins]: 
            raise Exception(f"Extension {plugin_instance.plugin_name} already added to {self.custom_skill.skill_name}")
        self._utility_skill_plugins.append(plugin_instance)
        return self

    def add_plugin_targetting_modifier(self, targeting_modifier: Callable[['CustomSkillUtilityBase'], UtilitySkillTargetingModifier] ) -> 'CustomSkillUtilityBase':
        plugin_instance: UtilitySkillPlugin = targeting_modifier(self)
        if plugin_instance.plugin_name in [capability.plugin_name for capability in self._utility_skill_plugins]: 
            raise Exception(f"Targeting modifier {plugin_instance.plugin_name} already added to {self.custom_skill.skill_name}")
        self._utility_skill_plugins.append(plugin_instance)
        return self
    
    def add_plugin_option(self, option: Callable[['CustomSkillUtilityBase'], UtilitySkillOption] ) -> 'CustomSkillUtilityBase':
        plugin_instance: UtilitySkillPlugin = option(self)
        if plugin_instance.plugin_name in [capability.plugin_name for capability in self._utility_skill_plugins]: 
            raise Exception(f"Option {plugin_instance.plugin_name} already added to {self.custom_skill.skill_name}")
        self._utility_skill_plugins.append(plugin_instance)
        return self

    def get_plugins(self) -> list[UtilitySkillPlugin]:
        return self._utility_skill_plugins
    
    def are_preconditions_satisfied(self) -> bool:
        for plugin in self._utility_skill_plugins:
            if not isinstance(plugin, UtilitySkillPrecondition):
                continue
            if not plugin.is_satisfied():
                return False
        return True

    def get_plugin_option(self, option_name: str) -> UtilitySkillOption | None:
        for plugin in self._utility_skill_plugins:
            if isinstance(plugin, UtilitySkillOption) and plugin.plugin_name == option_name:
                return plugin
        return None
    
    def get_plugin_watchdogs(self) -> list[UtilitySkillWatchdog]:
        return [plugin for plugin in self._utility_skill_plugins if isinstance(plugin, UtilitySkillWatchdog)]
    
    def _get_plugin_targeting_modifiers(self) -> list[UtilitySkillTargetingModifier]:
        return [plugin for plugin in self._utility_skill_plugins if isinstance(plugin, UtilitySkillTargetingModifier)]
    
    def get_plugin_targeting_modifiers_filtering_predicate(self) -> Callable[[int], bool]:
        modifiers = self._get_plugin_targeting_modifiers()
        if len(modifiers) == 0: return lambda agent_id: True
        # 'any' is good to cumulate filtering predicates on same skill.
        return lambda agent_id: any(modifier.get_agent_id_filtering_predicate()(agent_id) for modifier in modifiers)

    def get_plugin_targeting_modifiers_ordering_predicate(self) -> Callable[[int], int]:
        modifiers = self._get_plugin_targeting_modifiers()
        if len(modifiers) == 0: return lambda agent_id: 0
        return lambda agent_id: sum(modifier.get_agent_id_ordering_predicate()(agent_id) for modifier in modifiers)

    # End of plugin management ------------------

    @abstractmethod
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False

        if self.allowed_states is not None and current_state not in self.allowed_states:
            if constants.DEBUG: print(f'PreCheck Reject - Wrong State {self.custom_skill.skill_name}')
            return False
        if custom_behavior_helpers.Resources.get_player_absolute_energy() < self.mana_required_to_cast:
            if constants.DEBUG: print(f'PreCheck Reject - Energy Requirement for Utility {self.custom_skill.skill_name}')
            return False
        if not Routines.Checks.Skills.IsSkillSlotReady(self.custom_skill.skill_slot):
            if constants.DEBUG:
                print(f"custom_skill.skill_slot: {self.custom_skill.skill_slot}")
                print(f'PreCheck Reject - IsSkillSlotReady {self.custom_skill.skill_name}')
            return False
        if not custom_behavior_helpers.Resources.has_enough_resources(self.custom_skill):
            if constants.DEBUG: print(f'PreCheck Reject - Resources Requirement for Ability {self.custom_skill.skill_name}')
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

        if not self.are_preconditions_satisfied():
            if constants.DEBUG: print(f'Reject - Capabilities not satisfied for {self.custom_skill.skill_name}')
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
            score:float | None = None
            score = self._evaluate(current_state, previously_attempted_skills)

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
        return False or any(plugin.has_persistence() for plugin in self._utility_skill_plugins)
    
    @abstractmethod
    def delete_persisted_configuration(self):
        for plugin in self._utility_skill_plugins:
            plugin.delete_persisted_configuration()

    @abstractmethod
    def persist_configuration_as_global(self):
        for plugin in self._utility_skill_plugins:
            plugin.persist_configuration_as_global()

    @abstractmethod
    def persist_configuration_for_account(self):
        for plugin in self._utility_skill_plugins:
            plugin.persist_configuration_for_account()