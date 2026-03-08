from typing import Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range, Routines, Player
from Sources.Nikon_Scripts.BotUtilities import GameAreas
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class NecrosisUtility(CustomSkillUtilityBase):

    def __init__(self,
                event_bus: EventBus,
                current_build: list[CustomSkill],
                score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 15 if enemy_qte >= 3 else 45 if enemy_qte >= 2 else 70),
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Necrosis"),
            in_game_build=current_build,
            score_definition=score_definition)
        
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if self.nature_has_been_attempted_last(previously_attempted_skills): return None

        player_pos = Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], GameAreas.Earshot)

        return self.score_definition.get_score(len(enemy_array))
        
    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:

        # todo make sure condi or hex will last long enough
        condition = lambda agent_id: Agent.IsHexed(agent_id) or Agent.IsConditioned(agent_id)

        action: Callable[[], Generator[Any, Any, BehaviorResult]] = lambda: (yield from custom_behavior_helpers.Actions.cast_skill_to_lambda(
            skill=self.custom_skill,
            select_target=lambda: custom_behavior_helpers.Targets.get_first_or_default_from_enemy_ordered_by_priority(
                within_range=Range.Spellcast,
                condition=lambda agent_id: condition(agent_id),
                sort_key=(TargetingOrder.HP_ASC, TargetingOrder.CASTER_THEN_MELEE)
            )
        ))

        result: BehaviorResult = yield from custom_behavior_helpers.Helpers.wait_for_or_until_completion(2500, action)
        return result