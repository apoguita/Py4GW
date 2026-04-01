from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, Range, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["SmitingPrayers"]


class SmitingPrayers:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region J
    def Judges_Insight(self) -> BuildCoroutine:
        judges_insight_id: int = Skill.GetID("Judges_Insight")

        if not self.build.IsSkillEquipped(judges_insight_id):
            return False

        ally_array = Routines.Targeting.GetAllAlliesArray(Range.Spellcast.value)
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: Agent.IsAlive(agent_id),
        )
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: Agent.IsMartial(agent_id),
        )
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: not Routines.Checks.Agents.HasEffect(agent_id, judges_insight_id),
        )

        target_agent_id = ally_array[0] if ally_array else 0

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=judges_insight_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region B
    def Bane_Signet(self) -> BuildCoroutine:
        bane_signet_id: int = Skill.GetID("Bane_Signet")
        target_acquired, _ = self.build._resolve_target("EnemyAttacking")
        if not target_acquired:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=bane_signet_id,
            target_agent_id=self.build.current_target_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region C
    def Castigation_Signet(self) -> BuildCoroutine:
        castigation_signet_id: int = Skill.GetID("Castigation_Signet")
        target_acquired, _ = self.build._resolve_target("EnemyAttacking")
        if not target_acquired:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=castigation_signet_id,
            target_agent_id=self.build.current_target_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Smite_Hex(self) -> BuildCoroutine:
        smite_hex_id: int = Skill.GetID("Smite_Hex")
        smite_hex = self.build.GetCustomSkill(smite_hex_id)

        target_agent_id = self.build.ResolveAllyTarget(
            smite_hex_id,
            smite_hex,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=smite_hex_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
