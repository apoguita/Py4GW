from abc import abstractmethod
from typing import Any, Generator, override

import Py4GW
from Py4GWCoreLib import GLOBAL_CACHE, Agent, Player, Routines, Range, CombatEvents
from Py4GWCoreLib.enums import Allegiance

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.sortable_agent_data import SortableAgentData
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.parties.shared_lock_manager import ShareLockType
from Sources.oazix.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class InterruptSkillBase(CustomSkillUtilityBase):
    """
    Base class for interrupt-style skills. Handles all mechanics shared by
    every interrupt skill so concrete skills only declare what to interrupt
    and how to score it.

    Responsibilities:
      - Registers a CombatEvents.on_skill_activated callback for event-driven detection
      - Calculates cast-time feasibility (Fast Casting + ping + remaining cast time)
      - Coordinates party members via the shared lock manager
      - Falls back to polling when the event path misses (e.g. entered range after cast started)
      - Runs _execute() through the normal engine pipeline (history, metrics, watchdogs, plugins)

    Subclasses implement:
      - _filter_target(skill_id, activation_seconds) : what casts to interrupt
      - _compute_score(target_id) : skill-specific scoring (energy, cooldown, etc.)
    """

    def __init__(self,
                 event_bus: EventBus,
                 skill: CustomSkill,
                 in_game_build: list[CustomSkill],
                 score_definition: ScoreDefinition,
                 mana_required_to_cast: float = 0,
                 lock_ttl_seconds: int = 3,
                 min_activation_seconds: float = 1.00,
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=in_game_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast)

        self._lock_ttl_seconds: int = lock_ttl_seconds
        self._min_activation_seconds: float = min_activation_seconds

        self._interrupt_opportunity: tuple[int, int] | None = None  # (agent_id, skill_id)
        self._ping_handler = Py4GW.PingHandler()
        self._shared_lock_manager = CustomBehaviorParty().get_shared_lock_manager()
        CombatEvents.on_skill_activated(self._on_enemy_cast)

    # --- Abstract subclass hooks -------------------------------------------------

    @abstractmethod
    def _filter_target(self, skill_id: int, activation_seconds: float) -> bool:
        """Return True if this skill should try to interrupt the given enemy skill."""
        pass

    @abstractmethod
    def _compute_score(self, target_id: int) -> float | None:
        """
        Return the skill's priority score for this target, or None to skip.
        Subclass is responsible for its own gating (energy, cooldown, etc.)
        and should use its score_definition primitive.
        """
        pass

    # --- Event-driven detection --------------------------------------------------

    def _on_enemy_cast(self, caster_id: int, skill_id: int, target_id: int):
        if Agent.GetAllegiance(caster_id)[0] != Allegiance.Enemy: return
        activation = GLOBAL_CACHE.Skill.Data.GetActivation(skill_id)
        if activation < self._min_activation_seconds: return
        if not self._filter_target(skill_id, activation): return

        player_pos = Player.GetXY()
        enemy_pos = Agent.GetXY(caster_id)
        dx = player_pos[0] - enemy_pos[0]
        dy = player_pos[1] - enemy_pos[1]
        if (dx * dx + dy * dy) > Range.Spellcast.value ** 2: return

        self._interrupt_opportunity = (caster_id, skill_id)
        # Skip the 300ms score throttle so we react within one execute cycle
        from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
        CustomBehaviorBaseUtility.request_score_recompute()

    # --- Feasibility math --------------------------------------------------------

    def _get_fast_casting_level(self) -> int:
        for attr in Agent.GetAttributes(Player.GetAgentID()):
            if attr.GetName() == "Fast Casting":
                return attr.level
        return 0

    def _calculate_our_cast_time_ms(self) -> float:
        fc_level = self._get_fast_casting_level()
        activation_s, _ = Routines.Checks.Skills.apply_fast_casting(self.custom_skill.skill_id, fc_level)
        return activation_s * 1000.0

    def _is_feasible(self, target_id: int) -> bool:
        our_cast_ms = self._calculate_our_cast_time_ms()
        ping_ms = self._ping_handler.GetCurrentPing() * 1.2

        remaining_ms = CombatEvents.get_cast_time_remaining(target_id)
        if remaining_ms > 0:
            return remaining_ms > our_cast_ms + ping_ms

        # Fallback: use skill activation time as estimate (assume halfway through)
        casting_skill_id = Agent.GetCastingSkillID(target_id)
        if casting_skill_id == 0: return False
        estimated_remaining = GLOBAL_CACHE.Skill.Data.GetActivation(casting_skill_id) * 500.0
        return estimated_remaining > our_cast_ms + ping_ms

    # --- Polling fallback --------------------------------------------------------
    # Why this exists: the event callback only fires once per SKILL_ACTIVATED packet.
    # If an enemy starts casting while we're out of range, the callback rejects the
    # opportunity (range check). When we walk into range a moment later, no new event
    # fires — the enemy is still mid-cast but the event has already been consumed.
    # This polling pass catches that "cast already in progress when we entered range"
    # scenario, which is common at the start of engagements.

    def _detect_casting_enemies(self, sort_key=(TargetingOrder.CASTER_THEN_MELEE,)) -> list[SortableAgentData]:
        return custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            condition=lambda agent_id:
                Agent.IsCasting(agent_id) and
                self._filter_target(
                    Agent.GetCastingSkillID(agent_id),
                    GLOBAL_CACHE.Skill.Data.GetActivation(Agent.GetCastingSkillID(agent_id))),
            sort_key=sort_key,
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id)
        )

    # --- Target selection --------------------------------------------------------

    @staticmethod
    def _lock_key_for(skill_name: str, agent_id: int) -> str:
        return f"{skill_name}_{agent_id}"

    def _find_unlocked_target(self) -> int | None:
        # Event-driven path first
        if self._interrupt_opportunity is not None:
            caster_id, _ = self._interrupt_opportunity
            lock_key = self._lock_key_for(self.custom_skill.skill_name, caster_id)
            if (Agent.IsCasting(caster_id) and self._is_feasible(caster_id)
                    and not self._shared_lock_manager.is_lock_taken(lock_key)):
                return caster_id
            self._interrupt_opportunity = None

        # Polling fallback: scan casting enemies and take the first unlocked feasible one
        for t in self._detect_casting_enemies():
            lock_key = self._lock_key_for(self.custom_skill.skill_name, t.agent_id)
            if self._is_feasible(t.agent_id) and not self._shared_lock_manager.is_lock_taken(lock_key):
                self._interrupt_opportunity = (t.agent_id, Agent.GetCastingSkillID(t.agent_id))
                return t.agent_id
        return None

    # --- Default _evaluate: find target, delegate scoring to subclass ------------

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        target_id = self._find_unlocked_target()
        if target_id is None: return None
        return self._compute_score(target_id)

    # --- Standard _execute through the normal pipeline ---------------------------

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        opp = self._interrupt_opportunity
        self._interrupt_opportunity = None

        if opp is None: return BehaviorResult.ACTION_SKIPPED
        target_id, _ = opp

        if not Agent.IsCasting(target_id): return BehaviorResult.ACTION_SKIPPED
        if not self._is_feasible(target_id): return BehaviorResult.ACTION_SKIPPED

        lock_key = self._lock_key_for(self.custom_skill.skill_name, target_id)
        if not self._shared_lock_manager.try_aquire_lock(
                lock_key,
                timeout_seconds=self._lock_ttl_seconds,
                lock_type=ShareLockType.SKILLS):
            return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(
            self.custom_skill, target_agent_id=target_id)
        return result
