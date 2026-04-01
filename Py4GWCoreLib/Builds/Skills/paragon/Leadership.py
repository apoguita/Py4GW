from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Player, Routines
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["Leadership"]


class Leadership:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def _get_leadership_level(self) -> int:
        from Py4GWCoreLib import Agent

        player_agent_id = Player.GetAgentID()
        attributes = Agent.GetAttributes(player_agent_id)
        leadership = next((attribute for attribute in attributes if attribute.GetName() == "Leadership"), None)
        return int(getattr(leadership, "level", 0) or 0)

    #region H
    def Heroic_Refrain(self) -> BuildCoroutine:
        heroic_refrain_id: int = Skill.GetID("Heroic_Refrain")
        heroic_refrain = self.build.GetCustomSkill(heroic_refrain_id)

        if not self.build.IsSkillEquipped(heroic_refrain_id):
            return False

        player_agent_id = Player.GetAgentID()
        if self._get_leadership_level() < 20:
            return (yield from self.build.CastSkillIDAndRestoreTarget(
                skill_id=heroic_refrain_id,
                target_agent_id=player_agent_id,
                log=False,
                aftercast_delay=250,
            ))
        if not Routines.Checks.Agents.HasEffect(player_agent_id, heroic_refrain_id):
            return (yield from self.build.CastSkillIDAndRestoreTarget(
                skill_id=heroic_refrain_id,
                target_agent_id=player_agent_id,
                log=False,
                aftercast_delay=250,
            ))

        target_agent_id = self.build.ResolveAllyTarget(
            heroic_refrain_id,
            heroic_refrain,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=heroic_refrain_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region A
    def Aggressive_Refrain(self) -> BuildCoroutine:
        aggressive_refrain_id: int = Skill.GetID("Aggressive_Refrain")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(aggressive_refrain_id):
            return False
        if not Routines.Checks.Agents.InAggro():
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, aggressive_refrain_id):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=aggressive_refrain_id,
            target_agent_id=player_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region T
    def Theyre_on_Fire(self) -> BuildCoroutine:
        theyre_on_fire_id: int = Skill.GetID("Theyre_on_Fire")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(theyre_on_fire_id):
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, theyre_on_fire_id):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=theyre_on_fire_id,
            target_agent_id=player_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
