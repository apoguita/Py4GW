from Py4GWCoreLib import BuildMgr, Profession, Routines, GLOBAL_CACHE, Range
from Py4GWCoreLib.Builds.Any.AutoCombat import AutoCombat
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill


class Supported_Soul_Taker(BuildMgr):
    def __init__(self):
        super().__init__(
            name="Supported Soul Taker",
            required_primary=Profession.Necromancer,
            required_secondary=Profession.Dervish,
            template_code="",
            required_skills=[
                Skill.GetID("Soul_Taker"),
                Skill.GetID("Masochism"),
                Skill.GetID("Staggering_Force"),
                Skill.GetID("Dust_Cloak"),
                Skill.GetID("Twin_Moon_Sweep"),
                Skill.GetID("Eremites_Attack"),
            ],
            optional_skills=[],
        )

        self.minimum_required_match = 4

        self.SetFallback("AutoCombat", AutoCombat())
        self.SetSkillCastingFn(self._run_local_skill_logic)

        self.soul_taker = Skill.GetID("Soul_Taker")
        self.masochism = Skill.GetID("Masochism")
        self.staggering_force = Skill.GetID("Staggering_Force")
        self.dust_cloak = Skill.GetID("Dust_Cloak")
        self.twin_moon_sweep = Skill.GetID("Twin_Moon_Sweep")
        self.eremites_attack = Skill.GetID("Eremites_Attack")

    def _has_valid_enemy_target(self) -> bool:
        target_id = Player.GetTargetID()
        if target_id <= 0:
            return False
        return Agent.IsValid(target_id) and not Agent.IsDead(target_id)

    def _has_stagger_or_dust_buff(self, player_id: int) -> bool:
        return (
            Routines.Checks.Effects.HasBuff(player_id, self.staggering_force)
            or Routines.Checks.Effects.HasBuff(player_id, self.dust_cloak)
        )

    def _enemies_adjacent_count(self) -> int:
        px, py = Player.GetXY()
        enemies = Routines.Agents.GetFilteredEnemyArray(px, py, Range.Adjacent.value)
        return len(enemies)

    def _can_use_twin_moon_sweep(self) -> bool:
        slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.twin_moon_sweep)
        if slot <= 0:
            return False

        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        required = GLOBAL_CACHE.Skill.Data.GetAdrenaline(self.twin_moon_sweep)

        if required <= 0:
            return True
        return skill_data.adrenaline_a >= required

    def _run_local_skill_logic(self):
        player_id = Player.GetAgentID()

        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(40)
            return

        # Keep core self-buffs up at all times.
        if not Routines.Checks.Effects.HasBuff(player_id, self.soul_taker):
            if (
                yield from self.CastSkillID(
                    self.soul_taker,
                    extra_condition=lambda: not Routines.Checks.Effects.HasBuff(player_id, self.soul_taker),
                    log=False,
                    aftercast_delay=200,
                )
            ):
                return

        if not Routines.Checks.Effects.HasBuff(player_id, self.masochism):
            if (
                yield from self.CastSkillID(
                    self.masochism,
                    extra_condition=lambda: not Routines.Checks.Effects.HasBuff(player_id, self.masochism),
                    log=False,
                    aftercast_delay=200,
                )
            ):
                return

        enemies_adjacent = self._enemies_adjacent_count()

        # Cast local AoE prep when enemies are around.
        if enemies_adjacent > 0 and not Routines.Checks.Effects.HasBuff(player_id, self.staggering_force):
            if (
                yield from self.CastSkillID(
                    self.staggering_force,
                    extra_condition=lambda: self._enemies_adjacent_count() > 0
                    and not Routines.Checks.Effects.HasBuff(player_id, self.staggering_force),
                    log=False,
                    aftercast_delay=200,
                )
            ):
                return

        if enemies_adjacent > 0 and not Routines.Checks.Effects.HasBuff(player_id, self.dust_cloak):
            if (
                yield from self.CastSkillID(
                    self.dust_cloak,
                    extra_condition=lambda: self._enemies_adjacent_count() > 0
                    and not Routines.Checks.Effects.HasBuff(player_id, self.dust_cloak),
                    log=False,
                    aftercast_delay=200,
                )
            ):
                return

        # Use attack skills only while Staggering Force or Dust Cloak is active.
        if not self._has_stagger_or_dust_buff(player_id):
            return

        if not self._has_valid_enemy_target():
            yield from Routines.Yield.Agents.TargetNearestEnemy(Range.Adjacent.value)
            return

        if (
            yield from self.CastSkillID(
                self.twin_moon_sweep,
                extra_condition=lambda: self._has_stagger_or_dust_buff(player_id)
                and self._has_valid_enemy_target()
                and self._can_use_twin_moon_sweep(),
                log=False,
                aftercast_delay=150,
            )
        ):
            return

        if (
            yield from self.CastSkillID(
                self.eremites_attack,
                extra_condition=lambda: self._has_stagger_or_dust_buff(player_id) and self._has_valid_enemy_target(),
                log=False,
                aftercast_delay=150,
            )
        ):
            return
