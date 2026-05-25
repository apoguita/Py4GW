from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["BeastMastery"]


class BeastMastery:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region E
    def Edge_of_Extinction(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, AgentArray, Player, Range, SpiritModelID

        edge_of_extinction_id: int = Skill.GetID("Edge_of_Extinction")

        if not self.build.IsSkillEquipped(edge_of_extinction_id):
            return False
        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False

        self_agent_id = self.build._resolve_self_agent_id()
        spirits = AgentArray.GetSpiritPetArray()
        spirits = AgentArray.Filter.ByDistance(spirits, Player.GetXY(), Range.Spirit.value)
        if any(
            Agent.IsAlive(spirit_id)
            and Agent.IsSpawned(spirit_id)
            and Agent.GetOwnerID(spirit_id) == self_agent_id
            and Agent.GetPlayerNumber(spirit_id) == SpiritModelID.EDGE_OF_EXTINCTION.value
            for spirit_id in spirits
        ):
            return False

        return (yield from self.build.CastSpiritSkillID(
            skill_id=edge_of_extinction_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
