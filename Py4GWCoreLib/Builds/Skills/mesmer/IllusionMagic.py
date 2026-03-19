from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["IllusionMagic"]


class IllusionMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region S
    def Signet_of_Clumsiness(self) -> BuildCoroutine:
        signet_of_clumsiness_id: int = Skill.GetID("Signet_of_Clumsiness")
        target_acquired, _ = self.build._resolve_target("EnemyAttackingClustered")
        if not target_acquired:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=signet_of_clumsiness_id,
            target_agent_id=self.build.current_target_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
