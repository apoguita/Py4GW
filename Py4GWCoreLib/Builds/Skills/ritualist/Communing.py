from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, Player, Range, Routines, SpiritModelID
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["Communing"]


class Communing:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    _CORE_SPIRIT_MODELS = {
        SpiritModelID.SHELTER,
        SpiritModelID.UNION,
        SpiritModelID.DISPLACEMENT,
    }

    def _is_soul_twisting_ready(self, min_remaining_ms: int = 1200) -> bool:
        soul_twisting_id = Skill.GetID("Soul_Twisting")
        player_agent_id = Player.GetAgentID()
        if not Routines.Checks.Agents.HasEffect(player_agent_id, soul_twisting_id):
            return False
        remaining_ms = int(GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id, soul_twisting_id) or 0)
        return remaining_ms > min_remaining_ms

    def _get_owned_core_spirits(self, max_distance: float = Range.Spellcast.value) -> list[int]:
        player_agent_id = Player.GetAgentID()
        spirits = AgentArray.GetSpiritPetArray()
        spirits = AgentArray.Filter.ByDistance(spirits, Player.GetXY(), max_distance)
        spirits = AgentArray.Filter.ByCondition(
            spirits,
            lambda spirit_id: Agent.IsAlive(spirit_id) and Agent.IsSpawned(spirit_id),
        )

        owned_spirits: list[int] = []
        ownerless_spirits: list[int] = []
        nearby_spirits: list[int] = []
        for spirit_id in spirits:
            model_value = Agent.GetPlayerNumber(spirit_id)
            if model_value not in SpiritModelID._value2member_map_:
                continue
            if SpiritModelID(model_value) not in self._CORE_SPIRIT_MODELS:
                continue
            nearby_spirits.append(spirit_id)

            owner_id = Agent.GetOwnerID(spirit_id)
            if owner_id == player_agent_id:
                owned_spirits.append(spirit_id)
            elif owner_id == 0:
                ownerless_spirits.append(spirit_id)

        if owned_spirits:
            return owned_spirits
        if ownerless_spirits:
            return ownerless_spirits
        return nearby_spirits

    def _resolve_armor_of_unfeeling_target(self) -> int:
        spirits = self._get_owned_core_spirits(Range.Spellcast.value)
        if not spirits:
            return 0
        spirits = AgentArray.Sort.ByHealth(spirits)
        for spirit_id in spirits:
            model_value = Agent.GetPlayerNumber(spirit_id)
            if model_value not in SpiritModelID._value2member_map_:
                continue
            if SpiritModelID(model_value) == SpiritModelID.DISPLACEMENT:
                continue
            return spirit_id
        return spirits[0]

    def _cast_protective_spirit(self, skill_id: int) -> BuildCoroutine:
        if not self.build.IsSkillEquipped(skill_id):
            return False
        if not self._is_soul_twisting_ready():
            return False

        return (yield from self.build.CastSpiritSkillID(
            skill_id=skill_id,
            log=False,
            aftercast_delay=250,
        ))

    #region V
    def Vital_Weapon(self) -> BuildCoroutine:
        vital_weapon_id: int = Skill.GetID("Vital_Weapon")

        if not self.build.IsSkillEquipped(vital_weapon_id):
            return False
        vital_weapon: CustomSkill = self.build.GetCustomSkill(vital_weapon_id)
        target_agent_id = self.build.ResolveAllyTarget(
            vital_weapon_id,
            vital_weapon,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            vital_weapon_id,
            target_agent_id,
        ))
    #endregion

    #region A
    def Armor_of_Unfeeling(self) -> BuildCoroutine:
        armor_of_unfeeling_id: int = Skill.GetID("Armor_of_Unfeeling")

        if not self.build.IsSkillEquipped(armor_of_unfeeling_id):
            return False
        spirits = self._get_owned_core_spirits(Range.Spellcast.value)
        if len(spirits) < 2:
            return False

        target_agent_id = self._resolve_armor_of_unfeeling_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=armor_of_unfeeling_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region D
    def Displacement(self) -> BuildCoroutine:
        displacement_id: int = Skill.GetID("Displacement")
        return (yield from self._cast_protective_spirit(displacement_id))
    #endregion

    #region S
    def Shelter(self) -> BuildCoroutine:
        shelter_id: int = Skill.GetID("Shelter")
        return (yield from self._cast_protective_spirit(shelter_id))
    #endregion

    #region U
    def Union(self) -> BuildCoroutine:
        union_id: int = Skill.GetID("Union")
        return (yield from self._cast_protective_spirit(union_id))
    #endregion
