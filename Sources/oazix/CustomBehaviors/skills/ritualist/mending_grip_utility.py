from typing import Any, Generator, override

from Py4GWCoreLib import Range, Agent
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class MendingGripUtility(CustomSkillUtilityBase):
    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerHealthGravityDefinition = ScorePerHealthGravityDefinition(6),
        mana_required_to_cast: int = 5,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Mending_Grip"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )
        self.score_definition: ScorePerHealthGravityDefinition = score_definition

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        return custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,
            condition=lambda agent_id: (
                Agent.IsWeaponSpelled(agent_id)
                and Agent.IsConditioned(agent_id)
                and Agent.GetHealth(agent_id) < 0.8
            ),
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        targets = self._get_targets()
        if len(targets) == 0:
            return None
        if targets[0].hp < 0.40:
            return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY)
        return self.score_definition.get_score(HealingScore.MEMBER_CONDITIONED)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        targets = self._get_targets()
        if len(targets) == 0:
            return BehaviorResult.ACTION_SKIPPED
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=targets[0].agent_id)
        return result

