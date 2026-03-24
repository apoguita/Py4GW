from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["DaggerMastery"]


class DaggerMastery:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def _resolve_dagger_target(self) -> int:
        target_type = getattr(self.build, "dagger_target_type", "EnemyInjured")
        target_acquired, _ = self.build._resolve_target(target_type)
        if not target_acquired:
            return 0
        return self.build.current_target_id

    #region D
    def Death_Blossom(self) -> BuildCoroutine:
        death_blossom_id: int = Skill.GetID("Death_Blossom")
        target_agent_id = self._resolve_dagger_target()
        if not target_agent_id:
            return False

        cast_condition = lambda: Agent.GetDaggerStatus(target_agent_id) == 2
        if not cast_condition():
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=death_blossom_id,
            target_agent_id=target_agent_id,
            extra_condition=cast_condition,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region F
    def Fox_Fangs(self) -> BuildCoroutine:
        fox_fangs_id: int = Skill.GetID("Fox_Fangs")
        target_agent_id = self._resolve_dagger_target()
        if not target_agent_id:
            return False

        cast_condition = lambda: Agent.GetDaggerStatus(target_agent_id) == 1
        if not cast_condition():
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=fox_fangs_id,
            target_agent_id=target_agent_id,
            extra_condition=cast_condition,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region J
    def Jagged_Strike(self) -> BuildCoroutine:
        jagged_strike_id: int = Skill.GetID("Jagged_Strike")
        target_agent_id = self._resolve_dagger_target()
        if not target_agent_id:
            return False

        cast_condition = lambda: Agent.GetDaggerStatus(target_agent_id) in (0, 3)
        if not cast_condition():
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=jagged_strike_id,
            target_agent_id=target_agent_id,
            extra_condition=cast_condition,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
