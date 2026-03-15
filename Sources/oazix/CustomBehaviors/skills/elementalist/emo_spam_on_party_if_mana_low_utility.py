from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Range, Agent, Player
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class EmoSpamOnPartyIfManaLowUtility(CustomSkillUtilityBase):
    """
    Utility that spams healing skills on random party members when player's mana is low.
    This is used for Ether Renewal builds to regain energy by casting enchantments.
    
    When player's energy is below the threshold, it will cast one of the provided skills
    on a random party member to trigger energy gain from Ether Renewal.
    """

    def __init__(
        self,
        event_bus: EventBus,
        skills: list[CustomSkillUtilityBase],
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(78),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Emo_Spam_On_Party_If_Mana_Low"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition: ScoreStaticDefinition = score_definition
        self.skills: list[CustomSkillUtilityBase] = skills

        # Load persisted configuration or use defaults
        self.mana_low_threshold: float = float(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "mana_low_threshold", str(0.70)))


    def get_target(self) -> int | None:
        target = custom_behavior_helpers.Targets.get_first_or_default_from_allies_ordered_by_priority(
            within_range=Range.Spellcast.value,
            condition=lambda agent_id: agent_id != Player.GetAgentID(),
            sort_key=(TargetingOrder.HP_ASC,))
        return target

    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        """
        Evaluate if we should spam skills on party members.
        Returns score if player's energy is below threshold, None otherwise.
        """
        player_agent = Player.GetAgentID()
        player_energy_percent = Agent.GetEnergy(player_agent)
        
        if player_energy_percent > self.mana_low_threshold: return None

        target = self.get_target()
        if target is None: return None

        # Check if any of the skills can be cast
        for skill_utility in self.skills:
            if skill_utility.custom_skill.skill_slot > 0:
                return self.score_definition.get_score()
    
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        """
        Execute by casting one of the available skills on a random party member.
        """
        # Find a random party member to cast on (excluding self)

        target = self.get_target()
        if target is None: return BehaviorResult.ACTION_SKIPPED

        # Try to cast one of the available skills
        for skill_utility in self.skills:
            if skill_utility.custom_skill.skill_slot > 0:
                result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(skill_utility.custom_skill, target_agent_id=target)
                return result

        return BehaviorResult.ACTION_SKIPPED

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        self.mana_low_threshold = PyImGui.input_float(
            "mana_low_threshold##mana_low_threshold", self.mana_low_threshold)

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        PersistenceLocator().skills.write_for_account(
            str(self.custom_skill.skill_name), "mana_low_threshold", f"{self.mana_low_threshold:.2f}")
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        PersistenceLocator().skills.write_global(
            str(self.custom_skill.skill_name), "mana_low_threshold", f"{self.mana_low_threshold:.2f}")
        print("configuration saved as global")

    @override
    def delete_persisted_configuration(self):
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "mana_low_threshold")
        print("configuration deleted")

