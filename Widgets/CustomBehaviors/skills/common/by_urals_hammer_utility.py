from tkinter.constants import N
from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class ByUralsHammerUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda allies_qte: 99 if allies_qte >= 3 else 1),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("By_Urals_Hammer"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
        
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    def _get_lock_key(self) -> str:
        return f"ByUralsHammer"
    
    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()

        allies_qte = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Earshot,
            condition=lambda agent_id: not Agent.IsAlive(agent_id) and agent_id != player_agent_id,
            sort_key=(TargetingOrder.DISTANCE_ASC, )
        )
        if len(allies_qte) == 0: return None

        lock_key = self._get_lock_key()
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key): return None #someone is already resurrecting
        
        return self.score_definition.get_score(len(allies_qte))

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        lock_key = self._get_lock_key()
        if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, ) == False: 
            yield 
            return BehaviorResult.ACTION_SKIPPED 

        try:
            result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        finally:
            CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
        return result