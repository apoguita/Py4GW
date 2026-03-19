from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, Range, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from HeroAI.targeting import GetAllAlliesArray

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["RestorationMagic"]


class RestorationMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def _has_spirit_in_earshot(self) -> bool:
        return bool(Routines.Agents.GetNearestSpirit(Range.Earshot.value))

    #region B
    def Breath_of_the_Great_Dwarf(self) -> BuildCoroutine:
        if False:
            yield
        return False
    #endregion

    #region L
    def Life(self) -> BuildCoroutine:
        life_id: int = Skill.GetID("Life")

        if not self.build.IsSkillEquipped(life_id):
            return False

        return (yield from self.build.CastSpiritSkillID(
            skill_id=life_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region M
    def Mend_Body_and_Soul(self) -> BuildCoroutine:
        mend_body_and_soul_id: int = Skill.GetID("Mend_Body_and_Soul")
        mend_body_and_soul: CustomSkill = self.build.GetCustomSkill(mend_body_and_soul_id)

        def _resolve_mend_body_and_soul_target() -> int:
            ally_array = GetAllAlliesArray(Range.Spellcast.value)
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.IsAlive(agent_id),
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.GetHealth(agent_id) < mend_body_and_soul.Conditions.LessLife,
            )

            if self._has_spirit_in_earshot():
                conditioned_allies = AgentArray.Filter.ByCondition(
                    ally_array,
                    lambda agent_id: Agent.IsConditioned(agent_id),
                )
                if conditioned_allies:
                    conditioned_allies = AgentArray.Sort.ByHealth(conditioned_allies)
                    return conditioned_allies[0]

            ally_array = AgentArray.Sort.ByHealth(ally_array)
            return ally_array[0] if ally_array else 0

        if not self.build.IsSkillEquipped(mend_body_and_soul_id):
            return False

        target_agent_id = _resolve_mend_body_and_soul_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            mend_body_and_soul_id,
            target_agent_id,
        ))

    def Mending_Grip(self) -> BuildCoroutine:
        mending_grip_id: int = Skill.GetID("Mending_Grip")
        mending_grip: CustomSkill = self.build.GetCustomSkill(mending_grip_id)

        def _resolve_mending_grip_target() -> int:
            ally_array = GetAllAlliesArray(Range.Spellcast.value)
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.IsAlive(agent_id),
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.GetHealth(agent_id) < mending_grip.Conditions.LessLife,
            )

            conditioned_weapon_spelled_allies = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.IsConditioned(agent_id) and Agent.IsWeaponSpelled(agent_id),
            )
            if conditioned_weapon_spelled_allies:
                conditioned_weapon_spelled_allies = AgentArray.Sort.ByHealth(conditioned_weapon_spelled_allies)
                return conditioned_weapon_spelled_allies[0]

            ally_array = AgentArray.Sort.ByHealth(ally_array)
            return ally_array[0] if ally_array else 0

        if not self.build.IsSkillEquipped(mending_grip_id):
            return False

        target_agent_id = _resolve_mending_grip_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            mending_grip_id,
            target_agent_id,
        ))
    #endregion

    #region X
    def Xinraes_Weapon(self) -> BuildCoroutine:
        xinraes_weapon_id: int = Skill.GetID("Xinraes_Weapon")
        xinraes_weapon: CustomSkill = self.build.GetCustomSkill(xinraes_weapon_id)

        def _resolve_xinraes_weapon_target() -> int:
            return self.build.ResolveAllyTarget(
                xinraes_weapon_id,
                xinraes_weapon,
            )

        if not self.build.IsSkillEquipped(xinraes_weapon_id):
            return False

        target_agent_id = _resolve_xinraes_weapon_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            xinraes_weapon_id,
            target_agent_id,
        ))
    #endregion

    #region R
    def Recovery(self) -> BuildCoroutine:
        recovery_id: int = Skill.GetID("Recovery")

        if not self.build.IsSkillEquipped(recovery_id):
            return False

        return (yield from self.build.CastSpiritSkillID(
            skill_id=recovery_id,
            log=False,
            aftercast_delay=250,
        ))

    def Recuperation(self) -> BuildCoroutine:
        recuperation_id: int = Skill.GetID("Recuperation")

        if not self.build.IsSkillEquipped(recuperation_id):
            return False

        return (yield from self.build.CastSpiritSkillID(
            skill_id=recuperation_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Spirit_Light(self) -> BuildCoroutine:
        spirit_light_id: int = Skill.GetID("Spirit_Light")
        spirit_light: CustomSkill = self.build.GetCustomSkill(spirit_light_id)

        def _can_safely_cast_spirit_light() -> bool:
            return (
                self._has_spirit_in_earshot()
                or Agent.GetHealth(Player.GetAgentID()) > spirit_light.Conditions.SacrificeHealth
            )

        def _resolve_spirit_light_target() -> int:
            ally_array = GetAllAlliesArray(Range.Spellcast.value)
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.IsAlive(agent_id),
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.GetHealth(agent_id) < spirit_light.Conditions.LessLife,
            )

            if not self._has_spirit_in_earshot():
                ally_array = AgentArray.Filter.ByCondition(
                    ally_array,
                    lambda agent_id: agent_id != Player.GetAgentID(),
                )

            ally_array = AgentArray.Sort.ByHealth(ally_array)
            return ally_array[0] if ally_array else 0

        if not self.build.IsSkillEquipped(spirit_light_id):
            return False
        if not _can_safely_cast_spirit_light():
            return False

        target_agent_id = _resolve_spirit_light_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            spirit_light_id,
            target_agent_id,
            extra_condition=_can_safely_cast_spirit_light,
        ))

    def Spirit_Transfer(self) -> BuildCoroutine:
        spirit_transfer_id: int = Skill.GetID("Spirit_Transfer")
        spirit_transfer: CustomSkill = self.build.GetCustomSkill(spirit_transfer_id)

        def _resolve_spirit_transfer_target() -> int:
            if not Routines.Agents.GetNearestSpirit(Range.Spellcast.value):
                return 0

            ally_array = GetAllAlliesArray(Range.Spellcast.value)
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.IsAlive(agent_id),
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.GetHealth(agent_id) < spirit_transfer.Conditions.LessLife,
            )
            ally_array = AgentArray.Sort.ByHealth(ally_array)
            return ally_array[0] if ally_array else 0

        if not self.build.IsSkillEquipped(spirit_transfer_id):
            return False

        target_agent_id = _resolve_spirit_transfer_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            spirit_transfer_id,
            target_agent_id,
        ))
    #endregion

    #region W
    def Wielders_Boon(self) -> BuildCoroutine:
        wielders_boon_id: int = Skill.GetID("Wielders_Boon")
        wielders_boon: CustomSkill = self.build.GetCustomSkill(wielders_boon_id)

        def _resolve_wielders_boon_target() -> int:
            ally_array = GetAllAlliesArray(Range.Spellcast.value)
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.IsAlive(agent_id),
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.GetHealth(agent_id) < wielders_boon.Conditions.LessLife,
            )

            weapon_spelled_allies = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.IsWeaponSpelled(agent_id),
            )
            if weapon_spelled_allies:
                weapon_spelled_allies = AgentArray.Sort.ByHealth(weapon_spelled_allies)
                return weapon_spelled_allies[0]

            ally_array = AgentArray.Sort.ByHealth(ally_array)
            return ally_array[0] if ally_array else 0

        if not self.build.IsSkillEquipped(wielders_boon_id):
            return False

        target_agent_id = _resolve_wielders_boon_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            wielders_boon_id,
            target_agent_id,
        ))
    #endregion
