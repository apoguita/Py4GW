from Py4GWCoreLib import *

module_name = "BorealBot"

outpost_coordinate_list = [(8180, -27084), (4790, -27870)]
explorable_coordinate_list = [(2928,-24873), (2724,-22040), (-371,-20086), (-3294,-18164), (-5267,-14941), (-5297,-11045), (-1969,-12627), (1165,-14245), (4565,-15956)]


class BotVars:
    def __init__(self, map_id=0):
        self.starting_map = map_id
        self.bot_started = False
        self.window_module = None
        self.variables = {}

bot_vars = BotVars(map_id=675) #boreal station
bot_vars.window_module = ImGui.WindowModule(module_name, window_name="Boreal Chest Runner 1.0", window_size=(300, 300))

class StateMachineVars:
        def __init__(self):
            self.state_machine = FSM("Main")
            self.loot_chest = FSM("LootChest")
            self.sell_to_vendor = FSM("SellToVendor")
            self.outpost_pathing = Routines.Movement.PathHandler(outpost_coordinate_list)
            self.explorable_pathing = Routines.Movement.PathHandler(explorable_coordinate_list)
            self.chest_found_pathing = None
            self.movement_handler = Routines.Movement.FollowXY()

FSM_vars = StateMachineVars()

#Helper Functions
def StartBot():
    global bot_vars
    bot_vars.bot_started = True

def StopBot():
    global bot_vars
    bot_vars.bot_started = False

def IsBotStarted():
    global bot_vars
    return bot_vars.bot_started

def DoesNeedInventoryHandling():
    return ( Inventory.GetFreeSlotCount() < 1 or Inventory.GetModelCount(22751) < 1)

def IsChestFound(max_distance=2500):
    return Routines.Targeting.GetNearestChest(max_distance) != 0

def ResetFollowPath():
    global FSM_vars
    FSM_vars.movement_handler.reset()
    chest_id = Routines.Targeting.GetNearestChest(max_distance=2500)
    chest_x, chest_y = Agent.GetXY(chest_id)
    found_chest_coord_list = [(chest_x, chest_y)]
    FSM_vars.chest_found_pathing = Routines.Movement.PathHandler(found_chest_coord_list)

def LoadSkillBar():
    primary_profession, secondary_profession = Agent.GetProfessionNames(Player.GetAgentID())

    if primary_profession == "Warrior":
        SkillBar.LoadSkillTemplate("OQcAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Ranger":
        SkillBar.LoadSkillTemplate("OgcAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Monk":
        SkillBar.LoadSkillTemplate("OwcAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Necromancer":
        SkillBar.LoadSkillTemplate("OAdAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Mesmer":
        SkillBar.LoadSkillTemplate("OQdAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Elementalist":
        SkillBar.LoadSkillTemplate("OgdAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Assassin":
        SkillBar.LoadSkillTemplate("OwBAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Ritualist":
        SkillBar.LoadSkillTemplate("OAeAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Paragon":
        SkillBar.LoadSkillTemplate("OQeAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Dervish":
        SkillBar.LoadSkillTemplate("OgeAQ3lTQ0kAAAAAAAAAAA")

def IsSkillBarLoaded():
    global bot_vars
    primary_profession, secondary_profession = Agent.GetProfessionNames(Player.GetAgentID())
    if primary_profession != "Assassin" and secondary_profession != "Assassin":
        current_function = inspect.currentframe().f_code.co_name
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"{current_function} - This bot requires A/Any or Any/A to work, halting.", Py4GW.Console.MessageType.Error)
        ResetEnvironment()
        StopBot()
        return False
    
    
    #bot_vars.skill_caster.skills = SkillBar.GetSkillbar()
    Py4GW.Console.Log(bot_vars.window_module.module_name, f"SkillBar Loaded.", Py4GW.Console.MessageType.Info)       
    return True

#FSM Routine for looting chest
FSM_vars.loot_chest.AddState(name="Reset Follow Path To Chest",
                    execute_fn=lambda: ResetFollowPath())
FSM_vars.loot_chest.AddState(name="MoveToChest",
                    execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.chest_found_pathing, FSM_vars.movement_handler),
                    exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.chest_found_pathing, FSM_vars.movement_handler),
                    run_once=False)
FSM_vars.loot_chest.AddState(name="Select Chest",
                    execute_fn=lambda: Player.ChangeTarget(Routines.Targeting.GetNearestChest(max_distance=2500)),
                    transition_delay_ms=1000)
FSM_vars.loot_chest.AddState(name="InteractAgent",
                    execute_fn=lambda: Routines.Targeting.InteractTarget(),
                    transition_delay_ms=1000)
FSM_vars.loot_chest.AddState(name="Select Item",
                    execute_fn=lambda: Player.ChangeTarget(Routines.Targeting.GetNearestItem(max_distance=300)),
                    transition_delay_ms=1000)
FSM_vars.loot_chest.AddState(name="PickUpItem",
                    execute_fn=lambda: Routines.Targeting.InteractTarget(),
                    transition_delay_ms=1000)

#FSM Routine for Locating and following the merchant
FSM_vars.sell_to_vendor.AddState(name="Target Merchant",
                        execute_fn=lambda: Routines.Targeting.TargetMerchant(),
                        transition_delay_ms=1000)
FSM_vars.sell_to_vendor.AddState(name="InteractMerchant",
                        execute_fn=lambda: Routines.Targeting.InteractTarget(),
                        exit_condition=lambda: Routines.Targeting.HasArrivedToTarget())
                        #sell items

#MAIN STATE MACHINE CONFIGURATION
FSM_vars.state_machine.AddState(name="Boreal Station Map Check", 
                       execute_fn=lambda: Routines.Transition.TravelToOutpost(bot_vars.starting_map), #the Code to run
                       exit_condition=lambda: Routines.Transition.HasArrivedToOutpost(bot_vars.starting_map), #the condition that needs to be true to continue
                       transition_delay_ms=1000) #interval or delay to check the condition
FSM_vars.state_machine.AddState(name="Load SkillBar",
                       execute_fn=lambda: LoadSkillBar(),
                       transition_delay_ms=1000,
                       exit_condition=lambda: IsSkillBarLoaded())
FSM_vars.state_machine.AddSubroutine(name="Inventory Handling",
                       sub_fsm = FSM_vars.sell_to_vendor,
                       condition_fn=lambda: DoesNeedInventoryHandling())
FSM_vars.state_machine.AddState(name="Leaving Outpost",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.outpost_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.outpost_pathing, FSM_vars.movement_handler) or Map.IsMapLoading(),
                       run_once=False) #run once is false because we want to keep updating the pathing objects
FSM_vars.state_machine.AddState(name="Waiting for Explorable Map Load",
                       exit_condition=lambda: Routines.Transition.IsExplorableLoaded(log_actions=True),
                       transition_delay_ms=1000)
FSM_vars.state_machine.AddState(name="Seek for Chest",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.explorable_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.explorable_pathing, FSM_vars.movement_handler) or IsChestFound(max_distance=2500),
                       run_once=False)
FSM_vars.state_machine.AddSubroutine(name="Loot Chest",
                       sub_fsm = FSM_vars.loot_chest,
                       condition_fn=lambda: IsChestFound(max_distance=2500))

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
                if PyImGui.button("Start Bot"):
                    ResetEnvironment()
                    StartBot()

            PyImGui.separator()

            if PyImGui.begin_tab_bar("MyTabBar"):

                if PyImGui.begin_tab_item("State Machine"):

                    fsm_previous_step = FSM_vars.state_machine.get_previous_step_name()
                    fsm_current_step = FSM_vars.state_machine.get_current_step_name()
                    fsm_next_step = FSM_vars.state_machine.get_next_step_name()

                    headers = ["Value","Data"]
                    data = [
                        ("Previous Step:", f"{fsm_previous_step}"),
                        ("Current Step:", f"{fsm_current_step}"),
                        ("Next Step:", f"{fsm_next_step}"),
                        ("State Machine is started:", f"{FSM_vars.state_machine.is_started()}"),
                        ("State Machine is finished:", f"{FSM_vars.state_machine.is_finished()}"),
                    ]

                    ImGui.table("state machine info", headers, data)

                    PyImGui.text("FollowXY Pathing")
                    headers = ["Value","Data"]
                    data = [
                        ("Waypoint:", f"{FSM_vars.movement_handler.waypoint}"),
                        ("Folowing:", f"{FSM_vars.movement_handler.is_following()}"),
                        ("Has Arrived:", f"{FSM_vars.movement_handler.has_arrived()}"),
                        ("Distance to Waypoint:", f"{FSM_vars.movement_handler.get_distance_to_waypoint()}"),
                        ("Time Elapsed:", f"{FSM_vars.movement_handler.get_time_elapsed()}"),
                        ("wait Timer:", f"{FSM_vars.movement_handler.wait_timer.GetElapsedTime()}"),
                        ("wait timer run once", f"{FSM_vars.movement_handler.wait_timer_run_once}"),
                        ("is casting", f"{Agent.IsCasting(Player.GetAgentID())}"),
                        ("is moving", f"{Agent.IsMoving(Player.GetAgentID())}"),
                    ]

                    ImGui.table("follow info", headers, data)
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Skillbar"):
                    PyImGui.text("This is content in Tab 2")
                    
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Tab 3"):
                    PyImGui.text("This is content in Tab 3")
                    PyImGui.end_tab_item()

                PyImGui.end_tab_bar()

        PyImGui.end()

    except Exception as e:
        current_function = inspect.currentframe().f_code.co_name
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Error in {current_function}: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def ResetEnvironment():
    global FSM_vars
    FSM_vars.outpost_pathing.reset()
    FSM_vars.explorable_pathing.reset()
    FSM_vars.movement_handler.reset()
    if FSM_vars.chest_found_pathing is not None:
        FSM_vars.chest_found_pathing.reset()

    FSM_vars.state_machine.reset()
    FSM_vars.loot_chest.reset()
    FSM_vars.sell_to_vendor.reset()

def main():
    global bot_vars,FSM_vars
    try:
        DrawWindow()

        if IsBotStarted():
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
