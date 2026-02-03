# python
from abc import abstractmethod
import random
from typing import Any, Generator, override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class SimpleSequenceUtility(CustomSkillUtilityBase):
    """
    Wait for two utility skills to both evaluate successfully, then execute them in sequence.

    - `_evaluate` returns the configured score only when both utilities evaluate to a valid score.
    - `_execute` executes utility_1 first, then utility_2 immediately after.

    This is useful for combos like Intensity -> Invoke Lightning where you want
    to guarantee both skills fire in sequence.
    """

    def __init__(
        self,
        event_bus: EventBus,
        utility_1: CustomSkillUtilityBase,
        utility_2: CustomSkillUtilityBase,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(60),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
    ) -> None:
        # Track utility_1's skill as this utility's primary skill
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill(f"SimpleSequenceUtility_{id(self)}"), # guid randomized to avoid conflict in the behavior
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )
        self.utility_1 = utility_1
        self.utility_2 = utility_2
        self.score_definition = score_definition

    @abstractmethod
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        # Both utilities must evaluate to a valid score
        try:
            score_1 = self.utility_1.evaluate(current_state, previously_attempted_skills)
        except Exception:
            score_1 = None

        if score_1 is None:
            return None

        try:
            score_2 = self.utility_2.evaluate(current_state, previously_attempted_skills)
        except Exception:
            score_2 = None

        if score_2 is None:
            return None

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        # Execute utility_1 first
        result_1 = yield from self.utility_1._execute(state)
        if result_1 is None or result_1 == BehaviorResult.ACTION_SKIPPED:
            return result_1 if result_1 is not None else BehaviorResult.ACTION_SKIPPED

        # Execute utility_2 immediately after
        result_2 = yield from self.utility_2._execute(state)
        return result_2

