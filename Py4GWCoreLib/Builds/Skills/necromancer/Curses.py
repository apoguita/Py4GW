from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Range, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["Curses"]


class Curses:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region E
    def Enfeebling_Blood(self) -> BuildCoroutine:
        enfeebling_blood_id: int = Skill.GetID("Enfeebling_Blood")
        enfeebling_blood: CustomSkill = self.build.GetCustomSkill(enfeebling_blood_id)

        def _can_safely_cast_enfeebling_blood() -> bool:
            return Agent.GetHealth(Player.GetAgentID()) > enfeebling_blood.Conditions.SacrificeHealth

        if not self.build.IsSkillEquipped(enfeebling_blood_id):
            return False
        if not _can_safely_cast_enfeebling_blood():
            return False
        if not (yield from self.build.AcquireTarget(target_type="EnemyClustered")):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=enfeebling_blood_id,
            extra_condition=_can_safely_cast_enfeebling_blood,
            log=False,
            aftercast_delay=250,
            target_agent_id=self.build.current_target_id,
        ))
    #endregion

    #region W
    def Weaken_Armor(self) -> BuildCoroutine:
        weaken_armor_id: int = Skill.GetID("Weaken_Armor")

        if not self.build.IsSkillEquipped(weaken_armor_id):
            return False
        
        target_agent_id = self.build._pick_clustered_target(
            Range.Spellcast.value,
            preferred_condition=lambda agent_id: not Routines.Checks.Agents.HasEffect(agent_id, weaken_armor_id),
        )
        if not target_agent_id:
            return False
        if Routines.Checks.Agents.HasEffect(target_agent_id, weaken_armor_id):
            return False
        
        return (yield from self.build.CastSkillID(
            skill_id=weaken_armor_id,
            log=False,
            aftercast_delay=250,
            target_agent_id=target_agent_id,
            extra_condition=lambda: not Routines.Checks.Agents.HasEffect(target_agent_id, weaken_armor_id),
        ))
    #endregion
