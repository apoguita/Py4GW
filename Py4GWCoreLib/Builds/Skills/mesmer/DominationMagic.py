from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["DominationMagic"]


class DominationMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def _get_enemy_array(self, max_distance: float) -> list[int]:
        from Py4GWCoreLib import Agent, AgentArray, Player, Routines

        player_x, player_y = Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, max_distance)
        return AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: Agent.IsValid(agent_id) and not Agent.IsDead(agent_id),
        )

    def _get_cluster_score(self, agent_id: int, cluster_radius: float) -> int:
        from Py4GWCoreLib import Agent, AgentArray, Routines

        if not agent_id or cluster_radius <= 0:
            return 0

        target_x, target_y = Agent.GetXY(agent_id)
        nearby_enemies = Routines.Agents.GetFilteredEnemyArray(target_x, target_y, cluster_radius)
        nearby_enemies = AgentArray.Filter.ByCondition(
            nearby_enemies,
            lambda enemy_id: Agent.IsValid(enemy_id) and not Agent.IsDead(enemy_id),
        )
        return max(0, len(nearby_enemies) - 1)

    def _pick_best_target(self, agent_ids: list[int], cluster_radius: float) -> int:
        from Py4GWCoreLib import Agent, Player, Utils

        if not agent_ids:
            return 0

        player_pos = Player.GetXY()
        scored_targets = [
            (
                self._get_cluster_score(agent_id, cluster_radius),
                Utils.Distance(player_pos, Agent.GetXY(agent_id)),
                agent_id,
            )
            for agent_id in agent_ids
        ]
        scored_targets.sort(key=lambda item: (-item[0], item[1]))
        return scored_targets[0][2]

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

    #region P
    def Power_Drain(self) -> BuildCoroutine:
        from Py4GWCoreLib import Routines, Range

        power_drain_id: int = Skill.GetID("Power_Drain")

        if not self.build.IsSkillEquipped(power_drain_id):
            return False

        target_agent_id: int = Routines.Targeting.GetEnemyCastingSpell(Range.Spellcast.value)
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=power_drain_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Shatter_Hex(self) -> BuildCoroutine:
        shatter_hex_id: int = Skill.GetID("Shatter_Hex")
        shatter_hex: CustomSkill = self.build.GetCustomSkill(shatter_hex_id)

        if not self.build.IsSkillEquipped(shatter_hex_id):
            return False

        target_agent_id = self.build.ResolveAllyTarget(
            shatter_hex_id,
            shatter_hex,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=shatter_hex_id,
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
