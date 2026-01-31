import re
from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Agent, Player
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, ThrottledTimer
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
import time
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class MoveToEnemyIfCloseEnoughUtility(CustomSkillUtilityBase):
    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
            allowed_states: list[BehaviorState] = [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("move_to_enemy_if_close_enough"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.BOTTING.value),
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.BOTTING,
            execution_strategy=UtilitySkillExecutionStrategy.STOP_EXECUTION_ONCE_SCORE_NOT_HIGHEST)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.BOTTING.value)
        self.throttle_timer = ThrottledTimer(1000)

    def __get_enemy_to_fight(self) -> int | None:
        enemy_aggressive_id = Routines.Agents.GetNearestEnemy(Range.Spellcast.value * 1.5, aggressive_only=True)
        if enemy_aggressive_id is not None and enemy_aggressive_id > 0 and Agent.IsValid(enemy_aggressive_id): 
            return enemy_aggressive_id

        enemy_id = Routines.Agents.GetNearestEnemy(Range.Spellcast.value + 300, aggressive_only=False)
        if enemy_id is not None and enemy_id > 0 and Agent.IsValid(enemy_id): 
            return enemy_id

        return None

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if not self.throttle_timer.IsExpired():
            return None

        enemy_id = self.__get_enemy_to_fight()
        if enemy_id is not None:
            return self.score_definition.get_score()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        enemy_id = self.__get_enemy_to_fight()
        if enemy_id is None: return BehaviorResult.ACTION_SKIPPED

        Player.ChangeTarget(enemy_id)
        yield from custom_behavior_helpers.Helpers.wait_for(100) 
        Player.Interact(enemy_id, False)
        yield from custom_behavior_helpers.Helpers.wait_for(5_000)

        self.throttle_timer.Reset()
        return BehaviorResult.ACTION_PERFORMED