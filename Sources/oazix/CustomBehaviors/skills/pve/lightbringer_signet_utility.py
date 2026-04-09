from typing import Any, Generator, override

from Py4GWCoreLib import Agent, Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class LightbringerSignetUtility(CustomSkillUtilityBase):
    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(70),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Lightbringer_Signet"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition: ScoreStaticDefinition = score_definition
        self.mana_gained : int = 24

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Area,
            condition=lambda agent_id: True, # no need to really check enemy type, let's consider we are in DoA
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, ),
        )
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        # we could imagine moving to a better place such as we do in TaO, i dont think it worth it.

        # only cast if we can earn 24 mana.
        current_mana = custom_behavior_helpers.Resources.get_player_absolute_energy()
        max_mana = Agent.GetMaxEnergy(Player.GetAgentID())
        if current_mana + self.mana_gained > max_mana: return None

        targets = self._get_targets()
        if len(targets) == 0: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result

