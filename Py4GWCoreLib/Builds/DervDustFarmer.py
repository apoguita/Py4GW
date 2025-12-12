import math
import random

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


# =================== BUILD ========================
class DervBuildFarmStatus:
    Setup = 'setup'
    Move = 'move'
    Ball = 'ball'
    Kill = 'kill'
    Loot = 'loot'
    Wait = 'wait'


class DervDustFarmer(BuildMgr):
    def __init__(self):
        super().__init__(
            name="Derv Dust Farmer",
            required_primary=Profession.Dervish,
            required_secondary=Profession.Assassin,
            template_code='Ogekkiq5qymU333m2Vz1E0d53F7F',
            skills=[
                GLOBAL_CACHE.Skill.GetID("Grenths_Aura"),
                GLOBAL_CACHE.Skill.GetID("Vow_of_Strength"),
                GLOBAL_CACHE.Skill.GetID("Staggering_Force"),
                GLOBAL_CACHE.Skill.GetID("Eremites_Attack"),
                GLOBAL_CACHE.Skill.GetID("Dash"),
                GLOBAL_CACHE.Skill.GetID("Dwarven_Stability"),
                GLOBAL_CACHE.Skill.GetID("Mystic_Vigor"),
                GLOBAL_CACHE.Skill.GetID("Mystic_Regeneration"),
            ],
        )

        self.auto_combat_handler: BuildMgr = AutoCombat()
        # assign extra skill attributes from the already populated self.skills
        self.grenths_aura = self.skills[0]
        self.vow_of_strength = self.skills[1]
        self.staggering_force = self.skills[2]
        self.eremites_attack = self.skills[3]
        self.dash = self.skills[4]
        self.dwarven_stability = self.skills[5]
        self.mystic_vigor = self.skills[6]
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
            yield from Routines.Yield.wait(750)

    def is_target_correct_model_id(self, agent_id, model_id):
        if not agent_id:
            return False

        if GLOBAL_CACHE.Agent.GetModelID(agent_id) == model_id:
            return True
        return False

    def get_fog_nightmare_or_aloe_target(self, agent_ids):
        aloe_target = None
        fog_nightmare_target = None
        fog_nightmare_count = 0
        for agent_id in agent_ids:
            if self.is_target_correct_model_id(agent_id, AgentModelID.SPINED_ALOE):
                aloe_target = agent_id

        for agent_id in agent_ids:
            if self.is_target_correct_model_id(agent_id, AgentModelID.FOG_NIGHTMARE):
                fog_nightmare_count += 1
                fog_nightmare_target = agent_id

        if aloe_target and fog_nightmare_target and fog_nightmare_count > 1:
            return Routines.Agents.GetNearestEnemy(Range.Earshot.value)
        if aloe_target and fog_nightmare_count and fog_nightmare_count <= 1:
            return aloe_target
        if aloe_target:
            return aloe_target or fog_nightmare_target
        if fog_nightmare_target:
            return Routines.Agents.GetNearestEnemy(Range.Earshot.value)

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

        if self.status == DervBuildFarmStatus.Loot or self.status == DervBuildFarmStatus.Wait:
            yield from Routines.Yield.wait(100)
            return

        if self.status == DervBuildFarmStatus.Setup:
            yield from self.swap_to_shield_set()
            self.spiked = False
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.dash)) and GLOBAL_CACHE.Agent.IsMoving(
                GLOBAL_CACHE.Player.GetAgentID()
            ):
                yield from Routines.Yield.Skills.CastSkillID(self.dash, aftercast_delay=100)
                return

        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        has_dwarven_stability = Routines.Checks.Effects.HasBuff(player_agent_id, self.dwarven_stability)
        has_mystic_regen = Routines.Checks.Effects.HasBuff(player_agent_id, self.mystic_regen)
        has_mystic_vigor = Routines.Checks.Effects.HasBuff(player_agent_id, self.mystic_vigor)
        player_hp = GLOBAL_CACHE.Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID())

        if (
            (yield from Routines.Yield.Skills.IsSkillIDUsable(self.mystic_vigor))
            and not has_mystic_vigor
            and player_hp < 0.80
            and not self.status == DervBuildFarmStatus.Setup
        ):
            yield from Routines.Yield.Skills.CastSkillID(self.mystic_vigor, aftercast_delay=750)
            return

        if (
            (yield from Routines.Yield.Skills.IsSkillIDUsable(self.dwarven_stability))
            and not has_dwarven_stability
            and not self.status == DervBuildFarmStatus.Setup
        ):
            yield from Routines.Yield.Skills.CastSkillID(self.dwarven_stability, aftercast_delay=250)
            return

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
                and GLOBAL_CACHE.Agent.IsMoving(GLOBAL_CACHE.Player.GetAgentID())
            ):
                yield from Routines.Yield.Skills.CastSkillID(self.dash, aftercast_delay=100)
                return

        if self.status == DervBuildFarmStatus.Ball:
            yield from self.swap_to_shield_set()
            self.spiked = False

        if self.status == DervBuildFarmStatus.Kill:
            player_pos = GLOBAL_CACHE.Player.GetXY()
            player_current_energy = GLOBAL_CACHE.Agent.GetEnergy(player_agent_id) * GLOBAL_CACHE.Agent.GetMaxEnergy(
                player_agent_id
            )
            remaining_enemies = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.Earshot.value)
            next_target = self.get_fog_nightmare_or_aloe_target(remaining_enemies)

            if next_target:
                yield from self.swap_to_scythe()
                if self.is_target_correct_model_id(next_target, AgentModelID.SPINED_ALOE):
                    agent_x, agent_y = GLOBAL_CACHE.Agent.GetXY(next_target)
                    player_x, player_y = GLOBAL_CACHE.Player.GetXY()

                    # === Step 1: Calculate vector from player -> target ===
                    dx = agent_x - player_x
                    dy = agent_y - player_y
                    dist = math.hypot(dx, dy)

                    if dist > Range.Adjacent.value:
                        # === Step 2: Normalize direction vector ===
                        nx, ny = dx / dist, dy / dist

                        # === Step 3: Pick sidestep direction (left or right) ===
                        sidestep_dir = random.choice([-1, 1])  # -1 = left, +1 = right
                        sidestep_distance = random.randint(200, 400)  # adjust to how big sidestep should be

                        # perpendicular vector for sidestep
                        sx, sy = -ny * sidestep_dir, nx * sidestep_dir

                        sidestep_x = player_x + sx * sidestep_distance
                        sidestep_y = player_y + sy * sidestep_distance

                        # === Step 4: Move to sidestep position first ===
                        GLOBAL_CACHE.Player.Move(sidestep_x, sidestep_y)
                        yield from Routines.Yield.wait(1000)  # small wait

                        # === Step 5: Move to a point within Adjacent range of target ===
                        stop_distance = Range.Adjacent.value
                        final_x = agent_x - nx * stop_distance
                        final_y = agent_y - ny * stop_distance

                        GLOBAL_CACHE.Player.Move(final_x, final_y)
                        yield from Routines.Yield.wait(2000)  # allow move to finish

                yield from Routines.Yield.Agents.InteractAgent(next_target)
                has_vow_of_strength = Routines.Checks.Effects.HasBuff(player_agent_id, self.vow_of_strength)
                has_grenths_aura = Routines.Checks.Effects.HasBuff(player_agent_id, self.grenths_aura)
                if (
                    (yield from Routines.Yield.Skills.IsSkillIDUsable(self.grenths_aura))
                    and len(remaining_enemies) >= 2
                    and not has_grenths_aura
                ) or player_hp < 0.50:
                    yield from Routines.Yield.Skills.CastSkillID(self.grenths_aura, aftercast_delay=250)
                    return

                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.vow_of_strength)) and not has_vow_of_strength:
                    yield from Routines.Yield.Skills.CastSkillID(self.vow_of_strength, aftercast_delay=250)
                    return
                has_vow_of_strength = Routines.Checks.Effects.HasBuff(player_agent_id, self.vow_of_strength)

                if (
                    (
                        yield from Routines.Yield.Skills.IsSkillIDUsable(self.staggering_force)
                        and Routines.Yield.Skills.IsSkillIDUsable(self.eremites_attack)
                    )
                    and has_vow_of_strength
                    and has_grenths_aura
                    and player_current_energy >= 12
                    and len(remaining_enemies) >= 2
                ):
                    yield from Routines.Yield.Agents.TargetNearestEnemy(Range.Earshot.value)
                    yield from Routines.Yield.Skills.CastSkillID(self.staggering_force, aftercast_delay=250)
                    has_staggering_force = Routines.Checks.Effects.HasBuff(player_agent_id, self.staggering_force)
                    if has_staggering_force and player_current_energy >= 10:
                        yield from Routines.Yield.Skills.CastSkillID(self.eremites_attack, aftercast_delay=250)
                        return
                yield
                return
        yield
        return


# =================== BUILD END ========================
