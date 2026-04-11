from abc import abstractmethod
from typing import Any, Generator, override

import Py4GW
from Py4GWCoreLib import GLOBAL_CACHE, Agent, Player, Routines, Range, CombatEvents

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
    Base class for interrupt-style skills. Scans for enemies currently casting,
    checks cast-time feasibility (Fast Casting + ping + remaining cast time),
    coordinates with party members via the shared lock manager, and runs
    _execute() through the normal engine pipeline.
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

        self._pending_target_id: int | None = None  # target selected in _evaluate, consumed in _execute
        self._ping_handler = Py4GW.PingHandler()
        self._shared_lock_manager = CustomBehaviorParty().get_shared_lock_manager()

    @abstractmethod
    def _filter_target(self, skill_id: int, activation_seconds: float) -> bool:
        """Return True if this skill should try to interrupt the given enemy skill."""
        pass

    @abstractmethod
    def _compute_score(self, target_id: int) -> float | None:
        """
        Return the skill's priority score for this target, or None to skip.
        Subclass handles its own gating (energy, cooldown, etc.) using its
        score_definition primitive.
        """
        pass

    def _calculate_our_cast_time_ms(self) -> float:
        fast_casting_level = 0
        for attr in Agent.GetAttributes(Player.GetAgentID()):
            if attr.GetName() == "Fast Casting":
                fast_casting_level = attr.level
                break
        activation_s, _ = Routines.Checks.Skills.apply_fast_casting(self.custom_skill.skill_id, fast_casting_level)
        return activation_s * 1000.0

    def _is_feasible(self, target_id: int) -> bool:
        our_cast_ms = self._calculate_our_cast_time_ms()
        ping_ms = self._ping_handler.GetCurrentPing() * 1.2

        remaining_ms = CombatEvents.get_cast_time_remaining(target_id)
        if remaining_ms > 0:
            return remaining_ms > our_cast_ms + ping_ms

        # Fallback: assume enemy is halfway through their cast
        casting_skill_id = Agent.GetCastingSkillID(target_id)
        if casting_skill_id == 0: return False
        estimated_remaining = GLOBAL_CACHE.Skill.Data.GetActivation(casting_skill_id) * 500.0
        return estimated_remaining > our_cast_ms + ping_ms

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

    def _lock_key(self, agent_id: int) -> str:
        return f"{self.custom_skill.skill_name}_{agent_id}"

    def _find_unlocked_target(self) -> int | None:
        for t in self._detect_casting_enemies():
            if self._is_feasible(t.agent_id) and not self._shared_lock_manager.is_lock_taken(self._lock_key(t.agent_id)):
                return t.agent_id
        return None

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        target_id = self._find_unlocked_target()
        self._pending_target_id = target_id
        if target_id is None: return None
        return self._compute_score(target_id)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        target_id = self._pending_target_id
        self._pending_target_id = None

        if target_id is None: return BehaviorResult.ACTION_SKIPPED
        if not Agent.IsCasting(target_id): return BehaviorResult.ACTION_SKIPPED
        if not self._is_feasible(target_id): return BehaviorResult.ACTION_SKIPPED

        if not self._shared_lock_manager.try_aquire_lock(
                self._lock_key(target_id),
                timeout_seconds=self._lock_ttl_seconds,
                lock_type=ShareLockType.SKILLS):
            return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(
            self.custom_skill, target_agent_id=target_id)
        return result
