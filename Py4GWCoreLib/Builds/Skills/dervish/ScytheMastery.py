from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib import GLOBAL_CACHE, Range, Routines, SkillBar, Utils
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr


class ScytheMastery:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def Count_Active_Dervish_Enchantments(self, skill_ids: tuple[int, ...] | None = None) -> int:
        player_agent_id = Player.GetAgentID()
        if skill_ids is not None:
            return sum(
                1
                for skill_id in skill_ids
                if Routines.Checks.Agents.HasEffect(player_agent_id, skill_id)
            )

        count = 0
        for effect_skill_id in self.build.GetEffectAndBuffIds(player_agent_id):
            _, skill_type_name = GLOBAL_CACHE.Skill.GetType(effect_skill_id)
            _, profession_name = GLOBAL_CACHE.Skill.GetProfession(effect_skill_id)
            if skill_type_name == "Enchantment" and profession_name == "Dervish":
                count += 1
        return count

    def Has_Enough_Adrenaline(self, skill_id: int) -> bool:
        slot = SkillBar.GetSlotBySkillID(skill_id)
        if not (1 <= slot <= 8):
            return False
        return bool(Routines.Checks.Skills.HasEnoughAdrenalineBySlot(slot))

    def _resolve_attack_target(self, target_agent_id: int = 0) -> int:
        return int(target_agent_id or self.build.current_target_id or Player.GetTargetID() or 0)

    def _is_in_melee_contact(self, target_agent_id: int) -> bool:
        if not target_agent_id or not Agent.IsValid(target_agent_id) or Agent.IsDead(target_agent_id):
            return False
        return Utils.Distance(Player.GetXY(), Agent.GetXY(target_agent_id)) <= Range.Adjacent.value

    def _can_use_scythe_attack(
        self,
        skill_id: int,
        target_agent_id: int,
        *,
        min_self_energy_pct: float = 0.0,
        require_dervish_enchantment: bool = False,
    ) -> bool:
        if not self.build.IsSkillEquipped(skill_id):
            return False
        if not self._is_in_melee_contact(target_agent_id):
            return False
        if float(Agent.GetEnergy(Player.GetAgentID()) or 0.0) < min_self_energy_pct:
            return False
        if require_dervish_enchantment and self.Count_Active_Dervish_Enchantments() <= 0:
            return False
        return True

    #region E
    def Eremites_Attack(
        self,
        target_agent_id: int = 0,
        *,
        cluster_size: int = 0,
        min_cluster_size: int = 0,
        min_self_energy_pct: float = 0.0,
        require_dervish_enchantment: bool = False,
    ) -> BuildCoroutine:
        eremites_attack_id: int = Skill.GetID("Eremites_Attack")
        target_agent_id = self._resolve_attack_target(target_agent_id)

        if min_cluster_size and cluster_size < min_cluster_size:
            return False
        if not self._can_use_scythe_attack(
            eremites_attack_id,
            target_agent_id,
            min_self_energy_pct=min_self_energy_pct,
            require_dervish_enchantment=require_dervish_enchantment,
        ):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=eremites_attack_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region T
    def Twin_Moon_Sweep(
        self,
        target_agent_id: int = 0,
        *,
        cluster_size: int = 0,
        min_self_energy_pct: float = 0.0,
        require_dervish_enchantment: bool = False,
    ) -> BuildCoroutine:
        del cluster_size

        twin_moon_sweep_id: int = Skill.GetID("Twin_Moon_Sweep")
        target_agent_id = self._resolve_attack_target(target_agent_id)

        if not self._can_use_scythe_attack(
            twin_moon_sweep_id,
            target_agent_id,
            min_self_energy_pct=min_self_energy_pct,
            require_dervish_enchantment=require_dervish_enchantment,
        ):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=twin_moon_sweep_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
