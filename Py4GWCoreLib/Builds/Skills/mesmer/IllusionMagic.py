from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib import Agent, GLOBAL_CACHE, Player, Range, Routines
from .._targeting import EnemyClusterTargetingMixin

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["IllusionMagic"]


class IllusionMagic(EnemyClusterTargetingMixin):
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def _pick_illusion_target(self, skill_id: int) -> int:
        enemy_array = self._get_enemy_array(Range.Spellcast.value)
        if not enemy_array:
            return 0

        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(skill_id) or Range.Nearby.value
        attacking_targets = [agent_id for agent_id in enemy_array if Agent.IsAttacking(agent_id)]
        target_agent_id = self._pick_best_target(attacking_targets, aoe_range)

        if not target_agent_id:
            current_target_id = Player.GetTargetID()
            best_enemy_target_id = self._pick_best_target(enemy_array, aoe_range)
            if (
                current_target_id in enemy_array
                and Agent.IsValid(current_target_id)
                and not Agent.IsDead(current_target_id)
            ):
                current_target_score = self._get_cluster_score(current_target_id, aoe_range)
                best_enemy_score = self._get_cluster_score(best_enemy_target_id, aoe_range)
                if current_target_score >= best_enemy_score:
                    target_agent_id = current_target_id

        if not target_agent_id:
            target_agent_id = self._pick_best_target(enemy_array, aoe_range)

        return target_agent_id

    #region A
    def Arcane_Conundrum(self) -> BuildCoroutine:
        arcane_conundrum_id: int = Skill.GetID("Arcane_Conundrum")

        if not self.build.IsSkillEquipped(arcane_conundrum_id):
            return False

        target_agent_id: int = Routines.Agents.GetNearestEnemyCaster(Range.Spellcast.value)
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=arcane_conundrum_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region I
    def Ineptitude(self) -> BuildCoroutine:
        ineptitude_id: int = Skill.GetID("Ineptitude")
        if not self.build.IsSkillEquipped(ineptitude_id):
            return False
        target_agent_id = self._pick_illusion_target(ineptitude_id)
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=ineptitude_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Signet_of_Clumsiness(self) -> BuildCoroutine:
        signet_of_clumsiness_id: int = Skill.GetID("Signet_of_Clumsiness")
        if not self.build.IsSkillEquipped(signet_of_clumsiness_id):
            return False
        target_agent_id = self._pick_illusion_target(signet_of_clumsiness_id)
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=signet_of_clumsiness_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region W
    def Wandering_Eye(self) -> BuildCoroutine:
        wandering_eye_id: int = Skill.GetID("Wandering_Eye")
        if not self.build.IsSkillEquipped(wandering_eye_id):
            return False
        target_agent_id = self._pick_illusion_target(wandering_eye_id)
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=wandering_eye_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
