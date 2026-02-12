from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, Agent, Range, Player
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
import time
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class WaitIfPartyMemberTooFarUtility(CustomSkillUtilityBase):
    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("wait_if_party_member_too_far"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.BOTTING.value+ 0.0091),
            allowed_states=[BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.BOTTING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.BOTTING.value)

        default_max_distance = Range.Spellcast.value * 1.25
        self.max_distance: float = float(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "max_distance", str(default_max_distance)))
        
    def __should_wait_for_party(self) -> bool:
        player_pos: tuple[float, float] = Player.GetXY()
        agent_ids: list[int] = AgentArray.GetAllyArray()
        party_size = len(agent_ids)
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: Agent.IsAlive(agent_id))
        agent_ids = AgentArray.Filter.ByDistance(agent_ids, player_pos, self.max_distance)
        party_size_within_range = len(agent_ids)
        return party_size_within_range < party_size

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True
    
    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        should_wait_for_party = self.__should_wait_for_party()
        if should_wait_for_party:
            return self.score_definition.get_score()
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        yield from custom_behavior_helpers.Helpers.wait_for(300) # we stuck the flow. (not yield from)
        return BehaviorResult.ACTION_PERFORMED

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"max_distance :")
        self.max_distance = PyImGui.input_float("##max_distance", self.max_distance)

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "max_distance", f"{self.max_distance:.2f}")
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "max_distance", f"{self.max_distance:.2f}")
        print("configuration saved as global")