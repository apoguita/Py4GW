from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
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
            event_bus: EventBus,
            current_build: list[CustomSkill],
            mana_limit: float = 0.5,
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("wait_if_lock_taken"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(0.00001),
            allowed_states= [BehaviorState.IDLE, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO], # no need during aggro
            utility_skill_typology=UtilitySkillTypology.BOTTING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(0.00001)
        self.mana_limit = mana_limit
        self.no_lock_timer = ThrottledTimer(3_500)
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        # Stop executing if no locks are active for 1.5 seconds
        # This prevents bots from continuing actions when no coordination is needed

        # If locks are active, continue executing (return score)
        if CustomBehaviorParty().get_shared_lock_manager().is_any_lock_taken():
            self.no_lock_timer.Reset()  # Reset timer when locks are active
            return self.score_definition.get_score()

        # If no locks are active, check timer
        if self.no_lock_timer.IsExpired():
            # Timer expired with no locks - stop executing
            return None

        # No locks but timer hasn't expired yet - keep waiting
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        yield from custom_behavior_helpers.Helpers.wait_for(300) # we simply wait
        return BehaviorResult.ACTION_PERFORMED