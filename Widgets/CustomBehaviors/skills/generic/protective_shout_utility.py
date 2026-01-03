from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class ProtectiveShoutUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        skill: CustomSkill,
        current_build: list[CustomSkill],
        allies_health_less_than_percent: float = 0.8,
        allies_quantity_required: int = 2,
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(90),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScoreStaticDefinition = score_definition
        self.allies_health_less_than_percent: float = allies_health_less_than_percent
        self.allies_quantity_required: int = allies_quantity_required

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        
        targets: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Earshot,
            condition=lambda agent_id: Agent.GetHealth(agent_id) < self.allies_health_less_than_percent,
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC))
        
        if len(targets) == 0: return None
        if len(targets) < self.allies_quantity_required: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result