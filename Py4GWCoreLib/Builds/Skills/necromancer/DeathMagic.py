from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, Range, Routines, Utils
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["DeathMagic"]


class DeathMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region P
    def Putrid_Bile(self) -> BuildCoroutine:
        putrid_bile_id: int = Skill.GetID("Putrid_Bile")
        assassins_promise_id: int = Skill.GetID("Assassins_Promise")

        if not self.build.IsSkillEquipped(putrid_bile_id):
            return False
        if not self.build.IsInAggro():
            return False

        # Snapshot alive enemies in spellcast range — used by the Assasins promise-focus
        # search and the single-target fallback.
        player_pos = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, Range.Spellcast.value)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
        if not enemy_array:
            return False

        def _has_putrid_bile(agent_id: int) -> bool:
            return putrid_bile_id in self.build.GetEffectAndBuffIds(agent_id)

        # Tier 1: live Assassins Promise-hexed enemy without Putrid Bile already up. Piggybacks
        # on the Assassins Promise focus so both hexes detonate when the target dies.
        target_agent_id = 0
        for enemy_id in enemy_array:
            effect_ids = self.build.GetEffectAndBuffIds(enemy_id)
            if assassins_promise_id in effect_ids and putrid_bile_id not in effect_ids:
                target_agent_id = enemy_id
                break

        # Tier 2: best cluster with 2+ neighbors in Range.Nearby. Anchor must
        # be < 25% HP (about to die) so the detonation pays off.
        if not target_agent_id:
            target_agent_id = self.build._pick_clustered_target(
                cluster_radius=Range.Nearby.value,
                preferred_condition=lambda agent_id: (
                    self.build._count_nearby_enemies(agent_id, Range.Nearby.value) >= 2
                    and Agent.GetHealth(agent_id) < 0.25
                    and not _has_putrid_bile(agent_id)
                ),
                filter_radius=Range.Spellcast.value,
            )

        # Tier 3: best cluster with 1+ neighbor in Range.Nearby. Anchor must
        # be < 35% HP.
        if not target_agent_id:
            target_agent_id = self.build._pick_clustered_target(
                cluster_radius=Range.Nearby.value,
                preferred_condition=lambda agent_id: (
                    self.build._count_nearby_enemies(agent_id, Range.Nearby.value) >= 1
                    and Agent.GetHealth(agent_id) < 0.35
                    and not _has_putrid_bile(agent_id)
                ),
                filter_radius=Range.Spellcast.value,
            )

        # Tier 4: any enemy < 35% HP without Putrid Bile (no cluster
        # requirement). Closest first so the cast is least likely to whiff.
        if not target_agent_id:
            candidates = [
                aid for aid in enemy_array
                if Agent.GetHealth(aid) < 0.35 and not _has_putrid_bile(aid)
            ]
            if candidates:
                target_agent_id = sorted(
                    candidates,
                    key=lambda aid: Utils.Distance(player_pos, Agent.GetXY(aid)),
                )[0]

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=putrid_bile_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def Putrid_Explosion(self) -> BuildCoroutine:
        putrid_explosion_id: int = Skill.GetID("Putrid_Explosion")

        if not self.build.IsSkillEquipped(putrid_explosion_id):
            return False
        if not self.build.IsInAggro():
            return False

        # Tiered fallback: prefer corpses with the largest enemy-target cluster
        # around them. If no corpse has 4+ enemy targets in Range.Nearby, fall
        # through to 3+, 2+, 1+. Each tier returns the highest-scoring corpse
        # meeting its floor.
        target_corpse_id = (
            self.build._pick_clustered_corpse(
                cluster_radius=Range.Nearby.value,
                filter_radius=Range.Spellcast.value,
                min_enemy_targets=4,
            )
            or self.build._pick_clustered_corpse(
                cluster_radius=Range.Nearby.value,
                filter_radius=Range.Spellcast.value,
                min_enemy_targets=3,
            )
            or self.build._pick_clustered_corpse(
                cluster_radius=Range.Nearby.value,
                filter_radius=Range.Spellcast.value,
                min_enemy_targets=2,
            )
            or self.build._pick_clustered_corpse(
                cluster_radius=Range.Nearby.value,
                filter_radius=Range.Spellcast.value,
                min_enemy_targets=1,
            )
        )
        if not target_corpse_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=putrid_explosion_id,
            target_agent_id=target_corpse_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region R
    def Rising_Bile(self) -> BuildCoroutine:
        rising_bile_id: int = Skill.GetID("Rising_Bile")

        if not self.build.IsSkillEquipped(rising_bile_id):
            return False
        if not self.build.IsInAggro():
            return False

        # Pure cluster pick: anchor with the most alive enemies in Range.Area.
        # Hard floor of 2+ neighbors (3+ total foes damaged) — Rising Bile only
        # pays off when the on-end AoE hits a real cluster. Cast as the opening
        # hex so the 20s timer accumulates maximum per-second damage.
        target_agent_id = self.build._pick_clustered_target(
            cluster_radius=Range.Area.value,
            preferred_condition=lambda agent_id: (
                self.build._count_nearby_enemies(agent_id, Range.Area.value) >= 2
                and rising_bile_id not in self.build.GetEffectAndBuffIds(agent_id)
            ),
            filter_radius=Range.Spellcast.value,
        )

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=rising_bile_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
