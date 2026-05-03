from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, Range, Routines, Utils
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["DeadlyArts"]


class DeadlyArts:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region A
    def Assassins_Promise(self) -> BuildCoroutine:
        assassins_promise_id: int = Skill.GetID("Assassins_Promise")

        if not self.build.IsSkillEquipped(assassins_promise_id):
            return False
        if not self.build.IsInAggro():
            return False

        # Tier 1: best cluster with 2+ enemies in Range.Nearby — ideal anchor
        # for the bile detonation chain.
        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=Range.Nearby.value,
            preferred_condition=lambda agent_id: Routines.Targeting.CountNearbyEnemies(
                agent_id, Range.Nearby.value
            ) >= 2,
            filter_radius=Range.Spellcast.value,
        )

        # Tier 2: best cluster with 1+ enemy in Range.Nearby.
        if not target_agent_id:
            target_agent_id = Routines.Targeting.PickClusteredTarget(
                cluster_radius=Range.Nearby.value,
                preferred_condition=lambda agent_id: Routines.Targeting.CountNearbyEnemies(
                    agent_id, Range.Nearby.value
                ) >= 1,
                filter_radius=Range.Spellcast.value,
            )

        # Tier 3: closest alive enemy in spellcast range — single-target AP
        # still triggers the all-skills-recharge on kill.
        if not target_agent_id:
            player_pos = Player.GetXY()
            enemy_array = AgentArray.GetEnemyArray()
            enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, Range.Spellcast.value)
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
            if enemy_array:
                target_agent_id = sorted(
                    enemy_array,
                    key=lambda aid: Utils.Distance(player_pos, Agent.GetXY(aid)),
                )[0]

        if not target_agent_id:
            return False

        # Skip if AP is already up on the picked target — wait for the kill
        # (which recharges everything anyway) before recasting on this enemy.
        if assassins_promise_id in self.build.GetEffectAndBuffIds(target_agent_id):
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=assassins_promise_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
