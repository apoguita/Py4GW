from tkinter.constants import N
from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState

from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class HeartofShadowUtility(CustomSkillUtilityBase):
    def __init__(self,
    event_bus: EventBus,
    current_build: list[CustomSkill],
    score_definition: ScoreStaticDefinition,
    mana_required_to_cast: int = 0,
    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Heart_of_Shadow"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition
        self.is_player_stuck: bool = False
        self.player_stuck_target: int | None = None

        self.event_bus.subscribe(EventType.PLAYER_STUCK, self.on_player_stuck, subscriber_name=self.custom_skill.skill_name)
    
    def on_player_stuck(self, message: EventMessage)-> Generator[Any, Any, Any]:
        self.is_player_stuck = True
        self.player_stuck_target = message.data
        yield

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        
        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
                    within_range=Range.Spellcast,
                    condition=lambda agent_id: Agent.IsAggressive(agent_id),
                    sort_key=(TargetingOrder.DISTANCE_DESC, ),
                    range_to_count_enemies=None)
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID()) < 0.05:
            return 97

        if Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID()) < 0.35:
            return 97

        if self.is_player_stuck:
            return 97

        return self.score_definition.get_score() 

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        target: int|None = None
        targets = self._get_targets()
        if len(targets) > 0: 
            target = targets[0].agent_id

        if target is None: 
            result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
            if result is BehaviorResult.ACTION_PERFORMED:
                self.is_player_stuck = False
                self.player_stuck_target = None
            return result
        else:
            result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target)
            if result is BehaviorResult.ACTION_PERFORMED:
                self.is_player_stuck = False
                self.player_stuck_target = None
            return result