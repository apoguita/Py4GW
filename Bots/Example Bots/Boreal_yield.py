from Py4GWCoreLib import *
from typing import Generator, List, Tuple

MODULE_NAME = "Boreal Bot 3.0 YIELD"

#region globals
path_points_to_exit_outpost = [(8180.0, -27084.0), (4790.0, -27870.0)]
path_points_to_look_for_chest: List[Tuple[float, float]] = [(2928,-24873), (2724,-22040), (-371,-20086), (-3294,-18164), (-5267,-14941), (-5297,-11045), (-1969,-12627), (1165,-14245), (4565,-15956)]
      
class Botconfig:
    def __init__(self):
        self.is_script_running = False  
        self.log_to_console = True
        self.routine_finished = False
        self.window_module = ImGui.WindowModule()

class BOTVARIABLES:
    def __init__(self):
        self.config = Botconfig()
        self.window_module = ImGui.WindowModule()

bot_variables = BOTVARIABLES()
bot_variables.config.window_module = ImGui.WindowModule(MODULE_NAME, window_name=MODULE_NAME, window_size=(300, 300), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
#endregion

coroutines = GLOBAL_CACHE.Coroutines

def StopEnvironment():
    global bot_variables
    bot_variables.config.routine_finished = True
    bot_variables.config.is_script_running = False
 
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
                coroutines.append(RunBotSequentialLogic())
                coroutines.append(SkillHandler())    

        bot_variables.config.log_to_console = PyImGui.checkbox("Log to Console", bot_variables.config.log_to_console)
    PyImGui.end()   

def LoadSkillBar():
    primary_profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())

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
        GLOBAL_CACHE.SkillBar.LoadSkillTemplate(template)

    yield from Routines.Yield.wait(500)
      
def IsSkillBarLoaded():
    primary_profession, secondary_profession = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if primary_profession != "Assassin" and secondary_profession != "Assassin":
        Py4GW.Console.Log("Boreal Bot", f"IsSkillBarLoaded - This bot requires A/Any or Any/A to work, halting.", Py4GW.Console.MessageType.Error)
        return False
    return True
               
def IsChestFound(max_distance=4500) -> bool:
    return Routines.Agents.GetNearestChest(max_distance) != 0
        
#endregion

#region skillhandler
def scan_for_aloes():
    enemy_array = GLOBAL_CACHE.AgentArray.GetEnemyArray()
    for enemy in enemy_array:
        if GLOBAL_CACHE.Agent.GetPlayerNumber(enemy) == 6489: 
            return True
    return False

    
def evaluate_skill_casting_status():
    global bot_variables   
    """Returns True if the bot can cast skills, False otherwise."""
    if GLOBAL_CACHE.Map.IsMapLoading():
        yield from Routines.Yield.wait(3000)
        return False
    elif not (GLOBAL_CACHE.Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded() and GLOBAL_CACHE.Map.IsExplorable()):
        yield from Routines.Yield.wait(1000)
        return False
    elif bot_variables.config.routine_finished:
        yield from Routines.Yield.wait(1000)
        return False
    elif not Routines.Checks.Skills.CanCast():
        yield from Routines.Yield.wait(1000)
        return False
    else:
        return True

#region SkillHandler   
def SkillHandler():
    """Thread function to handle skill casting based on conditions."""
    global bot_variables

    dwarven_stability = GLOBAL_CACHE.Skill.GetID("Dwarven_Stability")
    dash = GLOBAL_CACHE.Skill.GetID("Dash")
    i_am_unstoppable = GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable")

    while True:
        can_cast = yield from evaluate_skill_casting_status()
        if not can_cast:
            yield from Routines.Yield.wait(500)
            continue
        
        log_to_console = bot_variables.config.log_to_console
        if Routines.Sequential.Skills.CastSkillID(dwarven_stability,log_to_console):
            yield from Routines.Yield.wait(500)
                        
        if Routines.Sequential.Skills.CastSkillID(dash, log_to_console):
            yield from Routines.Yield.wait(200)
              
        if scan_for_aloes():
            if Routines.Sequential.Skills.CastSkillID(i_am_unstoppable,log_to_console):
                yield from Routines.Yield.wait(200)
        yield
        
#endregion

#region Sequential Code
def pre_run_checks(log_to_console):
    """Verify skillbar, inventory, lockpick checks before starting."""
    if not IsSkillBarLoaded():
        ConsoleLog("Skillbar", "Skillbar not loaded, halting.", Console.MessageType.Error, log=True)
        StopEnvironment()
        return False

    ConsoleLog("Skillbar", "Skillbar loaded", Console.MessageType.Info, log=log_to_console)

    if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1:
        ConsoleLog("Inventory", "No free slots in inventory, halting.", Console.MessageType.Error, log=True)
        StopEnvironment()
        return False

    if GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Lockpick) < 1:
        ConsoleLog("Inventory", "No lockpicks in inventory, halting.", Console.MessageType.Error, log=True)
        StopEnvironment()
        return False

    return True

def RunBotSequentialLogic():
    """Thread function that manages counting based on ImGui button presses."""
    global bot_variables
    while True:
        if not bot_variables.config.is_script_running:
            yield from Routines.Yield.wait(300)
            continue

        while not Routines.Checks.Map.MapValid():
            yield from Routines.Yield.wait(1000)
        
        log_to_console = bot_variables.config.log_to_console
        boreal_station = outpost_name_to_id["Boreal Station"]
        ice_cliff_chasms = explorable_name_to_id["Ice Cliff Chasms"]
        
        bot_variables.config.routine_finished = True
        #correct map?
        yield from Routines.Yield.Map.TravelToOutpost(boreal_station, log_to_console)
        yield from LoadSkillBar()
        
        if not pre_run_checks(log_to_console):
            StopEnvironment()
            continue
            
        ConsoleLog("Boreal Bot", "Exiting Outpost", Console.MessageType.Info, log=log_to_console)
        
        yield from Routines.Yield.Movement.FollowPath(path_points_to_exit_outpost, custom_exit_condition=lambda: Map.IsMapLoading())
        yield from Routines.Yield.Map.WaitforMapLoad(ice_cliff_chasms)
        ConsoleLog("Boreal Bot", "Map loaded", Console.MessageType.Info, log=log_to_console)
        bot_variables.config.routine_finished = False
        yield from Routines.Yield.Movement.FollowPath(path_points_to_look_for_chest, custom_exit_condition=lambda: IsChestFound(max_distance=2500))
        bot_variables.config.routine_finished = True
        if not IsChestFound(max_distance=2500):
            ConsoleLog("Boreal Bot", "No chest found", Console.MessageType.Error, log=log_to_console)
            yield from Routines.Yield.wait(1000)
            continue

        ConsoleLog("Boreal Bot", "Chest found", Console.MessageType.Info, log=log_to_console)
        yield from Routines.Yield.Agents.InteractWithNearestChest()
        ConsoleLog("Boreal Bot", "Finished, restarting", Console.MessageType.Info, log=log_to_console)
        yield from Routines.Yield.wait(1000)

            
            
#endregion   
def main():
    DrawWindow()

if __name__ == "__main__":
    main()
