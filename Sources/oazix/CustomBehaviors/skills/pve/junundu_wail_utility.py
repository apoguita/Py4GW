from typing import Any, Generator, override

from Py4GWCoreLib import Agent, Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.lock_key_helper import LockKeyHelper
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class JununduWailUtility(CustomSkillUtilityBase):

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerHealthGravityDefinition = ScorePerHealthGravityDefinition(1),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        required_hp_fraction: float = 0.6,
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Junundu_Wail"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition: ScorePerHealthGravityDefinition = score_definition

    def _get_target(self) -> int | None:
        return custom_behavior_helpers.Targets.get_first_or_default_from_allies_ordered_by_priority(
            within_range=Range.Earshot.value,
            sort_key=(TargetingOrder.DISTANCE_ASC,),
            is_alive=False
        )
    
    def _get_lock_key(self, agent_id: int) -> str:
        return LockKeyHelper.resurrection(agent_id)

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        target = self._get_target()

        if target is not None: 
            lock_key = self._get_lock_key(target)
            if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key): return None #someone is already resurrecting
            return self.score_definition.get_score(HealingScore.RESURRECTION)

        if current_state != BehaviorState.IN_AGGRO:
            player_hp = Agent.GetHealth(Player.GetAgentID())
            if player_hp <= 0.95:
                return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED)
            
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        target = self._get_target()
        if target is not None: 
            lock_key = self._get_lock_key(target)
            if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key) == False: 
                return BehaviorResult.ACTION_SKIPPED
            try:
                result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target)
            finally:
                CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
            return result
        else:
            result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
            return result

