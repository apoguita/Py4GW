from typing import Any, Generator, override

from Py4GWCoreLib import Range, Agent, Player, AgentArray, GLOBAL_CACHE
from Py4GWCoreLib.Effect import Effects
from Py4GWCoreLib.enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class RecuperationUtility(CustomSkillUtilityBase):

    SPIRIT_MODEL_ID = SpiritModelID.RECUPERATION

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(40),
        mana_required_to_cast: int = 25,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Recuperation"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )
        self.score_definition: ScoreStaticDefinition = score_definition

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
    def _is_suffering_degen(agent_id: int, burning_skill_id: int) -> bool:
        """Check if an ally has any health-degen condition: poison (-4),
        bleeding (-3), burning (-7), or a degen hex."""
        if Agent.IsPoisoned(agent_id):
            return True
        if Agent.IsBleeding(agent_id):
            return True
        if Agent.IsDegenHexed(agent_id):
            return True
        if Effects.HasEffect(agent_id, burning_skill_id):
            return True
        return False

    @staticmethod
    def _count_allies_suffering_degen() -> int:
        ally_ids = AgentArray.GetAllyArray()
        ally_ids = AgentArray.Filter.ByDistance(ally_ids, Player.GetXY(), Range.Spirit.value)
        ally_ids = AgentArray.Filter.ByCondition(ally_ids, lambda aid: Agent.IsAlive(aid))

        burning_skill_id = GLOBAL_CACHE.Skill.GetID("Burning")
        count = 0
        for aid in ally_ids:
            if RecuperationUtility._is_suffering_degen(aid, burning_skill_id):
                count += 1
        return count

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if self._spirit_alive():
            return None

        score = self.score_definition.get_score()

        degen_count = self._count_allies_suffering_degen()
        if degen_count >= 3:
            score += 15
        elif degen_count >= 1:
            score += 8

        if custom_behavior_helpers.Heals.is_party_damaged(
            within_range=Range.Spirit.value,
            min_allies_count=2,
            less_health_than_percent=0.7,
        ):
            score += 5

        return min(score, 90)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        if result == BehaviorResult.ACTION_PERFORMED:
            yield from self.event_bus.publish(EventType.SPIRIT_CREATED, state, data=self.SPIRIT_MODEL_ID)
        return result
