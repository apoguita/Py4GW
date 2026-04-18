from __future__ import annotations

from typing import TYPE_CHECKING

from HeroAI.targeting import TargetCasterClusterEnemy, TargetMeleeOrMartialClusterEnemy
from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["IllusionMagic"]


class IllusionMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region A
    def Arcane_Conundrum(self) -> BuildCoroutine:
        arcane_conundrum_id: int = Skill.GetID("Arcane_Conundrum")

        if not self.build.IsSkillEquipped(arcane_conundrum_id):
            return False

        target_agent_id = TargetCasterClusterEnemy(arcane_conundrum_id)
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

        target_agent_id = TargetMeleeOrMartialClusterEnemy(ineptitude_id)
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

        # Signet of Clumsiness only interrupts and deals damage when the
        # target is attacking, so require an attacking enemy in both the
        # primary and fallback branches; if no attacker exists, skip the cast.
        target_agent_id = TargetMeleeOrMartialClusterEnemy(
            signet_of_clumsiness_id,
            require_attacking=True,
        )
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

        target_agent_id = TargetMeleeOrMartialClusterEnemy(wandering_eye_id)
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=wandering_eye_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
