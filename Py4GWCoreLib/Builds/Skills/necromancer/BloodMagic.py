from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["BloodMagic"]


class BloodMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self.bip_throttle: ThrottledTimer = ThrottledTimer(1500)
        self.bip_throttle.Stop()

    #region B
    def Blood_is_Power(self) -> BuildCoroutine:
        blood_is_power_id: int = Skill.GetID("Blood_is_Power")
        blood_is_power: CustomSkill = self.build.GetCustomSkill(blood_is_power_id)

        def _is_bip_throttle_ready() -> bool:
            return self.bip_throttle.IsStopped() or self.bip_throttle.IsExpired()

        def _can_safely_cast_bip() -> bool:
            return Agent.GetHealth(Player.GetAgentID()) > blood_is_power.Conditions.SacrificeHealth

        if not self.build.IsSkillEquipped(blood_is_power_id):
            return False

        target_agent_id: int = self.build.ResolveAllyTarget(
            blood_is_power_id,
            blood_is_power,
        )
        if not target_agent_id:
            return False
        if not _is_bip_throttle_ready():
            return False
        if not _can_safely_cast_bip():
            return False

        if (yield from self.build.CastSkillIDAndRestoreTarget(
            blood_is_power_id,
            target_agent_id,
            extra_condition=_can_safely_cast_bip,
        )):
            self.bip_throttle.Reset()
            return True

        return False
    #endregion
