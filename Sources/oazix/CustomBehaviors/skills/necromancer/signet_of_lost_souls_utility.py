from typing import Any, Generator, override, Tuple

from Py4GWCoreLib import GLOBAL_CACHE, Range, Agent, Player
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_boosted_definition import ScoreBoostedDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class SignetOfLostSoulsUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreBoostedDefinition = ScoreBoostedDefinition(score_boosted=83, score_nominal=33),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
        low_mana_threshold: float = 0.3
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Signet_of_Lost_Souls"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScoreBoostedDefinition = score_definition
        self.low_mana_threshold: float = low_mana_threshold

    @staticmethod
    def _get_target() -> int | None:
        targets: Tuple[int, ...] = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority(
            within_range=Range.Spellcast,
            condition=lambda agent_id: Agent.GetHealth(agent_id) < 0.5,
            sort_key=(TargetingOrder.DISTANCE_ASC, TargetingOrder.HP_ASC)
        )
        if len(targets) == 0: return None

        return targets[0]

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        target = self._get_target()

        if not target:
            return None

        player_agent_id = Player.GetAgentID()
        player_energy_percent = Agent.GetEnergy(player_agent_id)

        if player_energy_percent <= self.low_mana_threshold:
            return self.score_definition.get_score(True)
        else:
            return self.score_definition.get_score(False)

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        target = self._get_target()
        if target is None: return BehaviorResult.ACTION_SKIPPED
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target)
        return result
