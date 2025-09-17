from Py4GWCoreLib import *

from Bots.DervFeatherFarmer import DervFeatherFarmer
from Bots.DervFeatherFarmer import DervBuildFarmStatus


selected_step = 0
bot_current_step = 0
SEITUING_HARBOR = "Seitung Harbor"
STATUS = 'status'
SENSALI = 'Sensali'

bot = Botting("Feather Farmer", custom_build=DervFeatherFarmer())
stuck_timer = ThrottledTimer(3000)
movement_check_timer = ThrottledTimer(3000)
stuck_counter = 0
old_player_position = (0, 0)
initial_run = True


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
            bot.config.build_handler.__setattr__(STATUS, DervBuildFarmStatus.Move)
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


def handle_stuck(bot):
    global stuck_timer
    global movement_check_timer
    global old_player_position
    global stuck_counter
    global initial_run

    while True:
        # Wait until map is valid
        if not Routines.Checks.Map.MapValid() and Routines.Checks.Map:
            yield from Routines.Yield.wait(1000)
            continue

        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            return

        if GLOBAL_CACHE.Map.GetMapID() == 196 and bot.config.build_handler.status == DervBuildFarmStatus.Move:

            # Check if character hasn't moved
            if movement_check_timer.IsExpired():
                current_player_pos = GLOBAL_CACHE.Player.GetXY()
                if old_player_position == current_player_pos:
                    GLOBAL_CACHE.Player.SendChatCommand("stuck")
                    print("Player is stuck!")
                    # Pause FSM and remember where we are
                    fsm = bot.config.FSM
                    current_step = fsm.get_current_state_number()
                    target_name = fsm.get_state_name_by_number(current_step)

                    fsm.pause()

                    print('Killing sensalis that got me stuck')
                    # Deal with local enemies before resuming
                    yield from kill_sensalis(bot, kill_immediately=True)

                    print('Resetting to state', target_name)
                    # Jump back into the same step
                    fsm.jump_to_state_by_name(target_name)
                    fsm.resume()
                    yield
                else:
                    old_player_position = current_player_pos
                    stuck_timer.Reset()
                    stuck_counter = 0

                movement_check_timer.Reset()

            # Hard reset if too many consecutive stuck detections
            if stuck_counter >= 10:
                print("Too many stuck detections, forcing reset.")
                stuck_counter = 0
                fsm = bot.config.FSM
                yield from fsm._reset_execution()

        yield from Routines.Yield.wait(500)


def load_skill_bar(bot):
    yield from bot.config.build_handler.LoadSkillBar()


def main_farm(bot):
    bot.Properties.Enable("auto_combat")
    bot.Events.OnDeathCallback(lambda: death_or_completion_callback(bot))
    bot.States.AddManagedCoroutine('Stuck handler', lambda: handle_stuck(bot))

    bot.States.AddHeader('Starting Loop')
    map_id = GLOBAL_CACHE.Map.GetMapID()
    if map_id != 250:
        bot.Map.Travel(target_map_name=SEITUING_HARBOR)
        bot.Wait.ForMapLoad(target_map_name=SEITUING_HARBOR)
    bot.States.AddCustomState(lambda: load_skill_bar(bot), "Loading Skillbar")

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
    bot.States.AddHeader('Kill Spot 1')
    bot.States.AddCustomState(lambda: kill_sensalis(bot, kill_immediately=True), "Killing Sensalis Immediately")

    bot.Move.XY(-1536, -1686, "Move to Kill Spot 2")
    bot.States.AddHeader('Kill Spot 2')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(586, -76, "Move to Kill Spot 3")
    bot.States.AddHeader('Kill Spot 3')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-1556, 2786, "Move to Kill Spot 4")
    bot.States.AddHeader('Kill Spot 4')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-2229, -815, "Move to Kill Spot 5")
    bot.States.AddHeader('Kill Spot 5')
    bot.States.AddCustomState(lambda: kill_sensalis(bot, kill_immediately=True), "Killing Sensalis Immediately")

    bot.Move.XY(-5247, -3290, "Move to Kill Spot 6")
    bot.States.AddHeader('Kill Spot 6')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-6994, -2273, "Move to Kill Spot 7")
    bot.States.AddHeader('Kill Spot 7')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-5042, -6638, "Move to Kill Spot 8")
    bot.States.AddHeader('Kill Spot 8')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-11040, -8577, "Move to Kill Spot 9")
    bot.States.AddHeader('Kill Spot 9')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-10860, -2840, "Move to Kill Spot 10")
    bot.States.AddHeader('Kill Spot 10')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-14900, -3000, "Move to Kill Spot 11")
    bot.States.AddHeader('Kill Spot 11')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-12200, 150, "Move to Kill Spot 12")
    bot.States.AddHeader('Kill Spot 12')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-12500, 4000, "Move to Kill Spot 13")
    bot.States.AddHeader('Kill Spot 13')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-12111, 1690, "Move to Kill Spot 14")
    bot.States.AddHeader('Kill Spot 14')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-10303, 4110, "Move to Kill Spot 15")
    bot.States.AddHeader('Kill Spot 15')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-10500, 5500, "Move to Kill Spot 16")
    bot.States.AddHeader('Kill Spot 16')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-9700, 2400, "Move to Kill Spot 17")
    bot.States.AddHeader('Kill Spot 17')
    bot.States.AddCustomState(lambda: kill_sensalis(bot), "Killing Sensalis")
    bot.States.AddCustomState(lambda: death_or_completion_callback(bot), "Return to Seitung Harbor")


bot.SetMainRoutine(main_farm)


def main():
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()
