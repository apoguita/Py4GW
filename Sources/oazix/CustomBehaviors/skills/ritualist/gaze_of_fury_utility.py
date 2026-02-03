from typing import Any, Generator, override

from Py4GWCoreLib import Routines, Range
from Py4GWCoreLib.enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class GazeOfFuryUtility(CustomSkillUtilityBase):
    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(75),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Gaze_of_Fury"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
                
        self.score_definition: ScoreStaticDefinition = score_definition

        self.owned_spirit_model_id: SpiritModelID = SpiritModelID.FURY

        # todo propose to be customizable
        self.vampirism_skill: CustomSkill = CustomSkill("Vampirism")
        self.vampirism_spirit_model_id: SpiritModelID = SpiritModelID.VAMPIRISM

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if not Routines.Checks.Skills.IsSkillIDReady(self.vampirism_skill.skill_id): return None # if vampirism not-ready, we can't cast
        
        is_gaze_of_fury_spirit_exist = custom_behavior_helpers.Targets.get_first_or_default_from_spirits_raw(within_range=Range.Spirit, spirit_model_ids=[self.owned_spirit_model_id], condition=lambda agent_id: True)
        if is_gaze_of_fury_spirit_exist: return None # no cast, if gaze of fury spirit exist

        is_vampirism_spirit_exist = custom_behavior_helpers.Targets.get_first_or_default_from_spirits_raw(within_range=Range.Spirit, spirit_model_ids=[self.vampirism_spirit_model_id], condition=lambda agent_id: True)
        if not is_vampirism_spirit_exist: return None # no cast, if vampirism spirit not exist

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        # we target vampirism spirit to destroy it

        vampirism_spirit: custom_behavior_helpers.SpiritAgentData | None = custom_behavior_helpers.Targets.get_first_or_default_from_spirits_raw(within_range=Range.Spirit, spirit_model_ids=[self.vampirism_spirit_model_id], condition=lambda agent_id: True)
        if vampirism_spirit is None: return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=vampirism_spirit.agent_id)
        return result