import Py4GW
from Py4GWCoreLib import (Routines, Item, Botting, ActionQueueManager, ConsoleLog, GLOBAL_CACHE, Agent, HeroType)
from Py4GWCoreLib.Builds import SF_Assassin_Barbarous, SF_Derv_Barbarous
from Py4GWCoreLib.Builds.BuildHelpers import BuildDangerHelper, DangerTable
from Bots.Sasemoi.bot_helpers import BotStuckHelper
from Bots.Sasemoi.utils.inventory_utils import filter_valuable_inscription_type, get_unidentified_items, filter_valuable_weapon_type, filter_valuable_rune_type
from Bots.Sasemoi.bot_helpers.bot_mystic_healing_support import MysticHealingSupport

#region Constants and Globals
# Globals
BARBAROUS_SHORE = 375
CAMP_HOJANU = 376
BARB_SHORE_RUNNER = "Barbarous Shore Chestrun"

# Danger Tables
barbarous_cripple_kd_table: DangerTable = (
    ([5048 + 51, 5059 + 51, 5043 + 51, 5051 + 51, 5050 + 51, 5029 + 51, 5032 + 51, 5030 + 51], "Corsair"),
    ([4904 + 51], "Mesa")
)
barbarous_spellcast_table: DangerTable = ((
    ([5048 + 51, 5059 + 51, 5043 + 51, 5051 + 51, 5050 + 51, 5029 + 51, 5032 + 51, 5030 + 51], "Corsair"),
    ([4980], "Iboga")
)) # Not using spellcaster detection because the script permanently keeps Shadow Form up

hero_list = [
    HeroType.Gwen,
    HeroType.MOX,
    HeroType.Melonni
]

hero_template_list = [
    (HeroType.Gwen, "OQpjAwDjKP3XlAAAAAAAAAAAAA"),
    (HeroType.MOX, "Ogmioys8cfpxAAAAAAAAAAAA"),
    (HeroType.Melonni, "Ogmioys8cfpxAAAAAAAAAAAA")
]

# Script states
opened_chests: set[int] = set()
should_manage_inventory = False

bot = Botting(
    BARB_SHORE_RUNNER,
    custom_build=SF_Derv_Barbarous(
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

#region Setup
# ==================== SETUP ====================

def create_bot_routine(bot: Botting) -> None:    
    InitialTravelAndSetup(bot)
    InitializeBot(bot)
    SetupHeroes(bot)
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
    profession, _ = Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    match profession:
        case "Assassin":
            bot.OverrideBuild(SF_Assassin_Barbarous())

        case "Dervish":
            bot.OverrideBuild(SF_Derv_Barbarous(
                build_danger_helper=BuildDangerHelper(
                    cripple_kd_table=barbarous_cripple_kd_table,
                    spellcast_table=barbarous_spellcast_table
                )
            ))
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
    yield from Routines.Yield.wait(10000)  # Wait for death to complete
    yield from ConditionallyMoveToMerchant()
    yield from ManageInventory(bot)

    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Barbarous Shore Running_6") 
    fsm.resume()                           
    yield  


def on_death(bot: Botting):
    ConsoleLog("Death detected", "Player Died - Run Failed, Restarting...", Py4GW.Console.MessageType.Notice)

    # Reset Action Queues and FSM
    ResetUnopenedChests()
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

        # Identify Items
        yield from Routines.Yield.Items.IdentifyItems(all_items)
        yield from Routines.Yield.wait(500)

        # Filter valuable loot
        valuable_loot = [item_id for item_id in all_items if filter_valuable_weapon_type(item_id)]
        valuable_runes = [item_id for item_id in all_items if filter_valuable_rune_type(item_id)]
        valuable_inscriptions = [item_id for item_id in all_items if filter_valuable_inscription_type(item_id)]
        items_to_keep = valuable_loot[:]
        items_to_keep.extend(valuable_runes)
        items_to_keep.extend(valuable_inscriptions)

        # Make items unique
        items_to_keep = list(set(items_to_keep)) # Remove duplicates

        # Deposit valuable loot
        for item_id in items_to_keep:
            GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
            yield from Routines.Yield.wait(500)

        # Sell remaining items
        remaining_items = [item_id for item_id in all_items if item_id not in items_to_keep]
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

# Reset opened chests for next run so they don't pass over through instance load
def ResetUnopenedChests():
    global opened_chests
    opened_chests = set()

# ==================== END SETUP ====================

#region Routines
# ==================== ROUTINES ====================

# Initial travel to Barbarous Shore and setup runner build
def InitialTravelAndSetup(bot: Botting) -> None:
    bot.States.AddHeader("Travel and Setup")
    bot.Map.Travel(CAMP_HOJANU)
    bot.States.AddCustomState(lambda: EquipSkillBar(bot), "Equip SkillBar")
    bot.States.AddCustomState(lambda: SetupDangerTables(), "Setup Danger Tables for Barbarous Shore")


# Check if inventory management is needed and perform it
def SetupInventoryManagement(bot: Botting) -> None:
    bot.States.AddHeader("Inventory Management")
    bot.States.AddCustomState(lambda: AssessLootManagement(), "Loot management check")
    bot.States.AddCustomState(lambda: ConditionallyMoveToMerchant(), "Move to merchant for inventory check")
    bot.Wait.ForTime(1000)
    bot.States.AddCustomState(lambda: ManageInventory(bot), "Manage Inventory before run")


# Setup heroes for mystic healing support
def SetupHeroes(bot: Botting):
    bot.States.AddHeader("Setup Heroes for Mystic Healing Support")
    MysticHealingSupport.SetupHealingParty(bot, hero_list=hero_template_list)


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
    bot.Wait.ForTime(500)
    bot.Party.FlagAllHeroes(-12323, 17313)

    MysticHealingSupport.InitHeroComanagedRoutines(bot, hero_list=hero_list)

    bot.Properties.Enable("auto_combat")
    bot.Properties.Enable("alcohol")
    
    path_points: list[tuple[float, float]] = [
        (-14616, 8558),
        (-15474, 4744),
        (-16036, 3647),
        (-14193, 4443),
        (-9489, 1759),
        (-13644, -1846),
        (-11687, -5170),
        (-13006, -9314),
        (-14329, -11996),
        (-16625, -14953),
        (-16042, -15539),
        (-7940, -11834),
        (-6941, -7614),
        # (-5765, -3661),
        # (-3917, -3608),
        # (-1273, -4529),
        # (1016, -2442),

        # # Exit cove up north
        # (-511, 201),
        
        # # Corsair bay
        # (1347, 581),
        # (826, 888),
        # (982, -3058),

        # # Mandragor corridor
        # (3059, -5966),

        # # Before big plains
        # (8115, -2483),
        # (12993, -3892)
        # (3540, -6390),
        # Traverse plains
        # (10524, -3770),
        # (12569, -4510),
        # (14580, -2447),
        # (15119, -648),
        # (13607, 994),

        # Last corridor
        # (16471, 3187),
        # (14646, 4945),
        # (16882, 1506),
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

    MysticHealingSupport.RemoveHeroComanagedRoutines(bot, hero_list=hero_list)

    bot.States.AddCustomState(lambda: ResetUnopenedChests(), "Reset Opened Chests List")
    bot.Party.Resign()
    bot.States.AddCustomState(lambda: AssessLootManagement(), "Loot management check")
    bot.Wait.ForTime(10000)
    bot.States.AddCustomState(lambda: ConditionallyMoveToMerchant(), "Move to merchant for inventory check")
    bot.States.AddCustomState(lambda: ManageInventory(bot), "Manage management execution")
    bot.States.JumpToStepName("[H]Barbarous Shore Running_6")


# ==================== END ROUTINES ====================



#region Main
# ==================== MAIN ====================

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

# ==================== END MAIN ====================