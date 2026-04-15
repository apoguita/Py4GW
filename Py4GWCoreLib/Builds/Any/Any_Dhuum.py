import time

from Py4GWCoreLib import Agent, AgentArray, BuildMgr, GLOBAL_CACHE, Party, Player, Profession, Range, Routines, Skill, ThrottledTimer
from Py4GWCoreLib.CombatEvents import CombatEvents as CombatEvents, EventType
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.Builds.Skills.any.PvE import PvE


class _DhuumModeTracker:
    """Tracks Reaper casts and exposes a lightweight shared mode for Dhuum skills."""

    MODE_DREST = "drest"
    MODE_FURY = "fury"

    MODE_SWITCH_DEBOUNCE_MS = 6000.0

    REAPER_NAME_MATCHERS = (
        "reaper of the bone pits",
        "reaper of the chaos planes",
        "reaper of the forgotten vale",
        "reaper of the ice wastes",
        "reaper of the labyrinth",
        "reaper of the spawning pools",
        "reaper of the twin serpent mountains",
    )

    ACTIVATION_EVENT_TYPES = (
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
    _GHOSTLY_FURY_CANDIDATES = (
        "Ghostly_Fury",
        "Ghostly Fury",
        "Ghostly Fury_reaper_skill",
    )

    _shared_mode: str | None = None
    _shared_mode_locked_until_ms: float = 0.0

    _reaper_refresh_timer: ThrottledTimer | None = None
    _event_refresh_timer: ThrottledTimer | None = None

    _cached_reaper_ids: set[int] = set()
    _learned_reaper_ids: set[int] = set()

    _dhuums_rest_skill_ids: set[int] = set()
    _ghostly_fury_skill_ids: set[int] = set()

    _last_logged_candidate_signature: tuple[int, int, int] | None = None

    @classmethod
    def _ensure_timers(cls) -> None:
        if cls._reaper_refresh_timer is None:
            cls._reaper_refresh_timer = ThrottledTimer(1200)
            cls._reaper_refresh_timer.Reset()

        if cls._event_refresh_timer is None:
            cls._event_refresh_timer = ThrottledTimer(250)
            cls._event_refresh_timer.Reset()

        if len(cls._dhuums_rest_skill_ids) == 0:
            for name in cls._DHUUMS_REST_CANDIDATES:
                try:
                    skill_id = int(Skill.GetID(name))
                except Exception:
                    skill_id = 0
                if skill_id > 0:
                    cls._dhuums_rest_skill_ids.add(skill_id)
            cls._dhuums_rest_skill_ids.update({3079, 3087})

        if len(cls._ghostly_fury_skill_ids) == 0:
            for name in cls._GHOSTLY_FURY_CANDIDATES:
                try:
                    skill_id = int(Skill.GetID(name))
                except Exception:
                    skill_id = 0
                if skill_id > 0:
                    cls._ghostly_fury_skill_ids.add(skill_id)
            cls._ghostly_fury_skill_ids.add(3091)

    @classmethod
    def _refresh_reaper_ids(cls) -> None:
        cls._ensure_timers()
        if cls._reaper_refresh_timer is None:
            return

        if not cls._reaper_refresh_timer.IsExpired() and cls._cached_reaper_ids:
            return

        reaper_ids: set[int] = set()
        candidate_agent_ids = set(AgentArray.GetAllyArray())
        candidate_agent_ids.update(AgentArray.GetNeutralArray())
        candidate_agent_ids.update(AgentArray.GetNPCMinipetArray())
        candidate_agent_ids.update(AgentArray.GetSpiritPetArray())

        for agent_id in candidate_agent_ids:
            name = str(Agent.GetNameByID(agent_id) or "").strip().lower()
            if any(matcher in name for matcher in cls.REAPER_NAME_MATCHERS):
                reaper_ids.add(int(agent_id))

        cls._cached_reaper_ids = reaper_ids
        cls._reaper_refresh_timer.Reset()

    @classmethod
    def _get_reaper_candidate_agent_ids(cls) -> set[int]:
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
        if int(skill_id) in candidate_skill_ids:
            return True
        skill_name = str(GLOBAL_CACHE.Skill.GetName(int(skill_id)) or "").strip().lower().replace("_", " ")
        if not skill_name:
            return False
        normalized_candidates = [name.lower().replace("_", " ") for name in candidate_names]
        return any(candidate in skill_name for candidate in normalized_candidates)

    @classmethod
    def _log_candidate_detection(cls, ts: int, caster_id: int, skill_id: int, candidate_type: str) -> None:
        signature = (int(ts), int(caster_id), int(skill_id))
        if cls._last_logged_candidate_signature == signature:
            return
        cls._last_logged_candidate_signature = signature
        try:
            import Py4GW
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
    def _set_mode(cls, mode: str, now_ms: float) -> None:
        if cls._shared_mode is None or cls._shared_mode == mode:
            cls._shared_mode = mode
            cls._shared_mode_locked_until_ms = now_ms + cls.MODE_SWITCH_DEBOUNCE_MS
            return

        if now_ms >= cls._shared_mode_locked_until_ms:
            cls._shared_mode = mode
            cls._shared_mode_locked_until_ms = now_ms + cls.MODE_SWITCH_DEBOUNCE_MS

    @classmethod
    def refresh_mode_from_reaper_events(cls) -> None:
        cls._ensure_timers()
        cls._refresh_reaper_ids()

        if cls._event_refresh_timer is None:
            return
        if not cls._event_refresh_timer.IsExpired():
            return

        cls._event_refresh_timer.Reset()

        effective_reaper_ids = set(cls._cached_reaper_ids).union(cls._learned_reaper_ids)
        now_ms = time.monotonic() * 1000.0
        player_id = int(Player.GetAgentID())

        recent_skills = CombatEvents.GetRecentSkills(80)

        reaper_candidate_agent_ids = cls._get_reaper_candidate_agent_ids()
        party_member_agent_ids = cls._get_party_member_agent_ids()

        for ts, caster_id, skill_id, _, event_type in reversed(recent_skills):
            if int(event_type) not in cls.ACTIVATION_EVENT_TYPES:
                continue

            caster_id_int = int(caster_id)
            skill_id_int = int(skill_id)

            is_drest_candidate = cls._skill_id_matches_candidates(
                skill_id_int, cls._dhuums_rest_skill_ids, cls._DHUUMS_REST_CANDIDATES
            )
            is_fury_candidate = cls._skill_id_matches_candidates(
                skill_id_int, cls._ghostly_fury_skill_ids, cls._GHOSTLY_FURY_CANDIDATES
            )
            if not is_drest_candidate and not is_fury_candidate:
                continue

            if (
                caster_id_int in reaper_candidate_agent_ids
                and caster_id_int != player_id
                and caster_id_int not in party_member_agent_ids
                and caster_id_int not in effective_reaper_ids
            ):
                cls._learned_reaper_ids.add(caster_id_int)
                effective_reaper_ids.add(caster_id_int)

            if caster_id_int not in effective_reaper_ids:
                continue

            if is_drest_candidate:
                cls._log_candidate_detection(int(ts), caster_id_int, skill_id_int, "_DHUUMS_REST_CANDIDATES")
                cls._set_mode(cls.MODE_DREST, now_ms)
                return
            if is_fury_candidate:
                cls._log_candidate_detection(int(ts), caster_id_int, skill_id_int, "_GHOSTLY_FURY_CANDIDATES")
                cls._set_mode(cls.MODE_FURY, now_ms)
                return

    @classmethod
    def is_dhuums_rest_mode(cls) -> bool:
        cls.refresh_mode_from_reaper_events()
        return cls._shared_mode == cls.MODE_DREST

    @classmethod
    def is_ghostly_fury_mode(cls) -> bool:
        cls.refresh_mode_from_reaper_events()
        return cls._shared_mode == cls.MODE_FURY


class Any_Dhuum(BuildMgr):
    """HeroAI BuildMgr adaptation of the CustomBehavior Dhuum utility build."""

    TEMPLATE_CODE = "OQBDAqwDSPwQwRwSwTwAAAAAAA"

    def __init__(self, match_only: bool = False):
        self.unyielding_aura_id = self._resolve_skill_id(("Unyielding_Aura", "Unyielding Aura"))
        self.dhuums_rest_id = self._resolve_skill_id(("Dhuum_s_Rest", "Dhuum's Rest", "Dhuums_Rest"), fallback=3087)
        self.spiritual_healing_id = self._resolve_skill_id(("Spiritual_Healing", "Spiritual Healing"), fallback=3088)
        self.encase_skeletal_id = self._resolve_skill_id(("Encase_Skeletal", "Encase Skeletal"), fallback=3089)
        self.reversal_of_death_id = self._resolve_skill_id(("Reversal_of_Death", "Reversal of Death"), fallback=3090)
        self.ghostly_fury_id = self._resolve_skill_id(("Ghostly_Fury", "Ghostly Fury"), fallback=3091)

        required_candidates = [
            self.unyielding_aura_id,
            self.dhuums_rest_id,
            self.spiritual_healing_id,
            self.reversal_of_death_id,
            self.ghostly_fury_id,
        ]
        required_skills = [sid for sid in required_candidates if sid > 0]

        optional_candidates = [self.encase_skeletal_id]
        optional_skills = [sid for sid in optional_candidates if sid > 0 and sid not in required_skills]

        super().__init__(
            name="Any Dhuum",
            required_primary=Profession(0),
            required_secondary=Profession(0),
            template_code=self.TEMPLATE_CODE,
            required_skills=required_skills,
            optional_skills=optional_skills,
        )

        # Match when at least one known Dhuum-bar skill is present.
        self.minimum_required_match = 1

        if match_only:
            return

        # Register resolved skill IDs into the shared tracker sets.
        if self.dhuums_rest_id > 0:
            _DhuumModeTracker._dhuums_rest_skill_ids.add(self.dhuums_rest_id)
        if self.ghostly_fury_id > 0:
            _DhuumModeTracker._ghostly_fury_skill_ids.add(self.ghostly_fury_id)
        _DhuumModeTracker._ensure_timers()

        self._pve = PvE(self)
        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)

    @staticmethod
    def _resolve_skill_id(names: tuple[str, ...], fallback: int = 0) -> int:
        for name in names:
            try:
                skill_id = int(Skill.GetID(name))
            except Exception:
                skill_id = 0
            if skill_id > 0:
                return skill_id
        return int(fallback)

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        # Priority order matching CB scores (highest first):
        # Unyielding Aura — HeroAI-specific, highest priority
        if (yield from self._pve.Unyielding_Aura()):
            return True
        # Dhuum's Rest (score 97) — mirror Reaper phase
        if (yield from self._pve.Dhuums_Rest(is_active=_DhuumModeTracker.is_dhuums_rest_mode())):
            return True
        # Ghostly Fury (score 97) — mirror Reaper phase
        if (yield from self._pve.Ghostly_Fury(is_active=_DhuumModeTracker.is_ghostly_fury_mode())):
            return True
        # Reversal of Death (score 94) — death penalty removal
        if (yield from self._pve.Reversal_of_Death()):
            return True
        # Spiritual Healing (score 90) — heal low HP allies
        if (yield from self._pve.Spiritual_Healing()):
            return True
        # Encase Skeletal intentionally left passive (same as CB)
        return False
