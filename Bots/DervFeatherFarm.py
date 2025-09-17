from Py4GWCoreLib import *

# from Bots.DervFeatherFarmer import DervFeatherFarmer
# from Bots.DervFeatherFarmer import DervBuildFarmStatus

from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import Range
from Py4GWCoreLib import Profession
from Py4GWCoreLib import Keystroke
from Py4GWCoreLib import Key
from Py4GWCoreLib import Player
from Py4GWCoreLib import Weapon
from Py4GWCoreLib.Builds.AutoCombat import AutoCombat


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
            template_code='OgejkmrMbSmXfbaXNXTQ3lEYsXA',
            skills=[
                GLOBAL_CACHE.Skill.GetID("Sand_Shards"),
                GLOBAL_CACHE.Skill.GetID("Vow_of_Strength"),
                GLOBAL_CACHE.Skill.GetID("Staggering_Force"),
                GLOBAL_CACHE.Skill.GetID("Eremites_Attack"),
                GLOBAL_CACHE.Skill.GetID("Dash"),
                GLOBAL_CACHE.Skill.GetID("Dwarven_Stability"),
                GLOBAL_CACHE.Skill.GetID("Conviction"),
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
        self.conviction = self.skills[6]
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

        SENSALI = 'Sensali'
        if SENSALI in GLOBAL_CACHE.Agent.GetName(agent_id):
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
        has_conviction = Routines.Checks.Effects.HasBuff(player_agent_id, self.conviction)

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
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.dash)) and has_dwarven_stability:
                yield from Routines.Yield.Skills.CastSkillID(self.dash, aftercast_delay=100)
                return

        if self.status == DervBuildFarmStatus.Ball:
            yield from self.swap_to_shield_set()
            self.spiked = False
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.conviction)):
                yield from Routines.Yield.Skills.CastSkillID(self.conviction, aftercast_delay=750)
                return

        if self.status == DervBuildFarmStatus.Kill:
            player_pos = GLOBAL_CACHE.Player.GetXY()
            enemies = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.Earshot.value)
            target_sensali = self.get_sensali_target(enemies)

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.conviction)) and not has_conviction:
                yield from Routines.Yield.Skills.CastSkillID(self.conviction, aftercast_delay=1000)
                return

            player_current_energy = GLOBAL_CACHE.Agent.GetEnergy(player_agent_id) * GLOBAL_CACHE.Agent.GetMaxEnergy(
                player_agent_id
            )
            if self.spiking or (not self.spiked and target_sensali and player_current_energy >= 25):
                print('Currently Spiking!')
                self.spiking = True
                has_sand_shards = Routines.Checks.Effects.HasBuff(player_agent_id, self.sand_shards)

                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.sand_shards)):
                    print('Casting Sand Shards!')
                    yield from Routines.Yield.Skills.CastSkillID(self.sand_shards, aftercast_delay=250)
                    return

                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.vow_of_strength)) and has_sand_shards:
                    print('Casting Vow of Strength!')
                    yield from Routines.Yield.Skills.CastSkillID(self.vow_of_strength, aftercast_delay=750)
                    return

                has_vow_of_strength = Routines.Checks.Effects.HasBuff(player_agent_id, self.vow_of_strength)
                if (
                    (
                        yield from Routines.Yield.Skills.IsSkillIDUsable(self.staggering_force)
                        and Routines.Yield.Skills.IsSkillIDUsable(self.eremites_attack)
                    )
                    and has_vow_of_strength
                    and has_sand_shards
                ):
                    yield from Routines.Yield.Agents.TargetNearestEnemy(Range.Earshot.value)
                    print('Spiking with Staggering Force and Eremites!')
                    yield from Routines.Yield.Skills.CastSkillID(self.staggering_force, aftercast_delay=250)
                    has_staggering_force = Routines.Checks.Effects.HasBuff(player_agent_id, self.staggering_force)
                    if has_staggering_force:
                        yield from self.swap_to_scythe()
                        yield from Routines.Yield.Skills.CastSkillID(self.eremites_attack, aftercast_delay=750)
                        self.spiked = True
                        self.spiking = False
                        return

            if self.spiked:
                print('Cleaning up survivors, Noone lives!')
                if target_sensali:
                    if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.vow_of_strength)):
                        yield from Routines.Yield.Skills.CastSkillID(self.vow_of_strength, aftercast_delay=750)
                        return
                    GLOBAL_CACHE.Player.Interact(target_sensali, False)
                    yield
                    return

                remaining_enemies = Routines.Agents.GetFilteredEnemyArray(
                    player_pos[0], player_pos[1], Range.Earshot.value
                )
                next_sensali = self.get_sensali_target(remaining_enemies)
                if not target_sensali and next_sensali:
                    if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.vow_of_strength)):
                        yield from Routines.Yield.Skills.CastSkillID(self.vow_of_strength, aftercast_delay=750)
                        return
                    GLOBAL_CACHE.Player.Interact(next_sensali, False)
                    yield
                    return

                if not next_sensali:
                    self.status = DervBuildFarmStatus.Move
                    return


# =================== BUILD END ========================


selected_step = 0
SEITUING_HARBOR = "Seitung Harbor"
STATUS = 'status'
SENSALI = 'Sensali'

bot = Botting("Feather Farmer", custom_build=DervFeatherFarmer())


def return_to_outpost():
    yield from Routines.Yield.wait(4000)
    is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
    is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
    is_explorable = GLOBAL_CACHE.Map.IsExplorable()
    is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated()

    if is_map_ready and is_party_loaded and is_explorable and is_party_defeated:
        GLOBAL_CACHE.Party.ReturnToOutpost()
        yield from Routines.Yield.wait(4000)


def ball_sensalis(bot):
    bot.config.build_handler.__setattr__(STATUS, DervBuildFarmStatus.Ball)
    yield from Routines.Yield.wait(100)

    elapsed = 0
    while elapsed < 50:  # 50 * 100ms = 5s
        # Player position
        px, py = GLOBAL_CACHE.Player.GetXY()

        # Enemies nearby
        enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, Range.Adjacent.value)
        player_hp = GLOBAL_CACHE.Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID())
        if player_hp < 0.6:
            return True

        # Count sensali in Adjacent range
        ball_count = sum(1 for agent_id in enemy_array if SENSALI in GLOBAL_CACHE.Agent.GetName(agent_id))

        if ball_count >= 4:
            return True  # condition satisfied

        # wait 100ms
        yield from Routines.Yield.wait(100)
        elapsed += 1

    # timeout reached
    return False


def kill_sensalis(bot, kill_immediately=False):
    if kill_immediately:
        bot.config.build_handler.__setattr__(STATUS, DervBuildFarmStatus.Kill)
    else:
        yield from ball_sensalis(bot)
        bot.config.build_handler.__setattr__(STATUS, DervBuildFarmStatus.Kill)

    start_time = Utils.GetBaseTimestamp()
    timeout = 120000  # 2 minutes max

    player_id = GLOBAL_CACHE.Player.GetAgentID()

    while True:
        px, py = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, Range.Earshot.value)

        sensali_array = [agent_id for agent_id in enemy_array if SENSALI in GLOBAL_CACHE.Agent.GetName(agent_id)]

        if len(sensali_array) == 0:
            break  # all sensalis dead

        # Timeout check
        current_time = Utils.GetBaseTimestamp()
        if timeout > 0 and current_time - start_time > timeout:
            return

        # Death check
        if GLOBAL_CACHE.Agent.IsDead(player_id):
            # handle death here
            return

        yield from Routines.Yield.wait(1000)

    yield from Routines.Yield.wait(1000)


def death_or_completion_callback(bot):
    bot.Party.Resign()
    bot.States.AddCustomState(return_to_outpost, "Return to Seitung Harbor")
    bot.States.JumpToStepName("[H]Farm Loop_2")


def Routine(bot):
    bot.Properties.Enable("auto_combat")
    bot.Events.OnDeathCallback(lambda: death_or_completion_callback(bot))

    map_id = GLOBAL_CACHE.Map.GetMapID()
    if map_id != 250:
        bot.Map.Travel(target_map_name=SEITUING_HARBOR)
        bot.Wait.ForMapLoad(target_map_name=SEITUING_HARBOR)

    bot.Move.XY(16570, 17713, "Exit Outpost for resign spot")
    bot.Wait.ForMapLoad(target_map_name="Jaya Bluffs")
    bot.Move.XY(11962, -14017, "Setup resign spot")
    bot.Wait.ForMapLoad(target_map_name=SEITUING_HARBOR)

    bot.States.AddHeader('Farm Loop')
    bot.Move.XY(16570, 17713, "Exit Outpost To Farm")
    bot.Wait.ForMapLoad(target_map_name="Jaya Bluffs")

    bot.Move.XY(9000, -12680, 'Run 1')
    bot.Move.XY(7588, -10609, 'Run 2')

    bot.Move.XY(2900, -9700, 'Move spot 1')
    bot.Move.XY(1540, -6995, 'Move spot 2')

    bot.Move.XY(-472, -4342, 'Move to Kill Spot 1')
    bot.States.AddCustomState(lambda: kill_sensalis(bot, kill_immediately=True), "Killing Sensalis Immediately")

    bot.Move.XY(-1536, -1686, "Move to Kill Spot 2")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(586, -76, "Move to Kill Spot 3")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-1556, 2786, "Move to Kill Spot 4")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-2229, -815, "Move to Kill Spot 5")
    bot.States.AddCustomState(lambda: kill_sensalis(bot, kill_immediately=True), "Killing Sensalis Immediately")

    bot.Move.XY(-5247, -3290, "Move to Kill Spot 6")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-6994, -2273, "Move to Kill Spot 7")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-5042, -6638, "Move to Kill Spot 8")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-11040, -8577, "Move to Kill Spot 9")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-10860, -2840, "Move to Kill Spot 10")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-14900, -3000, "Move to Kill Spot 11")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-12200, 150, "Move to Kill Spot 12")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-12500, 4000, "Move to Kill Spot 13")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-12111, 1690, "Move to Kill Spot 14")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-10303, 4110, "Move to Kill Spot 15")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-10500, 5500, "Move to Kill Spot 16")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-9700, 2400, "Move to Kill Spot 17")
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.States.AddCustomState(death_or_completion_callback, "Return to Seitung Harbor")


bot.Routine = Routine.__get__(bot)


def main():
    global selected_step

    bot.Update()

    if PyImGui.begin("Feather Farmer", PyImGui.WindowFlags.AlwaysAutoResize):

        if PyImGui.button("start bot"):
            bot.Start()

        if PyImGui.button("stop bot"):
            bot.Stop()

    PyImGui.end()


if __name__ == "__main__":
    main()
