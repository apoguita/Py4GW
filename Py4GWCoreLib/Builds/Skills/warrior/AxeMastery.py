from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["AxeMastery"]


class AxeMastery:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def _resolve_axe_target(self) -> int:
        target_acquired, _ = self.build._resolve_target("EnemyClustered")
        if not target_acquired:
            return 0
        return self.build.current_target_id

    #region C
    def Cyclone_Axe(self) -> BuildCoroutine:
        cyclone_axe_id: int = Skill.GetID("Cyclone_Axe")
        target_agent_id = self._resolve_axe_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=cyclone_axe_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region E
    def Executioners_Strike(self) -> BuildCoroutine:
        executioners_strike_id: int = Skill.GetID("Executioners_Strike")
        target_agent_id = self._resolve_axe_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=executioners_strike_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
