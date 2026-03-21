from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill
from .._targeting import EnemyClusterTargetingMixin

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["DominationMagic"]


class DominationMagic(EnemyClusterTargetingMixin):
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region E
    def Energy_Surge(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, Player, Range, GLOBAL_CACHE

        energy_surge_id: int = Skill.GetID("Energy_Surge")

        if not self.build.IsSkillEquipped(energy_surge_id):
            return False

        enemy_array = self._get_enemy_array(Range.Spellcast.value)
        if not enemy_array:
            return False

        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(energy_surge_id) or Range.Nearby.value

        def _is_enemy_casting_spell(agent_id: int) -> bool:
            if not (
                agent_id
                and Agent.IsValid(agent_id)
                and not Agent.IsDead(agent_id)
                and Agent.IsCaster(agent_id)
            ):
                return False
            if not Agent.IsCasting(agent_id):
                return False
            casting_skill_id = Agent.GetCastingSkillID(agent_id)
            return bool(casting_skill_id and GLOBAL_CACHE.Skill.Flags.IsSpell(casting_skill_id))

        casting_spell_targets = [
            agent_id for agent_id in enemy_array
            if _is_enemy_casting_spell(agent_id)
        ]
        target_agent_id = self._pick_best_target(casting_spell_targets, aoe_range)

        if not target_agent_id:
            current_target_id = Player.GetTargetID()
            best_enemy_target_id = self._pick_best_target(enemy_array, aoe_range)
            if Agent.IsValid(current_target_id) and not Agent.IsDead(current_target_id):
                current_target_score = self._get_cluster_score(current_target_id, aoe_range)
                best_enemy_score = self._get_cluster_score(best_enemy_target_id, aoe_range)
                if current_target_score >= best_enemy_score:
                    target_agent_id = current_target_id

        if not target_agent_id:
            target_agent_id = self._pick_best_target(enemy_array, aoe_range)

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=energy_surge_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region C
    def Cry_of_Frustration(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, Range, GLOBAL_CACHE

        cry_of_frustration_id: int = Skill.GetID("Cry_of_Frustration")
        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(cry_of_frustration_id) or Range.Nearby.value

        def _is_enemy_using_skill(agent_id: int) -> bool:
            return bool(
                agent_id
                and Agent.IsValid(agent_id)
                and not Agent.IsDead(agent_id)
                and Agent.IsCasting(agent_id)
            )

        enemy_array = self._get_enemy_array(Range.Spellcast.value)
        casting_targets = [
            agent_id for agent_id in enemy_array
            if _is_enemy_using_skill(agent_id)
        ]
        target_agent_id = self._pick_best_target(casting_targets, aoe_range)

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=cry_of_frustration_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region M
    def Mistrust(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, Range, GLOBAL_CACHE

        mistrust_id: int = Skill.GetID("Mistrust")
        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(mistrust_id) or Range.Nearby.value

        def _is_enemy_casting_spell(agent_id: int) -> bool:
            if not agent_id:
                return False
            if not Agent.IsValid(agent_id) or Agent.IsDead(agent_id):
                return False
            if not Agent.IsCasting(agent_id):
                return False
            casting_skill_id = Agent.GetCastingSkillID(agent_id)
            return bool(casting_skill_id and GLOBAL_CACHE.Skill.Flags.IsSpell(casting_skill_id))

        enemy_array = self._get_enemy_array(Range.Spellcast.value)
        casting_spell_targets = [
            agent_id for agent_id in enemy_array
            if _is_enemy_casting_spell(agent_id)
        ]
        target_agent_id = self._pick_best_target(casting_spell_targets, aoe_range)

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=mistrust_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region O
    def Overload(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, Player, Range, GLOBAL_CACHE

        overload_id: int = Skill.GetID("Overload")
        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(overload_id) or Range.Adjacent.value

        def _is_enemy_using_skill(agent_id: int) -> bool:
            return bool(
                agent_id
                and Agent.IsValid(agent_id)
                and not Agent.IsDead(agent_id)
                and Agent.IsCasting(agent_id)
            )

        enemy_array = self._get_enemy_array(Range.Spellcast.value)
        casting_targets = [
            agent_id for agent_id in enemy_array
            if _is_enemy_using_skill(agent_id)
        ]
        target_agent_id = self._pick_best_target(casting_targets, aoe_range)

        if not target_agent_id:
            current_target_id = Player.GetTargetID()
            best_enemy_target_id = self._pick_best_target(enemy_array, aoe_range)
            if Agent.IsValid(current_target_id) and not Agent.IsDead(current_target_id):
                current_target_score = self._get_cluster_score(current_target_id, aoe_range)
                best_enemy_score = self._get_cluster_score(best_enemy_target_id, aoe_range)
                if current_target_score >= best_enemy_score:
                    target_agent_id = current_target_id

        if not target_agent_id:
            target_agent_id = self._pick_best_target(enemy_array, aoe_range)

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=overload_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region U
    def Unnatural_Signet(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, Range, GLOBAL_CACHE

        unnatural_signet_id: int = Skill.GetID("Unnatural_Signet")

        if not self.build.IsSkillEquipped(unnatural_signet_id):
            return False

        enemy_array = self._get_enemy_array(Range.Spellcast.value)
        if not enemy_array:
            return False

        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(unnatural_signet_id) or Range.Adjacent.value

        preferred_targets = [
            agent_id for agent_id in enemy_array
            if Agent.IsHexed(agent_id) or Agent.IsEnchanted(agent_id)
        ]
        target_agent_id = self._pick_best_target(preferred_targets, aoe_range)
        if not target_agent_id:
            target_agent_id = self._pick_best_target(enemy_array, aoe_range)

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=unnatural_signet_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
