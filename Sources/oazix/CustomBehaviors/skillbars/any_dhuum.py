"""AnyDhuum_UtilitySkillBar — Dhuum phase skill behavior for the Underworld bot.

This module implements the skill utilities activated during the Dhuum soul-splitting
(rez) phase. Four utilities are active at any given time:

  - SpiritualHealingUtility:  Heal the weakest nearby ally that is below 70% HP.
  - ReversalOfDeathUtility:   Cast Reversal of Death on the ally with the highest
                               death penalty. Activates only once the Spirit Form
                               phase begins (≥1 account with Spirit Form buff 3134).
                               When ≤2 accounts carry Spirit Form, only those
                               soul-split allies are targeted; once >2 have it, any
                               ally with a death penalty becomes a valid target.
  - DhuumsRestUtility:        Mirrors Reaper casts of Dhuum's Rest by watching the
                               CombatEvents stream for reaper skill activations.
  - GhostlyFuryUtility:       Mirrors Reaper casts of Ghostly Fury the same way.

Two additional utilities are instantiated but excluded from the active skill list:
  - UnyieldingAuraUtility:    Available for party resurrection between fights.
  - PendingConditionUtility:  Placeholder for Encase Skeletal (conditions TBD).
"""
from typing import Any, Generator, override
import time

from Py4GWCoreLib import Agent, AgentArray, CombatEvents, GLOBAL_CACHE, Party, Player, Range, ThrottledTimer
from Py4GWCoreLib.Py4GWcorelib import Utils
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

# ─── Module-level constants ──────────────────────────────────────────────────
# Underworld Chest spawn data used to suppress all skill casts after Dhuum dies.
# When the chest is present the fight is definitively over and no skills should fire.
_UW_CHEST_POS = (-13987, 17291)              # approximate world-space position near the Dhuum altar
_UW_CHEST_RADIUS = 3000.0                    # detection radius in game units
_UW_CHEST_NAME_FRAGMENT = "underworld chest" # substring matched against gadget names (lowercase)

def _is_uw_chest_present() -> bool:
    """Return True if the Underworld Chest (gadget) has spawned near the Dhuum arena.

    The chest only appears after Dhuum is defeated. All skill utilities check this
    function and suppress casts immediately once it returns True, preventing any
    wasteful skill activation after the encounter is finished.
    """
    for agent_id in AgentArray.GetAgentArray():
        # Only gadget-type agents can be the chest; skip all other agent types early.
        if not Agent.IsGadget(agent_id):
            continue
        name = (Agent.GetNameByID(agent_id) or "").strip().lower()
        if _UW_CHEST_NAME_FRAGMENT not in name:
            continue
        # Confirm the gadget is within the expected radius of the Dhuum altar position.
        if Utils.Distance(_UW_CHEST_POS, Agent.GetXY(agent_id)) <= _UW_CHEST_RADIUS:
            return True
    return False


# ─── Placeholder utility ─────────────────────────────────────────────────────

class PendingConditionUtility(CustomSkillUtilityBase):
    """Placeholder for skills that are registered in the build but have no cast logic yet.

    Currently wraps Encase Skeletal, which appears on the Dhuum skillbar but whose
    exact usage conditions have not been implemented. The utility will never fire
    and serves only as a registered stub so the skill is tracked by the framework.
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
        # No conditions implemented yet — never evaluate to a score.
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


# ─── Spiritual Healing utility ───────────────────────────────────────────────

class SpiritualHealingUtility(CustomSkillUtilityBase):
    """Spiritual Healing: cast on the lowest-HP ally currently below 70% health.

    Score: 90. Suppressed when the Underworld Chest is present (fight over).
    Targets are sorted by ascending HP first, then by ascending distance.
    """

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

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if _is_uw_chest_present():
            return False
        return super().are_common_pre_checks_valid(current_state)

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        """Return allies within cast range whose HP fraction is below 70%, sorted by lowest HP."""
        return custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,  # slightly extended range for safety
            condition=lambda agent_id: Agent.GetHealth(agent_id) < 0.70,  # 70% HP threshold
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


# ─── Reversal of Death utility ───────────────────────────────────────────────

class ReversalOfDeathUtility(CustomSkillUtilityBase):
    """Reversal of Death: cast on the ally with the highest death penalty.

    Death penalty is derived from shared-memory morale data
    (morale < 100 ⇒ death_penalty = 100 − morale).

    Activation is gated on the Spirit Form phase:
      - Requires at least _SPIRIT_FORM_MIN_COUNT accounts to have Spirit Form
        (buff skill ID 3134) before any cast attempt is made.
      - When ≤2 accounts have Spirit Form, only those soul-split allies are
        targeted — they are the ones accumulating death penalty during failed rez.
      - Once more than 2 accounts carry Spirit Form, any ally with a death penalty
        becomes a valid target, as the split phase is fully active.

    Score: 94. Suppressed when the Underworld Chest is present (fight over).
    """

    # Skill ID for the Spirit Form disguise buff applied during the Dhuum rez phase.
    _SPIRIT_FORM_SKILL_ID = 3134
    # Minimum number of same-party accounts with Spirit Form required before this
    # skill fires at all. Set to 1 so the utility activates as soon as the first
    # account enters the soul-split phase.
    _SPIRIT_FORM_MIN_COUNT = 1

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

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if _is_uw_chest_present():
            return False
        if self._count_spirit_form_accounts() < self._SPIRIT_FORM_MIN_COUNT:
            return False
        return super().are_common_pre_checks_valid(current_state)

    def _count_spirit_form_accounts(self) -> int:
        """Count how many active same-party accounts currently have Spirit Form (buff 3134)."""
        self_email = Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(self_email)
        if self_account is None:
            return 0
        count = 0
        for account in (GLOBAL_CACHE.ShMem.GetAllAccountData() or []):
            if not account.IsSlotActive or account.IsIsolated:
                continue
            if not self._same_party_and_map(self_account, account):
                continue
            try:
                if any(
                    b.SkillId == self._SPIRIT_FORM_SKILL_ID
                    for b in account.AgentData.Buffs.Buffs
                    if b.SkillId != 0
                ):
                    count += 1
            except Exception:
                pass
        return count

    @staticmethod
    def _same_party_and_map(self_account, other_account) -> bool:
        """Return True when other_account shares the same party, map, region, district and language.

        All five fields must match to ensure we only consider accounts that are
        truly in the same in-game instance. Accounts on a different map, region,
        or district are silently excluded from all shared-memory scans.
        """
        return (
            int(self_account.AgentPartyData.PartyID) == int(other_account.AgentPartyData.PartyID)
            and int(self_account.AgentData.Map.MapID) == int(other_account.AgentData.Map.MapID)
            and int(self_account.AgentData.Map.Region) == int(other_account.AgentData.Map.Region)
            and int(self_account.AgentData.Map.District) == int(other_account.AgentData.Map.District)
            and int(self_account.AgentData.Map.Language) == int(other_account.AgentData.Map.Language)
        )

    def _get_spirit_form_agent_ids(self) -> set[int]:
        """Return agent IDs of same-party accounts that currently have Spirit Form (buff 3134)."""
        result: set[int] = set()
        self_email = Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(self_email)
        if self_account is None:
            return result
        for account in (GLOBAL_CACHE.ShMem.GetAllAccountData() or []):
            if not account.IsSlotActive or account.IsIsolated:
                continue
            if not self._same_party_and_map(self_account, account):
                continue
            try:
                if any(
                    b.SkillId == self._SPIRIT_FORM_SKILL_ID
                    for b in account.AgentData.Buffs.Buffs
                    if b.SkillId != 0
                ):
                    agent_id = int(account.AgentData.AgentID or 0)
                    if agent_id > 0:
                        result.add(agent_id)
            except Exception:
                pass
        return result

    def _get_morale_by_agent_id(self) -> dict[int, int]:
        """Return a mapping of {agent_id: morale_value} for all same-party accounts.

        Morale is stored as an integer (0–100). A value below 100 indicates a death
        penalty: death_penalty = 100 − morale. Accounts that are isolated, inactive,
        or on a different map instance are excluded.
        """
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
        """Return the in-range ally with the largest death penalty, or None if none qualify.

        Targeting mode depends on how many accounts currently carry Spirit Form:
          - ≤2 Spirit Form accounts: only soul-split allies (those with Spirit Form)
            are considered. This avoids healing accounts that have not yet entered
            the split and are not accumulating the rez-death penalty.
          - >2 Spirit Form accounts: all living allies with any death penalty are
            valid, because the split is in full swing and anyone may need the skill.

        Among all eligible allies the one with the highest death penalty is chosen.
        Allies at full morale (no death penalty) are skipped entirely.
        """
        spirit_form_count     = self._count_spirit_form_accounts()
        spirit_form_agent_ids = self._get_spirit_form_agent_ids()

        # Restrict to Spirit Form allies while the split is still small.
        # Once >2 accounts are split, open up targeting to everyone with a penalty.
        restrict_to_spirit_form = spirit_form_count <= 2

        my_id = int(Player.GetAgentID())

        def _condition(agent_id: int) -> bool:
            # Never target ourselves.
            if int(agent_id) == my_id:
                return False
            # In restricted mode, skip any ally that is not in Spirit Form.
            if restrict_to_spirit_form and int(agent_id) not in spirit_form_agent_ids:
                return False
            return True

        allies = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Spellcast.value * 1.2,
            condition=_condition,
            sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC),
            is_alive=True,
        )
        if len(allies) == 0:
            return None

        # Fetch morale from shared memory (populated by each account's own process).
        morale_by_agent = self._get_morale_by_agent_id()
        if len(morale_by_agent) == 0:
            return None

        best_target: custom_behavior_helpers.SortableAgentData | None = None
        best_death_penalty = 0

        for ally in allies:
            # Default to morale 100 (no penalty) when the account is absent from shared mem.
            morale = int(morale_by_agent.get(int(ally.agent_id), 100))
            death_penalty = max(0, 100 - morale)
            if death_penalty <= 0:
                # No death penalty — this ally does not need the skill.
                continue
            if best_target is None or death_penalty > best_death_penalty:
                best_target      = ally
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


# ─── Dhuum's Rest / Ghostly Fury utility ─────────────────────────────────────────

class DhuumsRestUtility(CustomSkillUtilityBase):
    """Mirror Reaper skill casts for the Dhuum phase.

    When a Reaper casts Dhuum's Rest the active mode switches to DREST and this
    utility casts Dhuum's Rest on our side. When a Reaper casts Ghostly Fury the
    mode switches to FURY and GhostlyFuryUtility fires instead.

    The active *mode* is class-level (shared across all instances) so every account
    reacts to the same reaper event without each doing a separate event scan.
    Mode switches are debounced to suppress noise from closely-spaced events.

    Score: 97 (highest active utility). Suppressed when the Underworld Chest is present.
    """

    # ── Mode constants ─────────────────────────────────────────────────────────────
    _MODE_DREST = "DREST"   # Reaper cast Dhuum's Rest  → we cast Dhuum's Rest
    _MODE_FURY  = "FURY"    # Reaper cast Ghostly Fury  → we cast Ghostly Fury
    # Minimum milliseconds before a mode flip to the opposite value is allowed.
    # Prevents rapid DREST↔FURY oscillation when both skills appear in the event log.
    _MODE_SWITCH_DEBOUNCE_MS = 6000.0

    # ── Reaper identification ──────────────────────────────────────────────────
    # All seven Underworld Reapers, lowercase for case-insensitive name matching.
    _REAPER_NAME_MATCHERS = (
        "reaper of the bone pits",
        "reaper of the chaos planes",
        "reaper of the forgotten vale",
        "reaper of the ice wastes",
        "reaper of the labyrinth",
        "reaper of the spawning pools",
        "reaper of the twin serpent mountains",
    )

    # Event types that indicate a skill was *activated* (cast started), not just queued.
    _ACTIVATION_EVENT_TYPES = (
        EventType.SKILL_ACTIVATED,
        EventType.ATTACK_SKILL_ACTIVATED,
        EventType.INSTANT_SKILL_ACTIVATED,
    )

    # ── Skill name candidates ──────────────────────────────────────────────────
    # Multiple spellings and localisations so the look-up is locale-tolerant.
    _DHUUMS_REST_CANDIDATES = (
        "Dhuum_s_Rest",
        "Dhuum's Rest",
        "Dhuums_Rest",
        "Dhuums_Rest_reaper_skill",
    )
    _GHOSTLY_FURY_CANDIDATES = (
        "Ghostly_Fury",
        "Ghostly Fury",
        # Reapers always cast Ghostly Fury and Dhuum's Rest together; the reaper-skill
        # variant of Ghostly Fury can therefore serve as a reliable fallback proxy.
        "Ghostly Fury_reaper_skill",
    )

    # ── Shared (class-level) runtime state ────────────────────────────────────────
    # All instances share these fields so exactly one "current mode" exists globally.
    _shared_mode: str | None = None               # active mode, or None before first detection
    _shared_mode_locked_until_ms: float = 0.0     # wall-clock ms until a mode flip is allowed
    _reaper_id_refresh_timer: ThrottledTimer | None = None  # throttles the full-scan (1200 ms)
    _event_refresh_timer:     ThrottledTimer | None = None  # throttles CombatEvents polling (250 ms)
    _cached_reaper_ids:      set[int] = set()  # IDs found via name-matching scan
    _learned_reaper_ids:     set[int] = set()  # IDs discovered via fallback event learning
    _dhuums_rest_skill_ids:  set[int] = set()  # resolved runtime skill IDs for Dhuum's Rest
    _ghostly_fury_skill_ids: set[int] = set()  # resolved runtime skill IDs for Ghostly Fury
    _last_logged_candidate_signature: tuple[int, int, int] | None = None  # dedup guard for console log

    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill]):
        dhuums_rest_skill = AnyDhuum_UtilitySkillBar._resolve_custom_skill("Dhuum_s_Rest", "Dhuum's Rest", "Dhuums_Rest")
        super().__init__(
            event_bus=event_bus,
            skill=dhuums_rest_skill,
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(97),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )

        # Keep local resolved skill available for matching if this runtime ID differs by locale.
        if int(self.custom_skill.skill_id) > 0:
            DhuumsRestUtility._dhuums_rest_skill_ids.add(int(self.custom_skill.skill_id))

        DhuumsRestUtility._ensure_tracking_initialized()

    @classmethod
    def _ensure_tracking_initialized(cls) -> None:
        """Lazily initialise all class-level timers and skill-ID sets on first call.

        Safe to call multiple times — each guard checks whether the work is already done.
        Must be called before any method that reads the timer or skill-ID fields.
        """
        if cls._reaper_id_refresh_timer is None:
            cls._reaper_id_refresh_timer = ThrottledTimer(1200)
            cls._reaper_id_refresh_timer.Reset()

        if cls._event_refresh_timer is None:
            cls._event_refresh_timer = ThrottledTimer(250)
            cls._event_refresh_timer.Reset()

        if len(cls._dhuums_rest_skill_ids) == 0:
            for name in cls._DHUUMS_REST_CANDIDATES:
                skill_id = AnyDhuum_UtilitySkillBar._resolve_skill_id(name)
                if skill_id > 0:
                    cls._dhuums_rest_skill_ids.add(int(skill_id))
            cls._dhuums_rest_skill_ids.add(3079)

        if len(cls._ghostly_fury_skill_ids) == 0:
            for name in cls._GHOSTLY_FURY_CANDIDATES:
                skill_id = AnyDhuum_UtilitySkillBar._resolve_skill_id(name)
                if skill_id > 0:
                    cls._ghostly_fury_skill_ids.add(int(skill_id))

    @classmethod
    def _refresh_reaper_ids(cls) -> None:
        """Scan all visible agents and rebuild the cached set of Reaper agent IDs.

        The scan is throttled by _reaper_id_refresh_timer (1200 ms interval) and is
        skipped when entries already exist in the cache and the timer has not expired.
        """
        cls._ensure_tracking_initialized()
        if cls._reaper_id_refresh_timer is None:
            return

        if not cls._reaper_id_refresh_timer.IsExpired() and len(cls._cached_reaper_ids) > 0:
            return

        reaper_ids: set[int] = set()
        candidate_agent_ids = set(AgentArray.GetAllyArray())
        candidate_agent_ids.update(AgentArray.GetNeutralArray())
        candidate_agent_ids.update(AgentArray.GetNPCMinipetArray())
        candidate_agent_ids.update(AgentArray.GetSpiritPetArray())

        for agent_id in candidate_agent_ids:
            name = str(Agent.GetNameByID(agent_id) or "").strip().lower()
            if any(matcher in name for matcher in cls._REAPER_NAME_MATCHERS):
                reaper_ids.add(int(agent_id))

        cls._cached_reaper_ids = reaper_ids
        cls._reaper_id_refresh_timer.Reset()

    @classmethod
    def _get_effective_reaper_ids(cls) -> set[int]:
        """Return the union of name-matched reaper IDs and event-learned reaper IDs."""
        return set(cls._cached_reaper_ids).union(cls._learned_reaper_ids)

    @classmethod
    def _get_reaper_candidate_agent_ids(cls) -> set[int]:
        """Return all agent IDs that could possibly be a Reaper.

        Reapers appear in ally, neutral, NPC/minipet, and spirit/pet arrays depending
        on their current faction relationship, so all four arrays are merged.
        """
        candidate_agent_ids = set(AgentArray.GetAllyArray())
        candidate_agent_ids.update(AgentArray.GetNeutralArray())
        candidate_agent_ids.update(AgentArray.GetNPCMinipetArray())
        candidate_agent_ids.update(AgentArray.GetSpiritPetArray())
        return {int(x) for x in candidate_agent_ids}

    @classmethod
    def _get_party_member_agent_ids(cls) -> set[int]:
        party_member_ids: set[int] = set()

        for player in Party.GetPlayers():
            login_number = int(getattr(player, "login_number", 0) or 0)
            if login_number <= 0:
                continue
            agent_id = int(Party.Players.GetAgentIDByLoginNumber(login_number) or 0)
            if agent_id > 0:
                party_member_ids.add(agent_id)

        for hero in Party.GetHeroes():
            agent_id = int(getattr(hero, "agent_id", 0) or 0)
            if agent_id > 0:
                party_member_ids.add(agent_id)

        for henchman in Party.GetHenchmen():
            agent_id = int(getattr(henchman, "agent_id", 0) or 0)
            if agent_id > 0:
                party_member_ids.add(agent_id)

        return party_member_ids

    @classmethod
    def _skill_id_matches_candidates(cls, skill_id: int, candidate_skill_ids: set[int], candidate_names: tuple[str, ...]) -> bool:
        """Return True if skill_id belongs to the candidate set or matches by normalised name.

        Two-stage check:
          1. Fast numeric lookup against the pre-resolved runtime ID set.
          2. Fallback name comparison (lowercased, underscores → spaces) to handle
             locales where GLOBAL_CACHE returns a different numeric ID than expected.
        """
        if int(skill_id) in candidate_skill_ids:
            return True

        # Normalise both sides by lowercasing and replacing underscores with spaces.
        skill_name = str(GLOBAL_CACHE.Skill.GetName(int(skill_id)) or "").strip().lower().replace("_", " ")
        if len(skill_name) == 0:
            return False

        normalized_candidates = [name.lower().replace("_", " ") for name in candidate_names]
        return any(candidate in skill_name for candidate in normalized_candidates)

    @classmethod
    def _set_mode(cls, mode: str, now_ms: float) -> None:
        """Update the shared mode and extend the debounce lock window.

        If the requested mode matches the current mode (or no mode is set yet), the
        transition is always accepted and the debounce window is refreshed.
        Switching to a *different* mode is only allowed once the debounce window has
        expired, preventing rapid DREST↔FURY oscillation from noisy event bursts.
        """
        if cls._shared_mode is None or cls._shared_mode == mode:
            # Same mode or first-time set: always accept and refresh the lock window.
            cls._shared_mode = mode
            cls._shared_mode_locked_until_ms = now_ms + cls._MODE_SWITCH_DEBOUNCE_MS
            return

        # Different mode requested: only allow after the debounce window has expired.
        if now_ms >= cls._shared_mode_locked_until_ms:
            cls._shared_mode = mode
            cls._shared_mode_locked_until_ms = now_ms + cls._MODE_SWITCH_DEBOUNCE_MS

    @classmethod
    def _log_candidate_detection(cls, ts: int, caster_id: int, skill_id: int, candidate_type: str) -> None:
        signature = (int(ts), int(caster_id), int(skill_id))
        if cls._last_logged_candidate_signature == signature:
            return
        cls._last_logged_candidate_signature = signature

        try:
            import Py4GW  # local import to avoid a circular dependency at module level

            caster_name = str(Agent.GetNameByID(int(caster_id)) or "<unknown>").strip()
            skill_name = str(GLOBAL_CACHE.Skill.GetName(int(skill_id)) or "<unknown>").strip()
            Py4GW.Console.Log(
                "AnyDhuum",
                f"Detected {candidate_type} candidate: ts={int(ts)} caster={int(caster_id)} ('{caster_name}') skill={int(skill_id)} ('{skill_name}')",
                Py4GW.Console.MessageType.Info,
            )
        except Exception:
            pass

    @classmethod
    def refresh_mode_from_reaper_events(cls) -> None:
        """Poll the CombatEvents stream and update the shared mode from reaper casts.

        This method is throttled to run at most every 250 ms. On each poll:
          1. The recent skill event list is walked in reverse order (newest first).
          2. Events are filtered to skill-activation types (ACTIVATED / INSTANT).
          3. Each event is checked against both the Dhuum's Rest and Ghostly Fury
             candidate sets using _skill_id_matches_candidates.
          4. When the caster is a confirmed Reaper, the shared mode is set and the
             loop exits immediately (the newest matching event always wins).
          5. Fallback learning: if a non-player, non-party ally casts a candidate
             skill, the caster is promoted to the learned-reaper set for future polls.
        """
        cls._ensure_tracking_initialized()
        cls._refresh_reaper_ids()

        if cls._event_refresh_timer is None:
            return
        if not cls._event_refresh_timer.IsExpired():
            return  # Not yet due for the next poll — skip entirely.

        cls._event_refresh_timer.Reset()

        effective_reaper_ids = cls._get_effective_reaper_ids()

        now_ms        = time.monotonic() * 1000.0
        CombatEvents.update()
        recent_skills = CombatEvents.get_recent_skills(80)  # fetch last 80 combat events
        player_id                 = int(Player.GetAgentID())
        reaper_candidate_agent_ids = cls._get_reaper_candidate_agent_ids()
        party_member_agent_ids    = cls._get_party_member_agent_ids()

        # Walk events newest-first so the most recent reaper cast determines the mode.
        for ts, caster_id, skill_id, target_id, event_type in reversed(recent_skills):
            if int(event_type) not in cls._ACTIVATION_EVENT_TYPES:
                continue  # Ignore non-activation events (e.g. skill-end, attack-end).

            caster_id_int = int(caster_id)
            skill_id_int  = int(skill_id)

            is_drest_candidate = cls._skill_id_matches_candidates(
                skill_id_int,
                cls._dhuums_rest_skill_ids,
                cls._DHUUMS_REST_CANDIDATES,
            )
            is_fury_candidate = cls._skill_id_matches_candidates(
                skill_id_int,
                cls._ghostly_fury_skill_ids,
                cls._GHOSTLY_FURY_CANDIDATES,
            )
            if not is_drest_candidate and not is_fury_candidate:
                continue  # Not a skill we care about — skip.

            # Fallback learning: if a non-player, non-party ally casts a candidate
            # skill that is not yet in the reaper set, promote it as a learned reaper.
            # This handles cases where name-based matching fails (e.g. locale differences).
            if (
                caster_id_int in reaper_candidate_agent_ids
                and caster_id_int != player_id
                and caster_id_int not in party_member_agent_ids
                and caster_id_int not in effective_reaper_ids
            ):
                cls._learned_reaper_ids.add(caster_id_int)
                effective_reaper_ids.add(caster_id_int)

            if caster_id_int not in effective_reaper_ids:
                continue  # Caster is not a Reaper — discard this event.

            # Confirmed reaper cast: update the shared mode and stop processing.
            if is_drest_candidate:
                cls._log_candidate_detection(int(ts), caster_id_int, skill_id_int, "_DHUUMS_REST_CANDIDATES")
                cls._set_mode(cls._MODE_DREST, now_ms)
                return
            if is_fury_candidate:
                cls._log_candidate_detection(int(ts), caster_id_int, skill_id_int, "_GHOSTLY_FURY_CANDIDATES")
                cls._set_mode(cls._MODE_FURY, now_ms)
                return

    @classmethod
    def is_dhuums_rest_mode(cls) -> bool:
        """Return True when the most recent confirmed Reaper cast was Dhuum's Rest."""
        cls.refresh_mode_from_reaper_events()
        return cls._shared_mode == cls._MODE_DREST

    @classmethod
    def is_ghostly_fury_mode(cls) -> bool:
        """Return True when the most recent confirmed Reaper cast was Ghostly Fury."""
        cls.refresh_mode_from_reaper_events()
        return cls._shared_mode == cls._MODE_FURY

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if _is_uw_chest_present():
            return None
        if not DhuumsRestUtility.is_dhuums_rest_mode():
            return None
        return 97.0

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
    """Mirror Reaper casts: when Reapers cast Ghostly Fury, we cast Ghostly Fury."""

    def __init__(self, event_bus: EventBus, current_build: list[CustomSkill]):
        ghostly_fury_skill = AnyDhuum_UtilitySkillBar._resolve_custom_skill("Ghostly_Fury", "Ghostly Fury")
        super().__init__(
            event_bus=event_bus,
            skill=ghostly_fury_skill,
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(97),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )

        # Keep local resolved skill available for matching if this runtime ID differs by locale.
        if int(self.custom_skill.skill_id) > 0:
            DhuumsRestUtility._ghostly_fury_skill_ids.add(int(self.custom_skill.skill_id))
        DhuumsRestUtility._ensure_tracking_initialized()

    def _get_target(self) -> int | None:
        return custom_behavior_helpers.Targets.get_nearest_or_default_from_enemy_ordered_by_priority(
            within_range=Range.Spellcast.value,
            should_prioritize_party_target=True,
            condition=lambda agent_id: Agent.IsAlive(agent_id),
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if _is_uw_chest_present():
            return None
        if not DhuumsRestUtility.is_ghostly_fury_mode():
            return None
        if self._get_target() is None:
            return None
        return 97.0

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
            self.spiritual_healing_utility,
            self.dhuums_rest_utility,
            self.reversal_of_death_utility,
            self.ghostly_fury_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        # Curse of Dhuum is the reliable in-bar marker for this behavior profile.
        return [CustomSkill("Curse_of_Dhuum")]
