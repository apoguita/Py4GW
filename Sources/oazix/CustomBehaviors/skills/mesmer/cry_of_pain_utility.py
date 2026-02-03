from typing import Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class CryOfPainUtility(CustomSkillUtilityBase):

    def __init__(self,
                event_bus: EventBus,
                current_build: list[CustomSkill],
                score_definition: ScoreStaticDefinition = ScoreStaticDefinition(90),
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Cry_of_Pain"),
            in_game_build=current_build,
            score_definition=score_definition)
        
        self.score_definition: ScoreStaticDefinition = score_definition

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if self.nature_has_been_attempted_last(previously_attempted_skills): return None
        return self.score_definition.get_score()
        
    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:

        condition = lambda agent_id: Agent.IsHexed(agent_id)
        if not self.is_another_interrupt_ready(): # it's better to interrupt even without hex-effect
            condition = lambda agent_id: True

        action: Callable[[], Generator[Any, Any, BehaviorResult]] = lambda: (yield from custom_behavior_helpers.Actions.cast_skill_to_lambda(
            skill=self.custom_skill,
            select_target=lambda: custom_behavior_helpers.Targets.get_first_or_default_from_enemy_ordered_by_priority(
                within_range=Range.Spellcast,
                condition=lambda agent_id: condition(agent_id) and 
                Agent.IsCasting(agent_id) and 
                GLOBAL_CACHE.Skill.Data.GetActivation(Agent.GetCastingSkillID(agent_id)) >= 0.250,
                sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.CASTER_THEN_MELEE),
                range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))
        ))

        result: BehaviorResult = yield from custom_behavior_helpers.Helpers.wait_for_or_until_completion(500, action)
        return result