from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Range
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["Motivation"]


class Motivation:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region B
    def Blazing_Finale(self) -> BuildCoroutine:
        blazing_finale_id: int = Skill.GetID("Blazing_Finale")
        blazing_finale = self.build.GetCustomSkill(blazing_finale_id)

        if not self.build.IsSkillEquipped(blazing_finale_id):
            return False

        target_agent_id = self.build.ResolveAllyTarget(
            blazing_finale_id,
            blazing_finale,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=blazing_finale_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region H
    def Hasty_Refrain(self) -> BuildCoroutine:
        hasty_refrain_id: int = Skill.GetID("Hasty_Refrain")
        hasty_refrain = self.build.GetCustomSkill(hasty_refrain_id)

        if not self.build.IsSkillEquipped(hasty_refrain_id):
            return False

        target_agent_id = self.build.ResolveAllyTarget(
            hasty_refrain_id,
            hasty_refrain,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=hasty_refrain_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region N
    def Never_Surrender(self) -> BuildCoroutine:
        from HeroAI.targeting import GetAllAlliesArray
        from Py4GWCoreLib import AgentArray
        from Py4GWCoreLib.Agent import Agent

        never_surrender_id: int = Skill.GetID("Never_Surrender")

        if not self.build.IsSkillEquipped(never_surrender_id):
            return False

        ally_array = GetAllAlliesArray(Range.Earshot.value)
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: Agent.IsAlive(agent_id) and Agent.GetHealth(agent_id) < 0.70,
        )
        if len(ally_array or []) < 2:
            return False

        return (yield from self.build.CastSkillID(
            skill_id=never_surrender_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
