from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib import Routines

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr


class EnergyStorage:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region A
    def Aura_of_Restoration(self) -> BuildCoroutine:
        aura_of_restoration_id: int = Skill.GetID("Aura_of_Restoration")

        if not self.build.IsSkillEquipped(aura_of_restoration_id):
            return False

        not_has_aura = lambda: not Routines.Checks.Effects.HasBuff(Player.GetAgentID(), aura_of_restoration_id)
        if not not_has_aura():
            return False

        return (yield from self.build.CastSkillID(
            skill_id=aura_of_restoration_id,
            extra_condition=not_has_aura,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region E
    def Ether_Renewal(self) -> BuildCoroutine:
        ether_renewal_id: int = Skill.GetID("Ether_Renewal")

        if not self.build.IsSkillEquipped(ether_renewal_id):
            return False

        not_has_ether_renewal = lambda: not Routines.Checks.Effects.HasBuff(Player.GetAgentID(), ether_renewal_id)
        if not not_has_ether_renewal():
            return False

        return (yield from self.build.CastSkillID(
            skill_id=ether_renewal_id,
            extra_condition=not_has_ether_renewal,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
