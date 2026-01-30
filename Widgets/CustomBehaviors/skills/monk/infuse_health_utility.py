from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Range, Routines, Agent, Player
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Widgets.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class InfuseHealthUtility(CustomSkillUtilityBase):
    """
    Infuse_Health utility.

    Targets lowest-health injured ally (excluding the player) within spellcast range.
    Will only consider casting if the player currently has BOTH:
      - Aura of Restoration
      - Life Attunement

    The buff checks use Routines.Checks.Effects.HasBuff(...) as requested: if either check
    returns False, evaluation returns None and casting is skipped.
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
                (Agent.GetHealth(agent_id) is not None and Agent.GetHealth(agent_id) < 1.0),
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
        )
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        """
        Evaluate Infuse_Health:

        - First check player buffs using Routines.Checks.Effects.HasBuff for Aura_of_Restoration
          and Life_Attunement (both must be True to proceed).
        - If buff checks pass, pick top injured ally and return emergency/damaged score as in SeedOfLife.
        """
        player_agent = Player.GetAgentID()

        # Simple, direct buff checks using Routines.Checks.Effects.HasBuff as requested
        try:
            has_aura = bool(Routines.Checks.Effects.HasBuff(player_agent, self._aura_skill.skill_id))
            has_life = bool(Routines.Checks.Effects.HasBuff(player_agent, self._life_skill.skill_id))
        except Exception:
            # If the buff-check call itself fails, be conservative and skip
            return None

        if not (has_aura and has_life):
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
        Execution path re-checks buffs defensively and then casts on the top target.
        """
        player_agent = Player.GetAgentID()
        try:
            has_aura = bool(Routines.Checks.Effects.HasBuff(player_agent, self._aura_skill.skill_id))
            has_life = bool(Routines.Checks.Effects.HasBuff(player_agent, self._life_skill.skill_id))
        except Exception:
            return BehaviorResult.ACTION_SKIPPED

        if not (has_aura and has_life):
            return BehaviorResult.ACTION_SKIPPED

        targets = self._get_targets()
        if len(targets) == 0:
            return BehaviorResult.ACTION_SKIPPED

        target = targets[0]
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        return result