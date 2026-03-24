from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Player, Range, Routines
from Py4GWCoreLib.Agent import Agent
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

    #region F
    def For_Great_Justice(self) -> BuildCoroutine:
        for_great_justice_id: int = Skill.GetID("For_Great_Justice")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(for_great_justice_id):
            return False
        if not Routines.Checks.Agents.InAggro():
            return False
        if Agent.IsDead(player_agent_id):
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, for_great_justice_id):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=for_great_justice_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region P
    def Protectors_Defense(self) -> BuildCoroutine:
        from HeroAI.targeting import GetAllAlliesArray
        from Py4GWCoreLib import AgentArray

        protectors_defense_id: int = Skill.GetID("Protectors_Defense")

        if not self.build.IsSkillEquipped(protectors_defense_id):
            return False
        if Agent.IsMoving(Player.GetAgentID()):
            return False

        nearby_allies = GetAllAlliesArray(Range.Adjacent.value)
        nearby_allies = AgentArray.Filter.ByCondition(
            nearby_allies,
            lambda agent_id: agent_id != Player.GetAgentID() and Agent.IsAlive(agent_id),
        )
        if not nearby_allies:
            return False

        return (yield from self.build.CastSkillID(
            skill_id=protectors_defense_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
