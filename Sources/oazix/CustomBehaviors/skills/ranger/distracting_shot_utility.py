from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range, Player
from Py4GWCoreLib.Py4GWcorelib import Utils
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class DistractingShotUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(80),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Distracting_Shot"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
                
        self.score_definition: ScoreStaticDefinition = score_definition

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if self.nature_has_been_attempted_last(previously_attempted_skills):
            return 5
        else: 
            return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        player_position: tuple[float, float] = Player.GetXY()

        action: Callable[[], Generator[Any, Any, BehaviorResult]] = lambda: (yield from custom_behavior_helpers.Actions.cast_skill_to_lambda(
            skill=self.custom_skill,
            select_target=lambda: custom_behavior_helpers.Targets.get_first_or_default_from_enemy_ordered_by_priority(
                within_range=Range.Spellcast,
                condition=lambda agent_id: 
                    Agent.IsCasting(agent_id) and 
                    Utils.Distance(Agent.GetXY(agent_id), (player_position)) < Range.Spellcast.value * 0.6 and
                    GLOBAL_CACHE.Skill.Data.GetActivation(Agent.GetCastingSkillID(agent_id)) >= 0.510,
                sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.CASTER_THEN_MELEE))
        ))

        result: BehaviorResult = yield from custom_behavior_helpers.Helpers.wait_for_or_until_completion(500, action)
        return result