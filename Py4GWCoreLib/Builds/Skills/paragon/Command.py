from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["Command"]


class Command:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region C
    def Cant_Touch_This(self) -> BuildCoroutine:
        cant_touch_this_id: int = Skill.GetID("Cant_Touch_This")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(cant_touch_this_id):
            return False
        if not Routines.Checks.Agents.InAggro():
            return False

        if Routines.Checks.Agents.HasEffect(player_agent_id, cant_touch_this_id):
            remaining_ms = int(GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id, cant_touch_this_id) or 0)
            if remaining_ms > 1500:
                return False

        return (yield from self.build.CastSkillID(
            skill_id=cant_touch_this_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Stand_Your_Ground(self) -> BuildCoroutine:
        stand_your_ground_id: int = Skill.GetID("Stand_Your_Ground")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(stand_your_ground_id):
            return False
        if not Routines.Checks.Agents.InAggro():
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, stand_your_ground_id):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=stand_your_ground_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
