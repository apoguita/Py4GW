from typing import Any, Generator, override


from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class ToTheLimitUtility(CustomSkillUtilityBase):
    
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(79),
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("To_the_Limit"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=0,
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition

    def get_generated_strike_of_adrenaline(self) -> int:
        # how much allies in earshot
        allies = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Earshot.value,
            condition=lambda agent_id: agent_id != Player.GetAgentID()
        )

        return min(len(allies), 6)


    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        generated_strike_of_adrenaline = self.get_generated_strike_of_adrenaline()
        if generated_strike_of_adrenaline <= 1: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result