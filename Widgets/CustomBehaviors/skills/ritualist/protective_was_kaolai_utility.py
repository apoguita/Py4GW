from typing import Any, Generator, override

from Py4GWCoreLib import Routines, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Widgets.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class ProtectiveWasKaolaiUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerHealthGravityDefinition = ScorePerHealthGravityDefinition(5),
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Protective_Was_Kaolai"),
            in_game_build=current_build,
            score_definition=score_definition,
            allowed_states=allowed_states)

        self.score_definition: ScorePerHealthGravityDefinition = score_definition

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        #reusing the parent function without checking if the skill is ready
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if custom_behavior_helpers.Resources.get_player_absolute_energy() < self.mana_required_to_cast: return False
        if not custom_behavior_helpers.Resources.has_enough_resources(self.custom_skill): return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        
        is_player_holding_an_item: bool = custom_behavior_helpers.Resources.is_player_holding_an_item()
        is_skill_ready: bool = Routines.Checks.Skills.IsSkillIDReady(self.custom_skill.skill_id) and custom_behavior_helpers.Resources.has_enough_resources(self.custom_skill)
        
        if not is_player_holding_an_item and is_skill_ready: return 90

        # 3 allies or more with less than 40% health or average group health lower than 75%
        if custom_behavior_helpers.Heals.is_party_damaged(within_range=Range.Spirit.value, min_allies_count=3, less_health_than_percent=0.4) \
            or custom_behavior_helpers.Heals.party_average_health(within_range=Range.Spirit.value) < 0.75:
            return self.score_definition.get_score(HealingScore.PARTY_DAMAGE_EMERGENCY)

        #one ally with less than 40%
        first_member_damaged: int | None = custom_behavior_helpers.Heals.get_first_member_damaged(within_range=Range.Spirit.value, less_health_than_percent=0.4, exclude_player=False)
        if first_member_damaged is not None:
            return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY)

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        
        is_player_holding_an_item: bool = custom_behavior_helpers.Resources.is_player_holding_an_item()
        is_skill_ready: bool = Routines.Checks.Skills.IsSkillIDReady(self.custom_skill.skill_id) and custom_behavior_helpers.Resources.has_enough_resources(self.custom_skill)
        
        # either we are skill_ready & ashes hold
        # either we are skill_not_ready & ashes hold
        
        if is_skill_ready:
            result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
            return result 
        else:
            result = yield from custom_behavior_helpers.Actions.player_drop_item_if_possible()
            if result is BehaviorResult.ACTION_PERFORMED: return result

        return BehaviorResult.ACTION_SKIPPED