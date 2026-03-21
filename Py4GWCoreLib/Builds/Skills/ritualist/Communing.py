from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["Communing"]


class Communing:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region V
    def Vital_Weapon(self) -> BuildCoroutine:
        vital_weapon_id: int = Skill.GetID("Vital_Weapon")

        if not self.build.IsSkillEquipped(vital_weapon_id):
            return False
        vital_weapon: CustomSkill = self.build.GetCustomSkill(vital_weapon_id)
        target_agent_id = self.build.ResolveAllyTarget(
            vital_weapon_id,
            vital_weapon,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            vital_weapon_id,
            target_agent_id,
        ))
    #endregion
