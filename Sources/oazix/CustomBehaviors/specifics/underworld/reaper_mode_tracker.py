"""Reaper-event mode tracker for the Dhuum encounter.

Scans the CombatEvents stream to detect when an Underworld Reaper activates
Dhuum's Rest or Ghostly Fury, and exposes a debounced shared mode so skill
utilities can mirror the corresponding casts.

This module deliberately contains no skill-casting logic — it is pure event
observation and state management.
"""

import time

from Py4GWCoreLib import Agent, AgentArray, GLOBAL_CACHE, Party, Player, Skill, ThrottledTimer
from Py4GWCoreLib.CombatEvents import CombatEvents as CombatEvents, EventType


class ReaperModeTracker:
    """Class-level (module-singleton) tracker for the Dhuum reaper skill mode.

    Both DhuumsRestUtility and GhostlyFuryUtility read from this tracker so
    they react to the same reaper event without each running an independent scan.
    All state is class-level; multiple instances would share it identically.

    Usage:
        ReaperModeTracker.is_dhuums_rest_mode()  -> bool
        ReaperModeTracker.is_ghostly_fury_mode() -> bool
    """

    MODE_DREST = "DREST"
    MODE_FURY  = "FURY"

    # Minimum milliseconds before a flip to the opposite mode is accepted.
    MODE_SWITCH_DEBOUNCE_MS: float = 6000.0

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

    # Only these event types indicate a *cast* started (not queued or finished).
    _ACTIVATION_EVENT_TYPES = (
        EventType.SKILL_ACTIVATED,
        EventType.ATTACK_SKILL_ACTIVATED,
        EventType.INSTANT_SKILL_ACTIVATED,
    )

    # Locale-tolerant name candidates for the two tracked reaper skills.
    _DHUUMS_REST_CANDIDATES = (
        "Dhuums_Rest_Reaper_skill",
    )
    _GHOSTLY_FURY_CANDIDATES = (
        "Ghostly_Fury_Reaper_skill",
    )

    # ── Shared (class-level) runtime state ────────────────────────────────────
    _shared_mode: str | None = None
    _shared_mode_locked_until_ms: float = 0.0

    _reaper_id_refresh_timer: ThrottledTimer | None = None
    _event_refresh_timer:     ThrottledTimer | None = None

    _cached_reaper_ids:  set[int] = set()   # IDs found via name-matching scan
    _learned_reaper_ids: set[int] = set()   # IDs discovered via event-based fallback

    # Skill utilities register their resolved runtime IDs here after construction
    # so the tracker always recognises them regardless of locale differences.
    dhuums_rest_skill_ids:  set[int] = set()
    ghostly_fury_skill_ids: set[int] = set()

    _last_logged_candidate_signature: tuple[int, int, int] | None = None

    # ── Initialisation ────────────────────────────────────────────────────────

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Lazily initialise timers and skill ID sets. Safe to call repeatedly."""
        if cls._reaper_id_refresh_timer is None:
            cls._reaper_id_refresh_timer = ThrottledTimer(1200)
            cls._reaper_id_refresh_timer.Reset()
        if cls._event_refresh_timer is None:
            cls._event_refresh_timer = ThrottledTimer(250)
            cls._event_refresh_timer.Reset()
        if not cls.dhuums_rest_skill_ids:
            try:
                sid = int(Skill.GetID("Dhuums_Rest_Reaper_skill"))
            except Exception:
                sid = 0
            if sid > 0:
                cls.dhuums_rest_skill_ids.add(sid)
            cls.dhuums_rest_skill_ids.add(3079)   # known fallback numeric ID
        if not cls.ghostly_fury_skill_ids:
            try:
                sid = int(Skill.GetID("Ghostly_Fury_Reaper_skill"))
            except Exception:
                sid = 0
            if sid > 0:
                cls.ghostly_fury_skill_ids.add(sid)
            cls.ghostly_fury_skill_ids.add(3091)   # known fallback numeric ID

    # ── External registration (called by skill utilities at construction) ─────

    @classmethod
    def register_dhuums_rest_skill_id(cls, skill_id: int) -> None:
        """Register a runtime skill ID resolved by DhuumsRestUtility."""
        if skill_id > 0:
            cls.dhuums_rest_skill_ids.add(skill_id)

    @classmethod
    def register_ghostly_fury_skill_id(cls, skill_id: int) -> None:
        """Register a runtime skill ID resolved by GhostlyFuryUtility."""
        if skill_id > 0:
            cls.ghostly_fury_skill_ids.add(skill_id)

    # ── Debug state ─────────────────────────────────────────────────────────
    _reaper_scan_logged: bool = False
    _event_scan_logged: bool = False
    _event_scan_log_timer: ThrottledTimer | None = None

    @classmethod
    def _debug_log(cls, tag: str, msg: str) -> None:
        try:
            import Py4GW
            Py4GW.Console.Log("ReaperTracker", f"[{tag}] {msg}", Py4GW.Console.MessageType.Info)
        except Exception:
            pass

    # ── Internal helpers ──────────────────────────────────────────────────────

    @classmethod
    def _refresh_reaper_ids(cls) -> None:
        cls._ensure_initialized()
        if cls._reaper_id_refresh_timer is None:
            return
        if not cls._reaper_id_refresh_timer.IsExpired() and cls._cached_reaper_ids:
            return
        reaper_ids: set[int] = set()
        candidates = set(AgentArray.GetAllyArray())
        candidates.update(AgentArray.GetNeutralArray())
        candidates.update(AgentArray.GetNPCMinipetArray())
        candidates.update(AgentArray.GetSpiritPetArray())

        # One-time dump of all candidate agent names
        if not cls._reaper_scan_logged:
            cls._reaper_scan_logged = True
            ally_count = len(AgentArray.GetAllyArray())
            neutral_count = len(AgentArray.GetNeutralArray())
            npc_count = len(AgentArray.GetNPCMinipetArray())
            spirit_count = len(AgentArray.GetSpiritPetArray())
            cls._debug_log("Scan", f"Arrays: ally={ally_count} neutral={neutral_count} npc={npc_count} spirit={spirit_count} total_candidates={len(candidates)}")
            sample_names = []
            for agent_id in list(candidates)[:30]:
                if Agent.IsValid(agent_id):
                    name = str(Agent.GetNameByID(agent_id) or "").strip()
                    sample_names.append(f"{agent_id}='{name}'")
            cls._debug_log("Scan", f"Sample agents: {', '.join(sample_names)}")

        for agent_id in candidates:
            if not Agent.IsValid(agent_id):
                continue
            name = str(Agent.GetNameByID(agent_id) or "").strip().lower()
            if any(m in name for m in cls._REAPER_NAME_MATCHERS):
                reaper_ids.add(int(agent_id))
        cls._cached_reaper_ids = reaper_ids

        if not cls._reaper_scan_logged or reaper_ids:
            cls._debug_log("Reapers", f"Found {len(reaper_ids)} reapers: {reaper_ids}")

        cls._reaper_id_refresh_timer.Reset()

    @classmethod
    def _effective_reaper_ids(cls) -> set[int]:
        return set(cls._cached_reaper_ids).union(cls._learned_reaper_ids)

    @classmethod
    def _reaper_candidate_agent_ids(cls) -> set[int]:
        candidates = set(AgentArray.GetAllyArray())
        candidates.update(AgentArray.GetNeutralArray())
        candidates.update(AgentArray.GetNPCMinipetArray())
        candidates.update(AgentArray.GetSpiritPetArray())
        return {int(x) for x in candidates}

    @classmethod
    def _party_member_agent_ids(cls) -> set[int]:
        ids: set[int] = set()
        for player in Party.GetPlayers():
            login_number = int(getattr(player, "login_number", 0) or 0)
            if login_number <= 0:
                continue
            agent_id = int(Party.Players.GetAgentIDByLoginNumber(login_number) or 0)
            if agent_id > 0:
                ids.add(agent_id)
        for hero in Party.GetHeroes():
            agent_id = int(getattr(hero, "agent_id", 0) or 0)
            if agent_id > 0:
                ids.add(agent_id)
        for henchman in Party.GetHenchmen():
            agent_id = int(getattr(henchman, "agent_id", 0) or 0)
            if agent_id > 0:
                ids.add(agent_id)
        return ids

    @classmethod
    def _skill_matches(
        cls,
        skill_id: int,
        id_set: set[int],
        name_candidates: tuple[str, ...],
    ) -> bool:
        """Return True when skill_id is in id_set or matches a candidate by normalised name."""
        if int(skill_id) in id_set:
            return True
        skill_name = str(GLOBAL_CACHE.Skill.GetName(int(skill_id)) or "").strip().lower().replace("_", " ")
        if not skill_name:
            return False
        return any(c.lower().replace("_", " ") in skill_name for c in name_candidates)

    @classmethod
    def _set_mode(cls, mode: str, now_ms: float) -> None:
        """Update the shared mode, respecting the debounce window for mode flips."""
        if cls._shared_mode is None or cls._shared_mode == mode:
            cls._shared_mode = mode
            cls._shared_mode_locked_until_ms = now_ms + cls.MODE_SWITCH_DEBOUNCE_MS
            return
        if now_ms >= cls._shared_mode_locked_until_ms:
            cls._shared_mode = mode
            cls._shared_mode_locked_until_ms = now_ms + cls.MODE_SWITCH_DEBOUNCE_MS

    @classmethod
    def _log_candidate(cls, ts: int, caster_id: int, skill_id: int, kind: str) -> None:
        signature = (int(ts), int(caster_id), int(skill_id))
        if cls._last_logged_candidate_signature == signature:
            return
        cls._last_logged_candidate_signature = signature
        try:
            import Py4GW
            caster_name = str(Agent.GetNameByID(int(caster_id)) or "<unknown>").strip() if Agent.IsValid(int(caster_id)) else "<invalid>"
            skill_name  = str(GLOBAL_CACHE.Skill.GetName(int(skill_id)) or "<unknown>").strip()
            Py4GW.Console.Log(
                "AnyDhuum",
                f"Detected {kind}: ts={ts} caster={caster_id} ('{caster_name}') skill={skill_id} ('{skill_name}')",
                Py4GW.Console.MessageType.Info,
            )
        except Exception:
            pass

    # ── Public API ────────────────────────────────────────────────────────────

    @classmethod
    def refresh(cls) -> None:
        """Poll the CombatEvents stream and update the shared mode from reaper casts.

        Throttled to at most once every 250 ms. Called automatically by
        is_dhuums_rest_mode / is_ghostly_fury_mode before reading the mode.

        Steps:
          1. Walk the last 80 combat events newest-first.
          2. Filter to skill-activation event types.
          3. Check each event against the Dhuum's Rest and Ghostly Fury candidate sets.
          4. When the caster is a confirmed Reaper, update the mode and return.
          5. Fallback learning: a non-player, non-party ally that casts a candidate
             skill is promoted to the learned-reaper set for future polls.
        """
        cls._ensure_initialized()
        cls._refresh_reaper_ids()
        if cls._event_refresh_timer is None or not cls._event_refresh_timer.IsExpired():
            return
        cls._event_refresh_timer.Reset()

        effective_ids = cls._effective_reaper_ids()
        now_ms        = time.monotonic() * 1000.0
        player_id     = int(Player.GetAgentID())
        recent_skills        = CombatEvents.GetRecentSkills(80)
        candidate_agent_ids  = cls._reaper_candidate_agent_ids()
        party_member_ids     = cls._party_member_agent_ids()

        # Periodic event scan debug (every 10s)
        if cls._event_scan_log_timer is None:
            cls._event_scan_log_timer = ThrottledTimer(10000)
            cls._event_scan_log_timer.Reset()
        if cls._event_scan_log_timer.IsExpired():
            cls._event_scan_log_timer.Reset()
            activation_events = [
                (int(ts), int(cid), int(sid), int(et))
                for ts, cid, sid, _, et in recent_skills
                if int(et) in cls._ACTIVATION_EVENT_TYPES
            ]
            cls._debug_log("Events", f"total={len(recent_skills)} activations={len(activation_events)} effective_reapers={effective_ids} learned={cls._learned_reaper_ids} mode={cls._shared_mode}")
            cls._debug_log("SkillIDs", f"drest_ids={cls.dhuums_rest_skill_ids} fury_ids={cls.ghostly_fury_skill_ids}")
            # Log first few activation events with names
            for ts_i, cid_i, sid_i, et_i in activation_events[:5]:
                try:
                    cname = str(Agent.GetNameByID(cid_i) or "?").strip() if Agent.IsValid(cid_i) else "?"
                    sname = str(GLOBAL_CACHE.Skill.GetName(sid_i) or "?").strip()
                    in_eff = cid_i in effective_ids
                    is_party = cid_i in party_member_ids
                    cls._debug_log("Evt", f"caster={cid_i}('{cname}') skill={sid_i}('{sname}') type={et_i} reaper={in_eff} party={is_party}")
                except Exception:
                    pass

        for ts, caster_id, skill_id, _, event_type in reversed(recent_skills):
            if int(event_type) not in cls._ACTIVATION_EVENT_TYPES:
                continue
            caster_id_int = int(caster_id)
            skill_id_int  = int(skill_id)
            is_drest = cls._skill_matches(skill_id_int, cls.dhuums_rest_skill_ids,  cls._DHUUMS_REST_CANDIDATES)
            is_fury  = cls._skill_matches(skill_id_int, cls.ghostly_fury_skill_ids, cls._GHOSTLY_FURY_CANDIDATES)
            if not is_drest and not is_fury:
                continue
            # Fallback learning: unknown ally casting a candidate skill → promoted to reaper set
            if (
                caster_id_int in candidate_agent_ids
                and caster_id_int != player_id
                and caster_id_int not in party_member_ids
                and caster_id_int not in effective_ids
            ):
                cls._learned_reaper_ids.add(caster_id_int)
                effective_ids.add(caster_id_int)
            if caster_id_int not in effective_ids:
                continue
            if is_drest:
                cls._log_candidate(int(ts), caster_id_int, skill_id_int, "_DHUUMS_REST_CANDIDATES")
                cls._set_mode(cls.MODE_DREST, now_ms)
                return
            if is_fury:
                cls._log_candidate(int(ts), caster_id_int, skill_id_int, "_GHOSTLY_FURY_CANDIDATES")
                cls._set_mode(cls.MODE_FURY, now_ms)
                return

    @classmethod
    def is_dhuums_rest_mode(cls) -> bool:
        """Return True when the most recent confirmed Reaper cast was Dhuum's Rest."""
        cls.refresh()
        return cls._shared_mode == cls.MODE_DREST

    @classmethod
    def is_ghostly_fury_mode(cls) -> bool:
        """Return True when the most recent confirmed Reaper cast was Ghostly Fury."""
        cls.refresh()
        return cls._shared_mode == cls.MODE_FURY
