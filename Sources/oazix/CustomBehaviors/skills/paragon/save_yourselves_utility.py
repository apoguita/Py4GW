from re import S
from typing import Any, Callable, Generator, override
import random

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Agent, Player
from Py4GWCoreLib.enums import Profession, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class SaveYourSelfLuxonUtility(CustomSkillUtilityBase):
    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
            mana_required_to_cast: float = 0,
            skill: CustomSkill = CustomSkill("Save_Yourselves_luxon"),
            score_definition: ScoreStaticDefinition = ScoreStaticDefinition(90),
            allowed_states: list[BehaviorState] = [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.IN_AGGRO]
            ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            mana_required_to_cast=mana_required_to_cast,
            in_game_build=current_build,
            score_definition=score_definition,
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        has_buff = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.custom_skill.skill_id)
        
        if not has_buff: return self.score_definition.get_score()
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        lock_key = f"Save_yourselves_utility"

        if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=6) == False:
            yield
            return BehaviorResult.ACTION_SKIPPED

        result:BehaviorResult = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
        return result


class SaveYourSelfKurzUtility(SaveYourSelfLuxonUtility):
    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
            skill: CustomSkill = CustomSkill("Save_Yourselves_kurzick"),
            score_definition: ScoreStaticDefinition = ScoreStaticDefinition(90),
            allowed_states: list[BehaviorState] = [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.IN_AGGRO]
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            current_build=current_build,
            score_definition=score_definition,
            allowed_states=allowed_states)


class TheresNothingToFearUtility(SaveYourSelfLuxonUtility):
    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
            skill: CustomSkill = CustomSkill("Theres_Nothing_to_Fear"),
            score_definition: ScoreStaticDefinition = ScoreStaticDefinition(90),
            allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            current_build=current_build,
            score_definition=score_definition,
            allowed_states=allowed_states,
            mana_required_to_cast=15)
