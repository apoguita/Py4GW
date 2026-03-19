from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["Strength"]


class Strength:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region E
    def Endure_Pain(self) -> BuildCoroutine:
        endure_pain_id: int = Skill.GetID("Endure_Pain")
        endure_pain: CustomSkill = self.build.GetCustomSkill(endure_pain_id)

        def _should_cast_endure_pain() -> bool:
            if not self.build.IsSkillEquipped(endure_pain_id):
                return False
            return Agent.GetHealth(Player.GetAgentID()) < endure_pain.Conditions.LessLife

        if not _should_cast_endure_pain():
            return False

        return (yield from self.build.CastSkillID(
            skill_id=endure_pain_id,
            extra_condition=_should_cast_endure_pain,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Seven_Weapon_Stance(self) -> BuildCoroutine:
        seven_weapon_stance_id: int = Skill.GetID("Seven_Weapon_Stance")

        if not self.build.IsSkillEquipped(seven_weapon_stance_id):
            return False

        not_has_sws = lambda: not Routines.Checks.Effects.HasBuff(Player.GetAgentID(), seven_weapon_stance_id)
        if not not_has_sws():
            return False

        return (yield from self.build.CastSkillID(
            skill_id=seven_weapon_stance_id,
            extra_condition=not_has_sws,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
