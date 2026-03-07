from typing import Any, Generator, override
import PyImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.enums import Profession, Range
from Py4GWCoreLib import Agent, Player, Routines
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class GreatDwarfWeaponUtility(CustomSkillUtilityBase):

    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(30),
        mana_required_to_cast: int = 10,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Great_Dwarf_Weapon"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
                
        self.score_definition: ScoreStaticDefinition = score_definition

        data: str | None = PersistenceLocator().skills.read(self.custom_skill.skill_name, "buff_configuration")
        if data is not None:
            self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget.instanciate_from_string(self.event_bus, self.custom_skill, data)
        else:
            self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget(event_bus, self.custom_skill, buff_configuration_per_profession= BuffConfigurationPerProfession.BUFF_CONFIGURATION_MARTIAL)

        self.prefer_model_target: bool = bool(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "prefer_model_target", "1") == "1")
        self.model_id_filter: int = int(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "model_id_filter", "5903"))
        self.strict_model_targeting: bool = bool(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "strict_model_targeting", "0") == "1")

    def _get_target(self) -> int | None:

        if self.prefer_model_target and self.model_id_filter > 0:
            npc_agent_id = Routines.Agents.GetNearestAliveAgentByModelID(self.model_id_filter, Range.Spellcast.value)
            if npc_agent_id and npc_agent_id != Player.GetAgentID() and not Agent.IsWeaponSpelled(npc_agent_id):
                return npc_agent_id

        if self.strict_model_targeting:
            return None
        
        # Check if we have a valid target
        target = custom_behavior_helpers.Targets.get_first_or_default_from_allies_ordered_by_priority(
                within_range=Range.Spellcast.value * 1.2,
                condition=lambda agent_id: 
                    agent_id != Player.GetAgentID() and 
                    not Agent.IsWeaponSpelled(agent_id) and
                    self.buff_configuration.get_agent_id_predicate()(agent_id),
                sort_key=(TargetingOrder.DISTANCE_DESC, TargetingOrder.CASTER_THEN_MELEE),
                range_to_count_enemies=None,
                range_to_count_allies=None)
    
        return target

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        target = self._get_target()
        if target is None: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        target = self._get_target()
        if target is None: return BehaviorResult.ACTION_SKIPPED
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target)
        return result 

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return self.buff_configuration
    
    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text("prefer_model_target :")
        self.prefer_model_target = PyImGui.checkbox("##gdw_prefer_model_target", self.prefer_model_target)
        PyImGui.bullet_text("model_id_filter :")
        self.model_id_filter = PyImGui.input_int("##gdw_model_id_filter", self.model_id_filter)
        if self.model_id_filter < 0:
            self.model_id_filter = 0
        PyImGui.bullet_text("strict_model_targeting :")
        self.strict_model_targeting = PyImGui.checkbox("##gdw_strict_model_targeting", self.strict_model_targeting)

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "buff_configuration", self.buff_configuration.serialize_to_string())
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "prefer_model_target", "1" if self.prefer_model_target else "0")
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "model_id_filter", str(self.model_id_filter))
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "strict_model_targeting", "1" if self.strict_model_targeting else "0")
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "buff_configuration", self.buff_configuration.serialize_to_string())
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "prefer_model_target", "1" if self.prefer_model_target else "0")
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "model_id_filter", str(self.model_id_filter))
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "strict_model_targeting", "1" if self.strict_model_targeting else "0")
        print("configuration saved as global")

    @override
    def delete_persisted_configuration(self):
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "buff_configuration")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "prefer_model_target")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "model_id_filter")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "strict_model_targeting")
        print("configuration deleted")
