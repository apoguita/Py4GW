from Py4GWCoreLib import *

"""
Rollerbeetle Racing Bot
- Copephobia

This bot will constantly run the Rollerbeetle Racing event in the outpost.
It requires the player to have the outpost unlocked (traveled to at least once) or already be in the outpost.

Improvements to make:
- Wait until the "Waiting to start" frame box disappears, instead of waiting for 28 seconds.
- Better skill usage logic.
- Randomize some of the pathing to make it less obvious this is a bot.
- Don't target the nearest enemy if the ID doesn't change.
- Determine possible movement "stuck" spots.
- Hold forward for a few seconds before starting to increase RRPM at start of race.
"""

module_name = "Rollerbeetle Racing Bot"

race_coords_list = [
    (-5670, -2755),
    (-5512, -2278),
    (-5311, -1816),
    (-5051, -1380),
    (-4744, -1015),
    (-4420, -637),
    (-4105, -246),
    (-3796, 149),
    (-3629, 615),
    (-3944, 969),
    (-4367, 1154),
    (-4795, 1385),
    (-4798, 1394),
    (-4701, 1467),
    (-4953, 1954),
    (-5023, 2488),
    (-5079, 3190),
    (-5103, 3903),
    (-5087, 4472),
    (-4937, 5000),
    (-4717, 5662),
    (-4414, 6270),
    (-4048, 6824),
    (-3680, 7247),
    (-3466, 7910),
    (-3277, 8527),
    (-3044, 9103),
    (-2807, 9696),
    (-2518, 10247),
    (-2003, 10574),
    (-1431, 10775),
    (-1057, 11163),
    (-1473, 11701),
    (-1584, 12327),
    (-1093, 12830),
    (-568, 13286),
    (14, 13647),
    (617, 13950),
    (1279, 14165),
    (1634, 14266),
    (1811, 14606),
    (1994, 14276),
    (2167, 13892),
    (2478, 13263),
    (2907, 12708),
    (3214, 12355),
    (3327, 11914),
    (3275, 11420),
    (3250, 10938),
    (3266, 10492),
    (3347, 10093),
    (3484, 9713),
    (3595, 9357),
    (3707, 9014),
    (3827, 8630),
    (3934, 8264),
    (4066, 7853),
    (3964, 7404),
    (3510, 7213),
    (3084, 7056),
    (2707, 6877),
    (2347, 6674),
    (2024, 6456),
    (1764, 6176),
    (1717, 5815),
    (1751, 5460),
    (1775, 5127),
    (1746, 4743),
    (1626, 4385),
    (1412, 4136),
    (1044, 3984),
    (645, 3864),
    (531, 3587),
    (36, 3547),
    (-495, 3757),
    (-645, 3750),
    (-648, 3748),
    (-841, 3652),
    (-1093, 2991),
    (-1270, 2363),
    (-1295, 1870),
    (-978, 1507),
    (-594, 1180),
    (-191, 874),
    (229, 609),
    (671, 348),
    (1057, 132),
    (1340, -65),
    (1607, -229),
    (1853, -92),
    (2166, -38),
    (2504, -60),
    (2844, -137),
    (3264, -259),
    (3767, -423),
    (4253, -599),
    (4750, -745),
    (5305, -917),
    (5853, -1043),
    (6407, -1158),
    (6947, -1248),
    (7407, -1437),
    (7357, -1834),
    (7034, -2114),
    (6810, -2273),
    (6819, -2284),
    (6744, -2370),
    (6325, -2507),
    (5708, -2658),
    (5639, -2934),
    (5670, -3420),
    (5753, -3993),
    (5885, -4702),
    (6213, -5238),
    (6685, -5334),
    (7122, -5340),
    (7551, -5332),
    (7942, -5267),
    (8223, -5050),
    (8071, -4668),
    (7502, -4308),
    (7057, -4113),
    (6700, -4144),
    (6748, -4532),
    (7215, -4573),
    (7662, -4357),
    (8091, -4135),
    (8577, -4263),
    (8995, -4547),
    (9390, -4960),
    (9231, -5566),
    (8932, -6128),
    (8627, -6678),
    (8333, -7213),
    (8075, -7763),
    (8165, -8353),
    (8290, -8929),
    (8411, -9461),
    (8306, -9965),
    (7792, -10327),
    (7143, -10266),
    (6571, -9989),
    (6030, -9647),
    (5481, -9300),
    (4927, -9049),
    (4393, -8807),
    (3883, -8560),
    (3528, -8142),
    (3165, -7751),
    (2737, -7503),
    (2193, -7260),
    (1569, -6921),
    (1096, -6567),
    (703, -6396),
    (228, -6209),
    (-193, -5734),
    (-608, -5271),
    (-989, -4863),
    (-1503, -4405)
]

ROLLERBEETLE_RACING_OUTPOST_ID = 467
RACING_MEDAL_MODEL_ID = 37793

SKILL_DISHONORABLE = 2546

SKILL_RAM = 1918
SKILL_HARDEN_SHELL = 1919
SKILL_ROLLERBEETLE_DASH = 1920
SKILL_SUPER_ROLLERBEETLE = 1921
SKILL_ROLLERBEETLE_ECHO = 1922
SKILL_DISTRACTING_LUNGE = 1923
SKILL_ROLLERBEETLE_BLAST = 1924
SKILL_SPIT_ROCKS = 1925

class BotVars:
    def __init__(self, map_id=0):
        self.starting_map = map_id
        self.bot_started = False
        self.window_module = ImGui.WindowModule()
        self.variables = {}
        self.run_count = 0
        self.initial_medals = 0
        self.current_medals = 0
        self.start_time = 0.0
        self.aftercast_timer = Timer()
        self.current_target = 0
        self.result_first_place = 0
        self.result_second_place = 0
        self.result_third_place = 0
        self.result_fourth_place = 0
        self.result_fifth_sixth_place = 0
        self.result_did_not_finish = 0

bot_vars = BotVars(map_id=ROLLERBEETLE_RACING_OUTPOST_ID)
bot_vars.window_module = ImGui.WindowModule(module_name, window_name="Rollerbeetle Racing Bot", window_size=(250, 325))

class StateMachineVars:
    def __init__(self):
        self.state_machine = FSM("Rollerbeetle Racing Bot")
        self.wait_for_dishonorable_removal = FSM("Waiting for Dishonorable Removal")
        self.travel_and_enter_challenge = FSM("Travel and Enter Challenge")
        self.race_pathing = Routines.Movement.PathHandler(race_coords_list)
        self.movement_handler = Routines.Movement.FollowXY(300)
        self.in_waiting_routine = False
        self.is_running_race = False

FSM_vars = StateMachineVars()

# Helper Functions
def StartBot():
    global bot_vars
    bot_vars.bot_started = True
    bot_vars.start_time = time.time()
    bot_vars.current_medals = bot_vars.initial_medals = Inventory.GetModelCount(RACING_MEDAL_MODEL_ID)

def StopBot():
    global bot_vars
    bot_vars.bot_started = False

def IsBotStarted():
    global bot_vars
    return bot_vars.bot_started

def ResetEnvironment():
    global FSM_vars
    FSM_vars.race_pathing.reset()
    FSM_vars.movement_handler.reset()
    FSM_vars.state_machine.reset()
    FSM_vars.wait_for_dishonorable_removal.reset()
    FSM_vars.travel_and_enter_challenge.reset()
    FSM_vars.is_running_race = False
    FSM_vars.in_waiting_routine = False

def set_waiting_routine():
    global FSM_vars
    FSM_vars.in_waiting_routine = True

def end_waiting_routine():
    global FSM_vars
    FSM_vars.in_waiting_routine = False
    bot_vars.aftercast_timer.Reset()
    return True

def set_running_routine():
    global FSM_vars, bot_vars
    FSM_vars.is_running_race = True

def end_running_routine():
    global FSM_vars, bot_vars
    FSM_vars.is_running_race = False
    return True

def DoesPlayerHaveEffect(effect_id):
    """
    Returns True if the player's effects include the specified effect ID.
    """
    player_id = Player.GetAgentID()
    return Effects.EffectExists(player_id, effect_id)

# FSM States
FSM_vars.state_machine.AddState(
    name="Waiting for Map Ready",
    exit_condition=lambda: Map.IsMapReady(),
    transition_delay_ms=1000
)

FSM_vars.travel_and_enter_challenge.AddState(
    name="Traveling to Outpost",
    execute_fn=lambda: Routines.Transition.TravelToOutpost(bot_vars.starting_map),
    exit_condition=lambda: Routines.Transition.HasArrivedToOutpost(bot_vars.starting_map),
    transition_delay_ms=1000
)

FSM_vars.wait_for_dishonorable_removal.AddState(
    name="Waiting for Dishonorable Removal",
    execute_fn=lambda: None,  # No specific action, just waiting
    exit_condition=lambda: not DoesPlayerHaveEffect(SKILL_DISHONORABLE),  # Wait until the player no longer has Dishonorable effect
    transition_delay_ms=1000
)

FSM_vars.travel_and_enter_challenge.AddSubroutine(
    name="Waiting for Dishonorable Removal",
    sub_fsm=FSM_vars.wait_for_dishonorable_removal,
    condition_fn=lambda: DoesPlayerHaveEffect(SKILL_DISHONORABLE)
)

FSM_vars.travel_and_enter_challenge.AddState(
    name="Waiting to Enter Race",
    execute_fn=lambda: Map.EnterChallenge(),
    exit_condition=lambda: Map.IsMapReady() and Map.IsExplorable(),
    transition_delay_ms=1000
)

FSM_vars.state_machine.AddSubroutine(
    name="Travel and Enter Challenge",
    sub_fsm=FSM_vars.travel_and_enter_challenge,
    condition_fn=lambda: not Map.GetMapID() == ROLLERBEETLE_RACING_OUTPOST_ID or (Map.GetMapID() == ROLLERBEETLE_RACING_OUTPOST_ID and Map.IsOutpost() and Map.IsMapReady())
)

FSM_vars.state_machine.AddState(
    name="Waiting For Map Load",
    exit_condition=lambda: Routines.Transition.IsExplorableLoaded(),
    transition_delay_ms=1000
)

FSM_vars.state_machine.AddState(name="Waiting for Race to Start",
    execute_fn=lambda: set_waiting_routine(),
    transition_delay_ms=28100,
    exit_condition=lambda: end_waiting_routine()
)

FSM_vars.state_machine.AddState(name="Starting Race",
    execute_fn=lambda: set_running_routine()
)

FSM_vars.state_machine.AddState(
    name="Running Race Path",
    execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.race_pathing, FSM_vars.movement_handler),
    exit_condition=lambda: (
        Routines.Movement.IsFollowPathFinished(FSM_vars.race_pathing, FSM_vars.movement_handler)
        or Agent.IsDead(Player.GetAgentID())
        or Map.IsOutpost()
        or IsPlayerWithinRadius((-1508, -4410), 200)
    ),
    run_once=False
)

FSM_vars.state_machine.AddState(name="Finishing Race",
    execute_fn=lambda: end_running_routine(),
)

FSM_vars.state_machine.AddState(
    name="Updating Stats",
    execute_fn=lambda: UpdateBotStats(),
    transition_delay_ms=1000
)

FSM_vars.state_machine.AddState(
    name="Waiting for Map Load",
    exit_condition=lambda: Map.IsMapLoading(),
    transition_delay_ms=1000
)

def UpdateBotStats():
    global bot_vars
    bot_vars.run_count += 1
    new_meals_count = Inventory.GetModelCount(RACING_MEDAL_MODEL_ID)
    medals_gained = new_meals_count - bot_vars.current_medals
    bot_vars.current_medals = new_meals_count
    
    if medals_gained == 10:
        bot_vars.result_first_place += 1
    elif medals_gained == 7:
        bot_vars.result_second_place += 1
    elif medals_gained == 5:
        bot_vars.result_third_place += 1
    elif medals_gained == 3:
        bot_vars.result_fourth_place += 1
    elif medals_gained == 1:
        bot_vars.result_fifth_sixth_place += 1
    elif medals_gained == 0:
        bot_vars.result_did_not_finish += 1

def IsPlayerWithinRadius(target_coords, radius):
    player_x, player_y = Agent.GetXY(Player.GetAgentID())
    target_x, target_y = target_coords
    distance = ((player_x - target_x) ** 2 + (player_y - target_y) ** 2) ** 0.5
    return distance <= radius

def DrawWindow():
    global bot_vars, FSM_vars

    try:
        if bot_vars.window_module.first_run:
            PyImGui.set_next_window_size(bot_vars.window_module.window_size[0], bot_vars.window_module.window_size[1])
            PyImGui.set_next_window_pos(bot_vars.window_module.window_pos[0], bot_vars.window_module.window_pos[1])
            bot_vars.window_module.first_run = False

        if PyImGui.begin(bot_vars.window_module.window_name, bot_vars.window_module.window_flags):

            if IsBotStarted():
                if PyImGui.button("Stop Bot"):
                    ResetEnvironment()
                    StopBot()
            else:
                # Disable the "Start Bot" button if the current map ID is not 467 and the player does not have the outpost unlocked
                if not Map.GetMapID() == ROLLERBEETLE_RACING_OUTPOST_ID and not Map.IsMapUnlocked(ROLLERBEETLE_RACING_OUTPOST_ID):
                    PyImGui.text("Go to Rollerbeetle Racing Outpost first!\nVia Kamadan, Shing Jea, LA, GToB")
                elif Player.GetAccountName() == "":
                    PyImGui.text("Account is not registered yet!\nTalk to Tolkano [Tournament]")
                else:
                    if PyImGui.button("Start Bot"):
                        ResetEnvironment()
                        StartBot()

            PyImGui.separator()

            elapsed_time = time.time() - bot_vars.start_time if bot_vars.start_time else 0
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            seconds = int(elapsed_time % 60)
            formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

            average_runs = bot_vars.run_count / (elapsed_time / 3600) if elapsed_time > 0 else 0
            average_medals = (bot_vars.current_medals - bot_vars.initial_medals) / bot_vars.run_count if bot_vars.run_count > 0 else 0

            headers = ["Metric", "Value"]
            data = [
                ("Total Bot Runtime", formatted_time),
                ("Number of Runs", f"{bot_vars.run_count}"),
                ("Runs per Hour", f"{average_runs:.2f}"),
                ("Medals Gained", f"{(bot_vars.current_medals - bot_vars.initial_medals)}"),
                ("Medals per Run", f"{average_medals:.2f}"),
                ("First Place", f"{bot_vars.result_first_place}"),
                ("Second Place", f"{bot_vars.result_second_place}"),
                ("Third Place", f"{bot_vars.result_third_place}"),
                ("Fourth Place", f"{bot_vars.result_fourth_place}"),
                ("Fifth/Sixth Place", f"{bot_vars.result_fifth_sixth_place}"),
                ("Did Not Finish", f"{bot_vars.result_did_not_finish}"),
            ]

            ImGui.table("Bot Stats", headers, data)

            current_state = FSM_vars.state_machine.get_current_step_name() if FSM_vars.state_machine else "None"
            if IsBotStarted():
                PyImGui.text(f"Current State: {current_state}")

        PyImGui.end()

    except Exception as e:
        frame = inspect.currentframe()
        current_function = frame.f_code.co_name if frame else "Unknown"
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Error in {current_function}: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def UseSkills():
    """
    Logic to use skills based on the specified conditions:
    1. Always use skill slot 8 if it is available and the player does not have effect ID 78.
    2. Select the nearest target.
    3. If the nearest target is moving and skill slot 4 is available, use skill slot 4 on the nearest target.
    4. If the nearest target is moving and skill slot 5 is available, use skill slot 5 on the nearest target.
    5. If the nearest target is moving and skill slot 7 is available, use skill slot 7 on the nearest target.
    6. If skill slot 6 is available, check if skill slot 8 is available. If both are available, use skill slot 6 then skill slot 8.
    """
    global bot_vars

    if bot_vars.aftercast_timer.HasElapsed(200):
        # Reset the aftercast timer to avoid spamming skills
        bot_vars.aftercast_timer.Reset()
    else:
        return

    player_id = Player.GetAgentID()
    player_x, player_y = Agent.GetXY(player_id)

    skill_1_data = SkillBar.GetSkillData(1)
    skill_2_data = SkillBar.GetSkillData(2)
    skill_3_data = SkillBar.GetSkillData(3)
    skill_4_data = SkillBar.GetSkillData(4)
    skill_5_data = SkillBar.GetSkillData(5)
    skill_6_data = SkillBar.GetSkillData(6)
    skill_7_data = SkillBar.GetSkillData(7)
    skill_8_data = SkillBar.GetSkillData(8)

    # Try to double up Super Rollerbeetle if possible
    if (skill_6_data.recharge == 0 or DoesPlayerHaveEffect(SKILL_ROLLERBEETLE_ECHO)) and skill_8_data.recharge == 0:
        SkillBar.UseSkill(6)
        SkillBar.UseSkill(8)
        return
    
    # Try to double up Rollerbeetle Dash if possible
    if (skill_6_data.recharge == 0 or DoesPlayerHaveEffect(SKILL_ROLLERBEETLE_ECHO)) and skill_1_data.recharge == 0:
        SkillBar.UseSkill(6)
        SkillBar.UseSkill(1)
        return

    # Always use Super Rollerbeetle
    if not DoesPlayerHaveEffect(SKILL_SUPER_ROLLERBEETLE):
        if skill_8_data.recharge == 0 or (skill_6_data.id == SKILL_SUPER_ROLLERBEETLE and skill_6_data.recharge == 0):
            if skill_8_data.recharge == 0:
                SkillBar.UseSkill(8)
            elif skill_6_data.recharge == 0:
                SkillBar.UseSkill(6)
            return

    # Always use ram
    if not DoesPlayerHaveEffect(SKILL_SUPER_ROLLERBEETLE) and not DoesPlayerHaveEffect(SKILL_RAM):
        if skill_3_data.recharge == 0:
            SkillBar.UseSkill(3)
            return

    # Always use harden shell
    if not DoesPlayerHaveEffect(SKILL_HARDEN_SHELL):
        if skill_2_data.recharge == 0:
            SkillBar.UseSkill(2)
            return

    # Always use rollerbeetle dash
    if not DoesPlayerHaveEffect(SKILL_SUPER_ROLLERBEETLE) and not DoesPlayerHaveEffect(SKILL_ROLLERBEETLE_DASH) and not DoesPlayerHaveEffect(SKILL_RAM) and skill_1_data.recharge == 0:
        SkillBar.UseSkill(1)
        return

    # Get the nearest target
    agent_array = AgentArray.GetEnemyArray()
    agent_array = AgentArray.Filter.ByAttribute(agent_array, 'IsAlive')
    agent_array = AgentArray.Filter.ByDistance(agent_array, (player_x, player_y), 2000)
    agent_array = AgentArray.Sort.ByDistance(agent_array, Player.GetXY())

    if len(agent_array) > 0:
        target_id = agent_array[0]

        # Check if the nearest target is moving
        if Agent.IsMoving(target_id):
            # Only update target if changed
            if not target_id == bot_vars.current_target:
                Player.ChangeTarget(target_id)
                bot_vars.current_target = target_id

            # Use skill slot 4 if available
            if skill_4_data.recharge == 0:
                SkillBar.UseSkill(4, target_id)
                return

            # Use skill slot 5 if available
            if skill_5_data.recharge == 0:
                SkillBar.UseSkill(5, target_id)
                return

            # Use skill slot 7 if available
            if skill_7_data.recharge == 0:
                SkillBar.UseSkill(7, target_id)
                return

    # Get all agents within range
    agents_within_1000 = AgentArray.Filter.ByDistance(agent_array, (player_x, player_y), 1000)
    agents_within_500 = AgentArray.Filter.ByDistance(agent_array, (player_x, player_y), 500)

    # Use skill slot 2 if there are more than 1 agent within 1000 distance
    if len(agents_within_1000) >= 1:
        SkillBar.UseSkill(2)
        return

    # Knockdown adjacent foes
    if len(agents_within_500) >= 1:
        SkillBar.UseSkill(3)
        return

# Main Function
def main():
    global bot_vars, FSM_vars
    try:
        DrawWindow()

        if IsBotStarted():
            # Only call UseSkills if the map ID is 467, the map is explorable, and the race is running
            if Map.GetMapID() == ROLLERBEETLE_RACING_OUTPOST_ID and Map.IsExplorable() and FSM_vars.is_running_race:
                UseSkills()

            if FSM_vars.state_machine.is_finished():
                ResetEnvironment()
            else:
                FSM_vars.state_machine.update()

    except ImportError as e:
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass

if __name__ == "__main__":
    main()