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
from Sources.oazix.CustomBehaviors.skills.paragon.save_yourselves_utility import SaveYourSelfLuxonUtility


class WatchYourselfPowerbatteryUtility(SaveYourSelfLuxonUtility):
    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
            skill: CustomSkill = CustomSkill("Watch_Yourself"),
            score_definition: ScoreStaticDefinition = ScoreStaticDefinition(20),
            allowed_states: list[BehaviorState] = [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.IN_AGGRO]
            ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            current_build=current_build,
            score_definition=score_definition,
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition

    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        super___evaluate = super()._evaluate(current_state, previously_attempted_skills)
        if super___evaluate is None:
            return None
        player_energy_percent = Agent.GetEnergy(Player.GetAgentID())
        mult = 1.0

        # if not in need of power, only cast if the party needs this
        if player_energy_percent < 0.5:
            mult = 2.0

        return super___evaluate * mult

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        player_energy_percent = Agent.GetEnergy(Player.GetAgentID())

        # if not in need of power, only cast if the party needs this
        if player_energy_percent > 0.6:
            lock_key = f"Watch_Yourself_utility"

            if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(key=lock_key, timeout_seconds=10) == False:
                yield
                return BehaviorResult.ACTION_SKIPPED

        result:BehaviorResult = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        # intentional skip of CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
        return result
