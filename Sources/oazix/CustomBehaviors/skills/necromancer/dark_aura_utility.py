from typing import List, Any, Generator, Callable, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class DarkAuraUtility(CustomSkillUtilityBase):

    def __init__(self,
                 event_bus: EventBus,
                 current_build: list[CustomSkill],
                 score_definition: ScoreStaticDefinition = ScoreStaticDefinition(20),
                 mana_required_to_cast: int = 20,
                 allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Dark_Aura"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

        # Use the buff configuration helper. Choose a sensible default config; change to per-profession if desired.
        self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget(
            event_bus,
            self.custom_skill,
            buff_configuration_per_profession=BuffConfigurationPerProfession.BUFF_CONFIGURATION_ALL
        )

        self.soul_taker_skill = CustomSkill("Soul_Taker")
        self.masochism_skill = CustomSkill("Masochism")

    def _get_target(self) -> int | None:

        has_soul_taker_or_masochism = lambda agent_id: custom_behavior_helpers.Resources.is_ally_under_specific_effect(agent_id, self.soul_taker_skill.skill_id) or custom_behavior_helpers.Resources.is_ally_under_specific_effect(agent_id, self.masochism_skill.skill_id)
        has_not_dark_aura = lambda agent_id: not custom_behavior_helpers.Resources.is_ally_under_specific_effect(agent_id, self.custom_skill.skill_id)

        target = custom_behavior_helpers.Targets.get_first_or_default_from_allies_ordered_by_priority(
                within_range=Range.Spellcast.value * 1.5,
                condition=lambda agent_id: self.buff_configuration.get_agent_id_predicate()(agent_id) and has_soul_taker_or_masochism(agent_id) and has_not_dark_aura(agent_id) and Player.GetAgentID() != agent_id,
                sort_key=(TargetingOrder.DISTANCE_ASC,),
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
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target)
        return result

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return self.buff_configuration
    
    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        target = self._get_target()
        if target is not None:
            PyImGui.bullet_text(f"target : {target}")
        else:
            PyImGui.bullet_text(f"no target found")