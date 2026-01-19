from typing import Any, Generator, override

from Py4GWCoreLib.native_src.context.WorldContext import AttributeStruct
import PyImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.enums import Profession, Range
from Py4GWCoreLib import Player
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

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
        self.should_reach_leadership_attribute_score_of_20 = True # it will cause issue if you don't have 16 leadership base. can be dactivated through UI(customized_debug_ui & detailled mode)

    def _get_target_agent_id(self) -> int | None:

        # PHASE 1 - DOUBLE CAST ON PARAGON
        # it will cause issue if you don't have 16 leadership base. can be dactivated through UI(customized_debug_ui & detailled mode)

        if self.should_reach_leadership_attribute_score_of_20:
            attributes: list[AttributeStruct] = Agent.GetAttributes(Player.GetAgentID())
            leadership_attribute:AttributeStruct|None = next((attribute for attribute in attributes if attribute.GetName() == 'Leadership'), None)
            if leadership_attribute is not None and leadership_attribute.level < 20:
                return Player.GetAgentID()

        # PHASE 2 - CAST ON PARTY

        targets: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
                within_range=Range.Spellcast,
                condition=lambda agent_id: not custom_behavior_helpers.Resources.is_ally_under_specific_effect(agent_id, self.custom_skill.skill_id),
                sort_key=(TargetingOrder.DISTANCE_ASC, TargetingOrder.CASTER_THEN_MELEE),
                range_to_count_enemies=None,
                range_to_count_allies=None)

        if targets is None: return None
        if len(targets) <= 0: return None

        # take player first.
        for target in targets:
            if target.agent_id == Player.GetAgentID():
                return target.agent_id

        # then take party, no priority atm
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

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"should_reach_leadership_20 : {self.should_reach_leadership_attribute_score_of_20}")
        self.should_reach_leadership_attribute_score_of_20 = PyImGui.checkbox("should_reach_leadership_attribute_score_of_20", self.should_reach_leadership_attribute_score_of_20)

