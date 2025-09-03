import math
from tkinter.constants import N
from typing import Any, Generator, override

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
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class FollowFlagUtility(CustomSkillUtilityBase):


    def __init__(
            self, 
            current_build: list[CustomSkill], 
            allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:
        
        super().__init__(
            skill=CustomSkill("follow_flag"), 
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.FOLLOW_FLAG.value), 
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.FOLLOWING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.FOLLOW_FLAG.value)
        self.throttle_timer = ThrottledTimer(1000)
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if not self.throttle_timer.IsExpired():
            return None
        
        if self.allowed_states is not None and current_state not in self.allowed_states:
            return None

        party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
        cached_data = CacheData()
        all_player_struct:list[PlayerStruct] = cached_data.HeroAI_vars.all_player_struct
        if not all_player_struct[party_number].IsFlagged: return None
        follow_x = all_player_struct[party_number].FlagPosX
        follow_y = all_player_struct[party_number].FlagPosY

        distance_from_flag = Utils.Distance((follow_x, follow_y), GLOBAL_CACHE.Player.GetXY())

        if distance_from_flag < 10: return None
        if distance_from_flag > 100: return CommonScore.FOLLOW_FLAG_REQUIRED.value
        if distance_from_flag < 30: return CommonScore.FOLLOW_FLAG.value

        # if too far from flag => FOLLOW_FLAG_REQUIRED
        # if close to flag => FOLLOW_FLAG score
        # if very close to flag do_nothing

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
        cached_data = CacheData()
        all_player_struct:list[PlayerStruct] = cached_data.HeroAI_vars.all_player_struct
        follow_x = all_player_struct[party_number].FlagPosX
        follow_y = all_player_struct[party_number].FlagPosY

        position:tuple[float, float] = (follow_x, follow_y)
        ActionQueueManager().ResetQueue("ACTION")
        GLOBAL_CACHE.Player.Move(position[0], position[1])
        self.throttle_timer.Reset()
        yield
        return BehaviorResult.ACTION_PERFORMED