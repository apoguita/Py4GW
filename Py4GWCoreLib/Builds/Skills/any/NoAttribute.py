from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Range, Routines
from Py4GWCoreLib.Skill import Skill
from .._targeting import EnemyClusterTargetingMixin

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["NoAttribute"]


class NoAttribute(EnemyClusterTargetingMixin):
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region A
    def Air_of_Superiority(self) -> BuildCoroutine:
        from Py4GWCoreLib import Player, GLOBAL_CACHE

        air_of_superiority_id: int = Skill.GetID("Air_of_Superiority")
        refresh_window_ms = 2000

        if not self.build.IsSkillEquipped(air_of_superiority_id):
            return False
        if Routines.Checks.Agents.HasEffect(Player.GetAgentID(), air_of_superiority_id):
            remaining_duration = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(
                Player.GetAgentID(),
                air_of_superiority_id,
            )
            if remaining_duration > refresh_window_ms:
                return False

        return (yield from self.build.CastSkillID(
            skill_id=air_of_superiority_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region C
    def Cry_of_Pain(self, allow_hex_fallback: bool = True) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, GLOBAL_CACHE, Range
        from HeroAI.utils import GetEffectAndBuffIds

        cry_of_pain_id: int = Skill.GetID("Cry_of_Pain")
        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(cry_of_pain_id) or Range.Nearby.value

        def _has_mesmer_hex(agent_id: int) -> bool:
            if not agent_id or not Agent.IsHexed(agent_id):
                return False
            for effect_skill_id in GetEffectAndBuffIds(agent_id):
                if not GLOBAL_CACHE.Skill.Flags.IsHex(effect_skill_id):
                    continue
                profession_id, _ = GLOBAL_CACHE.Skill.GetProfession(effect_skill_id)
                if profession_id == 8:
                    return True
            return False

        def _is_enemy_using_skill(agent_id: int) -> bool:
            return bool(
                agent_id
                and Agent.IsValid(agent_id)
                and not Agent.IsDead(agent_id)
                and Agent.IsCasting(agent_id)
            )

        if not self.build.IsSkillEquipped(cry_of_pain_id):
            return False

        enemy_array = self._get_enemy_array(Range.Spellcast.value)
        preferred_targets = [
            agent_id for agent_id in enemy_array
            if _is_enemy_using_skill(agent_id) and _has_mesmer_hex(agent_id)
        ]
        target_agent_id = self._pick_best_target(preferred_targets, aoe_range)

        if not target_agent_id:
            fallback_targets = [
                agent_id for agent_id in enemy_array
                if _is_enemy_using_skill(agent_id)
            ]
            target_agent_id = self._pick_best_target(fallback_targets, aoe_range)

        if not target_agent_id and allow_hex_fallback:
            mesmer_hex_targets = [
                agent_id for agent_id in enemy_array
                if _has_mesmer_hex(agent_id)
            ]
            target_agent_id = self._pick_best_target(mesmer_hex_targets, aoe_range)

        if not target_agent_id and allow_hex_fallback:
            hexed_targets = [
                agent_id for agent_id in enemy_array
                if Agent.IsHexed(agent_id)
            ]
            target_agent_id = self._pick_best_target(hexed_targets, aoe_range)

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=cry_of_pain_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

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

    #region E
    def Ebon_Vanguard_Assassin_Support(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, Range

        evas_id: int = Skill.GetID("Ebon_Vanguard_Assassin_Support")
        cluster_radius = Range.Nearby.value

        def _is_preferred_target(agent_id: int) -> bool:
            return (
                Agent.IsValid(agent_id)
                and not Agent.IsDead(agent_id)
                and (Agent.IsHexed(agent_id) or Agent.IsConditioned(agent_id))
            )

        if not self.build.IsSkillEquipped(evas_id):
            return False

        enemy_array = self._get_enemy_array(Range.Spellcast.value)
        preferred_targets = [
            agent_id for agent_id in enemy_array
            if _is_preferred_target(agent_id)
        ]
        target_agent_id = self._pick_best_target(preferred_targets, cluster_radius)

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=evas_id,
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
