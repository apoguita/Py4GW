import PyImGui
from typing import Literal, Tuple
import time

from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib.Builds.Any.KeiranThackerayEOTN import KeiranThackerayEOTN
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          Map, ImGui, ActionQueueManager, Agent, Player, AgentArray, Pathing,
                          TitleID, TITLE_TIERS)
from Py4GWCoreLib import *

MODULE_NAME = "Auspicious Beginnings (War Supplies)" 
MODULE_ICON = "Textures\\Module_Icons\\Keiran Farm.png"

class BotSettings:
    # Map/Outpost IDs
    EOTN_OUTPOST_ID = 642
    HOM_OUTPOST_ID = 646
    AUSPICIOUS_BEGINNINGS_MAP_ID = 849

    # Custom Bow ID - If this is left 0 you will automatically craft a suitable bow.
    CUSTOM_BOW_ID = 0 # Change this is you already have a custom bow made for AB.
    
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

    # Vanguard title cache (populated at start and after each successful run)
    VANGUARD_SCANNED: bool = False
    VANGUARD_RANK: int = 0
    VANGUARD_TIER_NAME: str = "–"
    VANGUARD_POINTS: int = 0
    VANGUARD_NEXT_REQUIRED: int | None = None

    # Run timing
    CURRENT_RUN_START_TIME: float = 0.0
    TOTAL_RUN_TIME: float = 0.0
    FASTEST_RUN: float = float('inf')
    SLOWEST_RUN: float = 0.0

    # Misc
    DEBUG: bool = False


bot = Botting("Auspicious Beginnings")
bot.config.reset_pause_on_danger_fn(aggro_area=Range.Longbow)
navmesh = None
     
def create_bot_routine(bot: Botting) -> None:
    widget_handler = get_widget_handler()
    if not widget_handler.is_widget_enabled("Return to outpost on defeat"):
        widget_handler.enable_widget("Return to outpost on defeat")
        
    InitializeBot(bot)
    def _initial_vanguard_scan():
        _update_vanguard_cache()
        yield
    bot.States.AddCustomState(lambda: _initial_vanguard_scan(), "ScanVanguardRank")
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
    yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.HOM_OUTPOST_ID, timeout=30000)
    bot.Properties.ApplyNow("halt_on_death","active", False)
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

def _build_keiran(bot: Botting) -> KeiranThackerayEOTN:
    build = KeiranThackerayEOTN(fsm=bot.config.FSM, bot=bot, debug_fn=lambda: BotSettings.DEBUG)
    build.set_fsm(bot.config.FSM)
    build.set_bot(bot)
    build.set_debug_fn(lambda: BotSettings.DEBUG)
    return build

def _EnableCombat(bot: Botting):
    bot.OverrideBuild(_build_keiran(bot))
    bot.Templates.Aggressive(enable_imp=False)
    bot.Properties.ApplyNow("pause_on_danger", "active", True)
    bot.Properties.ApplyNow("halt_on_death", "active", False)
    bot.Properties.ApplyNow("movement_timeout", "value", -1)
    bot.Properties.ApplyNow("auto_combat", "active", True)
    bot.Properties.ApplyNow("hero_ai", "active", False)
    bot.Properties.ApplyNow("auto_loot", "active", True)
    bot.Properties.ApplyNow("imp", "active", False)
    yield
 
def _DisableCombat(bot: Botting) -> None:
    bot.Templates.Pacifist()

def InitializeBot(bot: Botting) -> None:
    condition = lambda: on_death(bot)
    bot.Events.OnDeathCallback(condition)

def _load_navmesh_object(bot) -> None:
    """Try to get the NavMesh for validation. If not cached yet, schedule async load."""
    try:
        nav = AutoPathing().get_navmesh()
        if nav is not None:
            navmesh = nav
            return
    except Exception as e:
        Py4GW.Console.Log("Navmesh", f"Navmesh load failed: {e}", Py4GW.Console.MessageType.Warning)
    def _load_coro():
        yield from AutoPathing().load_pathing_maps()
        nav = AutoPathing().get_navmesh()
        if nav is not None:
            navmesh = nav
    GLOBAL_CACHE.Coroutines.append(_load_coro())

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
        yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID, timeout=15000)
        bot.Party.SetHardMode(False)
        
    bot.States.AddCustomState(lambda: _go_to_eotn(bot), "GoToEOTN")
      
def GetBonusBow(bot: Botting):
    bot.States.AddHeader("Check for Bonus Bow")

    if BotSettings.CUSTOM_BOW_ID != 0 or Routines.Checks.Inventory.IsModelInInventoryOrEquipped(11723):
        return
    bot.Map.Travel(194)
    bot.Move.XY(1592.00, -796.00)  # Move to material merchant area
    bot.States.AddCustomState(withdraw_gold, "Withdraw 20k Gold")
    bot.Move.XYAndInteractNPC(1592.00, -796.00)  # Common material merchant
    bot.States.AddCustomState(BuyLongbowMaterials, "Buy Weapoon Materials")
    bot.Wait.ForTime(1500)
    bot.Move.XYAndInteractNPC(-1387.00, -3910.00)  # Weapon crafter in Shing Jea Monastery
    bot.Wait.ForTime(1000)
    exec_fn = lambda: DoCraftLongbow(bot)
    bot.States.AddCustomState(exec_fn, "Craft Weapons")

_SHORTBOW_DATA = {
    "buy":    [(ModelID.Wood_Plank.value, 10), (ModelID.Plant_Fiber.value, 5)],
    "pieces": [(11730, [ModelID.Wood_Plank.value, ModelID.Plant_Fiber.value], [100, 50])],  # Longbow, 10 wood planks
}

_LONGBOW_DATA = {
    "buy":    [(ModelID.Wood_Plank.value, 10), (ModelID.Feather.value, 5)],
    "pieces": [(11723, [ModelID.Wood_Plank.value, ModelID.Feather.value], [100, 50])],  # Longbow, 10 wood planks
}

def withdraw_gold(target_gold=20000, deposit_all=True):
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

    if gold_on_char > target_gold and deposit_all:
        to_deposit = gold_on_char - target_gold
        GLOBAL_CACHE.Inventory.DepositGold(to_deposit)
        yield from Routines.Yield.wait(250)

    if gold_on_char < target_gold:
        to_withdraw = target_gold - gold_on_char
        GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
        yield from Routines.Yield.wait(250)

def BuyShortbowMaterials():
    for mat, count in _SHORTBOW_DATA["buy"]:
        for _ in range(count):
            yield from Routines.Yield.Merchant.BuyMaterial(mat)

def DoCraftShortbow(bot: Botting):
    for weapon_id, mats, qtys in _SHORTBOW_DATA["pieces"]:
        result = yield from Routines.Yield.Items.CraftItem(weapon_id, 5000, mats, qtys)
        if not result:
            ConsoleLog("DoCraftWeapon", f"Failed to craft weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
        result = yield from Routines.Yield.Items.EquipItem(weapon_id)
        if not result:
            ConsoleLog("DoCraftWeapon", f"Failed to equip weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
    return True

def BuyLongbowMaterials():
    for mat, count in _LONGBOW_DATA["buy"]:
        for _ in range(count):
            yield from Routines.Yield.Merchant.BuyMaterial(mat)

def DoCraftLongbow(bot: Botting):
    for weapon_id, mats, qtys in _LONGBOW_DATA["pieces"]:
        result = yield from Routines.Yield.Items.CraftItem(weapon_id, 5000, mats, qtys)
        if not result:
            ConsoleLog("DoCraftWeapon", f"Failed to craft weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
        result = yield from Routines.Yield.Items.EquipItem(weapon_id)
        if not result:
            ConsoleLog("DoCraftWeapon", f"Failed to equip weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
    return True

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
                yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID, timeout=15000)
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
                yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID, timeout=15000)

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
    #bot.Wait.ForMapLoad(target_map_id=BotSettings.HOM_OUTPOST_ID)

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
        #bot.Wait.ForMapLoad(target_map_id=642)
        yield from Routines.Yield.wait(500)
        GLOBAL_CACHE.Inventory.DepositGold(gold_on_char)
        yield from Routines.Yield.wait(500)
        bot.Move.XYAndExitMap(-4873.00, 5284.00, target_map_id=646)
        #bot.Wait.ForMapLoad(target_map_id=646)
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
            if current_gold < 20000:  # Stop buying if gold is below 2k
                if BotSettings.DEBUG:
                    print(f"[DEBUG] Stopping ecto purchases - gold ({current_gold}) below 2k")
                break
            yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Glob_Of_Ectoplasm.value)
            BotSettings.ECTOS_BOUGHT += 1  # Increment ecto counter
            yield from Routines.Yield.wait(500)  # Small delay between purchases

def EnterQuest(bot: Botting) -> None:
    bot.States.AddHeader("Enter Quest")
    bot.Move.XYAndDialog(-6662.00, 6584.00, 0x63F) #enter quest with pool
    bot.Wait.ForMapLoad(target_map_id=BotSettings.AUSPICIOUS_BEGINNINGS_MAP_ID)
    
def RunQuest(bot: Botting) -> None:
    bot.States.AddHeader("Run Quest")

    def _start_run_timer():
        BotSettings.CURRENT_RUN_START_TIME = time.time()
        if BotSettings.DEBUG:
            print(f"[DEBUG] Started run timer at {BotSettings.CURRENT_RUN_START_TIME}")
        yield
    bot.States.AddCustomState(lambda: _start_run_timer(), "StartRunTimer")
    exec_fn = lambda: _load_navmesh_object(bot)
    bot.States.AddCustomState(exec_fn, "Navmesh Init")
    
    
    bot.States.AddCustomState(lambda: _EnableCombat(bot), "EnableCombat")
    bot.Move.XY(11864.74, -4899.19)
    
    bot.States.AddCustomState(lambda: _handle_bonus_bow(bot), "HandleBonusBow")
    bot.States.AddCustomState(lambda: _handle_war_supplies(bot, True), "EnableWarSupplies")
    
    bot.Wait.UntilOnCombat(Range.Spirit)
    
    bot.States.AddCustomState(lambda: _handle_war_supplies(bot, False), "DisableWarSupplies")

    bot.Move.XY(10165.07, -6181.43, step_name="First Spawn")
    bot.Move.XY(8270,-9010)
    bot.Move.XY(4245,-7412)
    bot.Move.XY(2025,-10726)
    bot.Move.XY(-1822,-11230)
    bot.Move.XY(-2292, -9034)
    bot.Move.XY(-4190,-10460)
    bot.Move.XY(-5640,-10371)
    bot.Move.XY(-8748,-8329)
    bot.Move.XY(-12122,-7530)
    bot.Move.XY(-15170,-8951)

    bot.Wait.ForMapLoad(target_map_id=BotSettings.HOM_OUTPOST_ID)
    
    # Increment success counter at runtime, not setup time
    def _increment_success():
        _increment_runs_counters(bot, "success")
        _update_vanguard_cache()
        yield
    
    bot.States.AddCustomState(lambda: _increment_success(), "IncrementSuccessCounter")
    
    # Loop back to check gold and run quest again
    bot.States.JumpToStepName("[H]Check and Deposit Gold_3")

def _handle_bonus_bow(bot: Botting):
    bonus_bow_id = 11723

    if BotSettings.CUSTOM_BOW_ID != 0:
        bonus_bow_id = BotSettings.CUSTOM_BOW_ID
    has_bonus_bow = Routines.Checks.Inventory.IsModelInInventory(bonus_bow_id)
    if has_bonus_bow:
        if BotSettings.DEBUG:   
            print(f"[DEBUG] Bonus bow found, equipping")
        yield from bot.helpers.Items._equip(bonus_bow_id)
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

def _get_vanguard_rank_info():
    """Returns (rank, tier_name, current_points, next_required) for the Ebon Vanguard title.
    next_required is None if the title is maxed (rank 10)."""
    tiers = TITLE_TIERS.get(TitleID.Ebon_Vanguard, [])
    title = Player.GetTitle(TitleID.Ebon_Vanguard)
    current_points = title.current_points if title is not None else 0

    current_rank = 0
    tier_name = "Unranked"
    for t in tiers:
        if current_points >= t.required:
            current_rank = t.tier
            tier_name = t.name
        else:
            break

    if current_rank >= len(tiers):
        return current_rank, tier_name, current_points, None  # Maxed

    next_required = tiers[current_rank].required
    return current_rank, tier_name, current_points, next_required


def _update_vanguard_cache():
    rank, tier_name, pts, pts_next = _get_vanguard_rank_info()
    BotSettings.VANGUARD_RANK = rank
    BotSettings.VANGUARD_TIER_NAME = tier_name
    BotSettings.VANGUARD_POINTS = pts
    BotSettings.VANGUARD_NEXT_REQUIRED = pts_next
    BotSettings.VANGUARD_SCANNED = True


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
        window_ready = bot.UI.draw_window(icon_path=full_path + "Keiran_art.png")
        if not window_ready:
            return

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

                    if PyImGui.collapsing_header("Items/Gold obtained"):
                        PyImGui.LabelTextV("Gold", "%s", [str(gold_obtained())])
                        PyImGui.LabelTextV("War Supplies", "%s", [str(war_supplies_obtained())])
                        PyImGui.LabelTextV("Glob of Ectoplasm", "%s", [str(BotSettings.ECTOS_BOUGHT)])

                    if PyImGui.collapsing_header("Vanguard Rank"):
                        if not BotSettings.VANGUARD_SCANNED:
                            PyImGui.text("Not scanned yet...")
                        else:
                            rank = BotSettings.VANGUARD_RANK
                            tier_name = BotSettings.VANGUARD_TIER_NAME
                            pts = BotSettings.VANGUARD_POINTS
                            pts_next = BotSettings.VANGUARD_NEXT_REQUIRED
                            if rank >= 10:
                                PyImGui.LabelTextV("Rank", "%s", [f"10 - {tier_name}"])
                                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.84, 0.0, 1.0))
                                PyImGui.LabelTextV("Status", "%s", ["Title Maxed!"])
                                PyImGui.pop_style_color(1)
                            else:
                                rank_label = f"{rank} - {tier_name}" if rank > 0 else "Unranked"
                                PyImGui.LabelTextV("Rank", "%s", [rank_label])
                                if pts_next is not None:
                                    PyImGui.LabelTextV("Points", "%s", [f"{pts:,} / {pts_next:,}"])
                                    PyImGui.LabelTextV("Needed", "%s", [f"{pts_next - pts:,} to next rank"])
                PyImGui.end_tab_item()
            PyImGui.end_tab_bar()
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log(bot.config.bot_name, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()
