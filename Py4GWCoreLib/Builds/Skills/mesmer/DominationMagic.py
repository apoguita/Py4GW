from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["DominationMagic"]


class DominationMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region U
    def Unnatural_Signet(self) -> BuildCoroutine:
        unnatural_signet_id: int = Skill.GetID("Unnatural_Signet")
        target_acquired, _ = self.build._resolve_target("EnemyHexedOrEnchantedClustered")
        if not target_acquired:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=unnatural_signet_id,
            target_agent_id=self.build.current_target_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
