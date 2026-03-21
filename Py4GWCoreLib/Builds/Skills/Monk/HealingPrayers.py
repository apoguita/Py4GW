from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, Range, Routines, Utils
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
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
        health_threshold: float = max(0.0, min(1.0, float(dwaynas_kiss.Conditions.LessLife or 0.80)))

        def _is_valid_dwaynas_kiss_target(agent_id: int) -> bool:
            return Agent.IsAlive(agent_id) and Agent.GetHealth(agent_id) <= health_threshold

        def _resolve_dwaynas_kiss_target() -> int:
            enchanted_target_skill: CustomSkill = deepcopy(dwaynas_kiss)
            enchanted_target_skill.Conditions.HasEnchantment = True
            enchanted_target: int = self.build.ResolveAllyTarget(
                dwaynas_kiss_id,
                enchanted_target_skill,
            )
            if enchanted_target and _is_valid_dwaynas_kiss_target(enchanted_target):
                return enchanted_target

            hexed_target_skill: CustomSkill = deepcopy(dwaynas_kiss)
            hexed_target_skill.Conditions.HasHex = True
            hexed_target: int = self.build.ResolveAllyTarget(
                dwaynas_kiss_id,
                hexed_target_skill,
            )
            if hexed_target and _is_valid_dwaynas_kiss_target(hexed_target):
                return hexed_target

            fallback_target = self.build.ResolveAllyTarget(
                dwaynas_kiss_id,
                dwaynas_kiss,
            )
            if fallback_target and _is_valid_dwaynas_kiss_target(fallback_target):
                return fallback_target
            return 0

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
        # Health-fraction gate for valid direct-heal targets. Expected range: 0.0 to 1.0.
        healing_burst_candidate_health_threshold: float = max(0.0, min(1.0, float(healing_burst.Conditions.LessLife or 0.80)))
        # Nearby allies below this health fraction count as injured for splash-value scoring. Expected range: 0.0 to 1.0.
        healing_burst_cluster_injured_health_threshold: float = 0.90
        # Minimum raw cluster score bonus required before overriding the lowest ally with a more clustered target. Expected range: 0.0 and up.
        healing_burst_min_cluster_score_bonus: float = 0.35

        def _get_healing_burst_candidates() -> list[int]:
            ally_array: list[int] = list(GetAllAlliesArray(Range.Spellcast.value) or [])
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.IsAlive(agent_id),
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.GetHealth(agent_id) <= healing_burst_candidate_health_threshold,
            )
            return list(ally_array or [])

        def _score_healing_burst_target(anchor_agent_id: int, ally_array: list[int]) -> tuple[float, float]:
            anchor_health: float = Agent.GetHealth(anchor_agent_id)
            anchor_missing: float = max(0.0, 1.0 - anchor_health)
            if anchor_health > healing_burst_candidate_health_threshold:
                return -1.0, -1.0

            anchor_x: float
            anchor_y: float
            anchor_x, anchor_y = Agent.GetXY(anchor_agent_id)
            cluster_missing: float = 0.0
            nearby_injured: int = 0

            for ally_agent_id in ally_array:
                ally_x: float
                ally_y: float
                ally_x, ally_y = Agent.GetXY(ally_agent_id)
                if Utils.Distance((anchor_x, anchor_y), (ally_x, ally_y)) > Range.Earshot.value:
                    continue

                ally_health: float = Agent.GetHealth(ally_agent_id)
                if ally_health >= healing_burst_cluster_injured_health_threshold:
                    continue

                cluster_missing += max(0.0, 1.0 - ally_health)
                nearby_injured += 1

            baseline_score = (anchor_missing * 100.0) + (1.0 - anchor_health)
            cluster_bonus = (
                max(0.0, cluster_missing - anchor_missing) * 100.0
                + max(0, nearby_injured - 1) * 15.0
            )
            return baseline_score, cluster_bonus

        def _resolve_healing_burst_target() -> int:
            ally_array: list[int] = _get_healing_burst_candidates()
            if not ally_array:
                return 0

            lowest_target: int = min(ally_array, key=lambda agent_id: Agent.GetHealth(agent_id))
            lowest_baseline_score, _ = _score_healing_burst_target(lowest_target, ally_array)
            best_target: int = lowest_target
            best_total_score: float = lowest_baseline_score

            for ally_agent_id in ally_array:
                baseline_score, cluster_bonus = _score_healing_burst_target(ally_agent_id, ally_array)
                total_score = baseline_score + cluster_bonus

                if cluster_bonus < healing_burst_min_cluster_score_bonus:
                    total_score = baseline_score

                if total_score > best_total_score:
                    best_total_score = total_score
                    best_target = ally_agent_id

            return best_target

        if not self.build.IsSkillEquipped(healing_burst_id):
            return False

        target_agent_id = _resolve_healing_burst_target()
        return (yield from self.build.CastSkillIDAndRestoreTarget(
            healing_burst_id,
            target_agent_id,
        ))
    #endregion

    #region I
    def Infuse_Health(self) -> BuildCoroutine:
        infuse_health_id: int = Skill.GetID("Infuse_Health")
        chain_count_attr = "_infuse_health_chain_count"

        def _get_infuse_health_chain_count() -> int:
            chain_count = getattr(self.build, chain_count_attr, 0)
            return int(chain_count if isinstance(chain_count, int) else 0)

        def _set_infuse_health_chain_count(chain_count: int) -> None:
            setattr(self.build, chain_count_attr, max(0, int(chain_count)))

        def _can_cast_infuse_health() -> bool:
            current_health = Agent.GetHealth(Player.GetAgentID())
            chain_count = _get_infuse_health_chain_count()
            if chain_count == 0:
                return current_health >= 0.75
            if chain_count == 1:
                return current_health > 0.30
            return False

        def _resolve_infuse_health_target() -> int:
            ally_array = Routines.Targeting.GetAllAlliesArray(Range.Spellcast.value)
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.IsAlive(agent_id),
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: agent_id != Player.GetAgentID(),
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.GetHealth(agent_id) < 0.40,
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: self.build.IsPartySpikeTarget(
                    agent_id,
                    drop_threshold=0.10,
                    sample_interval_ms=150,
                ),
            )

            ally_array = list(ally_array or [])
            ally_array.sort(
                key=lambda agent_id: (
                    -self.build.GetPartyHealthDelta(agent_id),
                    Agent.GetHealth(agent_id),
                )
            )
            return ally_array[0] if ally_array else 0

        if not self.build.IsSkillEquipped(infuse_health_id):
            return False
        if Agent.GetHealth(Player.GetAgentID()) >= 0.75:
            _set_infuse_health_chain_count(0)
        if not _can_cast_infuse_health():
            return False

        target_agent_id = _resolve_infuse_health_target()
        if not target_agent_id:
            return False

        if (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=infuse_health_id,
            target_agent_id=target_agent_id,
            extra_condition=_can_cast_infuse_health,
            log=False,
            aftercast_delay=250,
        )):
            _set_infuse_health_chain_count(_get_infuse_health_chain_count() + 1)
            return True

        return False

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

    
