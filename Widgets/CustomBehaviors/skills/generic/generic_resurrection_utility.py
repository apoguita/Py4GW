from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, Agent, Range, Player
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class GenericResurrectionUtility(CustomSkillUtilityBase):
    def __init__(self,
    event_bus: EventBus,
    skill: CustomSkill,
    current_build: list[CustomSkill],
    score_definition: ScoreStaticDefinition = ScoreStaticDefinition(85),
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
        
        self.score_definition: ScoreStaticDefinition = score_definition

    def _get_target(self) -> int | None:
        allies: list[int] = AgentArray.GetAllyArray()
        allies = AgentArray.Filter.ByCondition(allies, lambda agent_id: not Agent.IsAlive(agent_id))
        allies = AgentArray.Filter.ByDistance(allies, Player.GetXY(), Range.Spellcast.value)
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
        
        return self.score_definition.get_score()

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