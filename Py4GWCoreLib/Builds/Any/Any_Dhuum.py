import time

from Py4GWCoreLib import Agent, AgentArray, BuildMgr, CombatEvents, GLOBAL_CACHE, Party, Player, Profession, Range, Routines, Skill, ThrottledTimer
from Py4GWCoreLib.CombatEvents import EventType
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build


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

    DHUUMS_REST_IDS = {3079, 3087}
    GHOSTLY_FURY_IDS = {3091}

    _shared_mode: str | None = None
    _shared_mode_locked_until_ms: float = 0.0

    _reaper_refresh_timer: ThrottledTimer | None = None
    _event_refresh_timer: ThrottledTimer | None = None

    _cached_reaper_ids: set[int] = set()
    _learned_reaper_ids: set[int] = set()

    @classmethod
    def _ensure_timers(cls) -> None:
        if cls._reaper_refresh_timer is None:
            cls._reaper_refresh_timer = ThrottledTimer(1200)
            cls._reaper_refresh_timer.Reset()

        if cls._event_refresh_timer is None:
            cls._event_refresh_timer = ThrottledTimer(250)
            cls._event_refresh_timer.Reset()

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

        CombatEvents.update()
        recent_skills = CombatEvents.get_recent_skills(80)

        for _, caster_id, skill_id, _, event_type in reversed(recent_skills):
            if int(event_type) not in cls.ACTIVATION_EVENT_TYPES:
                continue

            caster_id_int = int(caster_id)
            skill_id_int = int(skill_id)

            # Fallback learning when name matching fails (locale/encoding edge cases).
            if (
                caster_id_int not in effective_reaper_ids
                and caster_id_int != player_id
                and caster_id_int in set(AgentArray.GetAllyArray()).union(AgentArray.GetNeutralArray())
                and skill_id_int in cls.DHUUMS_REST_IDS.union(cls.GHOSTLY_FURY_IDS)
            ):
                cls._learned_reaper_ids.add(caster_id_int)
                effective_reaper_ids.add(caster_id_int)

            if caster_id_int not in effective_reaper_ids:
                continue

            if skill_id_int in cls.DHUUMS_REST_IDS:
                cls._set_mode(cls.MODE_DREST, now_ms)
                return
            if skill_id_int in cls.GHOSTLY_FURY_IDS:
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

    def _can_use(self, skill_id: int) -> bool:
        return skill_id > 0 and self.IsSkillEquipped(skill_id)

    def _get_lowest_hp_ally(self, max_range: float, hp_below: float) -> int:
        me_x, me_y = Player.GetXY()
        candidates = AgentArray.Filter.ByCondition(
            AgentArray.GetAllyArray(),
            lambda aid: Agent.IsAlive(aid)
            and Agent.GetHealth(aid) < hp_below
            and ((Agent.GetXY(aid)[0] - me_x) ** 2 + (Agent.GetXY(aid)[1] - me_y) ** 2) ** 0.5 <= max_range,
        )
        if not candidates:
            return 0

        candidates.sort(key=lambda aid: (Agent.GetHealth(aid), ((Agent.GetXY(aid)[0] - me_x) ** 2 + (Agent.GetXY(aid)[1] - me_y) ** 2) ** 0.5))
        return int(candidates[0])

    @staticmethod
    def _same_party_and_map(self_account, other_account) -> bool:
        return (
            int(self_account.AgentPartyData.PartyID) == int(other_account.AgentPartyData.PartyID)
            and int(self_account.AgentData.Map.MapID) == int(other_account.AgentData.Map.MapID)
            and int(self_account.AgentData.Map.Region) == int(other_account.AgentData.Map.Region)
            and int(self_account.AgentData.Map.District) == int(other_account.AgentData.Map.District)
            and int(self_account.AgentData.Map.Language) == int(other_account.AgentData.Map.Language)
        )

    def _get_target_with_highest_death_penalty(self) -> int:
        self_email = Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(self_email)
        if self_account is None:
            return 0

        morale_by_agent: dict[int, int] = {}
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if not account.IsSlotActive or account.IsIsolated:
                continue
            if not self._same_party_and_map(self_account, account):
                continue
            agent_id = int(account.AgentData.AgentID or 0)
            if agent_id <= 0:
                continue
            morale_by_agent[agent_id] = int(account.AgentData.Morale)

        if not morale_by_agent:
            return 0

        me_x, me_y = Player.GetXY()
        best_target = 0
        best_death_penalty = 0
        best_distance = float("inf")

        for ally_id in AgentArray.GetAllyArray():
            ally_id = int(ally_id)
            if ally_id == int(Player.GetAgentID()):
                continue
            if not Agent.IsAlive(ally_id):
                continue

            morale = int(morale_by_agent.get(ally_id, 100))
            death_penalty = max(0, 100 - morale)
            if death_penalty <= 0:
                continue

            ax, ay = Agent.GetXY(ally_id)
            distance = ((ax - me_x) ** 2 + (ay - me_y) ** 2) ** 0.5
            if distance > Range.Spellcast.value * 1.2:
                continue

            if death_penalty > best_death_penalty or (
                death_penalty == best_death_penalty and distance < best_distance
            ):
                best_target = ally_id
                best_death_penalty = death_penalty
                best_distance = distance

        return int(best_target)

    def _get_enemy_target_for_fury(self) -> int:
        if self.priority_target and Agent.IsAlive(self.priority_target):
            return int(self.priority_target)

        me_x, me_y = Player.GetXY()
        enemies = AgentArray.Filter.ByCondition(
            AgentArray.GetEnemyArray(),
            lambda aid: Agent.IsAlive(aid)
            and ((Agent.GetXY(aid)[0] - me_x) ** 2 + (Agent.GetXY(aid)[1] - me_y) ** 2) ** 0.5 <= Range.Spellcast.value,
        )
        if not enemies:
            return 0

        enemies.sort(key=lambda aid: ((Agent.GetXY(aid)[0] - me_x) ** 2 + (Agent.GetXY(aid)[1] - me_y) ** 2) ** 0.5)
        return int(enemies[0])

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        # Highest priority: keep UA utility available.
        if self._can_use(self.unyielding_aura_id):
            ua_target = self.ResolveAllyTarget(self.unyielding_aura_id)
            if ua_target and (yield from self.CastSkillIDAndRestoreTarget(self.unyielding_aura_id, ua_target)):
                return True

        # Heal pressure handling.
        if self._can_use(self.spiritual_healing_id):
            sh_target = self._get_lowest_hp_ally(Range.Spellcast.value * 1.2, 0.70)
            if sh_target and (yield from self.CastSkillIDAndRestoreTarget(self.spiritual_healing_id, sh_target)):
                return True

        if self._can_use(self.reversal_of_death_id):
            rod_target = self._get_target_with_highest_death_penalty()
            if rod_target and (yield from self.CastSkillIDAndRestoreTarget(self.reversal_of_death_id, rod_target)):
                return True

        # Event-driven Dhuum phase mirroring.
        if self._can_use(self.dhuums_rest_id) and _DhuumModeTracker.is_dhuums_rest_mode():
            if (yield from self.CastSkillID(self.dhuums_rest_id)):
                return True

        if self._can_use(self.ghostly_fury_id) and _DhuumModeTracker.is_ghostly_fury_mode():
            fury_target = self._get_enemy_target_for_fury()
            if fury_target and (yield from self.CastSkillIDAndRestoreTarget(self.ghostly_fury_id, fury_target)):
                return True

        # Encase Skeletal intentionally left passive for now (same as CB pending utility).
        return False
