from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range, Player
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, ThrottledTimer, Utils
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
import time
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class MoveToPartyMemberIfDeadUtility(CustomSkillUtilityBase):
    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
            allowed_states: list[BehaviorState] = [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("move_to_party_member_if_dead"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.BOTTING.value),
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.BOTTING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.BOTTING.value+ 0.0091)
        self.throttle_timer = ThrottledTimer(3000)

        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    def _get_first_player_dead(self) -> int | None:
        # we could add support for GetHenchmen & GetHeroes
        players = GLOBAL_CACHE.Party.GetPlayers()
        for player in players:
            agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
            if Agent.IsDead(agent_id): 
                agent_id_position: tuple[float, float] = Agent.GetXY(agent_id)
                player_agent_id_position: tuple[float, float] = Agent.GetXY(Player.GetAgentID())
                if Utils.Distance(player_agent_id_position , agent_id_position) < 2500: #todo constant
                    return agent_id
        return None

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if not self.throttle_timer.IsExpired(): return None
        agent_id_dead = self._get_first_player_dead()
        if agent_id_dead is not None: return self.score_definition.get_score()
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        agent_id_dead = self._get_first_player_dead()
        if agent_id_dead is None: return BehaviorResult.ACTION_SKIPPED

        agent_id_position: tuple[float, float] = Agent.GetXY(agent_id_dead)
        Player.Move(agent_id_position[0], agent_id_position[1])
        yield from custom_behavior_helpers.Helpers.wait_for(100)
        self.throttle_timer.Reset()
        yield
        return BehaviorResult.ACTION_PERFORMED