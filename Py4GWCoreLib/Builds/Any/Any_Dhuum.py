import time

from Py4GWCoreLib import Agent, AgentArray, BuildMgr, GLOBAL_CACHE, Party, Player, Profession, Range, Routines, Skill, ThrottledTimer
#from Py4GWCoreLib.CombatEvents import CombatEvents as CombatEvents, EventType
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.Builds.Skills.any.PvE import PvE


class _DhuumModeTracker:
    """Tracks Reaper casts and exposes a lightweight shared mode for Dhuum skills.

    Aligned with Sources/oazix/CustomBehaviors/specifics/underworld/reaper_mode_tracker.py.
    """

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
        #EventType.SKILL_ACTIVATED,
        #EventType.ATTACK_SKILL_ACTIVATED,
        #EventType.INSTANT_SKILL_ACTIVATED,
    )

    # Skill name candidates matching the CB reaper_mode_tracker
    _DHUUMS_REST_CANDIDATES = (
        "Dhuums_Rest_Reaper_skill",
    )
    _GHOSTLY_FURY_CANDIDATES = (
        "Ghostly_Fury_Reaper_skill",
    )

    _shared_mode: str | None = None
    _shared_mode_locked_until_ms: float = 0.0

    _reaper_refresh_timer: ThrottledTimer | None = None
    _event_refresh_timer: ThrottledTimer | None = None

    _cached_reaper_ids: set[int] = set()
    _learned_reaper_ids: set[int] = set()

    _dhuums_rest_skill_ids: set[int] = set()
    _ghostly_fury_skill_ids: set[int] = set()

    _cached_reaper_candidate_ids: set[int] = set()
    _reaper_candidate_timer: ThrottledTimer | None = None
    _cached_party_member_ids: set[int] = set()
    _party_member_timer: ThrottledTimer | None = None

    _skill_name_cache: dict[int, str] = {}

    @classmethod
    def _ensure_timers(cls) -> None:
        if cls._reaper_refresh_timer is None:
            cls._reaper_refresh_timer = ThrottledTimer(1200)
            cls._reaper_refresh_timer.Reset()

        if cls._event_refresh_timer is None:
            cls._event_refresh_timer = ThrottledTimer(250)
            cls._event_refresh_timer.Reset()

        if cls._reaper_candidate_timer is None:
            cls._reaper_candidate_timer = ThrottledTimer(1200)
            cls._reaper_candidate_timer.Reset()

        if cls._party_member_timer is None:
            cls._party_member_timer = ThrottledTimer(2000)
            cls._party_member_timer.Reset()

        # Resolve reaper skill IDs (matching CB fallback IDs)
        if not cls._dhuums_rest_skill_ids:
            for name in cls._DHUUMS_REST_CANDIDATES:
                try:
                    skill_id = int(Skill.GetID(name))
                except Exception:
                    skill_id = 0
                if skill_id > 0:
                    cls._dhuums_rest_skill_ids.add(skill_id)
            cls._dhuums_rest_skill_ids.add(3079)

        if not cls._ghostly_fury_skill_ids:
            for name in cls._GHOSTLY_FURY_CANDIDATES:
                try:
                    skill_id = int(Skill.GetID(name))
                except Exception:
                    skill_id = 0
                if skill_id > 0:
                    cls._ghostly_fury_skill_ids.add(skill_id)
            cls._ghostly_fury_skill_ids.add(3136)

    @classmethod
    def _refresh_reaper_ids(cls) -> None:
        cls._ensure_timers()
        if cls._reaper_refresh_timer is None:
            return
        if not cls._reaper_refresh_timer.IsExpired() and cls._cached_reaper_ids:
            return

        reaper_ids: set[int] = set()
        for agent_id in cls._get_reaper_candidate_agent_ids():
            name = str(Agent.GetNameByID(agent_id) or "").strip().lower()
            if any(matcher in name for matcher in cls.REAPER_NAME_MATCHERS):
                reaper_ids.add(int(agent_id))

        cls._cached_reaper_ids = cls._cached_reaper_ids.union(reaper_ids)
        cls._reaper_refresh_timer.Reset()

    @classmethod
    def _get_reaper_candidate_agent_ids(cls) -> set[int]:
        if cls._reaper_candidate_timer is not None and not cls._reaper_candidate_timer.IsExpired() and cls._cached_reaper_candidate_ids:
            return cls._cached_reaper_candidate_ids
        candidates = set(AgentArray.GetAllyArray())
        candidates.update(AgentArray.GetNeutralArray())
        candidates.update(AgentArray.GetNPCMinipetArray())
        candidates.update(AgentArray.GetSpiritPetArray())
        cls._cached_reaper_candidate_ids = {int(x) for x in candidates}
        if cls._reaper_candidate_timer is not None:
            cls._reaper_candidate_timer.Reset()
        return cls._cached_reaper_candidate_ids

    @classmethod
    def _get_party_member_agent_ids(cls) -> set[int]:
        if cls._party_member_timer is not None and not cls._party_member_timer.IsExpired() and cls._cached_party_member_ids:
            return cls._cached_party_member_ids
        party_ids: set[int] = set()
        for player in Party.GetPlayers():
            login_number = int(getattr(player, "login_number", 0) or 0)
            if login_number <= 0:
                continue
            agent_id = int(Party.Players.GetAgentIDByLoginNumber(login_number) or 0)
            if agent_id > 0:
                party_ids.add(agent_id)
        for hero in Party.GetHeroes():
            agent_id = int(getattr(hero, "agent_id", 0) or 0)
            if agent_id > 0:
                party_ids.add(agent_id)
        for henchman in Party.GetHenchmen():
            agent_id = int(getattr(henchman, "agent_id", 0) or 0)
            if agent_id > 0:
                party_ids.add(agent_id)
        cls._cached_party_member_ids = party_ids
        if cls._party_member_timer is not None:
            cls._party_member_timer.Reset()
        return party_ids

    @classmethod
    def _skill_matches(cls, skill_id: int, id_set: set[int], name_candidates: tuple[str, ...]) -> bool:
        if int(skill_id) in id_set:
            return True
        skill_name = cls._skill_name_cache.get(int(skill_id))
        if skill_name is None:
            skill_name = str(GLOBAL_CACHE.Skill.GetName(int(skill_id)) or "").strip().lower().replace("_", " ")
            cls._skill_name_cache[int(skill_id)] = skill_name
        if not skill_name:
            return False
        return any(c.lower().replace("_", " ") in skill_name for c in name_candidates)

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
    def refresh(cls) -> None:
        cls._ensure_timers()
        cls._refresh_reaper_ids()

        if cls._event_refresh_timer is None or not cls._event_refresh_timer.IsExpired():
            return
        cls._event_refresh_timer.Reset()

        effective_ids = set(cls._cached_reaper_ids).union(cls._learned_reaper_ids)
        now_ms = time.monotonic() * 1000.0
        player_id = int(Player.GetAgentID())
        recent_skills = CombatEvents.GetRecentSkills(80)
        candidate_agent_ids = cls._get_reaper_candidate_agent_ids()
        party_member_ids = cls._get_party_member_agent_ids()

        for ts, caster_id, skill_id, _, event_type in reversed(recent_skills):
            if int(event_type) not in cls.ACTIVATION_EVENT_TYPES:
                continue
            caster_id_int = int(caster_id)
            skill_id_int = int(skill_id)

            is_drest = cls._skill_matches(skill_id_int, cls._dhuums_rest_skill_ids, cls._DHUUMS_REST_CANDIDATES)
            is_fury = cls._skill_matches(skill_id_int, cls._ghostly_fury_skill_ids, cls._GHOSTLY_FURY_CANDIDATES)
            if not is_drest and not is_fury:
                continue

            # Fallback learning: unknown non-party ally casting a candidate → promoted to reaper
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
                cls._set_mode(cls.MODE_DREST, now_ms)
                return
            if is_fury:
                cls._set_mode(cls.MODE_FURY, now_ms)
                return

    @classmethod
    def is_dhuums_rest_mode(cls) -> bool:
        cls.refresh()
        return cls._shared_mode == cls.MODE_DREST

    @classmethod
    def is_ghostly_fury_mode(cls) -> bool:
        cls.refresh()
        return cls._shared_mode == cls.MODE_FURY


class Any_Dhuum(BuildMgr):
    """HeroAI BuildMgr adaptation of the CustomBehavior Dhuum utility build."""

    TEMPLATE_CODE = "OQBDAqwDSPwQwRwSwTwAAAAAAA"

    def __init__(self, match_only: bool = False):
        # Skill name resolution aligned with CB CustomSkill names
        self.unyielding_aura_id = self._resolve_skill_id(("Unyielding_Aura",))
        self.dhuums_rest_id = self._resolve_skill_id(("Dhuum's_Rest",), fallback=3087)
        self.spiritual_healing_id = self._resolve_skill_id(("Spiritual_Healing",), fallback=3088)
        self.encase_skeletal_id = self._resolve_skill_id(("Encase_Skeletal",), fallback=3089)
        self.reversal_of_death_id = self._resolve_skill_id(("Reversal_of_Death",), fallback=3090)
        self.ghostly_fury_id = self._resolve_skill_id(("Ghostly_Fury",), fallback=3136)

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

        self.minimum_required_match = 1

        if match_only:
            return

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

        drest_mode = _DhuumModeTracker.is_dhuums_rest_mode()
        fury_mode = _DhuumModeTracker.is_ghostly_fury_mode()

        # When no Reaper activity detected (e.g. Dhuum fight — no Reapers
        # present), default Dhuum's Rest to active. Matches CB logic.
        no_mode = _DhuumModeTracker._shared_mode is None
        drest_active = drest_mode or no_mode
        fury_active = fury_mode

        # Priority order matching CB scores (highest first)
        if (yield from self._pve.Unyielding_Aura()):
            return True
        if (yield from self._pve.Dhuums_Rest(is_active=drest_active)):
            return True
        if (yield from self._pve.Ghostly_Fury(is_active=fury_active)):
            return True
        if (yield from self._pve.Reversal_of_Death()):
            return True
        if (yield from self._pve.Spiritual_Healing()):
            return True
        return False
