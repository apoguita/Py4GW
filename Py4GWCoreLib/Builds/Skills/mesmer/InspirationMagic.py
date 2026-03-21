from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr


class InspirationMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def Hex_Eater_Signet(self) -> BuildCoroutine:
        hex_eater_signet_id: int = Skill.GetID("Hex_Eater_Signet")

        if not self.build.IsSkillEquipped(hex_eater_signet_id):
            return False

        hex_eater_signet: CustomSkill = self.build.GetCustomSkill(hex_eater_signet_id)
        target_agent_id = self.build.ResolveAllyTarget(
            hex_eater_signet_id,
            hex_eater_signet,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            hex_eater_signet_id,
            target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
