from __future__ import annotations

from Py4GWCoreLib import AgentArray, BuildMgr, Profession, Range, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.Builds.Skills import SkillsTemplate
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils


MASOCHISM_ID = Skill.GetID("Masochism")
SOUL_TAKER_ID = Skill.GetID("Soul_Taker")
TWIN_MOON_SWEEP_ID = Skill.GetID("Twin_Moon_Sweep")
EREMITES_ATTACK_ID = Skill.GetID("Eremites_Attack")
STAGGERING_FORCE_ID = Skill.GetID("Staggering_Force")
DUST_CLOAK_ID = Skill.GetID("Dust_Cloak")
DRUNKEN_MASTER_ID = Skill.GetID("Drunken_Master")
I_AM_UNSTOPPABLE_ID = Skill.GetID("I_Am_Unstoppable")


class Soul_Taker_Scythe(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Soul Taker Scythe",
            required_primary=Profession.Necromancer,
            required_secondary=Profession.Dervish,
            template_code="OApjYwpzKTbhf1PXNXaXZXqi0kA",
            required_skills=[
                MASOCHISM_ID,
                SOUL_TAKER_ID,
                TWIN_MOON_SWEEP_ID,
                EREMITES_ATTACK_ID,
                STAGGERING_FORCE_ID,
                DUST_CLOAK_ID,
                DRUNKEN_MASTER_ID,
                I_AM_UNSTOPPABLE_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skillbook: SkillsTemplate = SkillsTemplate(self)

    def _get_player_contact_count(self) -> int:
        player_x, player_y = Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, Range.Adjacent.value)
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: Agent.IsValid(agent_id) and not Agent.IsDead(agent_id),
        )
        return len(enemy_array or [])

    def _is_in_melee_contact(self, target_agent_id: int) -> bool:
        if not target_agent_id or not Agent.IsValid(target_agent_id) or Agent.IsDead(target_agent_id):
            return False
        return Utils.Distance(Player.GetXY(), Agent.GetXY(target_agent_id)) <= Range.Adjacent.value

    def _auto_attack_cluster(self):
        return (yield from self.AutoAttack(target_type="EnemyClustered"))

    def _run_local_skill_logic(self):
        if not (self.IsInAggro() or self.IsCloseToAggro()):
            return False

        contact_count = self._get_player_contact_count()

        if self.IsSkillEquipped(I_AM_UNSTOPPABLE_ID) and (
            yield from self.skillbook.Any.NoAttribute.I_Am_Unstoppable(
                contact_count=contact_count,
                min_adjacent_enemies=2,
                refresh_window_ms=1000,
                aftercast_delay=150,
            )
        ):
            return True

        if self.IsSkillEquipped(MASOCHISM_ID) and (
            yield from self.skillbook.Necromancer.SoulReaping.Masochism()
        ):
            return True

        if (yield from self.skillbook.Necromancer.SoulReaping.Soul_Taker(refresh_window_ms=2000)):
            return True

        if (yield from self.skillbook.Any.PvE.Drunken_Master(refresh_window_ms=2000)):
            return True

        target_agent_id = self.current_target_id
        if not self._is_in_melee_contact(target_agent_id):
            if (yield from self._auto_attack_cluster()):
                return True
            target_agent_id = self.current_target_id

        target_cluster_size = 0
        if target_agent_id and Agent.IsValid(target_agent_id) and not Agent.IsDead(target_agent_id):
            target_cluster_size = 1 + Routines.Targeting.CountNearbyEnemies(
                target_agent_id,
                Range.Adjacent.value,
            )

        cluster_size = max(target_cluster_size, contact_count)

        # Compress damage by reapplying flash enchants during the spike window
        # when energy is comfortable, otherwise just keep them maintained.
        flash_chain_floor = 0.35 if cluster_size >= 2 else 0.15

        if self.IsSkillEquipped(DUST_CLOAK_ID) and (
            yield from self.skillbook.Dervish.EarthPrayers.Dust_Cloak(
                refresh_window_ms=1200,
                min_self_energy_pct=flash_chain_floor,
            )
        ):
            return True

        if self.IsSkillEquipped(STAGGERING_FORCE_ID) and (
            yield from self.skillbook.Dervish.EarthPrayers.Staggering_Force(
                refresh_window_ms=1200,
                min_self_energy_pct=flash_chain_floor,
            )
        ):
            return True

        if not self._is_in_melee_contact(target_agent_id):
            if (yield from self._auto_attack_cluster()):
                return True
            return False

        active_flash_enchants = self.skillbook.Dervish.ScytheMastery.Count_Active_Dervish_Enchantments(
            (DUST_CLOAK_ID, STAGGERING_FORCE_ID)
        )

        # Both scythe attacks consume a Dervish enchantment for their premium
        # effect. Preserve that removal logic explicitly:
        # - with 2 enchants up, fire Twin first then Eremite so both consume one
        # - with only 1 enchant up, spend it on Eremite for blob AoE when the
        #   player is already in the middle of a pack; otherwise Twin still gets
        #   the better single-target compression.
        twin_ready = self.CanCastSkillID(TWIN_MOON_SWEEP_ID)
        prefer_eremites_first = (
            not twin_ready
            or (active_flash_enchants == 1 and cluster_size >= 3)
        )
        attack_order = (
            (EREMITES_ATTACK_ID, TWIN_MOON_SWEEP_ID)
            if prefer_eremites_first
            else (TWIN_MOON_SWEEP_ID, EREMITES_ATTACK_ID)
        )

        for attack_skill_id in attack_order:
            if not self.IsSkillEquipped(attack_skill_id):
                continue

            if attack_skill_id == EREMITES_ATTACK_ID:
                if active_flash_enchants <= 0 and cluster_size < 2:
                    continue
                min_energy_pct = 0.10 if cluster_size < 2 else 0.0
                cast_skill = self.skillbook.Dervish.ScytheMastery.Eremites_Attack
            else:
                min_energy_pct = 0.0
                if active_flash_enchants <= 0:
                    min_energy_pct = max(min_energy_pct, 0.20)
                if cluster_size < 2:
                    min_energy_pct = max(min_energy_pct, 0.15)
                cast_skill = self.skillbook.Dervish.ScytheMastery.Twin_Moon_Sweep

            if (
                yield from cast_skill(
                    target_agent_id,
                    cluster_size=cluster_size,
                    min_self_energy_pct=min_energy_pct,
                )
            ):
                return True

            active_flash_enchants = self.skillbook.Dervish.ScytheMastery.Count_Active_Dervish_Enchantments(
                (DUST_CLOAK_ID, STAGGERING_FORCE_ID)
            )

        if (yield from self._auto_attack_cluster()):
            return True

        return False
