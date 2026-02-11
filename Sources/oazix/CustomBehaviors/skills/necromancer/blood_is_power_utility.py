from tkinter.constants import N
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Player
from Py4GWCoreLib.enums import Profession
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target import CustomBuffTarget
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_email import BuffConfigurationPerPlayerEmail
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class BloodIsPowerUtility(CustomSkillUtilityBase):
    def __init__(self, 
        event_bus:EventBus,
        current_build: list[CustomSkill], 
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(33),
        sacrifice_life_limit_percent: float = 0.55,
        sacrifice_life_limit_absolute: int = 175,
        required_target_mana_lower_than_percent: float = 0.40,
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Blood_is_Power"), 
            in_game_build=current_build, 
            score_definition=score_definition, 
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition

        data: str | None = PersistenceLocator().skills.read(self.custom_skill.skill_name, "buff_configuration")
        if data is not None:
            self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget.instanciate_from_string(self.event_bus, self.custom_skill, data)
        else:
            self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget(self.event_bus, self.custom_skill, buff_configuration_per_profession= BuffConfigurationPerProfession.BUFF_CONFIGURATION_CASTERS)

        self.sacrifice_life_limit_percent: float = float(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "sacrifice_life_limit_percent", str(sacrifice_life_limit_percent)))
        self.sacrifice_life_limit_absolute: int = int(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "sacrifice_life_limit_absolute", str(sacrifice_life_limit_absolute)))
        self.required_target_mana_lower_than_percent: float = float(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "required_target_mana_lower_than_percent", str(required_target_mana_lower_than_percent)))

    def _get_target(self) -> int | None:
 
        target: int | None = custom_behavior_helpers.Targets.get_first_or_default_from_allies_ordered_by_priority(
                within_range=Range.Spellcast.value,
                condition=lambda agent_id:
                    agent_id != Player.GetAgentID() and
                    custom_behavior_helpers.Resources.get_energy_percent_in_party(agent_id) < self.required_target_mana_lower_than_percent and
                    self.buff_configuration.get_agent_id_predicate()(agent_id),
                sort_key=(TargetingOrder.ENERGY_ASC, TargetingOrder.DISTANCE_ASC),
                range_to_count_enemies=None,
                range_to_count_allies=None)

        return target

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if not custom_behavior_helpers.Resources.player_can_sacrifice_health(33, self.sacrifice_life_limit_percent, self.sacrifice_life_limit_absolute):
            return None

        if self._get_target() is None: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        target = self._get_target()
        if target is None: return BehaviorResult.ACTION_SKIPPED
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target)
        return result

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return self.buff_configuration
    
    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"sacrifice_life_limit_percent :")
        self.sacrifice_life_limit_percent = PyImGui.input_float("##sacrifice_life_limit_percent", self.sacrifice_life_limit_percent)
        PyImGui.bullet_text(f"sacrifice_life_limit_absolute :")
        self.sacrifice_life_limit_absolute = PyImGui.input_int("##sacrifice_life_limit_absolute", self.sacrifice_life_limit_absolute)
        PyImGui.bullet_text(f"required_target_mana_lower_than_percent :")
        self.required_target_mana_lower_than_percent = PyImGui.input_float("##required_target_mana_lower_than_percent", self.required_target_mana_lower_than_percent)

    
    @override
    def has_persistence(self) -> bool:
        return True
    
    @override
    def persist_configuration_for_account(self):
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "buff_configuration", self.buff_configuration.serialize_to_string())
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "sacrifice_life_limit_percent", f"{self.sacrifice_life_limit_percent:.2f}")
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "sacrifice_life_limit_absolute", str(self.sacrifice_life_limit_absolute))
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "required_target_mana_lower_than_percent", f"{self.required_target_mana_lower_than_percent:.2f}")
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "buff_configuration", self.buff_configuration.serialize_to_string())
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "sacrifice_life_limit_percent", f"{self.sacrifice_life_limit_percent:.2f}")
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "sacrifice_life_limit_absolute", str(self.sacrifice_life_limit_absolute))
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "required_target_mana_lower_than_percent", f"{self.required_target_mana_lower_than_percent:.2f}")
        print("configuration saved as global")

    @override
    def delete_persisted_configuration(self):
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "buff_configuration")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "buff_configuration")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "sacrifice_life_limit_percent")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "sacrifice_life_limit_absolute")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "required_target_mana_lower_than_percent")
        print("configuration deleted")