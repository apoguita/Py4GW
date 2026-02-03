from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_combot_definition import ScoreCombotDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class RawCombotAttackUtility(CustomSkillUtilityBase):
    def __init__(self,
    event_bus: EventBus,
    skill: CustomSkill,
    current_build: list[CustomSkill],
    score_definition: ScoreCombotDefinition,
    mana_required_to_cast: int = 12,
    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
        
        self.score_definition: ScoreCombotDefinition = score_definition
        self.combot_type:int = GLOBAL_CACHE.Skill.Data.GetCombo(skill.skill_id) # 1,2,3 for lead(1) - offhand(2) - dual(3)

    def _is_agent_compatible_with_dagger_status(self, agent_id: int) -> bool:

        dagger_status:int = Agent.GetDaggerStatus(agent_id) # GetDaggerStatus is between 0 and 3. 0=None, 1= affected by lead, 2= affected by offhand, 3= affected by dual
        
        # this is a strict mode.

        if self.combot_type == 1:
            if dagger_status == 0: return True
            if dagger_status == 1: return False
            if dagger_status == 2: return False
            if dagger_status == 3: return True

        if self.combot_type == 2:
            if dagger_status == 0: return False
            if dagger_status == 1: return True
            if dagger_status == 2: return False
            if dagger_status == 3: return False

        if self.combot_type == 3:
            if dagger_status == 0: return False
            if dagger_status == 1: return False
            if dagger_status == 2: return True
            if dagger_status == 3: return False

        return False

    def _get_target(self) -> int | None:

        return custom_behavior_helpers.Targets.get_first_or_default_from_enemy_ordered_by_priority(
            within_range=Range.Spellcast,
            condition= lambda agent_id: self._is_agent_compatible_with_dagger_status(agent_id),
            sort_key=(TargetingOrder.DISTANCE_ASC, ))

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        
        target_id : int | None = self._get_target()
        if target_id is None: return None

        party_forced_target_prioritized = False
        if target_id == custom_behavior_helpers.CustomBehaviorHelperParty.get_party_custom_target():
            party_forced_target_prioritized = True

        return self.score_definition.get_score(self.combot_type, party_forced_target_prioritized = party_forced_target_prioritized)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        target = self._get_target()
        if target is None: return BehaviorResult.ACTION_SKIPPED
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target)
        return result