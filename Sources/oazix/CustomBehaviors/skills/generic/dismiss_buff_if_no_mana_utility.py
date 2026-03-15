from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Player, Effects
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class DismissBuffIfNoManaUtility(CustomSkillUtilityBase):
    """
    Utility that dismisses/drops specific buffs when player's mana is low.

    This is useful for builds that need to drop expensive maintained enchantments
    when energy is running low to prevent energy degeneration.

    The utility checks if the skills to dismiss are in the skillbar before attempting
    to drop the buffs.
    """

    def __init__(
        self,
        event_bus: EventBus,
        skill: CustomSkill,
        skills_to_dismiss: list[CustomSkillUtilityBase],
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(85),
        mana_required_to_cast: int = 0,
        mana_low_threshold: float = 0.20,
        enabled: bool = True,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition: ScoreStaticDefinition = score_definition
        self.skills_to_dismiss: list[CustomSkillUtilityBase] = skills_to_dismiss
        self.mana_low_threshold: float = mana_low_threshold

    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        """
        Evaluate if we should dismiss any buffs.
        Returns score if:
        - Utility is enabled
        - At least one skill to dismiss is in the skillbar
        - Player's energy is below threshold
        - Player has at least one of the buffs active
        """

        player_agent = Player.GetAgentID()
        player_energy_percent = Agent.GetEnergy(player_agent)
        
        # Check if energy is low
        if player_energy_percent > self.mana_low_threshold:
            return None

        # Check if any of the skills to dismiss are in skillbar and have active buffs
        for skill_utility in self.skills_to_dismiss:
            skill = skill_utility.custom_skill
            # Check if skill is in skillbar
            if skill.skill_slot == 0:
                continue

            # Check if player has the buff
            has_buff = GLOBAL_CACHE.Effects.BuffExists(player_agent, skill.skill_id)
            if has_buff:
                return self.score_definition.get_score()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        """
        Execute by dropping buffs if conditions are met.
        Drops all active buffs from the skills_to_dismiss list.
        """
        player_agent = Player.GetAgentID()
        player_energy_percent = Agent.GetEnergy(player_agent)

        # Check if energy is low
        if player_energy_percent > self.mana_low_threshold:
            return BehaviorResult.ACTION_SKIPPED

        # Drop all active buffs from the skills to dismiss list
        any_buff_dropped = False
        for skill_utility in self.skills_to_dismiss:
            skill = skill_utility.custom_skill

            # Check if skill is in skillbar
            if skill.skill_slot == 0:
                continue

            # Get the buff ID and drop it if it exists
            buff_id = GLOBAL_CACHE.Effects.GetBuffID(skill.skill_id)
            if buff_id != 0:
                GLOBAL_CACHE.Effects.DropBuff(buff_id)
                any_buff_dropped = True

        if not any_buff_dropped:
            return BehaviorResult.ACTION_SKIPPED

        # Wait a moment for the action to complete
        yield from custom_behavior_helpers.Helpers.wait_for(100)

        return BehaviorResult.ACTION_PERFORMED

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.text("Skills to dismiss:")
        for skill_utility in self.skills_to_dismiss:
            PyImGui.text(f"  - {skill_utility.custom_skill.skill_name}")
        self.mana_low_threshold = PyImGui.input_float(
            "mana_low_threshold##mana_low_threshold", self.mana_low_threshold)

