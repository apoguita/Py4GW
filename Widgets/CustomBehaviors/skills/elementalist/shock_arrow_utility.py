from operator import truediv
from token import STRING
from typing import Any, Generator, override

from HeroAI.combat import CombatClass
from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers, glimmer_tracker
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class ShockArrowUtility(CustomSkillUtilityBase):
    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(65),
        mana_required_to_cast: int = 5,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Shock_Arrow"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )
        self.score_definition = score_definition

    def _get_target(self) -> int | None:
        # prefer closest enemy in spellcast range; skip enemies that already have Glimmering_Mark


        target = custom_behavior_helpers.Targets.get_first_or_default_from_enemy_ordered_by_priority(
            within_range=Range.Spellcast,
            condition=lambda agent_id: (not glimmer_tracker.had_glimmer_recently(agent_id) and Agent.IsConditioned(agent_id)),
            sort_key=(TargetingOrder.DISTANCE_ASC,)
        )
        return target

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        # ensure the skill exists in the in-game build (prevents zero evaluation if slot removed)
        if not any(getattr(s, "skill_id", None) == self.custom_skill.skill_id for s in self.in_game_build):
            return None

        target = self._get_target()
        if target is None:
            return None

        # ensure we have enough resources to cast
        if not custom_behavior_helpers.Resources.has_enough_resources(self.custom_skill):
            return None

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        target = self._get_target()
        if target is None:
            return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target)
        return result