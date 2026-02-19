from typing import Any, Callable, Generator, override

import PyImGui

from Py4GWCoreLib import Player, Range, Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars import utility_skill_finder
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget, CustomBuffTargetMode
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.auto_combat_utility import AutoCombatUtility


class ArcaneMimicryUtility(CustomSkillUtilityBase):
    """
    Arcane Mimicry utility - Mesmer skill that copies an elite skill from target ally.
    Targets allies based on buff configuration (default: none).
    """

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        skill_to_copy_instance: Callable[[], CustomSkillUtilityBase] | None = None,
        pre_check_condition: Callable[[], bool] | None = None,
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(90),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Arcane_Mimicry"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition: ScoreStaticDefinition = score_definition
        self.skill_to_copy_default_instance: Callable[[], CustomSkillUtilityBase] | None = skill_to_copy_instance
        self.skill_to_copy_instance : CustomSkillUtilityBase | None = None
        self.pre_check_condition: Callable[[], bool] | None = pre_check_condition

        # Load persisted configuration or default to none (empty list = all professions deactivated)
        data: str | None = PersistenceLocator().skills.read(self.custom_skill.skill_name, "buff_configuration")
        if data is not None:
            self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget.instanciate_from_string(self.event_bus, self.custom_skill, data)
        else:
            # Default to none - pass empty list so all professions are deactivated
            self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget(event_bus, self.custom_skill, buff_mode=CustomBuffTargetMode.PER_EMAIL)

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        # arcane mimicry is a particular. we can't check it when it is replacing another skill.
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if custom_behavior_helpers.Resources.get_player_absolute_energy() < self.mana_required_to_cast: return False
        if self.pre_check_condition is not None and self.pre_check_condition() == False: return False
        return True
    
    def _get_target(self) -> int | None:
        target = custom_behavior_helpers.Targets.get_first_or_default_from_allies_ordered_by_priority(
            within_range=Range.Spellcast.value * 1.2,
            condition=lambda agent_id: self.buff_configuration.get_agent_id_predicate()(agent_id) and Player.GetAgentID() != agent_id,
            sort_key=(TargetingOrder.DISTANCE_ASC,),
            range_to_count_enemies=None,
            range_to_count_allies=None,
        )
        return target

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if not self.are_common_pre_checks_valid(current_state): return None
        
        if GLOBAL_CACHE.SkillBar.GetSkillData(self.custom_skill.skill_slot).event == -1: # arcane mimicry is in copy mode
            if self.skill_to_copy_instance is None:
                skill_id = GLOBAL_CACHE.SkillBar.GetSkillData(self.custom_skill.skill_slot).id.id
                skill_name = GLOBAL_CACHE.Skill.GetName(skill_id)
                if self.skill_to_copy_default_instance is not None:
                    self.skill_to_copy_instance = self.skill_to_copy_default_instance() # must be a callable so the utility skill is able to detect the correct skillbar slot (done at instanciation time)
                else:
                    self.skill_to_copy_instance = AutoCombatUtility(self.event_bus, CustomSkill(skill_name), self.in_game_build)
            return self.skill_to_copy_instance.evaluate(current_state, previously_attempted_skills)
        
        if GLOBAL_CACHE.SkillBar.GetSkillData(self.custom_skill.skill_slot).event == 0: # arcane mimicry is not in copy mode (available or recharging)
            # let's remove the copied skill
            if self.skill_to_copy_instance is not None: self.skill_to_copy_instance = None

            if not Routines.Checks.Skills.IsSkillIDReady(self.custom_skill.skill_id): return None
            target = self._get_target()
            if target is None: return None
            return self.score_definition.get_score()
        
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        if GLOBAL_CACHE.SkillBar.GetSkillData(self.custom_skill.skill_slot).event == 0: # arcane mimicry is not in copy mode (available or recharging)
            target = self._get_target()
            if target is None: return BehaviorResult.ACTION_SKIPPED
            result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target)
            return result

        if GLOBAL_CACHE.SkillBar.GetSkillData(self.custom_skill.skill_slot).event == -1: # arcane mimicry is in copy mode
            # let's execute the copied skill
            if self.skill_to_copy_instance is None: return BehaviorResult.ACTION_SKIPPED
            result = yield from self.skill_to_copy_instance.execute(state)
            return result

        return BehaviorResult.ACTION_SKIPPED
    
    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        if self.pre_check_condition is not None: 
            PyImGui.bullet_text(f"pre_check_condition result : {self.pre_check_condition()}")
        PyImGui.bullet_text(f"skill_to_copy_default_instance : {self.skill_to_copy_default_instance}")
        PyImGui.bullet_text(f"skill_to_copy_instance : {self.skill_to_copy_instance}")
        if self.skill_to_copy_instance is not None: 
            self.skill_to_copy_instance.customized_debug_ui(current_state)
            buff_config : CustomBuffMultipleTarget | None = self.skill_to_copy_instance.get_buff_configuration()
            if buff_config is not None: buff_config.render_buff_configuration()

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return self.buff_configuration

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        PersistenceLocator().skills.write_for_account(
            str(self.custom_skill.skill_name), "buff_configuration", self.buff_configuration.serialize_to_string()
        )
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        PersistenceLocator().skills.write_global(
            str(self.custom_skill.skill_name), "buff_configuration", self.buff_configuration.serialize_to_string()
        )
        print("configuration saved as global")

    @override
    def delete_persisted_configuration(self):
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "buff_configuration")
        print("configuration deleted")

