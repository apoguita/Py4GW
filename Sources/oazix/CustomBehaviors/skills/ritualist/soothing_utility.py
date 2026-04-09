from typing import Any, Generator, override

from Py4GWCoreLib import Range, Agent, Player, AgentArray
from Py4GWCoreLib.enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class SoothingUtility(CustomSkillUtilityBase):

    SPIRIT_MODEL_ID = SpiritModelID.SOOTHING

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda count: min(35 + count * 10, 90)),
        mana_required_to_cast: int = 15,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Soothing"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    def _spirit_alive(self) -> bool:
        spirit = custom_behavior_helpers.Targets.get_first_or_default_from_spirits_raw(
            within_range=Range.Spirit,
            spirit_model_ids=[self.SPIRIT_MODEL_ID],
            condition=lambda agent_id: True,
        )
        if spirit is None:
            return False
        return spirit.hp >= 0.2

    @staticmethod
    def _is_adrenaline_user(agent_id: int) -> bool:
        """Melee weapons and spears use adrenaline skills."""
        _, weapon_name = Agent.GetWeaponType(agent_id)
        return weapon_name in ("Axe", "Hammer", "Daggers", "Scythe", "Sword", "Spear")

    @staticmethod
    def _count_adrenaline_enemies_in_range() -> int:
        enemy_ids = AgentArray.GetEnemyArray()
        enemy_ids = AgentArray.Filter.ByDistance(enemy_ids, Player.GetXY(), Range.Spirit.value)
        enemy_ids = AgentArray.Filter.ByCondition(enemy_ids, lambda aid: Agent.IsAlive(aid) and SoothingUtility._is_adrenaline_user(aid))
        return len(enemy_ids)

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if self._spirit_alive():
            return None

        melee_count = self._count_adrenaline_enemies_in_range()
        if melee_count == 0:
            return None

        return self.score_definition.get_score(melee_count)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        if result == BehaviorResult.ACTION_PERFORMED:
            yield from self.event_bus.publish(EventType.SPIRIT_CREATED, state, data=self.SPIRIT_MODEL_ID)
        return result
