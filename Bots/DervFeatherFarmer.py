from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import AgentModelID
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Key
from Py4GWCoreLib import Keystroke
from Py4GWCoreLib import Player
from Py4GWCoreLib import Profession
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Weapon
from Py4GWCoreLib.Builds.AutoCombat import AutoCombat

SENSALI_MODEL_IDS = {AgentModelID.SENSALI_CLAW, AgentModelID.SENSALI_CUTTER, AgentModelID.SENSALI_DARKFEATHER}


# =================== BUILD ========================
class DervBuildFarmStatus:
    Move = 'move'
    Ball = 'ball'
    Kill = 'kill'


class DervFeatherFarmer(BuildMgr):
    def __init__(self):
        super().__init__(
            name="Derv Feather Farmer",
            required_primary=Profession.Dervish,
            required_secondary=Profession.Assassin,
            template_code='OgejkmrMbSmXfbaXNXTQ3l7XsXA',
            skills=[
                GLOBAL_CACHE.Skill.GetID("Sand_Shards"),
                GLOBAL_CACHE.Skill.GetID("Vow_of_Strength"),
                GLOBAL_CACHE.Skill.GetID("Staggering_Force"),
                GLOBAL_CACHE.Skill.GetID("Eremites_Attack"),
                GLOBAL_CACHE.Skill.GetID("Dash"),
                GLOBAL_CACHE.Skill.GetID("Dwarven_Stability"),
                GLOBAL_CACHE.Skill.GetID("Intimidating_Aura"),
                GLOBAL_CACHE.Skill.GetID("Mystic_Regeneration"),
            ],
        )

        self.auto_combat_handler: BuildMgr = AutoCombat()
        # assign extra skill attributes from the already populated self.skills
        self.sand_shards = self.skills[0]
        self.vow_of_strength = self.skills[1]
        self.staggering_force = self.skills[2]
        self.eremites_attack = self.skills[3]
        self.dash = self.skills[4]
        self.dwarven_stability = self.skills[5]
        self.intimidating_aura = self.skills[6]
        self.mystic_regen = self.skills[7]

        # Build usage status
        self.status = DervBuildFarmStatus.Move
        self.spiked = False
        self.spiking = False

    def swap_to_scythe(self):
        if GLOBAL_CACHE.Agent.GetWeaponType(Player.GetAgentID())[0] != Weapon.Scythe:
            Keystroke.PressAndRelease(Key.F1.value)
            yield

    def swap_to_shield_set(self):
        if GLOBAL_CACHE.Agent.GetWeaponType(Player.GetAgentID())[0] == Weapon.Scythe:
            Keystroke.PressAndRelease(Key.F2.value)
            self.status = DervBuildFarmStatus.Move
            yield from Routines.Yield.wait(750)

    def is_target_sensali(self, agent_id):
        if not agent_id:
            return False

        if GLOBAL_CACHE.Agent.GetModelID(agent_id) in SENSALI_MODEL_IDS:
            return True
        return False

    def get_sensali_target(self, agent_ids):
        for agent_id in agent_ids:
            if self.is_target_sensali(agent_id):
                return agent_id
        return None

    def ProcessSkillCasting(self):
        if not (
            Routines.Checks.Map.IsExplorable()
            and Routines.Checks.Player.CanAct()
            and Routines.Checks.Map.IsExplorable()
            and Routines.Checks.Skills.CanCast()
        ):
            ActionQueueManager().ResetAllQueues()
            yield from Routines.Yield.wait(1000)
            return

        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        has_dwarven_stability = Routines.Checks.Effects.HasBuff(player_agent_id, self.dwarven_stability)
        has_mystic_regen = Routines.Checks.Effects.HasBuff(player_agent_id, self.mystic_regen)
        has_intimidating_aura = Routines.Checks.Effects.HasBuff(player_agent_id, self.intimidating_aura)

        if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.intimidating_aura)) and not has_intimidating_aura:
            yield from Routines.Yield.Skills.CastSkillID(self.intimidating_aura, aftercast_delay=750)
            return

        if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.dwarven_stability)) and not has_dwarven_stability:
            yield from Routines.Yield.Skills.CastSkillID(self.dwarven_stability, aftercast_delay=100)
            return

        player_hp = GLOBAL_CACHE.Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID())
        if (
            (yield from Routines.Yield.Skills.IsSkillIDUsable(self.mystic_regen))
            and not has_mystic_regen
            and player_hp < 0.95
        ):
            yield from Routines.Yield.Skills.CastSkillID(self.mystic_regen, aftercast_delay=750)
            return

        if self.status == DervBuildFarmStatus.Move:
            yield from self.swap_to_shield_set()
            self.spiked = False
            if (
                (yield from Routines.Yield.Skills.IsSkillIDUsable(self.dash))
                and has_dwarven_stability
                and has_intimidating_aura
            ):
                yield from Routines.Yield.Skills.CastSkillID(self.dash, aftercast_delay=100)
                return

        if self.status == DervBuildFarmStatus.Ball:
            yield from self.swap_to_shield_set()
            self.spiked = False

        if self.status == DervBuildFarmStatus.Kill:
            player_pos = GLOBAL_CACHE.Player.GetXY()
            enemies = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.Spellcast.value)
            target_sensali = self.get_sensali_target(enemies)

            player_current_energy = GLOBAL_CACHE.Agent.GetEnergy(player_agent_id) * GLOBAL_CACHE.Agent.GetMaxEnergy(
                player_agent_id
            )
            if self.spiking or (not self.spiked and target_sensali):
                self.spiking = True
                has_sand_shards = Routines.Checks.Effects.HasBuff(player_agent_id, self.sand_shards)

                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.sand_shards)):
                    yield from Routines.Yield.Skills.CastSkillID(self.sand_shards, aftercast_delay=250)
                    return

                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.vow_of_strength)) and has_sand_shards:
                    yield from Routines.Yield.Skills.CastSkillID(self.vow_of_strength, aftercast_delay=250)
                    return

                has_vow_of_strength = Routines.Checks.Effects.HasBuff(player_agent_id, self.vow_of_strength)
                if (
                    (
                        yield from Routines.Yield.Skills.IsSkillIDUsable(self.staggering_force)
                        and Routines.Yield.Skills.IsSkillIDUsable(self.eremites_attack)
                    )
                    and has_vow_of_strength
                    and has_sand_shards
                    and player_current_energy >= 17
                ):
                    yield from Routines.Yield.Agents.TargetNearestEnemy(Range.Spellcast.value)
                    yield from Routines.Yield.Skills.CastSkillID(self.staggering_force, aftercast_delay=250)
                    has_staggering_force = Routines.Checks.Effects.HasBuff(player_agent_id, self.staggering_force)
                    if has_staggering_force and player_current_energy >= 10:
                        yield from self.swap_to_scythe()
                        yield from Routines.Yield.Skills.CastSkillID(self.eremites_attack, aftercast_delay=250)
                        self.spiked = True
                        self.spiking = False
                        return

            if self.spiked:
                remaining_enemies = Routines.Agents.GetFilteredEnemyArray(
                    player_pos[0], player_pos[1], Range.Spellcast.value
                )
                next_sensali = self.get_sensali_target(remaining_enemies)
                if next_sensali:
                    has_sand_shards = Routines.Checks.Effects.HasBuff(player_agent_id, self.sand_shards)
                    if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.sand_shards)) and len(
                        remaining_enemies
                    ) >= 3:
                        yield from Routines.Yield.Skills.CastSkillID(self.sand_shards, aftercast_delay=250)
                        return

                    if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.vow_of_strength)):
                        yield from Routines.Yield.Skills.CastSkillID(self.vow_of_strength, aftercast_delay=250)
                        return
                    has_vow_of_strength = Routines.Checks.Effects.HasBuff(player_agent_id, self.vow_of_strength)

                    if (
                        (
                            yield from Routines.Yield.Skills.IsSkillIDUsable(self.staggering_force)
                            and Routines.Yield.Skills.IsSkillIDUsable(self.eremites_attack)
                        )
                        and has_vow_of_strength
                        and has_sand_shards
                        and player_current_energy >= 12
                        and len(remaining_enemies) >= 3
                    ):
                        yield from Routines.Yield.Agents.TargetNearestEnemy(Range.Spellcast.value)
                        yield from Routines.Yield.Skills.CastSkillID(self.staggering_force, aftercast_delay=250)
                        has_staggering_force = Routines.Checks.Effects.HasBuff(player_agent_id, self.staggering_force)
                        if has_staggering_force and player_current_energy >= 10:
                            yield from Routines.Yield.Skills.CastSkillID(self.eremites_attack, aftercast_delay=250)
                            return

                    GLOBAL_CACHE.Player.Interact(next_sensali, False)
                    yield
                    return

                if not next_sensali:
                    self.status = DervBuildFarmStatus.Move
                    return


# =================== BUILD END ========================
