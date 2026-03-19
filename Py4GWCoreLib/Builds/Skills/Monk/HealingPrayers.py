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

__all__ = ["HealingPrayers"]


class HealingPrayers:
    build: BuildMgr

    def __init__(self, build: BuildMgr) -> None:
        self.build = build

    #region D
    def Dwaynas_Kiss(self) -> BuildCoroutine:
        dwaynas_kiss_id: int = Skill.GetID("Dwaynas_Kiss")
        dwaynas_kiss: CustomSkill = self.build.GetCustomSkill(dwaynas_kiss_id)

        def _resolve_dwaynas_kiss_target() -> int:
            enchanted_target_skill: CustomSkill = deepcopy(dwaynas_kiss)
            enchanted_target_skill.Conditions.HasEnchantment = True
            enchanted_target: int = self.build.ResolveAllyTarget(
                dwaynas_kiss_id,
                enchanted_target_skill,
            )
            if enchanted_target:
                return enchanted_target

            hexed_target_skill: CustomSkill = deepcopy(dwaynas_kiss)
            hexed_target_skill.Conditions.HasHex = True
            hexed_target: int = self.build.ResolveAllyTarget(
                dwaynas_kiss_id,
                hexed_target_skill,
            )
            if hexed_target:
                return hexed_target

            return self.build.ResolveAllyTarget(
                dwaynas_kiss_id,
                dwaynas_kiss,
            )

        if not self.build.IsSkillEquipped(dwaynas_kiss_id):
            return False

        target_agent_id = _resolve_dwaynas_kiss_target()
        return (yield from self.build.CastSkillIDAndRestoreTarget(
            dwaynas_kiss_id,
            target_agent_id,
        ))
    #endregion

    #region H
    def Healing_Burst(self) -> BuildCoroutine:
        healing_burst_id: int = Skill.GetID("Healing_Burst")
        healing_burst: CustomSkill = self.build.GetCustomSkill(healing_burst_id)
        healing_burst_anchor_threshold: float = 0.65
        healing_burst_cluster_threshold: float = 0.85
        healing_burst_emergency_threshold: float = 0.45
        healing_burst_min_other_injured: int = 2

        def _get_healing_burst_candidates() -> list[int]:
            ally_array: list[int] = list(GetAllAlliesArray(Range.Spellcast.value) or [])
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.IsAlive(agent_id),
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.GetHealth(agent_id) <= healing_burst_anchor_threshold,
            )
            return list(ally_array or [])

        def _score_healing_burst_target(anchor_agent_id: int, ally_array: list[int]) -> float:
            anchor_health: float = Agent.GetHealth(anchor_agent_id)
            anchor_missing: float = max(0.0, 1.0 - anchor_health)
            if anchor_health > healing_burst_anchor_threshold:
                return -1.0

            anchor_x: float
            anchor_y: float
            anchor_x, anchor_y = Agent.GetXY(anchor_agent_id)
            cluster_missing: float = 0.0
            other_injured: int = 0

            for ally_agent_id in ally_array:
                ally_x: float
                ally_y: float
                ally_x, ally_y = Agent.GetXY(ally_agent_id)
                if Utils.Distance((anchor_x, anchor_y), (ally_x, ally_y)) > Range.Earshot.value:
                    continue

                ally_health: float = Agent.GetHealth(ally_agent_id)
                if ally_health >= healing_burst_cluster_threshold:
                    continue

                cluster_missing += max(0.0, 1.0 - ally_health)
                if ally_agent_id != anchor_agent_id:
                    other_injured += 1

            if anchor_health <= healing_burst_emergency_threshold:
                return 1000.0 + (anchor_missing * 100.0) + (cluster_missing * 10.0)

            if other_injured < healing_burst_min_other_injured:
                return -1.0

            return (
                (cluster_missing * 100.0)
                + (anchor_missing * 40.0)
                + (other_injured * 20.0)
            )

        def _resolve_healing_burst_target() -> int:
            ally_array: list[int] = _get_healing_burst_candidates()
            if not ally_array:
                return 0

            best_target: int = 0
            best_score: float = -1.0
            for ally_agent_id in ally_array:
                score: float = _score_healing_burst_target(ally_agent_id, ally_array)
                if score > best_score:
                    best_score = score
                    best_target = ally_agent_id

            return best_target

        if not self.build.IsSkillEquipped(healing_burst_id):
            return False

        target_agent_id = _resolve_healing_burst_target()
        return (yield from self.build.CastSkillIDAndRestoreTarget(
            healing_burst_id,
            target_agent_id,
        ))

    #region S

    #region V
    def Vigorous_Spirit(self) -> BuildCoroutine:
        vigorous_spirit_id: int = Skill.GetID("Vigorous_Spirit")
        vigorous_spirit: CustomSkill = self.build.GetCustomSkill(vigorous_spirit_id)

        def _resolve_vigorous_spirit_target() -> int:
            return self.build.ResolveAllyTarget(
                vigorous_spirit_id,
                vigorous_spirit,
            )
            
        if not self.build.IsSkillEquipped(vigorous_spirit_id):
            return False
        target_agent_id = _resolve_vigorous_spirit_target()
        return (yield from self.build.CastSkillIDAndRestoreTarget(
            vigorous_spirit_id,
            target_agent_id,
        ))
    #endregion

    
