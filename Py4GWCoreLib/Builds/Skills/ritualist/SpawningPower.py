from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["SpawningPower"]


class SpawningPower:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def _maintain_self_effect(self, skill_id: int, renew_before_ms: int = 200) -> BuildCoroutine:
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(skill_id):
            return False

        has_effect = Routines.Checks.Agents.HasEffect(player_agent_id, skill_id)
        if has_effect:
            remaining_ms = int(GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id, skill_id) or 0)
            if remaining_ms > renew_before_ms:
                return False

        return (yield from self.build.CastSkillID(
            skill_id=skill_id,
            target_agent_id=player_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    #region B
    def Boon_of_Creation(self) -> BuildCoroutine:
        boon_of_creation_id: int = Skill.GetID("Boon_of_Creation")
        return (yield from self._maintain_self_effect(boon_of_creation_id, renew_before_ms=4000))
    #endregion

    #region S
    def Soul_Twisting(self) -> BuildCoroutine:
        soul_twisting_id: int = Skill.GetID("Soul_Twisting")
        return (yield from self._maintain_self_effect(soul_twisting_id, renew_before_ms=1200))

    def Spirits_Gift(self) -> BuildCoroutine:
        spirits_gift_id: int = Skill.GetID("Spirits_Gift")
        return (yield from self._maintain_self_effect(spirits_gift_id, renew_before_ms=500))
    #endregion
