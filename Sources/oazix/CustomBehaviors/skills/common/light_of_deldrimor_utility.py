from typing import Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range, Routines, Player
from Sources.Nikon_Scripts.BotUtilities import GameAreas
from Sources.oazix.CustomBehaviors.primitives import constants
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


class LightOfDeldrimorUtility(CustomSkillUtilityBase):

    def __init__(self,
                event_bus: EventBus,
                current_build: list[CustomSkill],
                score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 90 if enemy_qte >= 4 else 71 if enemy_qte >= 3 else 45 if enemy_qte >= 2 else 15 if enemy_qte >= 1 else 0),
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Light_of_Deldrimor"),
            in_game_build=current_build,
            score_definition=score_definition)
        
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition
        self.last_agent_quantity: int = 0

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        """This evaluated the number of enemies in the blast radius and uses ScorePerAgentQuantityDefinition to escalate the want to use this skill"""
        # if self.nature_has_been_attempted_last(previously_attempted_skills): return None

        player_pos = Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], GameAreas.Area)

        agent_quantity = len(enemy_array)
        score = self.score_definition.get_score(agent_quantity)

        if constants.DEBUG:
            if self.last_agent_quantity != agent_quantity:
                print(f"You have {agent_quantity} enemies to blast score={score}")
                self.last_agent_quantity = agent_quantity

        return score
        
    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:

        action: Callable[[], Generator[Any, Any, BehaviorResult]] = lambda: (yield from custom_behavior_helpers.Actions.cast_skill(
            skill=self.custom_skill
        ))

        result: BehaviorResult = yield from custom_behavior_helpers.Helpers.wait_for_or_until_completion(750, action)
        return result