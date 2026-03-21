from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Range, Routines
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["NoAttribute"]


class NoAttribute:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region B
    def Breath_of_the_Great_Dwarf(self) -> BuildCoroutine:
        breath_of_the_great_dwarf_id: int = Skill.GetID("Breath_of_the_Great_Dwarf")
        breath_of_the_great_dwarf: CustomSkill = self.build.GetCustomSkill(breath_of_the_great_dwarf_id)
        burning_id: int = Skill.GetID("Burning")

        def _party_has_burning() -> bool:
            ally_array = Routines.Targeting.GetAllAlliesArray(Range.SafeCompass.value)
            return any(
                Routines.Checks.Agents.HasEffect(agent_id, burning_id)
                for agent_id in (ally_array or [])
            )

        if not self.build.IsSkillEquipped(breath_of_the_great_dwarf_id):
            return False
        if not (
            self.build.EvaluatePartyWideThreshold(
                breath_of_the_great_dwarf_id,
                breath_of_the_great_dwarf,
            )
            or _party_has_burning()
        ):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=breath_of_the_great_dwarf_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region G
    def Great_Dwarf_Weapon(self) -> BuildCoroutine:
        great_dwarf_weapon_id: int = Skill.GetID("Great_Dwarf_Weapon")
        great_dwarf_weapon: CustomSkill = self.build.GetCustomSkill(great_dwarf_weapon_id)

        if not self.build.IsSkillEquipped(great_dwarf_weapon_id):
            return False

        target_agent_id = self.build.ResolveAllyTarget(
            great_dwarf_weapon_id,
            great_dwarf_weapon,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=great_dwarf_weapon_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region Y
    def You_Are_All_Weaklings(self) -> BuildCoroutine:
        you_are_all_weaklings_id: int = Skill.GetID("You_Are_All_Weaklings")

        if not self.build.IsSkillEquipped(you_are_all_weaklings_id):
            return False
        if not (yield from self.build.AcquireTarget(target_type="EnemyClustered")):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=you_are_all_weaklings_id,
            log=False,
            aftercast_delay=250,
            target_agent_id=self.build.current_target_id,
        ))
    #endregion
