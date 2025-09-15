from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
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

class WaitIfLockTakenUtility(CustomSkillUtilityBase):
    def __init__(
            self, 
            current_build: list[CustomSkill], 
            mana_limit: float = 0.5,
        ) -> None:
        
        super().__init__(
            skill=CustomSkill("wait_if_lock_taken"), 
            in_game_build=current_build, 
            score_definition=ScoreStaticDefinition(0.00001), 
            allowed_states= [BehaviorState.IDLE, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO], # no need during aggro
            utility_skill_typology=UtilitySkillTypology.BOTTING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.BOTTING.value)
        self.mana_limit = mana_limit
        self.no_lock_timer = ThrottledTimer(1_500)
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        # nothing fancy but we don't want to continue anything until any party lock is open.
        # once no more lock detected, wait for 1,5s more to ensure no one is taking a new lock.

        if self.no_lock_timer.IsExpired():
            return self.score_definition.get_score()

        if not CustomBehaviorParty().get_shared_lock_manager().is_any_lock_taken() == True:
            return self.score_definition.get_score()

        # start timer for 1500
        self.no_lock_timer.Reset()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        yield from custom_behavior_helpers.Helpers.wait_for(300) # we simply wait
        return BehaviorResult.ACTION_PERFORMED