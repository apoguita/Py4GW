from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr


class EarthPrayers:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region D
    def Dust_Cloak(
        self,
        *,
        refresh_window_ms: int = 1200,
        min_self_energy_pct: float = 0.0,
    ) -> BuildCoroutine:
        dust_cloak_id: int = Skill.GetID("Dust_Cloak")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(dust_cloak_id):
            return False
        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False
        if float(Agent.GetEnergy(player_agent_id) or 0.0) < min_self_energy_pct:
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, dust_cloak_id):
            remaining_ms = int(GLOBAL_CACHE.Effects.GetEffectTimeRemaining(
                player_agent_id,
                dust_cloak_id,
            ) or 0)
            if remaining_ms > refresh_window_ms:
                return False

        return (yield from self.build.CastSkillID(
            skill_id=dust_cloak_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Staggering_Force(
        self,
        *,
        refresh_window_ms: int = 1200,
        min_self_energy_pct: float = 0.0,
    ) -> BuildCoroutine:
        staggering_force_id: int = Skill.GetID("Staggering_Force")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(staggering_force_id):
            return False
        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False
        if float(Agent.GetEnergy(player_agent_id) or 0.0) < min_self_energy_pct:
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, staggering_force_id):
            remaining_ms = int(GLOBAL_CACHE.Effects.GetEffectTimeRemaining(
                player_agent_id,
                staggering_force_id,
            ) or 0)
            if remaining_ms > refresh_window_ms:
                return False

        return (yield from self.build.CastSkillID(
            skill_id=staggering_force_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
