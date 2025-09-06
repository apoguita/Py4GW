from typing import Any, Generator, override

from Py4GWCoreLib import Routines, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Widgets.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class LifeUtility(CustomSkillUtilityBase):
    def __init__(self, 
        current_build: list[CustomSkill], 
        score_definition: ScorePerHealthGravityDefinition = ScorePerHealthGravityDefinition(1),
        mana_required_to_cast: int = 10,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            skill=CustomSkill("Life"),
            in_game_build=current_build, 
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)

        self.score_definition: ScorePerHealthGravityDefinition = score_definition

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if current_state is BehaviorState.FAR_FROM_AGGRO: return None

        spirit_exists:bool = custom_behavior_helpers.Resources.is_spirit_exist(
            within_range=Range.Spirit,
            associated_to_skill=self.custom_skill
        )

        if spirit_exists:
            return None
        if current_state is BehaviorState.CLOSE_TO_AGGRO:
            return self.score_definition.get_score(HealingScore.PARTY_HEALTHY)

        return self.score_definition.get_score(HealingScore.PARTY_DAMAGE)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        is_skill_ready: bool = Routines.Checks.Skills.IsSkillIDReady(self.custom_skill.skill_id) and custom_behavior_helpers.Resources.has_enough_resources(self.custom_skill)

        if is_skill_ready:
            result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
            return result 
        else:
            result = yield from custom_behavior_helpers.Actions.player_drop_item_if_possible()
            if result is BehaviorResult.ACTION_PERFORMED: return result

        return BehaviorResult.ACTION_SKIPPED