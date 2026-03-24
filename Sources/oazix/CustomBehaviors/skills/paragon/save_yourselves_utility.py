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
from Sources.oazix.CustomBehaviors.skills.generic.protective_shout_utility import ProtectiveShoutUtility

class SaveYourselfsUtility(ProtectiveShoutUtility):
    def __init__(
            self,
            event_bus: EventBus,
            skill: CustomSkill, # pass the luxon or kurzick skill here
            current_build: list[CustomSkill],
            allies_health_less_than_percent: float = 1,
            allies_quantity_required: int = 1,
            score_definition: ScoreStaticDefinition = ScoreStaticDefinition(99),
            mana_required_to_cast: int = 0,
            allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
            ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill= skill,
            current_build=current_build,
            allies_health_less_than_percent=allies_health_less_than_percent,
            allies_quantity_required=allies_quantity_required,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        has_buff = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.custom_skill.skill_id)
        
        if not has_buff: return self.score_definition.get_score()
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        lock_key = f"Save_Yourselves_utility"

        if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=2) == False:
            yield
            return BehaviorResult.ACTION_SKIPPED

        result:BehaviorResult = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
        return result