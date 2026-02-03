import PyImGui
from typing import Literal, Tuple
import time

from Py4GWCoreLib.Builds import KeiranThackerayEOTN
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          Map, ImGui, ActionQueueManager)


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
    
    # Material purchases
    ECTOS_BOUGHT: int = 0

    # Run timing
    CURRENT_RUN_START_TIME: float = 0.0
    TOTAL_RUN_TIME: float = 0.0
    FASTEST_RUN: float = float('inf')
    SLOWEST_RUN: float = 0.0

    # Misc
    DEBUG: bool = False


bot = Botting("Auspicious Beginnings Test",
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
        current_map = Map.GetMapID()
        should_skip_travel = current_map in [BotSettings.EOTN_OUTPOST_ID, BotSettings.HOM_OUTPOST_ID]
        if should_skip_travel:
            if BotSettings.DEBUG:   
                print(f"[DEBUG] Already in EOTN or HOM, skipping travel")
            return

        Map.Travel(BotSettings.EOTN_OUTPOST_ID)
        yield from Routines.Yield.wait(1000)
        yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID) 

    bot.States.AddCustomState(lambda: _go_to_eotn(bot), "GoToEOTN")
      
def GetBonusBow(bot: Botting):
    bot.States.AddHeader("Check for Bonus Bow")

    def _get_bonus_bow(bot: Botting):
        current_map = Map.GetMapID()
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
        current_map = Map.GetMapID()
        gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
        gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()

        if BotSettings.DEBUG:   
            print(f"[DEBUG] CheckAndDepositGold: current_map={current_map}, gold={gold_on_char}, storage={gold_in_storage}")
        
        # Travel to EOTN if character has 90k+ gold
        if gold_on_char > BotSettings.GOLD_THRESHOLD_DEPOSIT:
            # Ensure we're in EOTN outpost
            if current_map != BotSettings.EOTN_OUTPOST_ID:
                if BotSettings.DEBUG:   
                    print(f"[DEBUG] Traveling to EOTN from map {current_map}")

                Map.Travel(BotSettings.EOTN_OUTPOST_ID)
                yield from Routines.Yield.wait(1000)
                yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID)
                current_map = BotSettings.EOTN_OUTPOST_ID

            # Deposit gold only if storage hasn't reached 800k
            if gold_in_storage < 800000:
                if BotSettings.DEBUG:   
                    print(f"Depositing {gold_on_char} gold in bank")
                GLOBAL_CACHE.Inventory.DepositGold(gold_on_char)
                yield from Routines.Yield.wait(1000)
            else:
                if BotSettings.DEBUG:   
                    print(f"Storage ({gold_in_storage}) has reached 800k+, keeping gold on character for ecto purchases")
        else:
            if BotSettings.DEBUG:   
                print(f"Gold ({gold_on_char}) below threshold ({BotSettings.GOLD_THRESHOLD_DEPOSIT}), skipping travel and deposit")
        
        # After deposit check, try to buy ectos if in EOTN outpost
        current_map = Map.GetMapID()
        if current_map == BotSettings.EOTN_OUTPOST_ID:
            yield from BuyMaterials(bot)

        if BotSettings.DEBUG:   
            print(f"[DEBUG] After gold check: current_map={current_map}, HOM={BotSettings.HOM_OUTPOST_ID}")

    bot.States.AddCustomState(lambda: _check_and_deposit_gold(bot), "CheckAndDepositGold")

def ExitToHOM(bot: Botting) -> None:
    bot.States.AddHeader("Exit to HOM")

    # Ensure we're in HOM for quest preparation
    def _exit_to_hom(bot: Botting):
        current_map = Map.GetMapID()
        should_exit_to_hom = current_map != BotSettings.HOM_OUTPOST_ID
        should_travel_to_eotn = current_map != BotSettings.EOTN_OUTPOST_ID

        if should_exit_to_hom:
            if BotSettings.DEBUG:   
                print(f"[DEBUG] Not in HOM, need to go there. Currently in map {current_map}")

            if should_travel_to_eotn:
                if BotSettings.DEBUG:   
                    print(f"[DEBUG] Not in EOTN, traveling there first")
                Map.Travel(BotSettings.EOTN_OUTPOST_ID)
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

def BuyMaterials(bot: Botting):
    """Buy Glob of Ectoplasm if gold conditions are met."""
    # Check gold conditions for buying Glob of Ectoplasm
    gold_in_inventory = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
    gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
    
    if gold_in_inventory >= 90000 and gold_in_storage >= 800000:
        # Move to and speak with rare material trader
        yield from bot.Move._coro_xy_and_dialog(-2079.00, 1046.00, dialog_id=0x00000001)
        
        # Buy Glob of Ectoplasm until inventory gold drops below 2k
        for _ in range(100):  # Max 100 Globs of Ectoplasm
            current_gold = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
            if current_gold < 2000:  # Stop buying if gold is below 2k
                if BotSettings.DEBUG:
                    print(f"[DEBUG] Stopping ecto purchases - gold ({current_gold}) below 2k")
                break
            yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Glob_Of_Ectoplasm.value)
            BotSettings.ECTOS_BOUGHT += 1  # Increment ecto counter
            yield from Routines.Yield.wait(100)  # Small delay between purchases

def EnterQuest(bot: Botting) -> None:
    bot.States.AddHeader("Enter Quest")
    bot.Wait.ForTime(3000)
    bot.Move.XY(-6626.18, 6553.94)
    bot.Move.XYAndDialog(-6662.00, 6584.00, 0x63F) #enter quest with pool
    bot.Wait.ForMapToChange(target_map_id=BotSettings.AUSPICIOUS_BEGINNINGS_MAP_ID)
    
def RunQuest(bot: Botting) -> None:    
    bot.States.AddHeader("Run Quest")
    
    def _start_run_timer():
        BotSettings.CURRENT_RUN_START_TIME = time.time()
        if BotSettings.DEBUG:
            print(f"[DEBUG] Started run timer at {BotSettings.CURRENT_RUN_START_TIME}")
        yield
    
    bot.States.AddCustomState(lambda: _start_run_timer(), "StartRunTimer")
    _EnableCombat(bot)
    bot.Move.XY(11864.74, -4899.19)
    bot.States.AddCustomState(lambda: _handle_bonus_bow(bot), "HandleBonusBow")
    bot.Wait.UntilOnCombat()
    bot.Move.XY(10165.07, -6181.43, step_name="First Spawn")
    bot.Move.XY(9449.19, -7082.19)
    bot.Move.XY(8047.82, -8626.89)
    bot.Move.XY(4694.51, -7458.37)
    bot.Move.XY(4356.91, -8154.74)
    bot.Move.XY(3440.59, -10756.03)
    bot.Move.XY(-3959.19, -12118.47)
    bot.Move.XY(-5393.59, -12199.84)
    bot.Move.XY(-6781.85, -12126.29)
    bot.Move.XY(-6837.46, -12047.07)
    bot.Move.XY(-6340.35, -10266.07)
    bot.Move.XY(-10813.61, -7816.87)
    bot.Move.XY(-15495.75, -8872.74)
    bot.Wait.ForMapToChange(target_map_id=BotSettings.HOM_OUTPOST_ID)
    _DisableCombat(bot)

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
    # Calculate run time only for successful runs
    if BotSettings.CURRENT_RUN_START_TIME > 0:
        run_time = time.time() - BotSettings.CURRENT_RUN_START_TIME
        
        if type == "success":
            BotSettings.TOTAL_RUN_TIME += run_time
            
            if run_time < BotSettings.FASTEST_RUN:
                BotSettings.FASTEST_RUN = run_time
            if run_time > BotSettings.SLOWEST_RUN:
                BotSettings.SLOWEST_RUN = run_time
        
        if BotSettings.DEBUG:
            print(f"[DEBUG] Run completed in {run_time:.2f}s (type: {type})")
        
        BotSettings.CURRENT_RUN_START_TIME = 0.0
    
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

def _format_time(seconds: float) -> str:
    """Format seconds into MM:SS format"""
    if seconds == float('inf') or seconds == 0.0:
        return "--:--"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def _average_run_time():
    if BotSettings.SUCCESSFUL_RUNS == 0:
        return "--:--"
    avg_time = BotSettings.TOTAL_RUN_TIME / BotSettings.SUCCESSFUL_RUNS
    return _format_time(avg_time)

def _fastest_run_time():
    return _format_time(BotSettings.FASTEST_RUN)

def _slowest_run_time():
    return _format_time(BotSettings.SLOWEST_RUN)

def _current_run_time():
    if BotSettings.CURRENT_RUN_START_TIME > 0:
        elapsed = time.time() - BotSettings.CURRENT_RUN_START_TIME
        return _format_time(elapsed)
    return "--:--"

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
        full_path = projects_path + "\\Sources\\ApoSource\\textures\\"
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
                        PyImGui.LabelTextV("Glob of Ectoplasm", "%s", [str(BotSettings.ECTOS_BOUGHT)])    	
                    
                    if PyImGui.collapsing_header("Run Times"):
                        # Current run timer with spinning indicator
                        if BotSettings.CURRENT_RUN_START_TIME > 0:
                            spinner_chars = ['|', '/', '-', '\\']
                            spinner_idx = int(time.time() * 4) % len(spinner_chars)
                            current_time_str = f"{spinner_chars[spinner_idx]} {_current_run_time()}"
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.4, 0.8, 1.0, 1.0))
                            PyImGui.LabelTextV("Current Run", "%s", [current_time_str])
                            PyImGui.pop_style_color(1)
                        
                        PyImGui.LabelTextV("Average", "%s", [_average_run_time()])
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.0, 1.0, 0.0, 1.0))
                        PyImGui.LabelTextV("Fastest", "%s", [_fastest_run_time()])
                        PyImGui.pop_style_color(1)
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.65, 0.0, 1.0))
                        PyImGui.LabelTextV("Slowest", "%s", [_slowest_run_time()])
                        PyImGui.pop_style_color(1)
                    
                PyImGui.end_tab_item()
            PyImGui.end_tab_bar()
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log(bot.config.bot_name, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()
