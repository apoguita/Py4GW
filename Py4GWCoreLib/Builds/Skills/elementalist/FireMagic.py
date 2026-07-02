from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Range, Routines
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["FireMagic"]


class FireMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region B
    def Burning_Speed(self) -> BuildCoroutine:
        """Self-cast Burning Speed while a foe stands within "nearby" range.

        Re-cast whenever the caster is not currently burning — independent of
        whether the Burning Speed enchantment itself is still up — so the caster
        is kept on fire for Contagion to spread. Burning is not exposed by the
        agent bitfield, so it is detected via the Burning effect id.
        """
        burning_speed_id: int = Skill.GetID("Burning_Speed")
        burning_id: int = Skill.GetID("Burning")

        if not self.build.IsSkillEquipped(burning_speed_id):
            return False
        if not Routines.Agents.GetNearestEnemy(Range.Nearby.value):
            return False
        if Routines.Checks.Agents.HasEffect(Player.GetAgentID(), burning_id):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=burning_speed_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
