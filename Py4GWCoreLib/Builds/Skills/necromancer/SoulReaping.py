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
    def Signet_of_Lost_Souls(self) -> BuildCoroutine:
        signet_of_lost_souls_id: int = Skill.GetID("Signet_of_Lost_Souls")
        signet_of_lost_souls: CustomSkill = self.build.GetCustomSkill(signet_of_lost_souls_id)

        def _should_cast_signet_of_lost_souls() -> bool:
            player_agent_id = Player.GetAgentID()
            return (
                Agent.GetHealth(player_agent_id) < signet_of_lost_souls.Conditions.LessLife
                or Agent.GetEnergy(player_agent_id) < signet_of_lost_souls.Conditions.LessEnergy
            )

        def _resolve_signet_of_lost_souls_target() -> int:
            enemy_array = AgentArray.GetEnemyArray()
            enemy_array = AgentArray.Filter.ByDistance(
                enemy_array,
                Player.GetXY(),
                Range.Spellcast.value,
            )
            enemy_array = AgentArray.Filter.ByCondition(
                enemy_array,
                lambda agent_id: Agent.IsAlive(agent_id),
            )
            enemy_array = AgentArray.Filter.ByCondition(
                enemy_array,
                lambda agent_id: Agent.GetHealth(agent_id) < 0.5,
            )
            enemy_array = AgentArray.Sort.ByHealth(enemy_array)
            return enemy_array[0] if enemy_array else 0

        if not self.build.IsSkillEquipped(signet_of_lost_souls_id):
            return False
        if not _should_cast_signet_of_lost_souls():
            return False

        target_agent_id = _resolve_signet_of_lost_souls_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillID(
            skill_id=signet_of_lost_souls_id,
            log=False,
            aftercast_delay=250,
            target_agent_id=target_agent_id,
        ))
    #endregion
