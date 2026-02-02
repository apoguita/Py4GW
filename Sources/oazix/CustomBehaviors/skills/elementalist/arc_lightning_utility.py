from operator import truediv
from token import STRING
from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Player, Range, Routines
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility

class ArcLightningUtility(RawAoeAttackUtility):
    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 66 if enemy_qte >= 3 else 51 if enemy_qte <= 1 else 1),
        mana_required_to_cast: int = 5,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Arc_Lightning"),
            current_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )
        self.score_definition = score_definition

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        # get parent class evaluation
        score = super()._evaluate(current_state, previously_attempted_skills)

        # 1 target if no overcast
        # 1 target + 2 nearby foes if overcast

        overcast_level = Agent.GetOvercast(Player.GetAgentID())
        if overcast_level < 2: 
            return self.score_definition.get_score(1) # 1 agent only...
        else:
            return score