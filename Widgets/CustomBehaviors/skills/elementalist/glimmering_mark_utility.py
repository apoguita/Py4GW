# File: `Widgets/CustomBehaviors/skills/elementalist/glimmering_mark_utility.py`

from typing import List, Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers, glimmer_tracker
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class GlimmeringMarkUtility(CustomSkillUtilityBase):
    """
    AoE Glimmering Mark utility:
    - Targets enemies that do NOT already have Glimmering_Mark.
    - Prefers targets that maximize number of enemies in AoE (cluster priority).
    - Very high score to make this the most important skill in the build.
    """

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda q: 84 if q >= 3 else 90 if q == 2 else 83),
        mana_required_to_cast: int = 10,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Glimmering_Mark"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    def _get_targets(self) -> List[custom_behavior_helpers.SortableAgentData]:
        # Exclude agents that currently have the buff OR that had glimmer applied recently
        return custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            condition=lambda agent_id: (not glimmer_tracker.had_glimmer_recently(agent_id)),
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_DESC),
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id),
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        targets = self._get_targets()
        if len(targets) == 0:
            return None
        # score based on number of enemies in range of the best candidate
        return self.score_definition.get_score(targets[0].enemy_quantity_within_range)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        enemies = self._get_targets()
        if len(enemies) == 0:
            return BehaviorResult.ACTION_SKIPPED

        target = enemies[0]
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)

        # record glimmer on success so other utilities avoid the target for the window
        try:
            if result == BehaviorResult.ACTION_PERFORMED:
                glimmer_tracker.record_glimmer_on(target.agent_id)
        except Exception:
            # be defensive - don't break flow if tracker fails
            pass

        return result