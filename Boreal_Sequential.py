from Py4GWCoreLib import *

MODULE_NAME = "Boreal Bot 2.0"

#region globals
path_points_to_exit_outpost = [(8180, -27084), (4790, -27870)]
path_points_to_look_for_chest = [(2928,-24873), (2724,-22040), (-371,-20086), (-3294,-18164), (-5267,-14941), (-5297,-11045), (-1969,-12627), (1165,-14245), (4565,-15956)]

            
class Botconfig:
    def __init__(self):
        self.is_script_running = False  
        self.log_to_console = True
        self.routine_finished = False
        self.window_module = ImGui.WindowModule()

class BOTVARIABLES:
    def __init__(self):
        self.action_queue = ActionQueueNode(100)
        self.loot_queue = ActionQueueNode(1250)
        self.config = Botconfig()
        self.window_module = ImGui.WindowModule()


MAIN_THREAD_NAME = "RunBotSequentialLogic"

bot_variables = BOTVARIABLES()
bot_variables.config.window_module = ImGui.WindowModule(MODULE_NAME, window_name=MODULE_NAME, window_size=(300, 300), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

thread_manager = MultiThreading(1)
#endregion

#region Window
def DrawWindow():
    global bot_variables

    if bot_variables.config.window_module.first_run:
        PyImGui.set_next_window_size(bot_variables.config.window_module.window_size[0], bot_variables.config.window_module.window_size[1])     
        PyImGui.set_next_window_pos(bot_variables.config.window_module.window_pos[0], bot_variables.config.window_module.window_pos[1])
        bot_variables.config.window_module.first_run = False

    if PyImGui.begin(bot_variables.config.window_module.window_name, bot_variables.config.window_module.window_flags):
        button_text = "Start script" if not bot_variables.config.is_script_running else "Stop script"
        if PyImGui.button(button_text):
            bot_variables.config.is_script_running = not bot_variables.config.is_script_running      

            if bot_variables.config.is_script_running:
                # Ensure no stale threads
                thread_manager.stop_all_threads()

                # Add threads cleanly
                thread_manager.add_thread(MAIN_THREAD_NAME, RunBotSequentialLogic)
                thread_manager.add_thread("SkillHandler", SkillHandler)
                # Start watchdog
                thread_manager.start_watchdog(MAIN_THREAD_NAME)

            else:
                # Stop all threads and clean environment
                reset_environment()

        if PyImGui.collapsing_header("Config"):
            bot_variables.config.log_to_console = PyImGui.checkbox("Log to Console", bot_variables.config.log_to_console)
    PyImGui.end()   

def LoadSkillBar(action_queue: ActionQueueNode):
    primary_profession, _ = Agent.GetProfessionNames(Player.GetAgentID())

    skill_templates = {
        "Warrior":      "OQcAQ3lTQ0kAAAAAAAAAAA",
        "Ranger":       "OgcAQ3lTQ0kAAAAAAAAAAA",
        "Monk":         "OwcAQ3lTQ0kAAAAAAAAAAA",
        "Necromancer":  "OAdAQ3lTQ0kAAAAAAAAAAA",
        "Mesmer":       "OQdAQ3lTQ0kAAAAAAAAAAA",
        "Elementalist": "OgdAQ3lTQ0kAAAAAAAAAAA",
        "Assassin":     "OwBAQ3lTQ0kAAAAAAAAAAA",
        "Ritualist":    "OAeAQ3lTQ0kAAAAAAAAAAA",
        "Paragon":      "OQeAQ3lTQ0kAAAAAAAAAAA",
        "Dervish":      "OgeAQ3lTQ0kAAAAAAAAAAA"
    }

    template = skill_templates.get(primary_profession)
    if template:
        action_queue.add_action(SkillBar.LoadSkillTemplate, template)

    sleep(0.5)
      
def IsSkillBarLoaded():
    primary_profession, secondary_profession = Agent.GetProfessionNames(Player.GetAgentID())
    if primary_profession != "Assassin" and secondary_profession != "Assassin":
        frame = inspect.currentframe()
        current_function = frame.f_code.co_name if frame else "Unknown"
        Py4GW.Console.Log("Boreal Bot", f"{current_function} - This bot requires A/Any or Any/A to work, halting.", Py4GW.Console.MessageType.Error)
        return False
    return True
               
def IsChestFound(max_distance=2500) -> bool:
    return Routines.Agents.GetNearestChest(max_distance) != 0
        
#endregion

#region skillhandler
def evaluate_skill_casting_status():
    global bot_variables   
    """Returns True if the bot can cast skills, False otherwise."""
    if Map.IsMapLoading():
        sleep(3)
        return False

    if not (Map.IsMapReady() and Party.IsPartyLoaded() and Map.IsExplorable()):
        sleep(1)
        return False

    if bot_variables.config.routine_finished:
        sleep(1)
        return False

    if not Routines.Checks.Skills.CanCast():
        sleep(0.1)
        return False
    
def SkillHandler():
    """Thread function to handle skill casting based on conditions."""
    global MAIN_THREAD_NAME, bot_variables

    dwarven_stability = Skill.GetID("Dwarven_Stability")
    dash = Skill.GetID("Dash")

    while True:
        if not evaluate_skill_casting_status():
            continue
        
        if Routines.Sequential.Skills.CastSkillID(dwarven_stability,bot_variables.action_queue, log=bot_variables.config.log_to_console):
            sleep(0.3)
            
        if Routines.Sequential.Skills.CastSkillID(dash,bot_variables.action_queue, log=bot_variables.config.log_to_console):
            sleep(0.05)
    
#endregion

#region Sequential Code
def pre_run_checks(log_to_console):
    """Verify skillbar, inventory, lockpick checks before starting."""
    if not IsSkillBarLoaded():
        ConsoleLog("Skillbar", "Skillbar not loaded, halting.", Console.MessageType.Error, log=True)
        reset_environment()
        return False

    ConsoleLog("Skillbar", "Skillbar loaded", Console.MessageType.Info, log=log_to_console)

    if Inventory.GetFreeSlotCount() < 1:
        ConsoleLog("Inventory", "No free slots in inventory, halting.", Console.MessageType.Error, log=True)
        reset_environment()
        return False

    if Inventory.GetModelCount(22751) < 1:
        ConsoleLog("Inventory", "No lockpicks in inventory, halting.", Console.MessageType.Error, log=True)
        reset_environment()
        return False

    return True


def RunBotSequentialLogic():
    """Thread function that manages counting based on ImGui button presses."""
    global MAIN_THREAD_NAME, bot_variables
    try:
        while True:
            if not bot_variables.config.is_script_running:
                time.sleep(0.1)
                continue

            log_to_console = bot_variables.config.log_to_console
            action_queue = bot_variables.action_queue
            boreal_station = 675
            ice_cliff_chasms = 499
            
            outpost_path = Routines.Movement.PathHandler(path_points_to_exit_outpost)
            explorable_path = Routines.Movement.PathHandler(path_points_to_look_for_chest)
            movement_object = Routines.Movement.FollowXY()
            #correct map?
            Routines.Sequential.Map.TravelToOutpost(boreal_station, action_queue, log_to_console)
            LoadSkillBar(action_queue)
            
            if not pre_run_checks(log_to_console):
                reset_environment()
                continue
                
            ConsoleLog("Boreal Bot", "Exiting Outpost", Console.MessageType.Info, log=log_to_console)
            
            Routines.Sequential.Movement.FollowPath(outpost_path, movement_object, action_queue, custom_exit_condition=lambda: Map.IsMapLoading())
            Routines.Sequential.Map.WaitforMapLoad(ice_cliff_chasms, log_to_console)
            ConsoleLog("Boreal Bot", "Map loaded", Console.MessageType.Info, log=log_to_console)
            bot_variables.config.routine_finished = False
            Routines.Sequential.Movement.FollowPath(explorable_path, movement_object, action_queue, custom_exit_condition=lambda: IsChestFound(max_distance=2500))

            if not IsChestFound(max_distance=2500):
                ConsoleLog("Boreal Bot", "No chest found", Console.MessageType.Error, log=log_to_console)
                bot_variables.config.routine_finished = True
                sleep(1)
                continue

            ConsoleLog("Boreal Bot", "Chest found", Console.MessageType.Info, log=log_to_console)
            bot_variables.config.routine_finished = True
            Routines.Sequential.Agents.InteractWithNearestChest(action_queue, movement_object)
            ConsoleLog("Boreal Bot", "Finished, restarting", Console.MessageType.Info, log=log_to_console)
            sleep(1)

            
    except Exception as e:
        ConsoleLog("Main Synch Thread", f"Error in SequentialCodeThread: {str(e)}", Console.MessageType.Error, log=True)
        bot_variables.config.is_script_running = False
        bot_variables.action_queue.clear()

            
#endregion   

#region reset_environment

def reset_environment():
    global bot_variables
    bot_variables.config.is_script_running = False
    bot_variables.config.routine_finished = True
    bot_variables.action_queue.clear()
    thread_manager.stop_all_threads()

#endregion

def main():
    if bot_variables.config.is_script_running:
        thread_manager.update_all_keepalives()

    DrawWindow()

    if Map.IsMapLoading():
        return

    if bot_variables.config.is_script_running:
        if not Agent.IsCasting(Player.GetAgentID()):
            if bot_variables.action_queue.IsExpired():
                bot_variables.action_queue.execute_next()
        else:
            bot_variables.action_queue.clear()

if __name__ == "__main__":
    main()
