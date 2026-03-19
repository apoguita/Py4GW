from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, Range, Routines, Utils
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Skill import Skill
from HeroAI.targeting import GetAllAlliesArray
from HeroAI.types import Skilltarget

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["ProtectionPrayers"]


class ProtectionPrayers:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build


    #region D
    def Draw_Conditions(self) -> BuildCoroutine:
        draw_conditions_id: int = Skill.GetID("Draw_Conditions")
        draw_conditions: CustomSkill = self.build.GetCustomSkill(draw_conditions_id)

        def _resolve_draw_conditions_target() -> int:
            return self.build.ResolveAllyTarget(
                draw_conditions_id,
                draw_conditions,
            )

        if not self.build.IsSkillEquipped(draw_conditions_id):
            return False

        target_agent_id = _resolve_draw_conditions_target()
        return (yield from self.build.CastSkillIDAndRestoreTarget(
            draw_conditions_id,
            target_agent_id,
        ))
