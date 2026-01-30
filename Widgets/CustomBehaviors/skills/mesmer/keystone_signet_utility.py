from tkinter.constants import N
from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Player
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class KeystoneSignetUtility(CustomSkillUtilityBase):
    '''
    This keystone signet implementation will require Symbolic Posture. Otherwise it will not be casted.
    '''
    def __init__(self,
    event_bus: EventBus,
    current_build: list[CustomSkill],
    score_definition: ScoreStaticDefinition,
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Keystone_Signet"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=0)
        
        self.score_definition: ScoreStaticDefinition = score_definition
        self.symbolic_posture_skill: CustomSkill = CustomSkill("Symbolic_Posture")

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        # no keystone signet buff, let's cast it.
        has_keystone_signet_buff = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.custom_skill.skill_id)
        if not has_keystone_signet_buff: return self.score_definition.get_score() 

        # if we have symbolic posture buff, just force refresh keystone signet.
        has_symbolic_posture_buff = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.symbolic_posture_skill.skill_id)
        if has_symbolic_posture_buff: return self.score_definition.get_score()
        
        # if we have keystone signet buff, let's check if it is worth to refresh it.
        symbolic_posture_recharge_time_remaining = custom_behavior_helpers.Resources.get_skill_recharge_time_remaining_in_milliseconds(self.symbolic_posture_skill)
        if symbolic_posture_recharge_time_remaining <= 15_000: return self.score_definition.get_score()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result