from typing import Any, Generator, override

from Py4GWCoreLib import Range, Agent
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.sortable_agent_data import SortableAgentData
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class XinraesWeaponUtility(CustomSkillUtilityBase):
    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(35),
        mana_required_to_cast: int = 5,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Xinraes_Weapon"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )
        self.score_definition: ScoreStaticDefinition = score_definition

        data: str | None = PersistenceLocator().skills.read(self.custom_skill.skill_name, "buff_configuration")
        if data is not None:
            self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget.instanciate_from_string(
                self.event_bus, self.custom_skill, data
            )
        else:
            self.buff_configuration: CustomBuffMultipleTarget = CustomBuffMultipleTarget(
                event_bus,
                self.custom_skill,
                buff_configuration_per_profession=BuffConfigurationPerProfession.BUFF_CONFIGURATION_ALL,
            )

    def _get_candidates(self) -> list[SortableAgentData]:
        return custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,
            condition=lambda agent_id: (
                self.buff_configuration.get_agent_id_predicate()(agent_id)
                and not Agent.IsWeaponSpelled(agent_id)
            ),
            sort_key=(
                TargetingOrder.ENEMIES_QUANTITY_WITHIN_RANGE_DESC,
                TargetingOrder.HP_ASC,
                TargetingOrder.DISTANCE_ASC,
            ),
            range_to_count_enemies=Range.Earshot.value,
            range_to_count_allies=None,
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        candidates = self._get_candidates()
        if len(candidates) == 0:
            return None

        best = candidates[0]
        score = self.score_definition.get_score()

        if best.hp < 0.5:
            score += 10
        if best.enemy_quantity_within_range >= 3:
            score += 5

        return min(score, 90)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        candidates = self._get_candidates()
        if len(candidates) == 0:
            return BehaviorResult.ACTION_SKIPPED
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=candidates[0].agent_id)
        return result

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return self.buff_configuration

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "buff_configuration", self.buff_configuration.serialize_to_string())
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "buff_configuration", self.buff_configuration.serialize_to_string())
        print("configuration saved as global")

    @override
    def delete_persisted_configuration(self):
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "buff_configuration")
        print("configuration deleted")
