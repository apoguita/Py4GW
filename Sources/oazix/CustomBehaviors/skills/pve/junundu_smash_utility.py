from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class JununduSmashUtility(CustomSkillUtilityBase):
    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 66 if enemy_qte >= 2 else 50),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Junundu_Smash"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Adjacent,
            condition=lambda agent_id: True,
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, ),
            range_to_count_enemies=Range.Adjacent.value
        )
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        """
        Return score based on the number of enemies in adjacent range of the best target.
        """
        targets = self._get_targets()
        if len(targets) == 0:
            return None
        
        # Get the best target (most enemies in adjacent range)
        best_target = targets[0]
        
        return self.score_definition.get_score(best_target.enemy_quantity_within_range)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        """
        Cast Junundu Smash on the target with the most enemies in adjacent range.
        """
        targets = self._get_targets()
        if len(targets) == 0: return BehaviorResult.ACTION_SKIPPED

        target = targets[0]
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        return result

