from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Player
from Py4GWCoreLib.Effect import Effects
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class UnyieldingAuraDropUtility(CustomSkillUtilityBase):
    """
    Unyielding Aura DROP utility.
    - Only responsible for dropping the Unyielding Aura buff when a party member is dead
    - Should be used in conjunction with UnyieldingAuraUtility which handles casting
    - Uses shared lock to prevent multiple drops for the same dead ally
    """
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(100),
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Unyielding_Aura_Drop"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=0,  # No mana needed to drop
            allowed_states=allowed_states)
                
        self.score_definition: ScoreStaticDefinition = score_definition
        # Store the actual Unyielding_Aura skill_id for buff checking
        self.unyielding_aura_skill_id: int = GLOBAL_CACHE.Skill.GetID("Unyielding_Aura")

    def _get_lock_key(self, agent_id: int) -> str:
        return f"Unyielding_Aura_Drop_{agent_id}"

    def has_buff(self) -> bool:
        return Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.unyielding_aura_skill_id)

    def _drop_unyielding_aura(self) -> None:
        buff_id = Effects.GetBuffID(self.custom_skill.skill_id)
        if buff_id != 0:
            Effects.DropBuff(buff_id)

    def _get_dead_allies(self) -> list[custom_behavior_helpers.SortableAgentData]:
        return custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.5,
            sort_key=(TargetingOrder.DISTANCE_ASC,),
            is_alive=False
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        
        has_buff = self.has_buff()
        if not has_buff:
            return None  # No buff to drop
        
        dead_allies = self._get_dead_allies()
        is_party_member_dead = dead_allies is not None and len(dead_allies) > 0
        
        # Only trigger if someone is dead and we have the buff active
        if is_party_member_dead:
            return self.score_definition.get_score()
        
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        
        has_buff = self.has_buff()
        if not has_buff:
            return BehaviorResult.ACTION_SKIPPED
    
        dead_allies = self._get_dead_allies()
        if dead_allies is None or len(dead_allies) == 0:
            return BehaviorResult.ACTION_SKIPPED
        
        lock_key = self._get_lock_key(dead_allies[0].agent_id)
        if not CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key):
            return BehaviorResult.ACTION_SKIPPED
        
        try:
            self._drop_unyielding_aura()
            # Wait a moment for the buff to be dropped
            yield from custom_behavior_helpers.Helpers.wait_for(500)
            return BehaviorResult.ACTION_PERFORMED
        finally:
            CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)

