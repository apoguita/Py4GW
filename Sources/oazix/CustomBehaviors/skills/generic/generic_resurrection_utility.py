from typing import List, Any, Generator, Callable, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, Agent, Range, Player
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class GenericResurrectionUtility(CustomSkillUtilityBase):
    def __init__(self,
    event_bus: EventBus,
    skill: CustomSkill,
    current_build: list[CustomSkill],
    score_definition: ScorePerHealthGravityDefinition = ScorePerHealthGravityDefinition(0),
    mana_required_to_cast: int = 10,
    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.FAR_FROM_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
        
        self.score_definition: ScorePerHealthGravityDefinition = score_definition

    def _get_target(self) -> int | None:
        allies: list[int] = AgentArray.GetAllyArray()
        allies = AgentArray.Filter.ByCondition(allies, lambda agent_id: not Agent.IsAlive(agent_id))
        allies = AgentArray.Filter.ByDistance(allies, Player.GetXY(), Range.Spellcast.value * 1.5)
        if len(allies) == 0: return None
        return allies[0]

    def _get_lock_key(self, agent_id: int) -> str:
        return f"GenericResurrection_{agent_id}"

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        """Evaluate if resurrection should be cast - only if there's a dead ally to resurrect"""
        
        target = self._get_target()
        if target is None: 
            return None  # No dead allies to resurrect

        lock_key = self._get_lock_key(target)
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key): return None #someone is already resurrecting
        
        return self.score_definition.get_score(HealingScore.RESURRECTION)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        """Execute resurrection on the target dead ally"""

        target = self._get_target()
        if target is None: 
            return BehaviorResult.ACTION_SKIPPED  # No dead allies to resurrect

        lock_key = self._get_lock_key(target)
        if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, ) == False: 
            yield 
            return BehaviorResult.ACTION_SKIPPED 

        try:
            result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target)
        finally:
            CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
        return result
    
    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"target : {self._get_target()}")
        