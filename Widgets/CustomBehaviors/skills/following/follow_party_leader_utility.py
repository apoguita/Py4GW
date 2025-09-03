from calendar import c
import math
from tkinter import Button
from tkinter.constants import N
from typing import Any, Generator, override

import PyImGui

from HeroAI.cache_data import CacheData
from HeroAI.types import PlayerStruct
from Py4GWCoreLib import GLOBAL_CACHE, Party, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, ThrottledTimer, Utils
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
import time
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.follow_party_leader_during_aggro_strategy import FollowPartyLeaderDuringAggroStrategy
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class FollowPartyLeaderUtility(CustomSkillUtilityBase):

    hero_formation = [ 0.0, 45.0, -45.0, 90.0, -90.0, 135.0, -135.0, 180.0 , -180.0, 225.0, -225.0, 270.0] # position on the grid of heroes

    def __init__(
            self, 
            current_build: list[CustomSkill], 
            allowed_states: list[BehaviorState] = [ BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO ],
            follow_party_leader_during_aggro_strategy = FollowPartyLeaderDuringAggroStrategy.STAY_FARTHEST
        ) -> None:
        
        super().__init__(
            skill=CustomSkill("follow_party_leader"), 
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.FOLLOW.value), 
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.FOLLOWING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.FOLLOW.value)
        self.throttle_timer = ThrottledTimer(1000)
        self.old_angle = 0
        self.follow_party_leader_strategy = follow_party_leader_during_aggro_strategy
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if not self.throttle_timer.IsExpired():
            return None
        
        if self.allowed_states is not None and current_state not in self.allowed_states:
            return None

        if GLOBAL_CACHE.Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
            return None

        party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
        cached_data = CacheData()
        all_player_struct:list[PlayerStruct] = cached_data.HeroAI_vars.all_player_struct
        if all_player_struct[party_number].IsFlagged: return None

        party_leader_position:tuple[float, float] = GLOBAL_CACHE.Agent.GetXY(GLOBAL_CACHE.Party.GetPartyLeaderID())
        max_distance_to_party_leader = self._get_max_distance_to_party_leader(current_state)

        party_leader_rotation_angle = GLOBAL_CACHE.Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())
        is_party_leader_angle_changed = False
        if self.old_angle != party_leader_rotation_angle:
            is_party_leader_angle_changed = True
            self.old_angle = party_leader_rotation_angle

        distance_from_leader = Utils.Distance((party_leader_position[0], party_leader_position[1]), GLOBAL_CACHE.Player.GetXY())
        # print(f"is_party_leader_in_aggro {custom_behavior_helpers.Targets.is_party_leader_in_aggro()}")
        # print(f"distance_from_leader {distance_from_leader}")
        # print(f"max_distance_to_party_leader {max_distance_to_party_leader}")
        is_close_enough = distance_from_leader <= max_distance_to_party_leader
        is_party_leader_angle_changed = False
        if not is_party_leader_angle_changed and is_close_enough:
            return None

        return self.score_definition.get_score()

    def _get_max_distance_to_party_leader(self, current_state: BehaviorState):
        max_distance_to_party_leader = 50

        if current_state == BehaviorState.IN_AGGRO:
            # should not be possible, but anyway, we want to escape that position asap
            max_distance_to_party_leader = Range.Spellcast.value * 0.6
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

    def _get_position_near_leader(self, current_state) -> tuple[float, float]:

        follow_x, follow_y = GLOBAL_CACHE.Agent.GetXY(GLOBAL_CACHE.Party.GetPartyLeaderID())
        follow_angle = GLOBAL_CACHE.Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())
        party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()

        hero_grid_pos = party_number # + cached_data.data.party_hero_count + cached_data.data.party_henchman_count
        angle_on_hero_grid = follow_angle + Utils.DegToRad(self.hero_formation[hero_grid_pos])

        xx:float = Range.Touch.value * math.cos(angle_on_hero_grid) + follow_x
        yy:float = Range.Touch.value * math.sin(angle_on_hero_grid) + follow_y

        return (xx, yy)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        position:tuple[float, float] = self._get_position_near_leader(state)

        ActionQueueManager().ResetQueue("ACTION")
        GLOBAL_CACHE.Player.Move(position[0], position[1])
        self.throttle_timer.Reset()
        yield
        return BehaviorResult.ACTION_PERFORMED

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        return
        PyImGui.bullet_text("Strategy")
        PyImGui.same_line(0, -1)

        members = list(FollowPartyLeaderDuringAggroStrategy)
        names = [m.name for m in members]

        cur_index = members.index(self.follow_party_leader_strategy)
        new_index = PyImGui.combo("", cur_index, names)

        self.follow_party_leader_strategy = members[new_index]
       

