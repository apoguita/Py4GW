from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Player, Routines
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class ComfortAnimalUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(85),
        mana_required_to_cast: int = 0,
        pet_heal_threshold: float = 0.50,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO, BehaviorState.IDLE]
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Comfort_Animal"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScoreStaticDefinition = score_definition
        self.pet_heal_threshold: float = pet_heal_threshold

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        pet_id = GLOBAL_CACHE.Party.Pets.GetPetID(Player.GetAgentID())
        if pet_id == 0:
            return None

        if Agent.IsDead(pet_id):
            return self.score_definition.get_score()

        if Agent.GetHealth(pet_id) < self.pet_heal_threshold:
            return self.score_definition.get_score()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result
