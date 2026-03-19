from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["FastCasting"]


class FastCasting:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region K
    def Keystone_Signet(self) -> BuildCoroutine:
        keystone_signet_id: int = Skill.GetID("Keystone_Signet")
        symbolic_celerity_id: int = Skill.GetID("Symbolic_Celerity")

        has_symbolic_celerity = lambda: Routines.Checks.Effects.HasBuff(Player.GetAgentID(), symbolic_celerity_id)
        has_keystone_signet = lambda: Routines.Checks.Effects.HasBuff(Player.GetAgentID(), keystone_signet_id)
        cast_condition = lambda: has_symbolic_celerity() and not has_keystone_signet()

        if not cast_condition():
            return False

        return (yield from self.build.CastSkillID(
            skill_id=keystone_signet_id,
            extra_condition=cast_condition,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Symbolic_Celerity(self) -> BuildCoroutine:
        symbolic_celerity_id: int = Skill.GetID("Symbolic_Celerity")
        cast_condition = lambda: not Routines.Checks.Effects.HasBuff(Player.GetAgentID(), symbolic_celerity_id)

        if not cast_condition():
            return False

        return (yield from self.build.CastSkillID(
            skill_id=symbolic_celerity_id,
            extra_condition=cast_condition,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
