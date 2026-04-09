from typing import Any, Generator, cast, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Range, Agent, Player, Routines
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.plugins.options.raw_number_option import RawNumberOption


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
        skills_on_party: list[CustomSkillUtilityBase],
        skills_on_self: list[CustomSkillUtilityBase],
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
        self.skills_on_party: list[CustomSkillUtilityBase] = skills_on_party
        self.skills_on_self: list[CustomSkillUtilityBase] = skills_on_self

        self.add_plugin_option(lambda x: RawNumberOption(x.custom_skill, "mana_low_threshold", 0.70))

    def get_party_target(self) -> int | None:
        target = custom_behavior_helpers.Targets.get_first_or_default_from_allies_ordered_by_priority(
            within_range=Range.Earshot.value,
            condition=lambda agent_id: agent_id != Player.GetAgentID(),
            sort_key=(TargetingOrder.HP_ASC,))
        return target

    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        player_agent = Player.GetAgentID()
        player_energy_percent = Agent.GetEnergy(player_agent)

        mana_low_threshold_option: RawNumberOption | None = cast(RawNumberOption | None, self.get_plugin_option("mana_low_threshold"))
        if mana_low_threshold_option is None: return None
        mana_low_threshold = mana_low_threshold_option.option_value
        if player_energy_percent > mana_low_threshold: return None
        
        # Check if any of the skills can be cast
        skills_to_check : list[CustomSkillUtilityBase] = self.skills_on_party + self.skills_on_self
        for skill_utility in skills_to_check:
            if skill_utility.custom_skill.skill_slot > 0:
                if not Routines.Checks.Skills.IsSkillSlotReady(skill_utility.custom_skill.skill_slot): continue
                return self.score_definition.get_score()
    
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        
        for skill_utility in self.skills_on_self:
            if skill_utility.custom_skill.skill_slot > 0:
                if not Routines.Checks.Skills.IsSkillSlotReady(skill_utility.custom_skill.skill_slot): continue
                result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(skill_utility.custom_skill, target_agent_id=Player.GetAgentID())
                return result
        
        party_target = self.get_party_target()
        if party_target is None: return BehaviorResult.ACTION_SKIPPED

        for skill_utility in self.skills_on_party:
            if skill_utility.custom_skill.skill_slot > 0:
                result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(skill_utility.custom_skill, target_agent_id=party_target)
                return result

        return BehaviorResult.ACTION_SKIPPED