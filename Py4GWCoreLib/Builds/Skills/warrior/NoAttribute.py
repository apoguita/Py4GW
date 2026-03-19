from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["NoAttribute"]


class NoAttribute:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def _resolve_warrior_target(self) -> int:
        target_acquired, _ = self.build._resolve_target("EnemyClustered")
        if not target_acquired:
            return 0
        return self.build.current_target_id

    #region W
    def Whirlwind_Attack(self) -> BuildCoroutine:
        whirlwind_attack_id: int = Skill.GetID("Whirlwind_Attack")
        target_agent_id = self._resolve_warrior_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=whirlwind_attack_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
