from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Range, Routines
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["PvE"]


class PvE:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def _get_enemy_array(self, max_distance: float) -> list[int]:
        from Py4GWCoreLib import Agent, AgentArray, Player, Routines

        player_x, player_y = Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, max_distance)
        return AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: Agent.IsValid(agent_id) and not Agent.IsDead(agent_id),
        )

    def _get_cluster_score(self, agent_id: int, cluster_radius: float) -> int:
        from Py4GWCoreLib import Agent, AgentArray, Routines

        if not agent_id or cluster_radius <= 0:
            return 0

        target_x, target_y = Agent.GetXY(agent_id)
        nearby_enemies = Routines.Agents.GetFilteredEnemyArray(target_x, target_y, cluster_radius)
        nearby_enemies = AgentArray.Filter.ByCondition(
            nearby_enemies,
            lambda enemy_id: Agent.IsValid(enemy_id) and not Agent.IsDead(enemy_id),
        )
        return max(0, len(nearby_enemies) - 1)

    def _pick_best_target(self, agent_ids: list[int], cluster_radius: float) -> int:
        from Py4GWCoreLib import Agent, Player, Utils

        if not agent_ids:
            return 0

        player_pos = Player.GetXY()
        scored_targets = [
            (
                self._get_cluster_score(agent_id, cluster_radius),
                Utils.Distance(player_pos, Agent.GetXY(agent_id)),
                agent_id,
            )
            for agent_id in agent_ids
        ]
        scored_targets.sort(key=lambda item: (-item[0], item[1]))
        return scored_targets[0][2]

    def Air_of_Superiority(self) -> BuildCoroutine:
        from Py4GWCoreLib import Player, GLOBAL_CACHE

        air_of_superiority_id: int = Skill.GetID("Air_of_Superiority")
        refresh_window_ms = 2000

        if not self.build.IsSkillEquipped(air_of_superiority_id):
            return False
        if Routines.Checks.Agents.HasEffect(Player.GetAgentID(), air_of_superiority_id):
            remaining_duration = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(
                Player.GetAgentID(),
                air_of_superiority_id,
            )
            if remaining_duration > refresh_window_ms:
                return False

        return (yield from self.build.CastSkillID(
            skill_id=air_of_superiority_id,
            log=False,
            aftercast_delay=250,
        ))

    def Cry_of_Pain(self, allow_hex_fallback: bool = True) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, GLOBAL_CACHE

        cry_of_pain_id: int = Skill.GetID("Cry_of_Pain")
        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(cry_of_pain_id) or Range.Nearby.value

        def _has_mesmer_hex(agent_id: int) -> bool:
            if not agent_id or not Agent.IsHexed(agent_id):
                return False
            for effect_skill_id in self.build.GetEffectAndBuffIds(agent_id):
                if not GLOBAL_CACHE.Skill.Flags.IsHex(effect_skill_id):
                    continue
                profession_id, _ = GLOBAL_CACHE.Skill.GetProfession(effect_skill_id)
                if profession_id == 8:
                    return True
            return False

        def _is_enemy_using_skill(agent_id: int) -> bool:
            return bool(
                agent_id
                and Agent.IsValid(agent_id)
                and not Agent.IsDead(agent_id)
                and Agent.IsCasting(agent_id)
            )

        if not self.build.IsSkillEquipped(cry_of_pain_id):
            return False

        enemy_array = self._get_enemy_array(Range.Spellcast.value)
        preferred_targets = [
            agent_id for agent_id in enemy_array
            if _is_enemy_using_skill(agent_id) and _has_mesmer_hex(agent_id)
        ]
        target_agent_id = self._pick_best_target(preferred_targets, aoe_range)

        if not target_agent_id:
            fallback_targets = [
                agent_id for agent_id in enemy_array
                if _is_enemy_using_skill(agent_id)
            ]
            target_agent_id = self._pick_best_target(fallback_targets, aoe_range)

        if not target_agent_id and allow_hex_fallback:
            mesmer_hex_targets = [
                agent_id for agent_id in enemy_array
                if _has_mesmer_hex(agent_id)
            ]
            target_agent_id = self._pick_best_target(mesmer_hex_targets, aoe_range)

        if not target_agent_id and allow_hex_fallback:
            hexed_targets = [
                agent_id for agent_id in enemy_array
                if Agent.IsHexed(agent_id)
            ]
            target_agent_id = self._pick_best_target(hexed_targets, aoe_range)

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=cry_of_pain_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def Ebon_Vanguard_Assassin_Support(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent

        evas_id: int = Skill.GetID("Ebon_Vanguard_Assassin_Support")
        cluster_radius = Range.Nearby.value

        def _is_preferred_target(agent_id: int) -> bool:
            return (
                Agent.IsValid(agent_id)
                and not Agent.IsDead(agent_id)
                and (Agent.IsHexed(agent_id) or Agent.IsConditioned(agent_id))
            )

        if not self.build.IsSkillEquipped(evas_id):
            return False

        enemy_array = self._get_enemy_array(Range.Spellcast.value)
        preferred_targets = [
            agent_id for agent_id in enemy_array
            if _is_preferred_target(agent_id)
        ]
        target_agent_id = self._pick_best_target(preferred_targets, cluster_radius)

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=evas_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    # ─── Dhuum Encounter Skills ───────────────────────────────────────────────

    _UW_CHEST_POS = (-13987, 17291)
    _UW_CHEST_RADIUS = 3000.0
    _UW_CHEST_NAME_FRAGMENT = "underworld chest"
    _SPIRIT_FORM_SKILL_ID = 3134
    _SPIRIT_FORM_MIN_COUNT = 1

    # Cache for _resolve_dhuum_skill: (names_tuple, fallback) -> skill_id
    _dhuum_skill_cache: dict[tuple, int] = {}

    # Throttled cache for _is_uw_chest_present
    _chest_present_cache: bool = False
    _chest_present_ts: float = 0.0
    _CHEST_CHECK_INTERVAL: float = 2.0  # seconds

    @staticmethod
    def _resolve_dhuum_skill(*names: str, fallback: int = 0) -> int:
        cache_key = (names, fallback)
        cached = PvE._dhuum_skill_cache.get(cache_key)
        if cached is not None:
            return cached
        for name in names:
            try:
                skill_id = int(Skill.GetID(name))
            except Exception:
                skill_id = 0
            if skill_id > 0:
                PvE._dhuum_skill_cache[cache_key] = skill_id
                return skill_id
        PvE._dhuum_skill_cache[cache_key] = int(fallback)
        return int(fallback)

    @staticmethod
    def _is_uw_chest_present() -> bool:
        import time as _time
        now = _time.monotonic()
        if now - PvE._chest_present_ts < PvE._CHEST_CHECK_INTERVAL:
            return PvE._chest_present_cache
        PvE._chest_present_ts = now
        from Py4GWCoreLib import Agent, AgentArray
        for agent_id in AgentArray.GetAgentArray():
            if not Agent.IsGadget(agent_id):
                continue
            name = (Agent.GetNameByID(agent_id) or "").strip().lower()
            if PvE._UW_CHEST_NAME_FRAGMENT not in name:
                continue
            ax, ay = Agent.GetXY(agent_id)
            cx, cy = PvE._UW_CHEST_POS
            if ((ax - cx) ** 2 + (ay - cy) ** 2) ** 0.5 <= PvE._UW_CHEST_RADIUS:
                PvE._chest_present_cache = True
                return True
        PvE._chest_present_cache = False
        return False

    def _count_spirit_form_accounts(self) -> int:
        return len(self._get_spirit_form_agent_ids())

    def _get_spirit_form_agent_ids(self) -> set[int]:
        from Py4GWCoreLib import GLOBAL_CACHE
        result: set[int] = set()
        for account in (GLOBAL_CACHE.ShMem.GetAllAccountData() or []):
            if not account.IsSlotActive or account.IsIsolated:
                continue
            if not GLOBAL_CACHE.ShMem.SameMapOrPartyAsAccount(account):
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
        from Py4GWCoreLib import GLOBAL_CACHE
        morale_by_agent: dict[int, int] = {}
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if not account.IsSlotActive or account.IsIsolated:
                continue
            if not GLOBAL_CACHE.ShMem.SameMapOrPartyAsAccount(account):
                continue
            agent_id = int(account.AgentData.AgentID or 0)
            if agent_id <= 0:
                continue
            morale_by_agent[agent_id] = int(account.AgentData.Morale)
        return morale_by_agent

    def _get_best_rod_target(self) -> int:
        from Py4GWCoreLib import Agent, AgentArray, Player

        spirit_form_ids = self._get_spirit_form_agent_ids()
        if len(spirit_form_ids) < self._SPIRIT_FORM_MIN_COUNT:
            return 0

        restrict_to_spirit_form = len(spirit_form_ids) <= 2
        morale_map = self._get_morale_by_agent_id()
        if not morale_map:
            return 0

        my_id = int(Player.GetAgentID())
        me_x, me_y = Player.GetXY()

        allies = AgentArray.Filter.ByCondition(
            AgentArray.GetAllyArray(),
            lambda aid: Agent.IsAlive(aid)
            and int(aid) != my_id
            and (not restrict_to_spirit_form or int(aid) in spirit_form_ids)
            and ((Agent.GetXY(aid)[0] - me_x) ** 2 + (Agent.GetXY(aid)[1] - me_y) ** 2) ** 0.5 <= Range.Spellcast.value * 1.4,
        )
        if not allies:
            return 0

        # Sort by HP ascending, then distance ascending (matching CB ordering)
        allies.sort(key=lambda aid: (
            Agent.GetHealth(aid),
            ((Agent.GetXY(aid)[0] - me_x) ** 2 + (Agent.GetXY(aid)[1] - me_y) ** 2) ** 0.5,
        ))

        best_target = 0
        best_penalty = 0
        for ally_id in allies:
            ally_id = int(ally_id)
            morale = int(morale_map.get(ally_id, 100))
            penalty = max(0, 100 - morale)
            if penalty <= 0:
                continue
            if penalty > best_penalty:
                best_target = ally_id
                best_penalty = penalty

        return best_target

    # ─── Dhuum debug helper (throttled per-skill) ─────────────────────────────
    _dhuum_pve_debug_ts: dict[str, float] = {}
    _DHUUM_PVE_DEBUG_INTERVAL: float = 5.0  # seconds

    @staticmethod
    def _dhuum_pve_log(tag: str, msg: str) -> None:
        import time as _t
        now = _t.monotonic()
        last = PvE._dhuum_pve_debug_ts.get(tag, 0.0)
        if now - last < PvE._DHUUM_PVE_DEBUG_INTERVAL:
            return
        PvE._dhuum_pve_debug_ts[tag] = now
        try:
            import Py4GW
            Py4GW.Console.Log("AnyDhuum.PvE", f"[{tag}] {msg}", Py4GW.Console.MessageType.Info)
        except Exception:
            pass

    def Unyielding_Aura(self) -> BuildCoroutine:
        ua_id: int = self._resolve_dhuum_skill("Unyielding_Aura", "Unyielding Aura")
        if not self.build.IsSkillEquipped(ua_id):
            self._dhuum_pve_log("UA", f"Not equipped (id={ua_id})")
            return False
        if self._is_uw_chest_present():
            self._dhuum_pve_log("UA", "UW chest present — skipped")
            return False
        target = self.build.ResolveAllyTarget(ua_id)
        if not target:
            self._dhuum_pve_log("UA", "No valid ally target")
            return False
        self._dhuum_pve_log("UA", f"Casting on target={target}")
        return (yield from self.build.CastSkillIDAndRestoreTarget(ua_id, target))

    def Dhuums_Rest(self, is_active: bool = True) -> BuildCoroutine:
        dhuums_rest_id: int = self._resolve_dhuum_skill("Dhuum_s_Rest", "Dhuum's Rest", "Dhuums_Rest", fallback=3087)
        if not self.build.IsSkillEquipped(dhuums_rest_id):
            self._dhuum_pve_log("DRest", f"Not equipped (id={dhuums_rest_id})")
            return False
        if not is_active:
            self._dhuum_pve_log("DRest", "Reaper not in drest mode")
            return False
        if self._is_uw_chest_present():
            self._dhuum_pve_log("DRest", "UW chest present — skipped")
            return False
        self._dhuum_pve_log("DRest", "Casting (no target needed)")
        return (yield from self.build.CastSkillID(dhuums_rest_id))

    def Ghostly_Fury(self, is_active: bool = True) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, AgentArray, Player

        ghostly_fury_id: int = self._resolve_dhuum_skill("Ghostly_Fury", "Ghostly Fury", fallback=3091)
        if not self.build.IsSkillEquipped(ghostly_fury_id):
            self._dhuum_pve_log("GFury", f"Not equipped (id={ghostly_fury_id})")
            return False
        if not is_active:
            self._dhuum_pve_log("GFury", "Reaper not in fury mode")
            return False
        if self._is_uw_chest_present():
            self._dhuum_pve_log("GFury", "UW chest present — skipped")
            return False

        target = 0
        if hasattr(self.build, "priority_target") and self.build.priority_target:
            pt = int(self.build.priority_target)
            if Agent.IsValid(pt) and Agent.IsAlive(pt):
                me_x, me_y = Player.GetXY()
                tx, ty = Agent.GetXY(pt)
                if ((tx - me_x) ** 2 + (ty - me_y) ** 2) ** 0.5 <= Range.Spellcast.value:
                    target = pt

        if not target:
            me_x, me_y = Player.GetXY()
            enemies = AgentArray.Filter.ByCondition(
                AgentArray.GetEnemyArray(),
                lambda aid: Agent.IsAlive(aid)
                and ((Agent.GetXY(aid)[0] - me_x) ** 2 + (Agent.GetXY(aid)[1] - me_y) ** 2) ** 0.5 <= Range.Spellcast.value,
            )
            if enemies:
                enemies.sort(key=lambda aid: ((Agent.GetXY(aid)[0] - me_x) ** 2 + (Agent.GetXY(aid)[1] - me_y) ** 2) ** 0.5)
                target = int(enemies[0])

        if not target:
            self._dhuum_pve_log("GFury", "No enemy target in range")
            return False
        self._dhuum_pve_log("GFury", f"Casting on target={target}")
        return (yield from self.build.CastSkillIDAndRestoreTarget(ghostly_fury_id, target))

    def Reversal_of_Death(self) -> BuildCoroutine:
        rod_id: int = self._resolve_dhuum_skill("Reversal_of_Death", "Reversal of Death", fallback=3090)
        if not self.build.IsSkillEquipped(rod_id):
            self._dhuum_pve_log("RoD", f"Not equipped (id={rod_id})")
            return False
        if self._is_uw_chest_present():
            self._dhuum_pve_log("RoD", "UW chest present — skipped")
            return False
        target = self._get_best_rod_target()
        if not target:
            self._dhuum_pve_log("RoD", "No penalty target found")
            return False
        self._dhuum_pve_log("RoD", f"Casting on target={target}")
        return (yield from self.build.CastSkillIDAndRestoreTarget(rod_id, target))

    def Spiritual_Healing(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, AgentArray, Player

        sh_id: int = self._resolve_dhuum_skill("Spiritual_Healing", "Spiritual Healing", fallback=3088)
        if not self.build.IsSkillEquipped(sh_id):
            self._dhuum_pve_log("SHeal", f"Not equipped (id={sh_id})")
            return False
        if self._is_uw_chest_present():
            self._dhuum_pve_log("SHeal", "UW chest present — skipped")
            return False

        me_x, me_y = Player.GetXY()
        candidates = AgentArray.Filter.ByCondition(
            AgentArray.GetAllyArray(),
            lambda aid: Agent.IsAlive(aid)
            and Agent.GetHealth(aid) < 0.70
            and ((Agent.GetXY(aid)[0] - me_x) ** 2 + (Agent.GetXY(aid)[1] - me_y) ** 2) ** 0.5 <= Range.Spellcast.value * 1.2,
        )
        if not candidates:
            self._dhuum_pve_log("SHeal", "No ally below 70% HP in range")
            return False
        candidates.sort(key=lambda aid: (
            Agent.GetHealth(aid),
            ((Agent.GetXY(aid)[0] - me_x) ** 2 + (Agent.GetXY(aid)[1] - me_y) ** 2) ** 0.5,
        ))
        self._dhuum_pve_log("SHeal", f"Casting on target={int(candidates[0])} HP={Agent.GetHealth(int(candidates[0])):.0%}")
        return (yield from self.build.CastSkillIDAndRestoreTarget(sh_id, int(candidates[0])))
