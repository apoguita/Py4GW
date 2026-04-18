from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, Range
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["SoulReaping"]


class SoulReaping:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region S
    def Signet_of_Lost_Souls(
        self,
        *,
        max_self_energy_pct: float | None = None,
    ) -> BuildCoroutine:
        from Py4GWCoreLib import Utils

        signet_of_lost_souls_id: int = Skill.GetID("Signet_of_Lost_Souls")

        if not self.build.IsSkillEquipped(signet_of_lost_souls_id):
            return False

        # Optional caster-energy gate. When set, fire only if the caster's energy
        # fraction is strictly below the threshold. When None (default) there is
        # no caster-side gate - the signet is free HP/energy whenever an eligible
        # target exists, so the caller's chain position bounds when it fires.
        if max_self_energy_pct is not None:
            if Agent.GetEnergy(Player.GetAgentID()) >= max_self_energy_pct:
                return False

        # Target filter: enemy within Spellcast range, alive, below the signet's
        # 50% trigger threshold. Sort closest-first with lower HP as tiebreak so
        # the target is both reliable (unlikely to slip out of range during the
        # 1/4s cast) and likely to still be <50% when the signet resolves.
        player_pos = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, Range.Spellcast.value)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.GetHealth(agent_id) < 0.5)
        if not enemy_array:
            return False

        target_agent_id = sorted(
            enemy_array,
            key=lambda aid: (Utils.Distance(player_pos, Agent.GetXY(aid)), Agent.GetHealth(aid)),
        )[0]

        return (yield from self.build.CastSkillID(
            skill_id=signet_of_lost_souls_id,
            log=False,
            aftercast_delay=250,
            target_agent_id=target_agent_id,
        ))
    #endregion
