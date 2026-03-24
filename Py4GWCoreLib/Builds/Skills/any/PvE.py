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
        from HeroAI.utils import GetEffectAndBuffIds

        cry_of_pain_id: int = Skill.GetID("Cry_of_Pain")
        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(cry_of_pain_id) or Range.Nearby.value

        def _has_mesmer_hex(agent_id: int) -> bool:
            if not agent_id or not Agent.IsHexed(agent_id):
                return False
            for effect_skill_id in GetEffectAndBuffIds(agent_id):
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
