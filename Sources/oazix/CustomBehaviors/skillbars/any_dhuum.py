from typing import Any, Generator, override
import time

from Py4GWCoreLib import Agent, AgentArray, CombatEvents, GLOBAL_CACHE, Player, Range, ThrottledTimer
from Py4GWCoreLib.CombatEvents import EventType
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.skills.monk.unyielding_aura_utility import UnyieldingAuraUtility

#OQBDAqwDSPwQwRwSwTwAAAAAAA


class PendingConditionUtility(CustomSkillUtilityBase):
    """
    Placeholder utility for skills that are registered in the build but do not
    have their final cast conditions yet.
    """

    def __init__(self, event_bus: EventBus, skill: CustomSkill, current_build: list[CustomSkill]):
        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(50),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        # Prepared only: final cast conditions will be added later.
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        if False:
            yield None
        return BehaviorResult.ACTION_SKIPPED

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        pass

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return None

    @override
    def has_persistence(self) -> bool:
        return False

    @override
    def delete_persisted_configuration(self):
        pass

    @override
    def persist_configuration_as_global(self):
        pass

    @override
    def persist_configuration_for_account(self):
        pass


class SpiritualHealingUtility(CustomSkillUtilityBase):
    """Spiritual Healing: heal the lowest-HP ally under 50% health."""

    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill]):
        spiritual_healing_skill = AnyDhuum_UtilitySkillBar._resolve_custom_skill("Spiritual_Healing", "Spiritual Healing")
        super().__init__(
            event_bus=event_bus,
            skill=spiritual_healing_skill,
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(90),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        return custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,
            condition=lambda agent_id: Agent.GetHealth(agent_id) < 0.50,
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        targets = self._get_targets()
        if len(targets) == 0:
            return None
        return 90.0

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        targets = self._get_targets()
        if len(targets) == 0:
            if False:
                yield None
            return BehaviorResult.ACTION_SKIPPED

        target = targets[0]
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(
            self.custom_skill,
            target_agent_id=target.agent_id,
        )
        return result

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        pass

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return None

    @override
    def has_persistence(self) -> bool:
        return False

    @override
    def delete_persisted_configuration(self):
        pass

    @override
    def persist_configuration_as_global(self):
        pass

    @override
    def persist_configuration_for_account(self):
        pass


class ReversalOfDeathUtility(CustomSkillUtilityBase):
    """Reversal of Death: cast on ally with the highest death penalty from shared memory."""

    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill]):
        reversal_skill = AnyDhuum_UtilitySkillBar._resolve_custom_skill("Reversal_of_Death", "Reversal of Death")
        super().__init__(
            event_bus=event_bus,
            skill=reversal_skill,
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(94),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )

    @staticmethod
    def _same_party_and_map(self_account, other_account) -> bool:
        return (
            int(self_account.AgentPartyData.PartyID) == int(other_account.AgentPartyData.PartyID)
            and int(self_account.AgentData.Map.MapID) == int(other_account.AgentData.Map.MapID)
            and int(self_account.AgentData.Map.Region) == int(other_account.AgentData.Map.Region)
            and int(self_account.AgentData.Map.District) == int(other_account.AgentData.Map.District)
            and int(self_account.AgentData.Map.Language) == int(other_account.AgentData.Map.Language)
        )

    def _get_morale_by_agent_id(self) -> dict[int, int]:
        morale_by_agent: dict[int, int] = {}
        self_email = Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(self_email)
        if self_account is None:
            return morale_by_agent

        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if not account.IsSlotActive or account.IsIsolated:
                continue
            if not self._same_party_and_map(self_account, account):
                continue
            agent_id = int(account.AgentData.AgentID or 0)
            if agent_id <= 0:
                continue
            morale_by_agent[agent_id] = int(account.AgentData.Morale)

        return morale_by_agent

    def _get_target_with_highest_death_penalty(self) -> custom_behavior_helpers.SortableAgentData | None:
        allies = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,
            condition=lambda agent_id: int(agent_id) != int(Player.GetAgentID()),
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
            is_alive=True,
        )
        if len(allies) == 0:
            return None

        morale_by_agent = self._get_morale_by_agent_id()
        if len(morale_by_agent) == 0:
            return None

        best_target: custom_behavior_helpers.SortableAgentData | None = None
        best_death_penalty = 0

        for ally in allies:
            morale = int(morale_by_agent.get(int(ally.agent_id), 100))
            death_penalty = max(0, 100 - morale)
            if death_penalty <= 0:
                continue

            if best_target is None or death_penalty > best_death_penalty:
                best_target = ally
                best_death_penalty = death_penalty

        return best_target

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        target = self._get_target_with_highest_death_penalty()
        if target is None:
            return None
        return 94.0

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        target = self._get_target_with_highest_death_penalty()
        if target is None:
            if False:
                yield None
            return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(
            self.custom_skill,
            target_agent_id=target.agent_id,
        )
        return result

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        pass

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return None

    @override
    def has_persistence(self) -> bool:
        return False

    @override
    def delete_persisted_configuration(self):
        pass

    @override
    def persist_configuration_as_global(self):
        pass

    @override
    def persist_configuration_for_account(self):
        pass


class DhuumsRestUtility(CustomSkillUtilityBase):
    """Dhuum's Rest monitor: tracks Reaper activity, never casts from player."""

    _reaper_dhuums_rest_pending: bool = False
    _reaper_dhuums_rest_deadline_ms: float = 0.0
    _reaper_force_fury_deadline_ms: float = 0.0
    _REAPER_DHUUMS_REST_CAST_WINDOW_MS = 20000

    _REAPER_NAME_MATCHERS = (
        "reaper of the bone pits",
        "reaper of the chaos planes",
        "reaper of the forgotten vale",
        "reaper of the ice wastes",
        "reaper of the labyrinth",
        "reaper of the spawning pools",
        "reaper of the twin serpent mountains",
    )

    _ACTIVATION_EVENT_TYPES = (
        EventType.SKILL_ACTIVATED,
        EventType.ATTACK_SKILL_ACTIVATED,
        EventType.INSTANT_SKILL_ACTIVATED,
    )

    _DHUUMS_REST_CANDIDATES = (
        "Dhuum_s_Rest",
        "Dhuum's Rest",
        "Dhuums_Rest",
        "Dhuums_Rest_reaper_skill",
    )
    _PLAYER_DHUUMS_REST_CANDIDATES = (
        "Dhuum_s_Rest",
        "Dhuum's Rest",
        "Dhuums_Rest",
    )
    _DHUUMS_REST_REAPER_SKILL_ID = 3079

    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill]):
        dhuums_rest_skill = AnyDhuum_UtilitySkillBar._resolve_custom_skill("Dhuum_s_Rest", "Dhuum's Rest", "Dhuums_Rest")
        super().__init__(
            event_bus=event_bus,
            skill=dhuums_rest_skill,
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(86),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )
        self._reaper_ids_refresh_timer = ThrottledTimer(1500)
        self._reaper_ids_refresh_timer.Reset()
        self._cached_reaper_ids: set[int] = set()
        self._dhuums_rest_skill_ids: set[int] = set()
        self._player_dhuums_rest_skill_ids: set[int] = set()
        for name in self._DHUUMS_REST_CANDIDATES:
            skill_id = AnyDhuum_UtilitySkillBar._resolve_skill_id(name)
            if skill_id > 0:
                self._dhuums_rest_skill_ids.add(int(skill_id))

        for name in self._PLAYER_DHUUMS_REST_CANDIDATES:
            skill_id = AnyDhuum_UtilitySkillBar._resolve_skill_id(name)
            if skill_id > 0:
                self._player_dhuums_rest_skill_ids.add(int(skill_id))

        self._dhuums_rest_skill_ids.add(int(self._DHUUMS_REST_REAPER_SKILL_ID))

        if int(self.custom_skill.skill_id) > 0:
            self._dhuums_rest_skill_ids.add(int(self.custom_skill.skill_id))
            self._player_dhuums_rest_skill_ids.add(int(self.custom_skill.skill_id))

    def _refresh_reaper_ids(self) -> None:
        if not self._reaper_ids_refresh_timer.IsExpired() and len(self._cached_reaper_ids) > 0:
            return

        reaper_ids: set[int] = set()
        for agent_id in AgentArray.GetAllyArray():
            name = (Agent.GetNameByID(agent_id) or "").strip().lower()
            if not name:
                continue
            if any(matcher in name for matcher in self._REAPER_NAME_MATCHERS):
                reaper_ids.add(int(agent_id))

        self._cached_reaper_ids = reaper_ids
        self._reaper_ids_refresh_timer.Reset()

    def _is_reaper_casting_dhuums_rest(self) -> bool:
        self._refresh_reaper_ids()
        if len(self._cached_reaper_ids) == 0:
            return False

        CombatEvents.update()
        recent_skills = CombatEvents.get_recent_skills(1500)
        for ts, caster_id, skill_id, target_id, event_type in reversed(recent_skills):
            if int(event_type) not in self._ACTIVATION_EVENT_TYPES:
                continue

            caster_id_int = int(caster_id)
            skill_id_int = int(skill_id)

            # Only refresh the cast window when a known Reaper used the explicit reaper skill id.
            if caster_id_int in self._cached_reaper_ids and skill_id_int == int(self._DHUUMS_REST_REAPER_SKILL_ID):
                return True

        return False

    def _has_player_casted_dhuums_rest(self) -> bool:
        player_id = int(Player.GetAgentID())
        if player_id <= 0:
            return False

        if len(self._player_dhuums_rest_skill_ids) == 0:
            return False

        CombatEvents.update()
        recent_skills = CombatEvents.get_recent_skills(3000)
        for ts, caster_id, skill_id, target_id, event_type in reversed(recent_skills):
            if int(caster_id) != player_id:
                continue
            if int(event_type) not in self._ACTIVATION_EVENT_TYPES:
                continue
            if int(skill_id) in self._player_dhuums_rest_skill_ids:
                return True

        return False

    @classmethod
    def is_reaper_dhuums_rest_pending(cls) -> bool:
        now_ms = time.monotonic() * 1000.0
        return now_ms < float(cls._reaper_dhuums_rest_deadline_ms)

    @classmethod
    def should_force_fury(cls) -> bool:
        now_ms = time.monotonic() * 1000.0
        return now_ms < float(cls._reaper_force_fury_deadline_ms)

    def _get_latest_reaper_activation_skill_id(self) -> int:
        self._refresh_reaper_ids()
        if len(self._cached_reaper_ids) == 0:
            return 0

        CombatEvents.update()
        recent_skills = CombatEvents.get_recent_skills(1500)
        for ts, caster_id, skill_id, target_id, event_type in reversed(recent_skills):
            if int(event_type) not in self._ACTIVATION_EVENT_TYPES:
                continue
            if int(caster_id) not in self._cached_reaper_ids:
                continue
            return int(skill_id)

        return 0

    def _update_pending_state_from_recent_events(self) -> bool:
        self._refresh_reaper_ids()

        if len(self._dhuums_rest_skill_ids) == 0:
            DhuumsRestUtility._reaper_dhuums_rest_pending = False
            return False

        player_id = int(Player.GetAgentID())
        CombatEvents.update()
        recent_skills = CombatEvents.get_recent_skills(8000)

        reaper_trigger_count = 0
        player_cast_count = 0

        for ts, caster_id, skill_id, target_id, event_type in recent_skills:
            if int(event_type) not in self._ACTIVATION_EVENT_TYPES:
                continue

            caster_id_int = int(caster_id)
            skill_id_int = int(skill_id)

            # Most reliable signal: Reaper-only Dhuum's Rest skill id.
            if skill_id_int == int(self._DHUUMS_REST_REAPER_SKILL_ID) and caster_id_int != player_id:
                reaper_trigger_count += 1
                continue

            if caster_id_int in self._cached_reaper_ids and skill_id_int in self._dhuums_rest_skill_ids:
                reaper_trigger_count += 1
                continue

            if caster_id_int == player_id and skill_id_int in self._player_dhuums_rest_skill_ids:
                player_cast_count += 1

        DhuumsRestUtility._reaper_dhuums_rest_pending = reaper_trigger_count > player_cast_count
        return DhuumsRestUtility._reaper_dhuums_rest_pending

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        now_ms = time.monotonic() * 1000.0
        latest_reaper_skill_id = self._get_latest_reaper_activation_skill_id()
        if latest_reaper_skill_id > 0:
            if latest_reaper_skill_id == int(self._DHUUMS_REST_REAPER_SKILL_ID):
                DhuumsRestUtility._reaper_dhuums_rest_deadline_ms = now_ms + float(self._REAPER_DHUUMS_REST_CAST_WINDOW_MS)
                DhuumsRestUtility._reaper_force_fury_deadline_ms = 0.0
            else:
                DhuumsRestUtility._reaper_force_fury_deadline_ms = now_ms + float(self._REAPER_DHUUMS_REST_CAST_WINDOW_MS)
                DhuumsRestUtility._reaper_dhuums_rest_deadline_ms = 0.0

        DhuumsRestUtility._reaper_dhuums_rest_pending = (
            DhuumsRestUtility.is_reaper_dhuums_rest_pending() and not DhuumsRestUtility.should_force_fury()
        )
        if not DhuumsRestUtility._reaper_dhuums_rest_pending:
            return None
        return 99.0

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        pass

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return None

    @override
    def has_persistence(self) -> bool:
        return False

    @override
    def delete_persisted_configuration(self):
        pass

    @override
    def persist_configuration_as_global(self):
        pass

    @override
    def persist_configuration_for_account(self):
        pass


class GhostlyFuryUtility(CustomSkillUtilityBase):
    """Ghostly Fury: simple offensive spell cast on enemy targets."""

    _REAPER_NAME_MATCHERS = (
        "reaper of the bone pits",
        "reaper of the chaos planes",
        "reaper of the forgotten vale",
        "reaper of the ice wastes",
        "reaper of the labyrinth",
        "reaper of the spawning pools",
        "reaper of the twin serpent mountains",
    )

    _ACTIVATION_EVENT_TYPES = (
        EventType.SKILL_ACTIVATED,
        EventType.ATTACK_SKILL_ACTIVATED,
        EventType.INSTANT_SKILL_ACTIVATED,
    )

    _GHOSTLY_FURY_CANDIDATES = ("Ghostly_Fury", "Ghostly Fury")

    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill]):
        ghostly_fury_skill = AnyDhuum_UtilitySkillBar._resolve_custom_skill("Ghostly_Fury", "Ghostly Fury")
        super().__init__(
            event_bus=event_bus,
            skill=ghostly_fury_skill,
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(85),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )
        self._reaper_ids_refresh_timer = ThrottledTimer(1500)
        self._reaper_ids_refresh_timer.Reset()
        self._cached_reaper_ids: set[int] = set()
        self._ghostly_fury_skill_ids: set[int] = set()
        for name in self._GHOSTLY_FURY_CANDIDATES:
            skill_id = AnyDhuum_UtilitySkillBar._resolve_skill_id(name)
            if skill_id > 0:
                self._ghostly_fury_skill_ids.add(int(skill_id))

        if int(self.custom_skill.skill_id) > 0:
            self._ghostly_fury_skill_ids.add(int(self.custom_skill.skill_id))

    def _get_target(self) -> int | None:
        return custom_behavior_helpers.Targets.get_nearest_or_default_from_enemy_ordered_by_priority(
            within_range=Range.Spellcast.value,
            should_prioritize_party_target=True,
            condition=lambda agent_id: Agent.IsAlive(agent_id),
        )

    def _refresh_reaper_ids(self) -> None:
        if not self._reaper_ids_refresh_timer.IsExpired() and len(self._cached_reaper_ids) > 0:
            return

        reaper_ids: set[int] = set()
        for agent_id in AgentArray.GetAllyArray():
            name = (Agent.GetNameByID(agent_id) or "").strip().lower()
            if not name:
                continue
            if any(matcher in name for matcher in self._REAPER_NAME_MATCHERS):
                reaper_ids.add(int(agent_id))

        self._cached_reaper_ids = reaper_ids
        self._reaper_ids_refresh_timer.Reset()

    def _is_reaper_casting_ghostly_fury(self) -> bool:
        self._refresh_reaper_ids()
        if len(self._cached_reaper_ids) == 0:
            return False

        if len(self._ghostly_fury_skill_ids) == 0:
            return False

        CombatEvents.update()
        recent_skills = CombatEvents.get_recent_skills(1500)
        for ts, caster_id, skill_id, target_id, event_type in reversed(recent_skills):
            if int(caster_id) not in self._cached_reaper_ids:
                continue
            if int(event_type) not in self._ACTIVATION_EVENT_TYPES:
                continue
            if int(skill_id) in self._ghostly_fury_skill_ids:
                return True

        return False

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if DhuumsRestUtility.should_force_fury():
            if self._get_target() is None:
                return None
            return 100.0
        if DhuumsRestUtility.is_reaper_dhuums_rest_pending():
            return None
        if not self._is_reaper_casting_ghostly_fury():
            return None
        if self._get_target() is None:
            return None
        return 85.0

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        target_agent_id = self._get_target()
        if target_agent_id is None:
            if False:
                yield None
            return BehaviorResult.ACTION_SKIPPED

        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(
            self.custom_skill,
            target_agent_id=target_agent_id,
        )
        return result

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        pass

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return None

    @override
    def has_persistence(self) -> bool:
        return False

    @override
    def delete_persisted_configuration(self):
        pass

    @override
    def persist_configuration_as_global(self):
        pass

    @override
    def persist_configuration_for_account(self):
        pass


class AnyDhuum_UtilitySkillBar(CustomBehaviorBaseUtility):
    """
    Dedicated build profile for the Dhuum rez phase.

    Detection is tolerant: if either the Dhuum marker skill or Unyielding Aura
    is present in the in-game skillbar, this behavior can be selected.
    """

    _DHUUM_MARKER_CANDIDATES = (
        "Curse_of_Dhuum",
        "Curse of Dhuum",
    )

    _PREPARED_SKILL_CANDIDATES: dict[str, tuple[str, ...]] = {
        "DhuumsRest": ("Dhuum's Rest", "Dhuum_s_Rest", "Dhuums_Rest"),
        "SpiritualHealing": ("Spiritual Healing", "Spiritual_Healing"),
        "ReversalOfDeath": ("Reversal of Death", "Reversal_of_Death"),
        "GhostlyFury": ("Ghostly Fury", "Ghostly_Fury"),
    }

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # Explicit utilities, following the common skillbar schema.
        self.dhuums_rest_utility: CustomSkillUtilityBase = DhuumsRestUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
        )
        self.spiritual_healing_utility: CustomSkillUtilityBase = SpiritualHealingUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
        )
        self.ghostly_fury_utility: CustomSkillUtilityBase = GhostlyFuryUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
        )
        self.unyielding_aura_utility: CustomSkillUtilityBase = UnyieldingAuraUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(98),
        )

        self.reversal_of_death_utility = ReversalOfDeathUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
        )

        self.encase_skeletal_utility: CustomSkillUtilityBase = PendingConditionUtility(
            event_bus=self.event_bus,
            skill=self._resolve_custom_skill("Encase_Skeletal", "Encase Skeletal"),
            current_build=in_game_build,
        )

    @staticmethod
    def _resolve_skill_id(*names: str) -> int:
        for name in names:
            try:
                skill_id = int(GLOBAL_CACHE.Skill.GetID(name))
            except Exception:
                skill_id = 0
            if skill_id > 0:
                return skill_id
        return 0

    @staticmethod
    def _resolve_custom_skill(*names: str) -> CustomSkill:
        for name in names:
            if AnyDhuum_UtilitySkillBar._resolve_skill_id(name) > 0:
                return CustomSkill(name)
        return CustomSkill(names[0])

    @override
    def count_matches_between_custom_behavior_and_in_game_build(self) -> int:
        in_game_ids = set(self.skillbar_management.get_in_game_build().keys())

        # Accept this profile as soon as one known Dhuum-bar skill is present.
        detection_candidates: list[tuple[str, ...]] = [
            self._DHUUM_MARKER_CANDIDATES,
            ("Unyielding_Aura", "Unyielding Aura"),
            *self._PREPARED_SKILL_CANDIDATES.values(),
        ]

        for candidate_names in detection_candidates:
            skill_id = self._resolve_skill_id(*candidate_names)
            if skill_id > 0 and skill_id in in_game_ids:
                return 1

        return 0

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.unyielding_aura_utility,
            self.spiritual_healing_utility,
            self.dhuums_rest_utility,
            self.reversal_of_death_utility,
            self.ghostly_fury_utility,
            self.encase_skeletal_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        # Keep a single required slot so loader ranking stays stable.
        return [CustomSkill("Unyielding_Aura")]
