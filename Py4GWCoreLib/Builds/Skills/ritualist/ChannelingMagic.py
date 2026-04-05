from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, Range, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["ChannelingMagic"]


class ChannelingMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region S
    def Signet_of_Spirits(self) -> BuildCoroutine:
        signet_of_spirits_id: int = Skill.GetID("Signet_of_Spirits")

        if not self.build.IsSkillEquipped(signet_of_spirits_id):
            return False

        return (yield from self.build.CastSpiritSkillID(
            skill_id=signet_of_spirits_id,
            log=False,
            aftercast_delay=250,
        ))

    def Summon_Spirits(self) -> BuildCoroutine:
        """Cast Summon Spirits (kurzick or luxon variant). Relocates owned spirits to player position."""
        summon_k_id: int = Skill.GetID("Summon_Spirits_kurzick")
        summon_l_id: int = Skill.GetID("Summon_Spirits_luxon")

        skill_id = summon_k_id if self.build.IsSkillEquipped(summon_k_id) else summon_l_id
        if not self.build.IsSkillEquipped(skill_id):
            return False

        spirits = AgentArray.GetSpiritPetArray()
        player_pos = Player.GetXY()
        far_spirits = AgentArray.Filter.ByCondition(
            spirits,
            lambda s: Agent.IsAlive(s) and Agent.IsSpawned(s),
        )
        far_spirits = [s for s in far_spirits if not AgentArray.Filter.ByDistance([s], player_pos, Range.Earshot.value)]
        if not far_spirits:
            return False

        return (yield from self.build.CastSkillID(
            skill_id=skill_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region B
    def Bloodsong(self) -> BuildCoroutine:
        bloodsong_id: int = Skill.GetID("Bloodsong")

        if not self.build.IsSkillEquipped(bloodsong_id):
            return False

        return (yield from self.build.CastSpiritSkillID(
            skill_id=bloodsong_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region V
    def Vampirism(self) -> BuildCoroutine:
        vampirism_id: int = Skill.GetID("Vampirism")

        if not self.build.IsSkillEquipped(vampirism_id):
            return False

        return (yield from self.build.CastSpiritSkillID(
            skill_id=vampirism_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region G
    def Gaze_of_Fury(self) -> BuildCoroutine:
        """Destroy target enemy spirit and create a spirit of Gaze of Fury."""
        gaze_of_fury_id: int = Skill.GetID("Gaze_of_Fury")

        if not self.build.IsSkillEquipped(gaze_of_fury_id):
            return False

        spirits = AgentArray.GetSpiritPetArray()
        spirits = AgentArray.Filter.ByDistance(spirits, Player.GetXY(), Range.Spellcast.value)
        enemy_spirits = AgentArray.Filter.ByCondition(
            spirits,
            lambda s: Agent.IsAlive(s) and not Agent.GetIsAlly(s),
        )
        if not enemy_spirits:
            return (yield from self.build.CastSpiritSkillID(
                skill_id=gaze_of_fury_id,
                log=False,
                aftercast_delay=250,
            ))

        target_id = enemy_spirits[0]
        return (yield from self.build.CastSkillID(
            skill_id=gaze_of_fury_id,
            target_agent_id=target_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region P
    def Painful_Bond(self) -> BuildCoroutine:
        """Hex target foe. Only effective if spirits are nearby."""
        painful_bond_id: int = Skill.GetID("Painful_Bond")

        if not self.build.IsSkillEquipped(painful_bond_id):
            return False

        spirits = AgentArray.GetSpiritPetArray()
        spirits = AgentArray.Filter.ByDistance(spirits, Player.GetXY(), Range.Earshot.value)
        spirits = AgentArray.Filter.ByCondition(spirits, lambda s: Agent.IsAlive(s))
        if len(spirits) < 2:
            return False

        enemies = Routines.Agents.GetFilteredEnemyArray(*Player.GetXY(), Range.Spellcast.value)
        if not enemies:
            return False

        return (yield from self.build.CastSkillID(
            skill_id=painful_bond_id,
            target_agent_id=enemies[0],
            log=False,
            aftercast_delay=250,
        ))
    #endregion
