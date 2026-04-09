from typing import Any, Generator, Callable, override

import Py4GW
from Py4GWCoreLib import GLOBAL_CACHE, Agent, Player, Routines, Range, CombatEvents, SkillBar
from Py4GWCoreLib.enums import Allegiance
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.sortable_agent_data import SortableAgentData
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.parties.shared_lock_manager import ShareLockType

class PowerDrainUtility(CustomSkillUtilityBase):

    def __init__(self,
                    event_bus: EventBus,
                    current_build: list[CustomSkill],
                    score_definition: ScoreStaticDefinition = ScoreStaticDefinition(82),
            ) -> None:

            super().__init__(
                event_bus=event_bus,
                skill=CustomSkill("Power_Drain"),
                in_game_build=current_build,
                score_definition=score_definition)

            self.score_definition: ScoreStaticDefinition = score_definition
            self._interrupt_opportunity: tuple[int, int] | None = None  
            self._ping_handler = Py4GW.PingHandler()
            self._shared_lock_manager = CustomBehaviorParty().get_shared_lock_manager()
            self._fast_path_fired = False
            CombatEvents.on_skill_activated(self._on_enemy_cast)

    @staticmethod
    def _lock_key(agent_id: int) -> str:
        return f"power_drain_{agent_id}"

    def _on_enemy_cast(self, caster_id: int, skill_id: int, target_id: int):
        if Agent.GetAllegiance(caster_id)[0] != Allegiance.Enemy: return
        if not (GLOBAL_CACHE.Skill.Flags.IsSpell(skill_id) or
                GLOBAL_CACHE.Skill.Flags.IsChant(skill_id)): return
        activation = GLOBAL_CACHE.Skill.Data.GetActivation(skill_id)
        if activation < 1.00: return
        player_pos = Player.GetXY()
        enemy_pos = Agent.GetXY(caster_id)
        dx = player_pos[0] - enemy_pos[0]
        dy = player_pos[1] - enemy_pos[1]
        if (dx * dx + dy * dy) > Range.Spellcast.value ** 2: return

        if self._try_fast_interrupt(caster_id, skill_id):
            return

        self._interrupt_opportunity = (caster_id, skill_id)

    def _try_fast_interrupt(self, caster_id: int, skill_id: int) -> bool:
        if self.custom_skill.skill_slot <= 0: return False
        if not Routines.Checks.Skills.IsSkillSlotReady(self.custom_skill.skill_slot): return False
        if SkillBar.GetCasting(): return False

        energy_pct = Agent.GetEnergy(Player.GetAgentID())
        if energy_pct > 0.85: return False

        lock_key = self._lock_key(caster_id)
        if self._shared_lock_manager.is_lock_taken(lock_key): return False
        if not self._shared_lock_manager.try_aquire_lock(lock_key, timeout_seconds=3, lock_type=ShareLockType.SKILLS):
            return False

        Player.ChangeTarget(caster_id)
        SkillBar.UseSkill(self.custom_skill.skill_slot, caster_id)
        self._fast_path_fired = True
        self._interrupt_opportunity = None
        return True

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

        casting_skill_id = Agent.GetCastingSkillID(target_id)
        if casting_skill_id == 0:
            return False
        estimated_remaining = GLOBAL_CACHE.Skill.Data.GetActivation(casting_skill_id) * 500.0
        return estimated_remaining > our_cast_ms + ping_ms

    def detect_casting_enemies(self) -> list[SortableAgentData]:
        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            condition=lambda agent_id:
                Agent.IsCasting(agent_id) and
                (GLOBAL_CACHE.Skill.Flags.IsSpell(Agent.GetCastingSkillID(agent_id)) or
                 GLOBAL_CACHE.Skill.Flags.IsChant(Agent.GetCastingSkillID(agent_id))) and
                GLOBAL_CACHE.Skill.Data.GetActivation(Agent.GetCastingSkillID(agent_id)) >= 1.00,
            sort_key=(TargetingOrder.CASTER_THEN_MELEE, ),
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id)
        )
        return targets

    def _find_unlocked_target(self) -> int | None:
        if self._interrupt_opportunity is not None:
            caster_id, _ = self._interrupt_opportunity
            if (Agent.IsCasting(caster_id) and self._is_feasible(caster_id)
                    and not self._shared_lock_manager.is_lock_taken(self._lock_key(caster_id))):
                return caster_id
            self._interrupt_opportunity = None

        targets = self.detect_casting_enemies()
        for t in targets:
            if self._is_feasible(t.agent_id) and not self._shared_lock_manager.is_lock_taken(self._lock_key(t.agent_id)):
                self._interrupt_opportunity = (t.agent_id, Agent.GetCastingSkillID(t.agent_id))
                return t.agent_id

        return None

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if self._fast_path_fired:
            self._fast_path_fired = False
            return None

        target_id = self._find_unlocked_target()
        if target_id is None: return None

        energy_pct = Agent.GetEnergy(Player.GetAgentID())
        if energy_pct > 0.85: return None

        energy_bonus = (0.85 - energy_pct) / 0.85 * 18.0
        return self.score_definition.get_score() + energy_bonus

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        opp = self._interrupt_opportunity
        self._interrupt_opportunity = None

        if opp is None: return BehaviorResult.ACTION_SKIPPED
        target_id, _ = opp

        if not Agent.IsCasting(target_id): return BehaviorResult.ACTION_SKIPPED
        if not self._is_feasible(target_id): return BehaviorResult.ACTION_SKIPPED

        lock_key = self._lock_key(target_id)
        if not self._shared_lock_manager.try_aquire_lock(lock_key, timeout_seconds=3, lock_type=ShareLockType.SKILLS):
            return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target_id)
        return result