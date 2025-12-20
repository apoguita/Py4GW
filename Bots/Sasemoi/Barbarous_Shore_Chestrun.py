import Py4GW
from Py4GWCoreLib import (Routines, Item, Botting, ActionQueueManager, ConsoleLog, GLOBAL_CACHE, ItemArray, Bags)
from Py4GWCoreLib.Builds import SF_Assassin_Barbarous
from Py4GWCoreLib.Builds.BuildHelpers import BuildDangerHelper, DangerTable
from Bots.Sasemoi.bot_helpers import BotStuckHelper


def get_unidentified_items(rarities: list[str], slot_blacklist: list[tuple[int,int]]) -> list[int]:
    ''' Returns a list of all unidentified item IDs in the player's inventory '''
    unidentified_items = []

    # Loop over all bags
    for bag_id in range(Bags.Backpack, Bags.Bag2+1):
        bag_to_check = ItemArray.CreateBagList(bag_id)
        item_array = ItemArray.GetItemArray(bag_to_check) # Get all items in the baglist

        # Loop over items
        for item_id in item_array:
            item_instance = Item.item_instance(item_id)
            slot = item_instance.slot
            if (bag_id, slot) in slot_blacklist:
                continue
            if item_instance.rarity.name not in rarities:
                continue
            if not item_instance.is_identified:
                unidentified_items.append(item_id)
    return unidentified_items

def filter_valuable_loot(item_id: int) -> bool:
    desired_types = [12, 24, 27] # Offhand, Shield, Sword
    item_instance = Item.item_instance(item_id)
    item_modifiers = item_instance.modifiers
    item_req = 13 # Default high req to skip uninteresting items

    # Check Q9 max stats
    for mod in item_modifiers:
        # Dont waste time on uninteresting mods
        # [requirement, shield armor, sword damage, offhand energy]
        if mod.GetIdentifier() not in [10136, 42936, 42920, 26568]:
            continue

        # Store item requirement
        if mod.GetIdentifier() == 10136:
            item_req = mod.GetArg2() # Item requirement value

            # Low req found, continue checking other mods
            if item_req <= 9:
                continue
            # High req found, skip entire item
            else:
                return False
        
        
        # Handle Shield
        # 42936 = Shield armor mod identifier
        if item_instance.item_type.ToInt() == 24 and mod.GetIdentifier() == 42936:
            has_ideal_q5_stats = mod.GetArg1() == 12 or mod.GetArg1() == 13 # Ideal shield armor for q5
            has_max_stats = mod.GetArg1() == 16 # Max armor

            # Handle Q5 Shields
            if item_req == 5 and has_ideal_q5_stats:
                return True

            # Handle uninteresting Shields
            if not has_max_stats :
                return False

        # Handle Sword -- Only Q8 and Q9 Swords with max stats are interesting
        # 42920 = Sword damage mod identifier
        if item_instance.item_type.ToInt() == 27 and mod.GetIdentifier() == 42920:
            has_max_stats = mod.GetArg2() == 15 and mod.GetArg1() == 22 # Max damage mod
            return has_max_stats
        

        # Handle Offhand -- Only Q8 and Q9 Offhands with max stats are interesting
        # 26568 = Offhand energy mod identifier
        if item_instance.item_type.ToInt() == 12 and mod.GetIdentifier() == 26568:
            has_max_stats = mod.GetArg1() == 12 # Max Energy mod
            return has_max_stats and item_req <= 9 # Only interested in Q8 or lower
        
        # Whalekin Wand
        if item_instance.model_id == 1453:
            q8_max_stats = mod.GetArg2() == 11 and mod.GetArg1() >= 21 # Max damage mod
            has_max_stats = mod.GetArg2() == 11 and mod.GetArg1() == 22 # Max damage mod
            return has_max_stats or (q8_max_stats and item_req == 8)
        
    return False

# Globals
BARBAROUS_SHORE = 375
CAMP_HOJANU = 376
BARB_SHORE_RUNNER = "Barbarous Shore Chestrun"

# Danger Tables
barbarous_cripple_kd_table: DangerTable = (
    ([5048 + 51, 5059 + 51, 5043 + 51, 5051 + 51, 5050 + 51, 5029 + 51, 5032 + 51, 5030 + 51], "Corsair"),
    ([4904 + 51], "Mesa")
)
barbarous_spellcast_table: DangerTable = () # Not using spellcaster detection because the script permanently keeps Shadow Form up

# Script states
opened_chests: set[int] = set()
should_manage_inventory = False

bot = Botting(
    BARB_SHORE_RUNNER,
    custom_build=SF_Assassin_Barbarous(
        build_danger_helper=BuildDangerHelper(
            cripple_kd_table=barbarous_cripple_kd_table,
            spellcast_table=barbarous_spellcast_table
        )),
    upkeep_alcohol_target_drunk_level=1,
    upkeep_auto_combat_active=False,
    config_log_actions=False,
)

# Would like to move this to Botting
stuck_helper = BotStuckHelper(
    config={
        "log_enabled": False,
        "movement_timeout_handler": lambda: HandleStuck()
    }
)


# ==================== REGION Setup ====================

def create_bot_routine(bot: Botting) -> None:    
    InitializeBot(bot)
    InitialTravelAndSetup(bot)
    SetupInventoryManagement(bot)
    SetupResign(bot)
    ChestRunRoutine(bot)
    ResetFarmLoop(bot)


def InitializeBot(bot: Botting) -> None:
    condition = lambda: on_death(bot)
    bot.Events.OnDeathCallback(condition)

    bot.States.AddHeader("Initialize Bot")
    bot.Properties.Disable("alcohol")
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Disable("auto_loot")
    bot.Properties.Disable("hero_ai")
    bot.Properties.Disable("auto_combat")
    bot.Properties.Disable("pause_on_danger")
    bot.Properties.Enable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=-1)
    bot.Properties.Disable("birthday_cupcake")
    bot.Properties.Disable("identify_kits")
    bot.Properties.Disable("salvage_kits")


# Only support assassin build for now
def AssignBuild(bot: Botting):
    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    match profession:
        case "Assassin":
            bot.OverrideBuild(SF_Assassin_Barbarous())
        case _:
            ConsoleLog("Unsupported Profession", f"The profession '{profession}' is not supported by this bot.", Py4GW.Console.MessageType.Error, True)
            bot.Stop()
            return
    yield
    

def EquipSkillBar(bot: Botting):
    yield from AssignBuild(bot)
    yield from bot.config.build_handler.LoadSkillBar()


# Danger tables define dangerous enemies for cripple/kd and spellcasting
def SetupDangerTables():
    if isinstance(bot.config.build_handler, SF_Assassin_Barbarous):
        build_danger_helper = bot.config.build_handler.build_danger_helper
        build_danger_helper.update_tables(cripple_kd_table=barbarous_cripple_kd_table)
    
    yield


# On Death Callback Routine
def _on_death(bot: Botting):
    yield from Routines.Yield.wait(1000)
    yield from Routines.Yield.Player.Resign()
    yield from Routines.Yield.wait(1000)
    yield from AssessLootManagement()
    yield from Routines.Yield.wait(10000)  # Wait for resign to complete
    yield from ConditionallyMoveToMerchant()
    yield from ManageInventory(bot)

    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Barbarous Shore Running_5") 
    fsm.resume()                           
    yield  


def on_death(bot: Botting):
    ConsoleLog("Death detected", "Player Died - Run Failed, Restarting...", Py4GW.Console.MessageType.Notice)

    # Reset Action Queues and FSM
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))

def HandleStuck():
    yield from Routines.Yield.Player.Resign()
    yield from Routines.Yield.wait(500)

def RunStuckHelper():
    yield from stuck_helper.Run()

def AssessLootManagement():
    global should_manage_inventory

    free_slots = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
    ConsoleLog("Inventory Check", f"Free Inventory Slots: {free_slots}", Py4GW.Console.MessageType.Info)

    should_manage_inventory = free_slots < 5
    if should_manage_inventory:
        ConsoleLog("Inventory Check", f"Free Inventory Slots: {free_slots} - Managing Inventory before next run", Py4GW.Console.MessageType.Info)

    yield from Routines.Yield.wait(1000)


def ConditionallyMoveToMerchant():
    global should_manage_inventory

    if should_manage_inventory:
        # bot.Move.XYAndInteractNPC(-17174, 19180, "Interact with Merchant Kahdeh")
        yield from Routines.Yield.Movement.FollowPath(path_points=[(-17174, 19180)])
        yield from Routines.Yield.Agents.InteractWithAgentXY(-17174, 19180)
    else:
        yield


def ManageInventory(bot: Botting):
    global should_manage_inventory

    # Handle inventory management only if flagged
    if should_manage_inventory:
        # Restock on ID kits
        desired_kits = 2
        id_kit_count = GLOBAL_CACHE.Inventory.GetModelCount(5899)
        
        if desired_kits - id_kit_count > 0:
            yield from Routines.Yield.Merchant.BuyIDKits(desired_kits - id_kit_count)

        # ID All
        rarities = ["Purple", "Gold"]
        all_items = get_unidentified_items(rarities=rarities, slot_blacklist=[])

        # Log all unidentified items length
        ConsoleLog("Item Info Test", f"Unidentified Items Count: {len(all_items)}", Py4GW.Console.MessageType.Info)

        # Filter valuable loot
        valuable_loot = [item_id for item_id in all_items if filter_valuable_loot(item_id)]

        # Log valuable loot length
        ConsoleLog("Item Info Test", f"Valuable Unidentified Items Count: {len(valuable_loot)}", Py4GW.Console.MessageType.Info)

        # Identify Items
        yield from Routines.Yield.Items.IdentifyItems(all_items)
        yield from Routines.Yield.wait(500)

        # Deposit valuable loot
        for item_id in valuable_loot:
            GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
            yield from Routines.Yield.wait(250)

        # Sell remaining items
        remaining_items = [item_id for item_id in all_items if item_id not in valuable_loot]
        yield from Routines.Yield.Merchant.SellItems(remaining_items)
        
        # End inventory management
        should_manage_inventory = False
        yield from Routines.Yield.wait(500)

    # Else do nothing
    else:
        yield


def DetectChestAndOpen(bot: Botting, max_distance=4000):
    # Log
    coord = GLOBAL_CACHE.Player.GetXY()
    ConsoleLog(BARB_SHORE_RUNNER, f"Arrived at point coordinates ::: {coord}", Py4GW.Console.MessageType.Info)
    # Checker for inventory
    nearby_chest_id = Routines.Agents.GetNearestChest(max_distance)

    # No chest found
    if nearby_chest_id == 0 or nearby_chest_id in opened_chests:
        ConsoleLog(bot.bot_name, f"No usable chest found", Py4GW.Console.MessageType.Info)

    # Handle chest found
    else:
        ConsoleLog(bot.bot_name, f"Located nearby chest ::: {nearby_chest_id}", Py4GW.Console.MessageType.Info)

        # Update build handler to signal looting state
        def set_looting_signal(is_looting: bool):
            if isinstance(bot.config.build_handler, SF_Assassin_Barbarous):
                bot.config.build_handler.SetLootingSignal(is_looting)

        # Prevent casting to ensure item gets picked up,
        yield from Routines.Yield.Agents.InteractWithNearestChest(
            max_distance,
            before_interact_fn=lambda: set_looting_signal(True),
            after_interact_fn=lambda: set_looting_signal(False)
        )

        opened_chests.add(nearby_chest_id)
        bot.Wait.ForTime(200)

    yield

# ==================== END REGION Setup ====================


# ==================== REGION Routines ====================


# Initial travel to Barbarous Shore and setup runner build
def InitialTravelAndSetup(bot: Botting) -> None:
    bot.States.AddHeader("Travel and Setup")
    bot.Map.Travel(CAMP_HOJANU)
    bot.States.AddCustomState(lambda: EquipSkillBar(bot), "Equip SkillBar")
    bot.States.AddCustomState(lambda: SetupDangerTables(), "Setup Danger Tables for Barbarous Shore")


def SetupInventoryManagement(bot: Botting) -> None:
    bot.States.AddHeader("Setup Inventory Management")
    bot.States.AddCustomState(lambda: AssessLootManagement(), "Loot management check")
    bot.States.AddCustomState(lambda: ConditionallyMoveToMerchant(), "Move to merchant for inventory check")
    bot.Wait.ForTime(1000)
    bot.States.AddCustomState(lambda: ManageInventory(bot), "Manage Inventory before run")


# Setup to spawn close to portal on resign
def SetupResign(bot: Botting):
    bot.States.AddHeader("Setup Resign")
    bot.Move.XYAndExitMap(-12636, 16906, target_map_id=BARBAROUS_SHORE) # target_map_name="Barbarous Shore"
    bot.Wait.ForTime(350)
    bot.Move.XYAndExitMap(-14707, 18571, target_map_id=CAMP_HOJANU) # target_map_name="Camp Hojanu"


# Chestrun routine follows a set path and opens chests along the way
def ChestRunRoutine(bot: Botting) -> None:
    bot.States.AddHeader("Barbarous Shore Running")
    bot.Move.XYAndExitMap(-12636, 16906, target_map_id=BARBAROUS_SHORE) # target_map_name="Barbarous Shore"
    bot.States.AddCustomState(lambda: stuck_helper.Toggle(True), "Activate Stuck Helper")
    bot.States.AddManagedCoroutine("Run Stuck Handler", lambda: RunStuckHelper())
    bot.Properties.Enable("auto_combat")
    bot.Properties.Enable("alcohol")
    
    path_points: list[tuple[float, float]] = [
        # (-7798, 15007),
        # (-7101, 11558),
        (-12675, 10190),
        (-14616, 8558),
        (-15474, 4744),
        (-16036, 3647),
        (-9489, 1759),
        (-11687, -5170),
        (-14329, -11996),
        (-16625, -14953),
        (-16042, -15539),
        (-7940, -11834),
        (-6941, -7614),
        (-6941, -7614),
        (-5765, -3661),
        (-3917, -3608),
        (-1273, -4529),
        (1016, -2442),

        # Exit cove up north
        (-511, 201),
        
        (1347, 581), # Corsair bay
        (826, 888),

        # Dunno what this is but it's on the way
        (3540, -6390),
        
        # Before big plains
        (8115, -2483),

        # Traverse plains
        # (10524, -3770),
        (12569, -4510),
        (14580, -2447),
        (15119, -648),
        (13607, 994),

        # Last corridor
        (16471, 3187),
        # (14646, 4945),
        # (16882, 1506),


        # Big plains?
        # (5980, -7937),
        # (9848, -4610),
        # (12569, -4510),
        # (16223, 1906),


        # (11659, 9010),
        # (5896, 11982),
        # (1361, 9582),
        # (-6506, 12177),
    ]

    for i, coord in enumerate(path_points):
        x, y = coord
        bot.Move.XY(x, y, f"Moving to point {i + 1}")
        bot.States.AddCustomState(lambda: DetectChestAndOpen(bot), f"Detect and Open Chest at point {i}")
        # bot.Move.XY(x, y, f"Repositioning at point {i + 1} after chest open")


# Reset the farm loop to run Barbarous Shore again
def ResetFarmLoop(bot: Botting):
    bot.States.AddHeader("Reset Farm Loop")
    bot.Properties.Disable("auto_combat")
    bot.States.AddCustomState(lambda: stuck_helper.Toggle(False), "Deactivate Stuck Helper")
    bot.States.RemoveManagedCoroutine("Run Stuck Handler")
    bot.Party.Resign()
    bot.States.AddCustomState(lambda: AssessLootManagement(), "Loot management check")
    bot.Wait.ForTime(10000)
    bot.States.AddCustomState(lambda: ConditionallyMoveToMerchant(), "Move to merchant for inventory check")
    bot.States.AddCustomState(lambda: ManageInventory(bot), "Manage management execution")
    bot.States.JumpToStepName("[H]Barbarous Shore Running_5")


# ==================== END REGION Routines ====================




# ==================== REGION Main ====================

bot.SetMainRoutine(create_bot_routine)
base_path = Py4GW.Console.get_projects_path()


def configure():
    global bot
    bot.UI.draw_configure_window()

def main():
    bot.Update()
    projects_path = Py4GW.Console.get_projects_path()
    widgets_path = projects_path + "\\Widgets\\Config\\textures\\"
    bot.UI.draw_window(icon_path=widgets_path + "YAVB 2.0 mascot.png")

if __name__ == "__main__":
    main()

# ==================== END REGION Main ====================