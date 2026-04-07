from typing import Any, Generator, cast, override

from Py4GWCoreLib.enums import Range
from Py4GWCoreLib import Agent, Player
from Py4GWCoreLib.native_src.context.WorldContext import AttributeStruct
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.plugins.options.raw_boolean_option import RawBooleanOption
from Sources.oazix.CustomBehaviors.skills.plugins.targeting_modifiers.buff_configurator import BuffConfigurator
from Sources.oazix.CustomBehaviors.skills.plugins.watchdogs.should_lock_until_buff_completion import ShouldLockUntilBuffCompletion

class HeroicRefrainUtility(CustomSkillUtilityBase):
    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(50)
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Heroic_Refrain"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])

        self.score_definition: ScoreStaticDefinition = score_definition
        
        self.add_plugin_option(lambda x: RawBooleanOption(x.custom_skill, "should_cast_on_self_until_leadership_is_20", True))
        self.add_plugin_targetting_modifier(lambda x: BuffConfigurator(event_bus, self.custom_skill, buff_configuration_per_profession= BuffConfigurationPerProfession.BUFF_CONFIGURATION_ALL))
        self.add_plugin_watchdog(lambda x: ShouldLockUntilBuffCompletion(x.custom_skill, is_buff_config_fulfilled= lambda: self._get_target_agent_id() is None, default_value= False))

    def get_leadership_attribute_level_on_self(self) -> int:
        attributes: list[AttributeStruct] = Agent.GetAttributes(Player.GetAgentID())
        leadership_attribute:AttributeStruct|None = next((attribute for attribute in attributes if attribute.GetName() == 'Leadership'), None)
        return leadership_attribute.level if leadership_attribute is not None else 0


    def _get_target_agent_id(self) -> int | None:

        # PHASE 1 - CAST ON SELF
        should_cast_on_self_option: RawBooleanOption | None = cast(RawBooleanOption | None, self.get_plugin_option("should_cast_on_self_until_leadership_is_20"))

        if should_cast_on_self_option is not None and should_cast_on_self_option.option_value and self.get_leadership_attribute_level_on_self() < 20:
            return Player.GetAgentID()
        
        # PHASE 2 - CAST ON PARTY

        targets: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
                within_range=Range.Spellcast.value * 1.2,
                condition=lambda agent_id: self.get_plugin_targeting_modifiers_filtering_predicate()(agent_id) ,
                sort_key=(TargetingOrder.DISTANCE_ASC, TargetingOrder.CASTER_THEN_MELEE),
                range_to_count_enemies=None,
                range_to_count_allies=None)
        
        # sort by priority
        targets.sort(key=lambda target: self.get_plugin_targeting_modifiers_ordering_predicate()(target.agent_id))

        if targets is None: return None
        if len(targets) <= 0: return None
        return targets[0].agent_id

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        target_agent_id: int | None = self._get_target_agent_id()
        if target_agent_id is None: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        target_agent_id: int | None = self._get_target_agent_id()
        if target_agent_id is None: return BehaviorResult.ACTION_SKIPPED
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target_agent_id)
        return result