from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Range, Routines, Agent, Player
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class InfuseHealthUtility(CustomSkillUtilityBase):
    """
    Infuse_Health utility.

    Targets lowest-health injured ally (excluding the player) within spellcast range.
    Will only consider casting if the player currently has BOTH:
      - Aura of Restoration (configurable)
      - Life Attunement (configurable)

    The buff checks use Routines.Checks.Effects.HasBuff(...) as requested: if either check
    returns False, evaluation returns None and casting is skipped.

    Safety: Uses player_can_sacrifice_health to prevent killing yourself.
    """

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerHealthGravityDefinition = ScorePerHealthGravityDefinition(10),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Infuse_Health"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition: ScorePerHealthGravityDefinition = score_definition

        # CustomSkill instances for the enchantments so we can reference their skill_id
        self._aura_skill = CustomSkill("Aura_of_Restoration")
        self._life_skill = CustomSkill("Life_Attunement")

        # Load persisted configuration or use defaults
        self.sacrifice_life_limit_percent: float = float(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "sacrifice_life_limit_percent", str(0.22)))
        self.sacrifice_life_limit_absolute: int = int(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "sacrifice_life_limit_absolute", str(100)))
        self.require_aura_of_restoration: bool = PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "require_aura_of_restoration", str(0)) == "1"
        self.require_life_attunement: bool = PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "require_life_attunement", str(0)) == "1"
        self.should_cast_when_mana_low: bool = PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "should_cast_when_mana_low", str(0)) == "1"
        self.mana_low_threshold: float = float(PersistenceLocator().skills.read_or_default(self.custom_skill.skill_name, "mana_low_threshold", str(0.40)))

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        """
        Return allies ordered by priority (lowest HP, then distance) within spellcast range,
        excluding the player (caster) and only including allies that are injured (health < 1.0).
        """
        player_agent = Player.GetAgentID()

        targets: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.5,
            condition=lambda agent_id:
                agent_id != player_agent and
                (Agent.GetHealth(agent_id) is not None and Agent.GetHealth(agent_id) < 0.9),
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
        )
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        """
        Evaluate Infuse_Health:

        - First check if we can safely sacrifice health (don't kill ourselves!)
        - Then check player buffs using Routines.Checks.Effects.HasBuff for Aura_of_Restoration
          and Life_Attunement (configurable requirements).
        - Optionally check if mana is low (if should_cast_when_mana_low is enabled).
        - If all checks pass, pick top injured ally and return emergency/damaged score.
        """
        # Safety check: don't kill ourselves! Infuse Health sacrifices 50% of our current health
        if not custom_behavior_helpers.Resources.player_can_sacrifice_health(50, self.sacrifice_life_limit_percent, self.sacrifice_life_limit_absolute):
            return None

        player_agent = Player.GetAgentID()

        # Check if mana is low (if enabled)
        if self.should_cast_when_mana_low:
            player_energy_percent = Agent.GetEnergy(player_agent)
            if player_energy_percent <= self.mana_low_threshold:
                return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY) # force cast when mana low (to regain energy)

        # Configurable buff checks using Routines.Checks.Effects.HasBuff
        try:
            has_aura = bool(Routines.Checks.Effects.HasBuff(player_agent, self._aura_skill.skill_id))
            has_life = bool(Routines.Checks.Effects.HasBuff(player_agent, self._life_skill.skill_id))
        except Exception:
            # If the buff-check call itself fails, be conservative and skip
            return None

        # Check if required buffs are present (based on configuration)
        if self.require_aura_of_restoration and not has_aura:
            return None
        if self.require_life_attunement and not has_life:
            return None

        targets = self._get_targets()
        if len(targets) == 0:
            return None

        top = targets[0]
        if top.hp < 0.40:
            return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY)
        if top.hp < 0.85:
            return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED)

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        """
        Execution path re-checks safety, mana, and buffs defensively and then casts on the top target.
        """
        # Safety check: don't kill ourselves!
        if not custom_behavior_helpers.Resources.player_can_sacrifice_health(50, self.sacrifice_life_limit_percent, self.sacrifice_life_limit_absolute):
            return BehaviorResult.ACTION_SKIPPED

        player_agent = Player.GetAgentID()

        # Check if mana is low (if enabled)
        if self.should_cast_when_mana_low:
            player_energy_percent = Agent.GetEnergy(player_agent)
            if player_energy_percent <= self.mana_low_threshold:
                # we force cast on a random party member to regain energy
                target = custom_behavior_helpers.Targets.get_first_or_default_from_allies_ordered_by_priority(
                    within_range=Range.Spellcast.value * 1.5,
                    condition=lambda agent_id: agent_id != player_agent,
                    sort_key=(TargetingOrder.DISTANCE_ASC,))
                if target is None: return BehaviorResult.ACTION_SKIPPED
                result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target)
                return result

        try:
            has_aura = bool(Routines.Checks.Effects.HasBuff(player_agent, self._aura_skill.skill_id))
            has_life = bool(Routines.Checks.Effects.HasBuff(player_agent, self._life_skill.skill_id))
        except Exception:
            return BehaviorResult.ACTION_SKIPPED

        # Check if required buffs are present (based on configuration)
        if self.require_aura_of_restoration and not has_aura:
            return BehaviorResult.ACTION_SKIPPED
        if self.require_life_attunement and not has_life:
            return BehaviorResult.ACTION_SKIPPED

        targets = self._get_targets()
        if len(targets) == 0:
            return BehaviorResult.ACTION_SKIPPED

        target = targets[0]
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        return result

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"sacrifice_life_limit_percent :")
        self.sacrifice_life_limit_percent = PyImGui.input_float("##sacrifice_life_limit_percent", self.sacrifice_life_limit_percent)
        PyImGui.bullet_text(f"sacrifice_life_limit_absolute :")
        self.sacrifice_life_limit_absolute = PyImGui.input_int("##sacrifice_life_limit_absolute", self.sacrifice_life_limit_absolute)
        PyImGui.bullet_text(f"require_aura_of_restoration :")
        self.require_aura_of_restoration = PyImGui.checkbox("##require_aura_of_restoration", self.require_aura_of_restoration)
        PyImGui.bullet_text(f"require_life_attunement :")
        self.require_life_attunement = PyImGui.checkbox("##require_life_attunement", self.require_life_attunement)
        PyImGui.bullet_text(f"should_cast_when_mana_low :")
        self.should_cast_when_mana_low = PyImGui.checkbox("##should_cast_when_mana_low", self.should_cast_when_mana_low)
        PyImGui.bullet_text(f"mana_low_threshold :")
        self.mana_low_threshold = PyImGui.input_float("##mana_low_threshold", self.mana_low_threshold)

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "sacrifice_life_limit_percent", f"{self.sacrifice_life_limit_percent:.2f}")
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "sacrifice_life_limit_absolute", str(self.sacrifice_life_limit_absolute))
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "require_aura_of_restoration", "1" if self.require_aura_of_restoration else "0")
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "require_life_attunement", "1" if self.require_life_attunement else "0")
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "should_cast_when_mana_low", "1" if self.should_cast_when_mana_low else "0")
        PersistenceLocator().skills.write_for_account(str(self.custom_skill.skill_name), "mana_low_threshold", f"{self.mana_low_threshold:.2f}")
        print("configuration saved for account")

    @override
    def persist_configuration_as_global(self):
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "sacrifice_life_limit_percent", f"{self.sacrifice_life_limit_percent:.2f}")
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "sacrifice_life_limit_absolute", str(self.sacrifice_life_limit_absolute))
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "require_aura_of_restoration", "1" if self.require_aura_of_restoration else "0")
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "require_life_attunement", "1" if self.require_life_attunement else "0")
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "should_cast_when_mana_low", "1" if self.should_cast_when_mana_low else "0")
        PersistenceLocator().skills.write_global(str(self.custom_skill.skill_name), "mana_low_threshold", f"{self.mana_low_threshold:.2f}")
        print("configuration saved as global")

    @override
    def delete_persisted_configuration(self):
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "sacrifice_life_limit_percent")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "sacrifice_life_limit_absolute")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "require_aura_of_restoration")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "require_life_attunement")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "should_cast_when_mana_low")
        PersistenceLocator().skills.delete(str(self.custom_skill.skill_name), "mana_low_threshold")
        print("configuration deleted")