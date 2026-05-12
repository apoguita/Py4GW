from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["NoAttribute"]


class NoAttribute:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region A
    def Arcane_Echo(self) -> BuildCoroutine:
        arcane_echo_id: int = Skill.GetID("Arcane_Echo")

        if not self.build.IsSkillEquipped(arcane_echo_id):
            return False
        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False

        # Skip if already active — Arcane Echo lasts 20s waiting for the next spell.
        # Reapplying mid-window wastes energy and resets the copy slot.
        if Routines.Checks.Agents.HasEffect(Player.GetAgentID(), arcane_echo_id):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=arcane_echo_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
