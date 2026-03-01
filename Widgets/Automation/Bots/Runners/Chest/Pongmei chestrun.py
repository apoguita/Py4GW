import Py4GW
from Py4GWCoreLib import (Routines, Item, Botting, ActionQueueManager, Agent, ConsoleLog, GLOBAL_CACHE, ItemArray, Bags, Player)
from Py4GWCoreLib.Builds import SF_Assassin_Hells_Precipice
from Py4GWCoreLib.Builds.BuildHelpers import BuildDangerHelper, DangerTable
from Sources.Sasemoi.bot_helpers import BotStuckHelper


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
    valuable_models = [344, 2247] # Magma Shield and Raven Staff are the only interesting loot here
    
    return True #(item_instance.model_id in valuable_models and item_instance.is_rarity_gold) 

# Globals
HP_RUNNER = "Pongmei Chestrun"
MAATU_KEEP_OUTPOST = 283
MODULE_NAME = "Pongmei Valley (Chestrun)"
MODULE_ICON = "Textures\\Module_Icons\\Chestrun - Pongmei Valley.png"


# Danger Tables
Pongmei_cripple_kd_table: DangerTable = (
    ([3768, 3774, 4096, 4076, 3787, 4248],"Pongmei KD/Cripple"),
)
Pongmei_spellcast_table: DangerTable = (
    ([3768, 3774, 4096, 4076, 3787, 4248], "Pongmei Casters"),
)

# Script states
opened_chests: set[int] = set()
should_manage_inventory = False

bot = Botting(
    HP_RUNNER,
    custom_build=SF_Assassin_Hells_Precipice(
        build_danger_helper=BuildDangerHelper(
            cripple_kd_table=Pongmei_cripple_kd_table,
            spellcast_table=Pongmei_spellcast_table
        )),
    upkeep_alcohol_target_drunk_level=1,
    upkeep_birthday_cupcake_active=True,
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
    bot.Properties.Disable("identify_kits")
    bot.Properties.Disable("salvage_kits")


# Only support assassin build for now
def AssignBuild(bot: Botting):
    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    match profession:
        case "Assassin":
            bot.OverrideBuild(SF_Assassin_Hells_Precipice())
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
    if isinstance(bot.config.build_handler, SF_Assassin_Hells_Precipice):
        build_danger_helper = bot.config.build_handler.build_danger_helper
        build_danger_helper.update_tables(cripple_kd_table=Pongmei_cripple_kd_table, spellcast_table=Pongmei_spellcast_table)
    
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
    fsm.jump_to_state_by_name("[H]Pongmei Chestrun Routine_4") 
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
        yield from Routines.Yield.Movement.FollowPath(path_points=[(6409.31, 8373.04)])
        yield from Routines.Yield.Agents.InteractWithAgentXY(6409.31, 8373.04)
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


def DetectChestAndOpen(bot: Botting, max_distance=3000):
    # Log
    coord = Player.GetXY()
    ConsoleLog(HP_RUNNER, f"Arrived at point coordinates ::: {coord}", Py4GW.Console.MessageType.Info)
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
            if isinstance(bot.config.build_handler, SF_Assassin_Hells_Precipice):
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

# Reset opened chests for next run so they don't pass over through instance load
def ResetUnopenedChests():
    global opened_chests
    opened_chests = set()

# ==================== END REGION Setup ====================


# ==================== REGION Routines ====================


# Initial travel to Maatu and setup runner build
def InitialTravelAndSetup(bot: Botting) -> None:
    bot.States.AddHeader("Travel and Setup")
    bot.Map.Travel(target_map_id=MAATU_KEEP_OUTPOST)
    bot.States.AddCustomState(lambda: EquipSkillBar(bot), "Equip SkillBar")
    bot.States.AddCustomState(lambda: SetupDangerTables(), "Setup Danger Tables for runner")


# Check if inventory management is needed and perform it
def SetupInventoryManagement(bot: Botting) -> None:
    bot.States.AddHeader("Inventory Management")
    bot.States.AddCustomState(lambda: AssessLootManagement(), "Loot management check")
    bot.States.AddCustomState(lambda: ConditionallyMoveToMerchant(), "Move to merchant for inventory check")
    bot.Wait.ForTime(1000)
    bot.States.AddCustomState(lambda: ManageInventory(bot), "Manage Inventory before run")



# Chestrun routine follows a set path and opens chests along the way
def ChestRunRoutine(bot: Botting) -> None:
    bot.States.AddHeader("Pongmei Chestrun Routine")
    bot.Party.SetHardMode(True)
    bot.Move.XYAndExitMap(-13350, 11350, target_map_id=211)
    bot.Wait.ForMapLoad(211)
    bot.Wait.ForTime(3000)
    bot.States.AddCustomState(lambda: stuck_helper.Toggle(True), "Activate Stuck Helper")
    bot.States.AddManagedCoroutine("Run Stuck Handler", lambda: RunStuckHelper())
    bot.Wait.ForTime(500)


    bot.Properties.Enable("auto_combat")
    bot.Properties.Enable("alcohol")
    
    path_points: list[tuple[float, float]] = [
        
        (-12529.30, 380.60),
        (-6576.30, 250.94),
        (-4640.75, -1109.55),
        (-1927.92, -506.08),
        (-383.40, 2419.55),
        (-942.53, 5764.20),
        (4463.03, 5611.61),
        (6986.71, 2235.84),
        (8983.32, -182.43),
        (12225.77, 703.96),
        (11954.12, 5828.85),
        (14140.11, 3045.75),
        (13403.77, -1254.65),
        (16097.21, -3239.54),
        (17725.88, 517.08),
        (19317.02, 2483.98),
        (21408.31, 4911.76)

    ]

    for i, coord in enumerate(path_points):
        x, y = coord
        bot.Move.XY(x, y, f"Moving to point {i + 1}")
        bot.States.AddCustomState(lambda: DetectChestAndOpen(bot), f"Detect and Open Chest at point {i}")
        # bot.Move.XY(x, y, f"Repositioning at point {i + 1} after chest open")


# Reset the farm loop to run Pongmei again
def ResetFarmLoop(bot: Botting):
    bot.States.AddHeader("Reset Farm Loop")
    bot.Properties.Disable("auto_combat")
    bot.States.AddCustomState(lambda: stuck_helper.Toggle(False), "Deactivate Stuck Helper")
    bot.States.RemoveManagedCoroutine("Run Stuck Handler")


    bot.States.AddCustomState(lambda: ResetUnopenedChests(), "Reset Opened Chests List")
    bot.Party.Resign()
    bot.States.AddCustomState(lambda: AssessLootManagement(), "Loot management check")
    bot.Wait.ForTime(10000)
    bot.States.AddCustomState(lambda: ConditionallyMoveToMerchant(), "Move to merchant for inventory check")
    bot.States.AddCustomState(lambda: ManageInventory(bot), "Manage management execution")
    bot.States.JumpToStepName("[H]Pongmei Chestrun Routine_4") # Jump back to travel and setup for next run


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