from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Range, Routines, ThrottledTimer
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.GlobalCache.WhiteboardLocks import (
    BLOOD_ENERGY_BUFF_LOCK_KEY,
    is_buff_target_lock_blocked,
    post_buff_target_lock,
)
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["BloodMagic"]


class BloodMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self.bip_throttle: ThrottledTimer = ThrottledTimer(1500)
        self.bip_throttle.Stop()
        self.blood_ritual_throttle: ThrottledTimer = ThrottledTimer(1500)
        self.blood_ritual_throttle.Stop()

    #region B
    def Blood_Bond(self) -> BuildCoroutine:
        blood_bond_id: int = Skill.GetID("Blood_Bond")

        if not self.build.IsSkillEquipped(blood_bond_id):
            return False
        if not self.build.IsInAggro():
            return False

        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=Range.Adjacent.value,
            preferred_condition=lambda agent_id: not Routines.Checks.Agents.HasEffect(agent_id, blood_bond_id),
            filter_radius=Range.Spellcast.value,
        )
        if not target_agent_id:
            return False
        if Routines.Checks.Agents.HasEffect(target_agent_id, blood_bond_id):
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            blood_bond_id,
            target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def Blood_Ritual(self) -> BuildCoroutine:
        blood_ritual_id: int = Skill.GetID("Blood_Ritual")
        blood_ritual: CustomSkill = self.build.GetCustomSkill(blood_ritual_id)

        def _is_blood_ritual_throttle_ready() -> bool:
            return self.blood_ritual_throttle.IsStopped() or self.blood_ritual_throttle.IsExpired()

        def _can_safely_cast_blood_ritual() -> bool:
            player_id = Player.GetAgentID()
            current_hp_fraction = float(Agent.GetHealth(player_id))
            sacrifice_floor = float(blood_ritual.Conditions.SacrificeHealth or 0.0)
            return current_hp_fraction > sacrifice_floor

        if not self.build.IsSkillEquipped(blood_ritual_id):
            return False

        target_agent_id: int = self.build.ResolveAllyTarget(
            blood_ritual_id,
            blood_ritual,
        )
        if not target_agent_id:
            return False
        if is_buff_target_lock_blocked(target_agent_id, BLOOD_ENERGY_BUFF_LOCK_KEY):
            return False
        if not _is_blood_ritual_throttle_ready():
            return False
        if not _can_safely_cast_blood_ritual():
            return False

        post_buff_target_lock(
            target_agent_id,
            key_id=BLOOD_ENERGY_BUFF_LOCK_KEY,
            skill_id=blood_ritual_id,
        )
        if (yield from self.build.CastSkillIDAndRestoreTarget(
            blood_ritual_id,
            target_agent_id,
            extra_condition=_can_safely_cast_blood_ritual,
        )):
            self.blood_ritual_throttle.Reset()
            return True

        return False

    def Blood_is_Power(self) -> BuildCoroutine:
        blood_is_power_id: int = Skill.GetID("Blood_is_Power")
        blood_is_power: CustomSkill = self.build.GetCustomSkill(blood_is_power_id)

        def _is_bip_throttle_ready() -> bool:
            return self.bip_throttle.IsStopped() or self.bip_throttle.IsExpired()

        def _can_safely_cast_bip() -> bool:
            # Refuse if the caster's HP after the BiP sacrifice would land at or
            # below the percent-of-max floor or the absolute-HP floor. Mirrors the
            # post-sacrifice safety check in HeroAI/combat.py so the build path
            # honors the same floors as the HeroAI fallback.
            player_id = Player.GetAgentID()
            conditions = blood_is_power.Conditions

            current_hp_fraction = float(Agent.GetHealth(player_id))
            sacrifice_floor = float(conditions.SacrificeHealth or 0.0)
            if current_hp_fraction <= sacrifice_floor:
                return False

            sacrifice_pct = float(conditions.SacrificePercent or 0.0)
            min_after_pct = float(conditions.MinHealthAfterSacrificePercent or 0.0)
            min_after_abs = int(conditions.MinHealthAfterSacrificeAbsolute or 0)
            if sacrifice_pct > 0 and (min_after_pct > 0 or min_after_abs > 0):
                max_hp = Agent.GetMaxHealth(player_id)
                if max_hp <= 0:
                    return False
                sacrifice_amount = max_hp * sacrifice_pct
                hp_after_sacrifice = (current_hp_fraction * max_hp) - sacrifice_amount
                if min_after_abs > 0 and hp_after_sacrifice <= min_after_abs:
                    return False
                if min_after_pct > 0 and (hp_after_sacrifice / max_hp) <= min_after_pct:
                    return False

            return True

        if not self.build.IsSkillEquipped(blood_is_power_id):
            return False

        target_agent_id: int = self.build.ResolveAllyTarget(
            blood_is_power_id,
            blood_is_power,
        )
        if not target_agent_id:
            return False
        if is_buff_target_lock_blocked(target_agent_id, BLOOD_ENERGY_BUFF_LOCK_KEY):
            return False
        if not _is_bip_throttle_ready():
            return False
        if not _can_safely_cast_bip():
            return False

        post_buff_target_lock(
            target_agent_id,
            key_id=BLOOD_ENERGY_BUFF_LOCK_KEY,
            skill_id=blood_is_power_id,
        )
        if (yield from self.build.CastSkillIDAndRestoreTarget(
            blood_is_power_id,
            target_agent_id,
            extra_condition=_can_safely_cast_bip,
        )):
            self.bip_throttle.Reset()
            return True

        return False
    #endregion
