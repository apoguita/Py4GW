from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Range, Agent
from Py4GWCoreLib.enums import Profession
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Widgets.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Widgets.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class MendBodyAndSoulUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerHealthGravityDefinition = ScorePerHealthGravityDefinition(7),
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Mend_Body_and_Soul"),
            in_game_build=current_build,
            score_definition=score_definition,
            allowed_states=allowed_states)

        self.score_definition: ScorePerHealthGravityDefinition = score_definition
        self.cure_effect_configuration: BuffConfigurationPerProfession = BuffConfigurationPerProfession(self.custom_skill, BuffConfigurationPerProfession.BUFF_CONFIGURATION_MARTIAL)

    @staticmethod
    def _get_lowest_hp_target() -> custom_behavior_helpers.SortableAgentData | None:

            targets: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
                within_range=Range.Spirit.value,
                condition=lambda agent_id: True,
                sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC))
            return targets[0] if len(targets) > 0 else None

    def _get_melee_blind_or_crippled_if_exist(self) -> custom_behavior_helpers.SortableAgentData | None:
        
        blind_skill_id = GLOBAL_CACHE.Skill.GetID("Blind")
        crippled_skill_id = GLOBAL_CACHE.Skill.GetID("Crippled")
        
        targets: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spirit.value,
            condition=lambda agent_id: 
                self.cure_effect_configuration.get_agent_id_predicate()(agent_id) and
                custom_behavior_helpers.Resources.is_ally_under_specific_effect(agent_id, blind_skill_id) and
                custom_behavior_helpers.Resources.is_ally_under_specific_effect(agent_id, crippled_skill_id),
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC))
        
        return targets[0] if len(targets) > 0 else None

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        lowest_target: custom_behavior_helpers.SortableAgentData | None = self._get_lowest_hp_target()
        if lowest_target is None: return None
        
        is_spirit_exist:bool = custom_behavior_helpers.Resources.is_spirit_exist(within_range=Range.Earshot)
        is_conditioned:bool = Agent.IsConditioned(lowest_target.agent_id)
        blind_or_crippled_melee_target: custom_behavior_helpers.SortableAgentData | None = self._get_melee_blind_or_crippled_if_exist()

        if lowest_target.hp < 0.40:
            return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY)
        
        if is_spirit_exist:
            if blind_or_crippled_melee_target is not None:
                return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY)
            if lowest_target.hp < 0.85 and is_conditioned:
                return self.score_definition.get_score(HealingScore.MEMBER_CONDITIONED)

        if lowest_target.hp < 0.75:
            return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED)

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        lowest_target: custom_behavior_helpers.SortableAgentData | None = self._get_lowest_hp_target()
        if lowest_target is None: return BehaviorResult.ACTION_SKIPPED
        final_target_id: int = lowest_target.agent_id

        if lowest_target.hp > 0.40:
            second_target: custom_behavior_helpers.SortableAgentData | None = self._get_melee_blind_or_crippled_if_exist()
            if second_target is not None:
                final_target_id = second_target.agent_id

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=final_target_id)
        return result
