from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr


class NoAttribute:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region E
    def Expel_Hexes(self) -> BuildCoroutine:
        expel_hexes_id: int = Skill.GetID("Expel_Hexes")
        expel_hexes: CustomSkill = self.build.GetCustomSkill(expel_hexes_id)

        if not self.build.IsSkillEquipped(expel_hexes_id):
            return False

        target_agent_id = self.build.ResolveRankedPartyAllyTarget(
            expel_hexes_id,
            expel_hexes,
            validator=lambda agent_id: Routines.Checks.Agents.IsHexed(agent_id),
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=expel_hexes_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

