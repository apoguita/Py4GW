import PyImGui
from typing import Literal, Tuple

from Py4GWCoreLib.Builds import KeiranThackerayEOTN
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui, ActionQueueManager)


class BotSettings:
    # Map/Outpost IDs
    EOTN_OUTPOST_ID = 642
    HOM_OUTPOST_ID = 646
    AUSPICIOUS_BEGINNINGS_MAP_ID = 849

    # Gold threshold for deposit
    GOLD_THRESHOLD_DEPOSIT: int = 90000

    # Properties to enable/disable via setting tab
    WAR_SUPPLIES_ENABLED: bool = False

    # Runs counters
    TOTAL_RUNS: int = 0
    SUCCESSFUL_RUNS: int = 0
    FAILED_RUNS: int = 0

    # Misc
    DEBUG: bool = False


bot = Botting("Auspicious Beginnings",
              custom_build=KeiranThackerayEOTN())
     
def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot)
    GoToEOTN(bot)
    GetBonusBow(bot)
    QuestLoopEntry(bot)  # Start the quest loop
    
def QuestLoopEntry(bot: Botting) -> None:
    """Main quest loop entry point: checks gold, deposits if needed, then runs quest"""
    CheckAndDepositGold(bot)   # Check gold and deposit if threshold exceeded
    ExitToHOM(bot)             # Exit to HOM (skiped if already in HOM)
    PrepareForQuest(bot)       # Get ready in HOM
    EnterQuest(bot)            # Enter the quest
    RunQuest(bot)              # Run the quest (loops back to CheckAndDepositGold)

def _on_death(bot: "Botting"):
    _increment_runs_counters(bot, "fail")
    bot.Properties.ApplyNow("pause_on_danger", "active", False)
    bot.Properties.ApplyNow("halt_on_death","active", True)
    bot.Properties.ApplyNow("movement_timeout","value", 15000)
    bot.Properties.ApplyNow("auto_combat","active", False)
    yield from Routines.Yield.wait(8000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Prepare for Quest_5") 
    fsm.resume()                           
    yield  
    
def on_death(bot: "Botting"):
    print ("Player is dead. Run Failed, Restarting...")
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))

def _EnableCombat(bot: Botting) -> None:
        bot.OverrideBuild(KeiranThackerayEOTN())
        bot.Templates.Aggressive(enable_imp=False)
 
def _DisableCombat(bot: Botting) -> None:
    bot.Templates.Pacifist()

def InitializeBot(bot: Botting) -> None:
    condition = lambda: on_death(bot)
    bot.Events.OnDeathCallback(condition)

def GoToEOTN(bot: Botting) -> None:
    bot.States.AddHeader("Go to EOTN")

    def _go_to_eotn(bot: Botting):
        current_map = GLOBAL_CACHE.Map.GetMapID()
        should_skip_travel = current_map in [BotSettings.EOTN_OUTPOST_ID, BotSettings.HOM_OUTPOST_ID]
        if should_skip_travel:
            if BotSettings.DEBUG:   
                print(f"[DEBUG] Already in EOTN or HOM, skipping travel")
            return

        GLOBAL_CACHE.Map.Travel(BotSettings.EOTN_OUTPOST_ID)
        yield from Routines.Yield.wait(1000)
        yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID) 

    bot.States.AddCustomState(lambda: _go_to_eotn(bot), "GoToEOTN")
      
def GetBonusBow(bot: Botting):
    bot.States.AddHeader("Check for Bonus Bow")

    def _get_bonus_bow(bot: Botting):
        current_map = GLOBAL_CACHE.Map.GetMapID()
        should_skip_bonus_bow = current_map == BotSettings.HOM_OUTPOST_ID
        if should_skip_bonus_bow:
            if BotSettings.DEBUG:   
                print(f"[DEBUG] Already in HOM, skipping bonus bow")
            return

        if not Routines.Checks.Inventory.IsModelInInventoryOrEquipped(ModelID.Bonus_Nevermore_Flatbow.value):
            yield from bot.helpers.Items._spawn_bonus_items()
        yield from Routines.Yield.wait(1000)
        yield from bot.helpers.Items._destroy_bonus_items(exclude_list=[ModelID.Bonus_Nevermore_Flatbow.value])

    bot.States.AddCustomState(lambda: _get_bonus_bow(bot), "GetBonusBow")

def CheckAndDepositGold(bot: Botting) -> None:
    """Check gold on character, deposit if needed"""
    bot.States.AddHeader("Check and Deposit Gold")

    def _check_and_deposit_gold(bot: Botting):
        current_map = GLOBAL_CACHE.Map.GetMapID()
        gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

        if BotSettings.DEBUG:   
            print(f"[DEBUG] CheckAndDepositGold: current_map={current_map}, gold={gold_on_char}")
        
        # Check if deposit is needed
        if gold_on_char > BotSettings.GOLD_THRESHOLD_DEPOSIT:
            if BotSettings.DEBUG:   
                print(f"Gold ({gold_on_char}) exceeds threshold ({BotSettings.GOLD_THRESHOLD_DEPOSIT}), depositing...")
            
            # Ensure we're in EOTN outpost
            if current_map != BotSettings.EOTN_OUTPOST_ID:
                if BotSettings.DEBUG:   
                    print(f"[DEBUG] Traveling to EOTN from map {current_map}")

                GLOBAL_CACHE.Map.Travel(BotSettings.EOTN_OUTPOST_ID)
                yield from Routines.Yield.wait(1000)
                yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID)
                current_map = BotSettings.EOTN_OUTPOST_ID

            # Deposit the gold
            if BotSettings.DEBUG:   
                print(f"Depositing {gold_on_char} gold in bank")
            GLOBAL_CACHE.Inventory.DepositGold(gold_on_char)
            yield from Routines.Yield.wait(1000)
        else:
            if BotSettings.DEBUG:   
                print(f"Gold ({gold_on_char}) below threshold ({BotSettings.GOLD_THRESHOLD_DEPOSIT}), skipping deposit")
        

        if BotSettings.DEBUG:   
            print(f"[DEBUG] After gold check: current_map={current_map}, HOM={BotSettings.HOM_OUTPOST_ID}")

    bot.States.AddCustomState(lambda: _check_and_deposit_gold(bot), "CheckAndDepositGold")

def ExitToHOM(bot: Botting) -> None:
    bot.States.AddHeader("Exit to HOM")

    # Ensure we're in HOM for quest preparation
    def _exit_to_hom(bot: Botting):
        current_map = GLOBAL_CACHE.Map.GetMapID()
        should_exit_to_hom = current_map != BotSettings.HOM_OUTPOST_ID
        should_travel_to_eotn = current_map != BotSettings.EOTN_OUTPOST_ID

        if should_exit_to_hom:
            if BotSettings.DEBUG:   
                print(f"[DEBUG] Not in HOM, need to go there. Currently in map {current_map}")

            if should_travel_to_eotn:
                if BotSettings.DEBUG:   
                    print(f"[DEBUG] Not in EOTN, traveling there first")
                GLOBAL_CACHE.Map.Travel(BotSettings.EOTN_OUTPOST_ID)
                yield from Routines.Yield.wait(1000)
                yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID)

            if BotSettings.DEBUG:   
                print(f"[DEBUG] Moving to portal coordinates and exiting to HOM")

            # Use coroutine version to move to portal and exit
            yield from bot.Move._coro_xy_and_exit_map(-4873.00, 5284.00, target_map_id=BotSettings.HOM_OUTPOST_ID)
        else:
            if BotSettings.DEBUG:   
                print(f"[DEBUG] Already in HOM, skipping travel")
        yield

    bot.States.AddCustomState(lambda: _exit_to_hom(bot), "ExitToHOM")

def PrepareForQuest(bot: Botting) -> None:
    """Prepare for quest in HOM: acquire and equip Keiran's Bow"""
    bot.States.AddHeader("Prepare for Quest")
    bot.Wait.ForMapLoad(target_map_id=BotSettings.HOM_OUTPOST_ID)

    def _prepare_for_quest(bot: Botting):
        # Get Keiran's Bow if we don't have it
        if not Routines.Checks.Inventory.IsModelInInventoryOrEquipped(ModelID.Keirans_Bow.value):
            yield from bot.Move._coro_xy_and_dialog(-6583.00, 6672.00, dialog_id=0x0000008A)
        
        # Equip Keiran's Bow if not already equipped
        if not Routines.Checks.Inventory.IsModelEquipped(ModelID.Keirans_Bow.value):
            yield from bot.helpers.Items._equip(ModelID.Keirans_Bow.value)

    bot.States.AddCustomState(lambda: _prepare_for_quest(bot), "PrepareForQuest")

def deposit_gold(bot: Botting):
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

    # Deposit all gold if character has 90k or more
    if gold_on_char >= 90000:
        bot.Map.Travel(target_map_id=642)
        bot.Wait.ForMapLoad(target_map_id=642)
        yield from Routines.Yield.wait(500)
        GLOBAL_CACHE.Inventory.DepositGold(gold_on_char)
        yield from Routines.Yield.wait(500)
        bot.Move.XYAndExitMap(-4873.00, 5284.00, target_map_id=646)
        bot.Wait.ForMapLoad(target_map_id=646)
        yield

def EnterQuest(bot: Botting) -> None:
    bot.States.AddHeader("Enter Quest")
    bot.Move.XYAndDialog(-6662.00, 6584.00, 0x63E) #enter quest with pool
    bot.Wait.ForMapLoad(target_map_id=BotSettings.AUSPICIOUS_BEGINNINGS_MAP_ID)
    
def RunQuest(bot: Botting) -> None:    
    bot.States.AddHeader("Run Quest")
    _EnableCombat(bot)
    bot.Move.XY(11864.74, -4899.19)
    
    bot.States.AddCustomState(lambda: _handle_bonus_bow(bot), "HandleBonusBow")
    bot.States.AddCustomState(lambda: _handle_war_supplies(bot, True), "EnableWarSupplies")

    bot.Wait.UntilOnCombat(Range.Spirit)
    
    bot.States.AddCustomState(lambda: _handle_war_supplies(bot, False), "DisableWarSupplies")

    bot.Move.XY(10165.07, -6181.43, step_name="First Spawn")
    #bot.Wait.UntilOutOfCombat()
    bot.Properties.Disable("pause_on_danger")
    path = [(8859.57, -7388.68), (9012.46, -9027.44)]
    bot.Move.FollowAutoPath(path, step_name="To corner")
    bot.Properties.Enable("pause_on_danger")
    #bot.Wait.UntilOutOfCombat()

    bot.Move.XY(4518.81, -9504.34, step_name="To safe spot 0")
    bot.Wait.ForTime(4000)
    bot.Properties.Disable("pause_on_danger")
    bot.Move.XY(2622.71, -9575.04, step_name="To patrol")
    bot.Properties.Enable("pause_on_danger")
    bot.Move.XY(325.22, -11728.24)
    
    bot.Properties.Disable("pause_on_danger")
    bot.Move.XY(-2860.21, -12198.37, step_name="To middle")
    bot.Move.XY(-5109.05, -12717.40, step_name="To patrol 3")
    bot.Move.XY(-6868.76, -12248.82, step_name="To patrol 4")
    bot.Properties.Enable("pause_on_danger")

    bot.Move.XY(-15858.25, -8840.35, step_name="To End of Path")
    bot.Wait.ForMapToChange(target_map_id=BotSettings.HOM_OUTPOST_ID)

    _DisableCombat(bot)

    bot.Wait.ForMapLoad(target_map_id=BotSettings.HOM_OUTPOST_ID)
    
    # Increment success counter at runtime, not setup time
    def _increment_success():
        _increment_runs_counters(bot, "success")
        yield
    
    bot.States.AddCustomState(lambda: _increment_success(), "IncrementSuccessCounter")
    
    # Loop back to check gold and run quest again
    bot.States.JumpToStepName("[H]Check and Deposit Gold_3")

def _handle_bonus_bow(bot: Botting):
    has_bonus_bow = Routines.Checks.Inventory.IsModelInInventory(ModelID.Bonus_Nevermore_Flatbow.value)
    if has_bonus_bow:
        if BotSettings.DEBUG:   
            print(f"[DEBUG] Bonus bow found, equipping")
        yield from bot.helpers.Items._equip(ModelID.Bonus_Nevermore_Flatbow.value)
    else:
        if BotSettings.DEBUG:
            print(f"[DEBUG] Bonus bow not found in inventory or equipped")
    yield

def _handle_war_supplies(bot: Botting, value: bool):
    if BotSettings.WAR_SUPPLIES_ENABLED:
        if BotSettings.DEBUG:   
            print(f"[DEBUG] War supplies { 'enabled' if value else 'disabled' }")
        bot.Properties.ApplyNow("war_supplies", "active", value)
    yield

def _increment_runs_counters(bot: Botting, type: Literal["success", "fail"]):
    """Increment run counters based on run result"""
    BotSettings.TOTAL_RUNS += 1
    if type == "success":
        BotSettings.SUCCESSFUL_RUNS += 1
    elif type == "fail":
        BotSettings.FAILED_RUNS += 1

def _success_rate():
    if BotSettings.TOTAL_RUNS == 0:
        return "0.00%"
    return f"{BotSettings.SUCCESSFUL_RUNS / BotSettings.TOTAL_RUNS * 100:.2f}%"

def _fail_rate():
    if BotSettings.TOTAL_RUNS == 0:
        return "0.00%"
    return f"{BotSettings.FAILED_RUNS / BotSettings.TOTAL_RUNS * 100:.2f}%"

def war_supplies_obtained():
    return 5 * BotSettings.SUCCESSFUL_RUNS # 5 war supplies per run

def gold_obtained():
    return 1000 * BotSettings.SUCCESSFUL_RUNS # 1000 gold per run

def _draw_settings(bot: Botting):
    PyImGui.text("Bot Settings")

    # Gold threshold controls
    gold_threshold = BotSettings.GOLD_THRESHOLD_DEPOSIT
    gold_threshold = PyImGui.input_int("Gold deposit threshold", gold_threshold)

    # War Supplies controls
    use_war_supplies = BotSettings.WAR_SUPPLIES_ENABLED
    use_war_supplies = PyImGui.checkbox("Use War Supplies", use_war_supplies)

    # Debug controls
    debug = BotSettings.DEBUG
    debug = PyImGui.checkbox("Debug", debug)

    BotSettings.WAR_SUPPLIES_ENABLED = use_war_supplies
    BotSettings.GOLD_THRESHOLD_DEPOSIT = gold_threshold
    BotSettings.DEBUG = debug

bot.SetMainRoutine(create_bot_routine)
bot.UI.override_draw_config(lambda: _draw_settings(bot))

def main():
    try:
        projects_path = Py4GW.Console.get_projects_path()
        full_path = projects_path + "\\Bots\\War Supply\\"
        main_child_dimensions: Tuple[int, int] = (350, 275)
        
        bot.Update()
        bot.UI.draw_window(icon_path=full_path + "Keiran_art.png")

        if PyImGui.begin(bot.config.bot_name, PyImGui.WindowFlags.AlwaysAutoResize):
            if PyImGui.begin_tab_bar(bot.config.bot_name + "_tabs"):
                if PyImGui.begin_tab_item("Main"):
                    PyImGui.dummy(*main_child_dimensions)

                    PyImGui.separator()

                    ImGui.push_font("Regular", 18)
                    PyImGui.text("Statistics")
                    ImGui.pop_font()
                    
                    if PyImGui.collapsing_header("Runs"):
                        # Total Runs
                        PyImGui.LabelTextV("Total", "%s", [str(BotSettings.TOTAL_RUNS)])    	

                        # Successful Runs
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.0, 1.0, 0.0, 1.0))
                        PyImGui.LabelTextV("Successful", "%s", [f"{BotSettings.SUCCESSFUL_RUNS} ({_success_rate()})"])
                        PyImGui.pop_style_color(1)

                        # Failed Runs
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.0, 0.0, 1.0))
                        PyImGui.LabelTextV("Failed", "%s", [f"{BotSettings.FAILED_RUNS} ({_fail_rate()})"])
                        PyImGui.pop_style_color(1)

                    if PyImGui.collapsing_header("Items/Gold obtained"):
                        PyImGui.LabelTextV("Gold", "%s", [str(gold_obtained())])    	
                        PyImGui.LabelTextV("War Supplies", "%s", [str(war_supplies_obtained())])    	
                    
                PyImGui.end_tab_item()
            PyImGui.end_tab_bar()
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log(bot.config.bot_name, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()
