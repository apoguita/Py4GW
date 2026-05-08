from __future__ import annotations

from Py4GWCoreLib import AgentArray, BuildMgr, Effects, GLOBAL_CACHE, ModelID, Profession, Range, Routines, SkillBar
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
ALCOHOL_MODEL_IDS = (
    ModelID.Aged_Dwarven_Ale.value,
    ModelID.Aged_Hunters_Ale.value,
    ModelID.Bottle_Of_Grog.value,
    ModelID.Flask_Of_Firewater.value,
    ModelID.Keg_Of_Aged_Hunters_Ale.value,
    ModelID.Krytan_Brandy.value,
    ModelID.Spiked_Eggnog.value,
    ModelID.Bottle_Of_Rice_Wine.value,
    ModelID.Eggnog.value,
    ModelID.Dwarven_Ale.value,
    ModelID.Hard_Apple_Cider.value,
    ModelID.Hunters_Ale.value,
    ModelID.Bottle_Of_Juniberry_Gin.value,
    ModelID.Shamrock_Ale.value,
    ModelID.Bottle_Of_Vabbian_Wine.value,
    ModelID.Vial_Of_Absinthe.value,
    ModelID.Witchs_Brew.value,
    ModelID.Zehtukas_Jug.value,
)


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

    def _has_effect_with_buffer(self, skill_id: int, refresh_window_ms: int = 2000) -> bool:
        player_id = Player.GetAgentID()
        if not Routines.Checks.Agents.HasEffect(player_id, skill_id):
            return False
        remaining_ms = int(GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_id, skill_id) or 0)
        return remaining_ms > refresh_window_ms

    def _should_refresh_self_buff(self, skill_id: int, refresh_window_ms: int = 2000) -> bool:
        if not self.IsSkillEquipped(skill_id):
            return False
        return not self._has_effect_with_buffer(skill_id, refresh_window_ms)

    def _get_drunk_level(self) -> int:
        try:
            return max(0, min(5, int(Effects.GetAlcoholLevel() or 0)))
        except Exception:
            return 0

    def _use_alcohol_if_needed(self, target_level: int = 1) -> bool:
        if self._get_drunk_level() >= target_level:
            return False

        for model_id in ALCOHOL_MODEL_IDS:
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(int(model_id))
            if item_id:
                GLOBAL_CACHE.Inventory.UseItem(item_id)
                return True

        return False

    def _cast_self_buff(
        self,
        skill_id: int,
        *,
        refresh_window_ms: int = 2000,
        aftercast_delay: int = 250,
        energy_floor: float = 0.0,
    ):
        if False:
            yield

        if Agent.GetEnergy(Player.GetAgentID()) < energy_floor:
            return False
        if not self._should_refresh_self_buff(skill_id, refresh_window_ms):
            return False
        if skill_id == DRUNKEN_MASTER_ID and self._use_alcohol_if_needed():
            yield from Routines.Yield.wait(500)
        return (
            yield from self.CastSkillID(
                skill_id=skill_id,
                log=False,
                aftercast_delay=aftercast_delay,
            )
        )

    def _get_target_cluster_size(self, target_agent_id: int) -> int:
        if not target_agent_id or not Agent.IsValid(target_agent_id) or Agent.IsDead(target_agent_id):
            return 0

        target_x, target_y = Agent.GetXY(target_agent_id)
        enemy_array = Routines.Agents.GetFilteredEnemyArray(target_x, target_y, Range.Adjacent.value)
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: Agent.IsValid(agent_id) and not Agent.IsDead(agent_id),
        )
        return len(enemy_array or [])

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

    def _count_active_flash_enchantments(self) -> int:
        player_id = Player.GetAgentID()
        count = 0
        for skill_id in (DUST_CLOAK_ID, STAGGERING_FORCE_ID):
            if Routines.Checks.Agents.HasEffect(player_id, skill_id):
                count += 1
        return count

    def _auto_attack_cluster(self):
        return (yield from self.AutoAttack(target_type="EnemyClustered"))

    def _has_enough_adrenaline(self, skill_id: int) -> bool:
        slot = SkillBar.GetSlotBySkillID(skill_id)
        if not (1 <= slot <= 8):
            return False
        return bool(Routines.Checks.Skills.HasEnoughAdrenalineBySlot(slot))

    def _should_use_i_am_unstoppable(self, contact_count: int) -> bool:
        player_agent_id = Player.GetAgentID()

        if self._has_effect_with_buffer(I_AM_UNSTOPPABLE_ID, refresh_window_ms=1000):
            return False

        is_knocked_down = Agent.IsKnockedDown(player_agent_id)
        is_crippled = Agent.IsCrippled(player_agent_id)
        is_low_health = Agent.GetHealth(player_agent_id) <= 0.70

        if is_knocked_down or is_crippled or is_low_health:
            return True

        # Frontload IAU when the scythe necro is already planted in a blob,
        # even if the client-side KD flag was too brief to catch reliably.
        return contact_count >= 2

    def _run_local_skill_logic(self):
        if not (self.IsInAggro() or self.IsCloseToAggro()):
            return False

        contact_count = self._get_player_contact_count()

        if (
            self.IsSkillEquipped(I_AM_UNSTOPPABLE_ID)
            and self._should_use_i_am_unstoppable(contact_count)
            and (yield from self.CastSkillID(I_AM_UNSTOPPABLE_ID, log=False, aftercast_delay=150))
        ):
            return True

        if self.IsSkillEquipped(MASOCHISM_ID) and (
            yield from self.skillbook.Necromancer.SoulReaping.Masochism()
        ):
            return True

        if (yield from self._cast_self_buff(SOUL_TAKER_ID, refresh_window_ms=2000, aftercast_delay=250)):
            return True

        if (yield from self._cast_self_buff(DRUNKEN_MASTER_ID, refresh_window_ms=2000, aftercast_delay=250)):
            return True

        target_agent_id = self.current_target_id
        if not self._is_in_melee_contact(target_agent_id):
            if (yield from self._auto_attack_cluster()):
                return True
            target_agent_id = self.current_target_id

        cluster_size = max(
            self._get_target_cluster_size(target_agent_id),
            contact_count,
        )
        energy_fraction = float(Agent.GetEnergy(Player.GetAgentID()) or 0.0)

        # Compress damage by reapplying flash enchants during the spike window
        # when energy is comfortable, otherwise just keep them maintained.
        flash_chain_floor = 0.35 if cluster_size >= 2 else 0.15

        if self.IsSkillEquipped(DUST_CLOAK_ID) and (
            yield from self._cast_self_buff(
                DUST_CLOAK_ID,
                refresh_window_ms=1200,
                aftercast_delay=250,
                energy_floor=flash_chain_floor,
            )
        ):
            return True

        if self.IsSkillEquipped(STAGGERING_FORCE_ID) and (
            yield from self._cast_self_buff(
                STAGGERING_FORCE_ID,
                refresh_window_ms=1200,
                aftercast_delay=250,
                energy_floor=flash_chain_floor,
            )
        ):
            return True

        if not self._is_in_melee_contact(target_agent_id):
            if (yield from self._auto_attack_cluster()):
                return True
            return False

        active_flash_enchants = self._count_active_flash_enchantments()

        # Both scythe attacks consume a Dervish enchantment for their premium
        # effect. Preserve that removal logic explicitly:
        # - with 2 enchants up, fire Twin first then Eremite so both consume one
        # - with only 1 enchant up, spend it on Eremite for blob AoE when the
        #   player is already in the middle of a pack; otherwise Twin still gets
        #   the better single-target compression.
        twin_ready = self._has_enough_adrenaline(TWIN_MOON_SWEEP_ID)
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
                if cluster_size < 2 and energy_fraction < 0.10:
                    continue
            else:
                if active_flash_enchants <= 0 and energy_fraction < 0.20:
                    continue
                if cluster_size < 2 and energy_fraction < 0.15:
                    continue

            if (
                yield from self.CastSkillID(
                    skill_id=attack_skill_id,
                    target_agent_id=target_agent_id,
                    log=False,
                    aftercast_delay=250,
                )
            ):
                return True

            active_flash_enchants = self._count_active_flash_enchantments()

        if (yield from self._auto_attack_cluster()):
            return True

        return False
