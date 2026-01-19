import random
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Player
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer, Utils

from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
import time
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class StuckDetectionUtility(CustomSkillUtilityBase):
    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill], threshold: int = 80) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("stuck_detection"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.DEAMON.value),
            allowed_states=[BehaviorState.IDLE, BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.DAEMON)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.DEAMON.value)
        self.__previous_player_position : tuple[float, float] = (0, 0)
        self.throttle_timer_aggro = ThrottledTimer(8_000)  # 12 seconds for IN_AGGRO
        self.throttle_timer_non_aggro = ThrottledTimer(5_000)  # 5 seconds for CLOSE_TO_AGGRO and FAR_FROM_AGGRO
        self.__previous_state: BehaviorState | None = None  # Track state changes
        self.__stuck_count = 0
        self.__moving_samples = 0
        self.__required_moving_samples = 2
        self.__is_currently_stuck = False
        self.__cumulative_move = 0.0
        self.__movement_clear_threshold = threshold

        self.movement_threshold = threshold / 2
        
        self.event_bus.subscribe(EventType.MAP_CHANGED, self.map_changed, subscriber_name=self.custom_skill.skill_name)

    def map_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:
        self.__stuck_count = 0
        self.throttle_timer_aggro.Reset()
        self.throttle_timer_non_aggro.Reset()
        self.__previous_state = None
        self.__previous_player_position = (0, 0)
        self.__moving_samples = 0
        self.__is_currently_stuck = False
        self.__cumulative_move = 0.0
        yield

    def _get_throttle_timer(self, current_state: BehaviorState) -> ThrottledTimer:
        """Get the appropriate throttle timer based on the current behavior state."""
        if current_state == BehaviorState.IN_AGGRO:
            return self.throttle_timer_aggro
        else:  # CLOSE_TO_AGGRO, FAR_FROM_AGGRO, or IDLE
            return self.throttle_timer_non_aggro

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        # if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        throttle_timer = self._get_throttle_timer(current_state)

        # Check if state has changed and reset timer if needed
        if self.__previous_state != current_state:
            throttle_timer.Reset()
            self.__previous_state = current_state

        # Initialize the previous position on first run and wait for next tick
        if self.__previous_player_position == (0, 0):
            self.__previous_player_position = Player.GetXY()
            throttle_timer.Reset()
            return None

        if not throttle_timer.IsExpired():
            return None

        current_player_pos = Player.GetXY()
        distance_moved = Utils.Distance(self.__previous_player_position, current_player_pos)

        if distance_moved < self.movement_threshold:  # likely stuck
            self.__is_currently_stuck = True
            self.__moving_samples = 0
            self.__cumulative_move = 0.0
            return self.score_definition.get_score()
        else:
            # Track sustained movement before clearing stuck state
            if self.__is_currently_stuck:
                self.__moving_samples += 1
                self.__cumulative_move += distance_moved
                if self.__moving_samples >= self.__required_moving_samples and self.__cumulative_move >= self.__movement_clear_threshold:
                    self.__is_currently_stuck = False
                    self.__stuck_count = 0
                    self.__moving_samples = 0
                    self.__cumulative_move = 0.0

            # Always update baseline to the latest position to measure fresh movement next tick
            self.__previous_player_position = current_player_pos
            throttle_timer.Reset()
            return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        throttle_timer = self._get_throttle_timer(state)

        yield from self.event_bus.publish(EventType.PLAYER_STUCK, state, data=self.movement_threshold, publisher_name="stuck_detection") # we do through event as there is other skill that could subscribe to that, as heart_of_shadow
        self.__stuck_count += 1

        if GLOBAL_CACHE.Party.IsPartyLeader():
            if self.__stuck_count > 20:
                yield from self.event_bus.publish(EventType.PLAYER_CRITICAL_STUCK, state)

        throttle_timer.Reset()
        yield
        return BehaviorResult.ACTION_PERFORMED

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        throttle_timer = self._get_throttle_timer(current_state)
        PyImGui.bullet_text(f"__stuck_count : {self.__stuck_count}")
        PyImGui.bullet_text(f"__stuck_timer (current) : {throttle_timer.GetTimeRemaining()}")
        PyImGui.bullet_text(f"__stuck_timer_aggro (12s) : {self.throttle_timer_aggro.GetTimeRemaining()}")
        PyImGui.bullet_text(f"__stuck_timer_non_aggro (5s) : {self.throttle_timer_non_aggro.GetTimeRemaining()}")
