from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Map, Agent, Player
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer

from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class DeathDetectionUtility(CustomSkillUtilityBase):
    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("death_detection"), 
            in_game_build=current_build, 
            score_definition=ScoreStaticDefinition(CommonScore.DEAMON.value), 
            allowed_states=[BehaviorState.IDLE, BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.DAEMON)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.BOTTING.value)

        self.__death_timer = ThrottledTimer(120_000)
        self.__party_death_timer = ThrottledTimer(5_000)
        
        self.event_bus.subscribe(EventType.MAP_CHANGED, self.map_changed, subscriber_name=self.custom_skill.skill_name)

    def map_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:
        del message  # Unused parameter
        self.__death_timer.Reset()
        self.__party_death_timer.Reset()
        yield

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        del current_state, previously_attempted_skills  # Unused parameters
        if not Map.IsExplorable(): return None
        if not custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader(): return None

        if custom_behavior_helpers.Resources.is_party_dead():
            return self.score_definition.get_score()
        
        if Agent.IsDead(Player.GetAgentID()):
            return self.score_definition.get_score()
        
        # Player/Party is alive again; clear any pending death timer
        self.__party_death_timer.Reset()
        self.__death_timer.Reset()
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
                    
        if custom_behavior_helpers.Resources.is_party_dead():
            if self.__party_death_timer.IsExpired():
                yield from self.event_bus.publish(EventType.PARTY_DEATH, state)
                return BehaviorResult.ACTION_PERFORMED
            
        if Agent.IsDead(Player.GetAgentID()):
            if self.__death_timer.IsExpired():
                yield from self.event_bus.publish(EventType.PLAYER_CRITICAL_DEATH, state)
                return BehaviorResult.ACTION_PERFORMED

        yield
        return BehaviorResult.ACTION_SKIPPED

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        pass
        # PyImGui.bullet_text(f"__stuck_count : {self.__stuck_count}")
        # PyImGui.bullet_text(f"__stuck_timer : {self.throttle_timer.GetTimeRemaining()}")