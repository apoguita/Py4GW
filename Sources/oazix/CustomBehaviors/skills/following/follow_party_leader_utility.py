import math
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import Agent, Map, Range, Player
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, ThrottledTimer, Utils
from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus

class FollowPartyLeaderUtility(CustomSkillUtilityBase):

    hero_formation = [ 0.0, 45.0, -45.0, 90.0, -90.0, 135.0, -135.0, 180.0 , -180.0, 225.0, -225.0, 270.0] # position on the grid of heroes

    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
            allowed_states: list[BehaviorState] = [ BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO ],
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("follow_party_leader"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.FOLLOW.value),
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.FOLLOWING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.FOLLOW.value)
        self.throttle_timer = ThrottledTimer(700)
        self.old_angle = 0
        self.last_map_signature: tuple[int, int, int, int] | None = None
        self.force_follow_after_map_change = False

        self.event_bus.subscribe(EventType.MAP_CHANGED, self.area_changed, subscriber_name=self.custom_skill.skill_name)

    def area_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:
        self.old_angle = 0
        self.last_map_signature = None
        self.force_follow_after_map_change = True
        self.throttle_timer.Reset()
        yield

    def _get_map_signature(self) -> tuple[int, int, int, int]:
        return (
            int(Map.GetMapID()),
            int(Map.GetRegion()[0]),
            int(Map.GetDistrict()),
            int(Map.GetLanguage()[0]),
        )
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        # Don't follow leader if this player has a defined flag position (should follow flag instead)
        if CustomBehaviorParty().party_flagging_manager.is_flag_defined(Player.GetAccountEmail()): return False

        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if self.allowed_states is not None and current_state not in self.allowed_states:
            return None

        if custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader():
            return None
        
        # flag_index = CustomBehaviorParty().party_flagging_manager.get_my_flag_index(Player.GetAccountEmail())
        # if flag_index is not None: 
        #     return None

        map_signature = self._get_map_signature()
        if self.last_map_signature != map_signature:
            self.last_map_signature = map_signature
            self.old_angle = 0
            self.force_follow_after_map_change = True

        party_leader_id = custom_behavior_helpers.CustomBehaviorHelperParty.get_party_leader_id()
        if party_leader_id <= 0 or not Agent.IsValid(party_leader_id) or not Agent.IsAlive(party_leader_id):
            return None

        party_leader_position:tuple[float, float] = Agent.GetXY(party_leader_id)
        max_distance_to_party_leader = self._get_max_distance_to_party_leader(current_state)

        party_leader_rotation_angle = Agent.GetRotationAngle(party_leader_id)
        is_party_leader_angle_changed = False
        if self.old_angle != party_leader_rotation_angle:
            is_party_leader_angle_changed = True
            self.old_angle = party_leader_rotation_angle

        distance_from_leader = Utils.Distance((party_leader_position[0], party_leader_position[1]), Player.GetXY())
        # print(f"is_party_leader_in_aggro {custom_behavior_helpers.Targets.is_party_leader_in_aggro()}")
        # print(f"distance_from_leader {distance_from_leader}")
        # print(f"max_distance_to_party_leader {max_distance_to_party_leader}")
        is_close_enough = distance_from_leader <= max_distance_to_party_leader
        if self.force_follow_after_map_change and distance_from_leader > Range.Touch.value:
            return self.score_definition.get_score()

        if not is_party_leader_angle_changed and is_close_enough:
            return None

        return self.score_definition.get_score()

    def _get_max_distance_to_party_leader(self, current_state: BehaviorState):
        max_distance_to_party_leader = 50

        if current_state == BehaviorState.IN_AGGRO:
            # should not be possible, but anyway, we want to escape that position asap
            max_distance_to_party_leader = Range.Spellcast.value * 0.5
        else:
            # not need to move closer
            max_distance_to_party_leader = 200

        # if custom_behavior_helpers.Targets.is_party_leader_in_aggro():
        #     if self.follow_party_leader_strategy == FollowPartyLeaderDuringAggroStrategy.STAY_FARTHEST:
        #         max_distance_to_party_leader = Range.Spellcast.value
        #     if self.follow_party_leader_strategy == FollowPartyLeaderDuringAggroStrategy.MID_DISTANCE:
        #         max_distance_to_party_leader = Range.Spellcast.value / 2
        #     if self.follow_party_leader_strategy == FollowPartyLeaderDuringAggroStrategy.CLOSE:
        #         max_distance_to_party_leader = Range.Area.value
        #     if self.follow_party_leader_strategy == FollowPartyLeaderDuringAggroStrategy.AS_CLOSE_AS_POSSIBLE:
        #         max_distance_to_party_leader = Range.Adjacent.value
        # else:
        #     if current_state == BehaviorState.IN_AGGRO:
        #         # should not be possible, but anyway, we want to escape that position asap
        #         max_distance_to_party_leader = Range.Touch.value
        #     else:
        #         # not need to move closer
        #         max_distance_to_party_leader = Range.Touch.value

        return max_distance_to_party_leader

    def _get_position_near_leader(self, current_state) -> tuple[float, float] | None:
        
        party_leader_id = custom_behavior_helpers.CustomBehaviorHelperParty.get_party_leader_id()
        if party_leader_id <= 0 or not Agent.IsValid(party_leader_id) or not Agent.IsAlive(party_leader_id):
            return None

        follow_x, follow_y = Agent.GetXY(party_leader_id)
        follow_angle = Agent.GetRotationAngle(party_leader_id)
        party_number = custom_behavior_helpers.CustomBehaviorHelperParty.get_own_party_index()

        if party_number <= 0 or party_number >= len(self.hero_formation):
            return None

        hero_grid_pos = party_number # + cached_data.data.party_hero_count + cached_data.data.party_henchman_count
        angle_on_hero_grid = follow_angle + Utils.DegToRad(self.hero_formation[hero_grid_pos])

        xx:float = Range.Touch.value * math.cos(angle_on_hero_grid) + follow_x
        yy:float = Range.Touch.value * math.sin(angle_on_hero_grid) + follow_y

        return (xx, yy)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        if not self.throttle_timer.IsExpired():
            yield
            return BehaviorResult.ACTION_SKIPPED

        position = self._get_position_near_leader(state)
        if position is None:
            yield
            return BehaviorResult.ACTION_SKIPPED

        ActionQueueManager().ResetQueue("ACTION")
        Player.Move(position[0], position[1])
        self.force_follow_after_map_change = False
        self.throttle_timer.Reset()
        yield
        return BehaviorResult.ACTION_PERFORMED

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:

        PyImGui.bullet_text(f"is_party_leader : {custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader()}")
        PyImGui.bullet_text(f"agent_id : {Player.GetAgentID()}")
        PyImGui.bullet_text(f"party_leader_id : {custom_behavior_helpers.CustomBehaviorHelperParty.get_party_leader_id()}")
        PyImGui.bullet_text(f"email : {Player.GetAccountEmail()}")
        return
