from typing import Any, Generator, override, Tuple

from Py4GWCoreLib import GLOBAL_CACHE, Range, Agent, Player, AgentArray
from Py4GWCoreLib.routines_src.Agents import Routines
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


class SignetOfSorrowUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        skill: CustomSkill=CustomSkill("Signet_of_Sorrow"),
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 40 if enemy_qte >= 1 else 10),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    def _my_condition(self, corpse_array: list[int], agent_id: int):
        corpse_filter = AgentArray.Filter.ByDistance(corpse_array, Agent.GetXY(agent_id), Range.Nearby.value)
        return len(corpse_filter) != 0

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        """Get attacking enemies ordered by cluster size. Not because the skill is aoe but to keep the sorrow chain going on kills"""
        corpses_list = Routines.Agents.GetCorpses(Range.Spirit.value)

        def condition(agent_id: int) -> bool:
            return self._my_condition(corpse_array=corpses_list, agent_id=agent_id)

        # Yes intentionally looking for nearby
        return custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            condition=condition,
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_ASC),
            range_to_count_enemies=Range.Nearby.value)

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        targets = self._get_targets()

        if len(targets) == 0: return 9

        return self.score_definition.get_score(targets[0].enemy_quantity_within_range)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:

        enemies = self._get_targets()
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = enemies[0]

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        return result

