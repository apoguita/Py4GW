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

__all__ = ["NoAttribute"]

class NoAttribute:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build


    #region S
    def Seed_of_Life(self) -> BuildCoroutine:
        seed_of_life_id: int = Skill.GetID("Seed_of_Life")
        seed_of_life: CustomSkill = self.build.GetCustomSkill(seed_of_life_id)

        def _resolve_seed_of_life_target() -> int:
            melee_target_skill: CustomSkill = deepcopy(seed_of_life)
            melee_target_skill.TargetAllegiance = Skilltarget.AllyMartialMelee.value
            melee_target: int = self.build.ResolveAllyTarget(
                seed_of_life_id,
                melee_target_skill,
            )
            if melee_target:
                return melee_target

            martial_target_skill: CustomSkill = deepcopy(seed_of_life)
            martial_target_skill.TargetAllegiance = Skilltarget.AllyMartial.value
            martial_target: int = self.build.ResolveAllyTarget(
                seed_of_life_id,
                martial_target_skill,
            )
            if martial_target:
                return martial_target

            return self.build.ResolveAllyTarget(
                seed_of_life_id,
                seed_of_life,
            )

        if not self.build.IsSkillEquipped(seed_of_life_id):
            return False
        target_agent_id = _resolve_seed_of_life_target()
        return (yield from self.build.CastSkillIDAndRestoreTarget(
            seed_of_life_id,
            target_agent_id,
        ))
