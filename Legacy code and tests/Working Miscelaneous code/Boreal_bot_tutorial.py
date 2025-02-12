from Py4GWCoreLib import *

boreal_station = 675

@dataclass
class BotVariables:
    window_info: ImGui.WindowModule = field(default=None)
    state: str = "Not Started"
    fsm: FSM = field(default=None)
    total_timer: Timer = field(default=None)
    run_timer: Timer = field(default=None)
    run_count: int = 0
    avg_run_time: int = 0
    lockpicks_consumed: int = 0
    lockpicks_retained: int = 0
    gold_item_count: int = 0
    sell_to_vendor_fsm = FSM("SellToVendor")

bot_vars = BotVariables(window_info = ImGui.WindowModule("Boreal Bot Tutorial",
                                 window_name = "Control Panel",
                                 window_flags = PyImGui.WindowFlags.AlwaysAutoResize),
                        fsm = FSM("MainRoutine"),
                        total_timer = Timer(),
                        run_timer = Timer())

bot_vars.total_timer.Start()

#Helper  functions to handle FSM states
def StopBot():
    global bot_vars
    bot_vars.state = "Not Started"
    bot_vars.fsm.stop()
    bot_vars.run_timer.Stop()

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

def IsSkillBarLoaded(log_action = True):
    global bot_vars
    primary_profession, secondary_profession = Agent.GetProfessionNames(Player.GetAgentID())
    if primary_profession != "Assassin" and secondary_profession != "Assassin":
        current_function = inspect.currentframe().f_code.co_name
        Py4GW.Console.Log(bot_vars.window_info.module_name, f"{current_function} - This bot requires A/Any or Any/A to work, halting.", Py4GW.Console.MessageType.Error)
        StopBot()
        return False

    if log_action:
        Py4GW.Console.Log(bot_vars.window_info.module_name, "Skill bar loaded successfully.", Py4GW.Console.MessageType.Info)
    return True

def IsInventoryHandlingNeeded():
    return ( Inventory.GetFreeSlotCount() < 1 or Inventory.GetModelCount(22751) < 1)


#End of Helper functions
#Sub routines for FSM
bot_vars.sell_to_vendor_fsm.AddState(name="Target Merchant",
                                     execute_fn=lambda: Routines.Targeting.TargetMerchant(),
                                     transition_delay_ms=1000)
bot_vars.sell_to_vendor_fsm.AddState(name="Interact with Merchant",
                                     execute_fn=lambda: Routines.Targeting.InteractTarget(),
                                     exit_condition=lambda: Routines.Targeting.HasArrivedToTarget())
                                     #we will revisit this routine to add the actual trading functions 
                                     #in a later oportunity

#Main FSM states

bot_vars.fsm.AddState(name="Are we in boreal station?", 
                       execute_fn=lambda: Routines.Transition.TravelToOutpost(boreal_station), #it will run this block of code (default is run code once)
                       exit_condition=lambda: Routines.Transition.HasArrivedToOutpost(boreal_station), #will check this condition until met
                       transition_delay_ms=1000) #interval or delay to check the condition
bot_vars.fsm.AddState(name="Load SkillBar",
                       execute_fn=lambda: LoadSkillBar(),
                       transition_delay_ms=1000,
                       exit_condition=lambda: IsSkillBarLoaded())
bot_vars.fsm.AddSubroutine(name="Inventory Handling",
                       sub_fsm = bot_vars.sell_to_vendor_fsm,
                       condition_fn=lambda: IsInventoryHandlingNeeded())

def DrawWindow():
    global bot_vars
    try:
        if bot_vars.window_info.first_run:
            PyImGui.set_next_window_size(bot_vars.window_info.window_size[0], bot_vars.window_info.window_size[1])     
            PyImGui.set_next_window_pos(bot_vars.window_info.window_pos[0], bot_vars.window_info.window_pos[1])
            bot_vars.window_info.first_run = False

        if PyImGui.begin(bot_vars.window_info.window_name, bot_vars.window_info.window_flags):

            headers = ["Value","Data"]
            data = [
                ("Current state", f"{bot_vars.state}"),
                ("FSM step", f"{bot_vars.fsm.get_current_step_name()}"),
                ("Uptime", f"{bot_vars.total_timer.FormatElapsedTime("hh:mm:ss")}"),
                ("Run timer", f"{bot_vars.run_timer.FormatElapsedTime("mm:ss:ms")}"),
                ("Run Count", f"{bot_vars.run_count}"),
                ("Average Run Time", f"{bot_vars.avg_run_time}"),
                ("Lockpicks Consumed", f"{bot_vars.lockpicks_consumed}"),
                ("Lockpicks Retained", f"{bot_vars.lockpicks_retained}"),
                ("Gold Item Count", f"{bot_vars.gold_item_count}"),
            ]

            ImGui.table("boreal Main window info", headers, data)

            PyImGui.separator()

            if bot_vars.state == "Not Started":
                if PyImGui.button("Start"):
                    bot_vars.fsm.reset()
                    bot_vars.run_timer.Start()
                    bot_vars.state = "Running"
            else:
                if PyImGui.button("Stop"):
                    StopBot()
        
                    
            PyImGui.end()
    except Exception as e:
        current_function = inspect.currentframe().f_code.co_name
        Py4GW.Console.Log(bot_vars.window_info.module_name, f"Error in {current_function}: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def main():
    global bot_vars
    try:
        DrawWindow()

        if bot_vars.state == "Running":
            if not bot_vars.fsm.is_finished():
                bot_vars.fsm.update()
            else:
                # Reset the FSM environment
                bot_vars.run_timer.Pause()
                bot_vars.fsm.reset()
                bot_vars.state = "Not Started"

        target = Player.GetTargetID()
        backfire_id =28
        interrupt_slot = 6
        player_number = Player.GetPlayerNumber()
        HeroAI = PyHeroAI.PyHeroAI()
        if Agent.IsCasting(target) and Agent.GetCastingSkill(target) == backfire_id and Agent.IsCaster(target):
            HeroAI.SetCombat(player_number, False)
            Skillbar.SkillBar.UseSkill(interrupt_slot)
            HeroAI.SetCombat(player_number, True)
            Skillbar.SkillBar.UseSkill(interrupt_slot)
            

            

    except ImportError as e:
        Py4GW.Console.Log(bot_vars.window_info.module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_info.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(bot_vars.window_info.module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_info.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(bot_vars.window_info.module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_info.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log(bot_vars.window_info.module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_info.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass

if __name__ == "__main__":
    main()
