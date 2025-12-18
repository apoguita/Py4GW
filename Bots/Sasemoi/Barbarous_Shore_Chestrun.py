import Py4GW
from Py4GWCoreLib import (Routines, Item, Botting, ActionQueueManager, ConsoleLog, GLOBAL_CACHE)
from Py4GWCoreLib.Builds import SF_Assassin_Barbarous
from Py4GWCoreLib.Builds.BuildHelpers import BuildDangerHelper, DangerTable

# Globals
BARBAROUS_SHORE = 375
CAMP_HOJANU = 376
BARB_SHORE_RUNNER = "Barbarous Shore Chestrun"

# Danger Tables
barbarous_cripple_kd_table: DangerTable = (([5048, 5059, 5043, 5051, 5050, 5029, 5032, 5030], "Corsair"),)
# barbarous_cripple_kd_model_table: DangerTable = (([5379, 26, 5395, 5362, 221, 221, 5398], "Corsair"),)
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
    upkeep_alcohol_active=True,
    upkeep_alcohol_target_drunk_level=1,
    upkeep_auto_combat_active=True,
    config_log_actions=False,
)


# ==================== REGION Setup ====================

def TestGetItemInfo():
    item_ids = Routines.Items.GetUnidentifiedItems(rarities=["Gold"], slot_blacklist=[])
    inspected_item_id = item_ids[0]

    item_name = Item.GetName(inspected_item_id)
    item_info = Item.GetItemType(inspected_item_id)
    ConsoleLog("Item Info Test", f"Item ID: {inspected_item_id}, Item Name: {item_name}, Item Type: {item_info}", Py4GW.Console.MessageType.Info)


    item_instance = Item.item_instance(inspected_item_id)
    item_modifiers = item_instance.modifiers

    # 10136 = requirement modifier
    requirement_modifier = None

    # Look for requirement modifier
    for mod in item_modifiers:
        if mod.GetIdentifier() == 10136:
            requirement_modifier = mod
            break

    if requirement_modifier is not None:
        ConsoleLog("Item Info Test", f"Requirement Modifiers: {requirement_modifier.GetArg2()}", Py4GW.Console.MessageType.Info)

def create_bot_routine(bot: Botting) -> None:

    TestGetItemInfo()
    # InitializeBot(bot)
    # InitialTravelAndSetup(bot)
    # SetupInventoryManagement(bot)
    # SetupResign(bot)
    # ChestRunRoutine(bot)
    # ResetFarmLoop(bot)


def InitializeBot(bot: Botting) -> None:
    condition = lambda: on_death(bot)
    bot.Events.OnDeathCallback(condition)
    # bot.Events.OnPartyWipeCallback(condition)
    # bot.Events.OnPartyDefeatedCallback(condition)

    bot.States.AddHeader("Initialize Bot")
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
def _on_death(bot: "Botting"):
    yield from Routines.Yield.wait(5000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Barbarous Shore Running_4") 
    fsm.resume()                           
    yield  


def on_death(bot: "Botting"):
    ConsoleLog("Death detected", "Player Died - Run Failed, Restarting...", Py4GW.Console.MessageType.Notice)
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))

# ==================== END REGION Setup ====================


# ==================== REGION Routines ====================

# Initial travel to Barbarous Shore and setup runner build
def InitialTravelAndSetup(bot: Botting) -> None:
    bot.States.AddHeader("Travel and Setup")
    bot.States.AddCustomState(lambda: EquipSkillBar(bot), "Equip SkillBar")
    bot.States.AddCustomState(lambda: SetupDangerTables(), "Setup Danger Tables for Barbarous Shore")

def SetupInventoryManagement(bot: Botting) -> None:
    bot.States.AddHeader("Setup Inventory Management")
    bot.States.AddCustomState(lambda: ManageInventory(bot), "Manage Inventory before run")

# Setup to spawn close to portal on resign
def SetupResign(bot: Botting):
    bot.States.AddHeader("Setup Resign")
    bot.Move.XYAndExitMap(-12636, 16906, target_map_id=BARBAROUS_SHORE) # target_map_name="Barbarous Shore"
    bot.Wait.ForTime(1000)
    bot.Move.XYAndExitMap(-14707, 18571, target_map_id=CAMP_HOJANU) # target_map_name="Camp Hojanu"

# Chestrun routine follows a set path and opens chests along the way
def ChestRunRoutine(bot: Botting) -> None:
    bot.States.AddHeader("Barbarous Shore Running")

    should_manage_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 5

    bot.Move.XYAndExitMap(-12636, 16906, target_map_id=BARBAROUS_SHORE) # target_map_name="Barbarous Shore"
    bot.Properties.Enable("auto_combat") # Enable combat to enter the ProcessSkillCasting loop of the build

    path_points: list[tuple[float, float]] = [
        # (-13211, 9451),
        (-13938, 9533),
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
        (3540, -6390),
        (5980, -7937),
        (9848, -4610),
        (12569, -4510),
        (16223, 1906),
        (11659, 9010),
        (5896, 11982),
        (1361, 9582),
        (-6506, 12177),
    ]

    for i, coord in enumerate(path_points):
        x, y = coord
        bot.Move.XY(x, y, f"Moving to point {i + 1}")
        bot.States.AddCustomState(lambda: DetectChestAndOpen(bot), f"Detect and Open Chest at point {i}")
        # bot.Move.XY(x, y, f"Repositioning at point {i + 1} after chest open")
    
    # bot.Move.FollowPath(path_points)


def DetectChestAndOpen(bot: Botting, max_distance=4000):
    nearby_chest_id = Routines.Agents.GetNearestChest(max_distance)

    # No chest found
    if nearby_chest_id == 0 or nearby_chest_id in opened_chests:
        ConsoleLog(bot.bot_name, f"No usable chest found", Py4GW.Console.MessageType.Info)

    # Handle chest found
    else:
        ConsoleLog(bot.bot_name, f"Located nearby chest ::: {nearby_chest_id}", Py4GW.Console.MessageType.Info)

        # Update build handler to signal looting state
        if isinstance(bot.config.build_handler, SF_Assassin_Barbarous):

            # Prevent casting to ensure item gets picked up,
            # ideally would move this to on_start and on_end methods inside InteractWithNearestChest
            bot.config.build_handler.SetLootingSignal(True)

            Routines.Yield.Agents.InteractWithNearestChest(max_distance)

            bot.config.build_handler.SetLootingSignal(False)
            opened_chests.add(nearby_chest_id)
            bot.Wait.ForTime(200)

    yield

# Reset the farm loop to run Barbarous Shore again
def ResetFarmLoop(bot: Botting):
    bot.States.AddHeader("Reset Farm Loop")
    bot.Properties.Disable("auto_combat")
    bot.Party.Resign()
    bot.Wait.ForTime(10000)

    # Wrap in generic 
    bot.States.AddCustomState(lambda: ManageInventory(bot), "Manage Inventory before next run if flagged")

    # Check inventory
    bot.States.JumpToStepName("[H]Barbarous Shore Running_4")


def ManageInventory(bot: Botting):
    if should_manage_inventory:
        # Restock on ID kits
        desired_kits = 4
        id_kit_count = GLOBAL_CACHE.Inventory.GetModelCount(5899)
        yield from Routines.Yield.Agents.InteractWithAgentByName("Kahdeh")
        yield from Routines.Yield.Merchant.BuyIDKits(desired_kits - id_kit_count)

        # ID All
        rarities = ["Purple", "Gold"]
        item_ids = Routines.Items.GetUnidentifiedItems(rarities=rarities, slot_blacklist=[])
        yield from Routines.Yield.Items.IdentifyItems(item_ids)

        # items to keep
        items_to_keep = []

        # for item_id in items:
        #     item_instance = Item.item_instance(item_id)
        #     if (item_instance.is_armor and item_instance.
        #     if item.rarity in rarities:
        #         items_to_keep.append(item)

        # Handle choosing which items to keep


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