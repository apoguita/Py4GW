from typing import Any, Generator, override
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.enums import Profession, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
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
        current_build: list[CustomSkill], 
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(50)
        ) -> None:

        super().__init__(
            skill=CustomSkill("Heroic_Refrain"), 
            in_game_build=current_build, 
            score_definition=score_definition, 
            mana_required_to_cast=0, 
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        
        self.score_definition: ScoreStaticDefinition = score_definition

    def _get_target(self) -> custom_behavior_helpers.SortableAgentData | None:

        # no double cast to reach 20 leadership for now - 19 is enough as POC

        from HeroAI.utils import CheckForEffect

        targets: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
                within_range=Range.Spellcast,
                condition=lambda agent_id: not CheckForEffect(agent_id, self.custom_skill.skill_id),
                sort_key=(TargetingOrder.DISTANCE_ASC, TargetingOrder.CASTER_THEN_MELEE),
                range_to_count_enemies=None,
                range_to_count_allies=None)

        if targets is None: return None
        if len(targets) <= 0: return None

        # take player first.
        for target in targets:
            if target.agent_id == GLOBAL_CACHE.Player.GetAgentID():
                return target

        # then take party, no priority atm
        return targets[0]

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        target: custom_behavior_helpers.SortableAgentData | None = self._get_target()
        if target is None: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        target: custom_behavior_helpers.SortableAgentData | None = self._get_target()
        if target is None: return BehaviorResult.ACTION_SKIPPED
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        return result