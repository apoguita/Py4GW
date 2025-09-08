from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Widgets.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class SpiritLightUtility(CustomSkillUtilityBase):
    def __init__(self, 
        current_build: list[CustomSkill], 
        score_definition: ScorePerHealthGravityDefinition = ScorePerHealthGravityDefinition(8),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            skill=CustomSkill("Spirit_Light"), 
            in_game_build=current_build, 
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)
                
        self.score_definition: ScorePerHealthGravityDefinition = score_definition

    @staticmethod
    def _get_targets() -> list[custom_behavior_helpers.SortableAgentData]:
        targets: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spirit,
            condition=lambda agent_id: GLOBAL_CACHE.Agent.GetHealth(agent_id) < 0.9,
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC))
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        targets = self._get_targets()
        if len(targets) == 0: return None

        is_spirit_exist:bool = custom_behavior_helpers.Resources.is_spirit_exist(within_range=Range.Earshot)
        # todo we could move close to it

        if not is_spirit_exist and not custom_behavior_helpers.Resources.player_can_sacrifice_health(17):
            return None

        if targets[0].hp < 0.85 and is_spirit_exist:
            return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED)
        if targets[0].hp < 0.40:
            return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY)
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        targets = self._get_targets()
        if len(targets) == 0: return BehaviorResult.ACTION_SKIPPED
        target = targets[0]
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        return result 