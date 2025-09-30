from Bots.marks_coding_corner.utils.loot_utils import VIABLE_LOOT
from Bots.marks_coding_corner.utils.loot_utils import get_valid_salvagable_loot_array
from Bots.marks_coding_corner.utils.loot_utils import sell_non_essential_mats
from Py4GWCoreLib.Builds.DervBoneFarmer import ENEMY_BLACKLIST
from Py4GWCoreLib.Builds.DervBoneFarmer import DervBuildFarmStatus
from Py4GWCoreLib.Builds.DervBoneFarmer import DervBoneFarmer
from Py4GWCoreLib import *

try:
    script_directory = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # __file__ is not defined (e.g. running in interactive mode or embedded interpreter)
    script_directory = os.getcwd()
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))
base_dir = os.path.join(project_root, "marks_coding_corner/textures")

COF_FARMER = "COF Farmer"
DOOMLORE_SHRINE = "Doomlore Shrine"
COF_LEVEL_1 = "Cathedral of Flames (level 1)"

VIABLE_LOOT |= {
    ModelID.Golden_Rin_Relic,
    ModelID.Diessa_Chalice,
}
# handler constants
HANDLE_STUCK = 'handle_stuck'
HANDLE_DANGER = 'handle_danger'
TEXTURE_ICON_PATH = os.path.join(base_dir, "cof_art.png")

bot = Botting(
    COF_FARMER,
    custom_build=DervBoneFarmer(),
    config_movement_timeout=15000,
    config_movement_tolerance=150,
    upkeep_auto_inventory_management_active=False,
    upkeep_auto_loot_active=False,
)
stuck_timer = ThrottledTimer(3000)
movement_check_timer = ThrottledTimer(3000)
item_id_blacklist = []
is_farming = False
unmanaged_fail_counter = 0


# region Direct Bot Actions
def return_to_outpost():
    if GLOBAL_CACHE.Map.IsOutpost():
        return

    is_explorable = GLOBAL_CACHE.Map.IsExplorable()
    while is_explorable:
        is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
        is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
        is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated() or GLOBAL_CACHE.Player.GetMorale() < 100

        if is_map_ready and is_party_loaded and is_explorable and is_party_defeated:
            yield from Routines.Yield.Player.Resign()
            yield from Routines.Yield.wait(2000)
            GLOBAL_CACHE.Party.ReturnToOutpost()
        else:
            is_explorable = GLOBAL_CACHE.Map.IsExplorable()
            yield from Routines.Yield.wait(4000)


def load_skill_bar(bot: Botting):
    yield from bot.config.build_handler.LoadSkillBar()


def farm(bot):
    global looted_areas
    global is_farming

    if is_farming:
        return

    # Auto detect if enemy in the area
    enemy_array = get_enemy_array(custom_range=Range.Spellcast.value)
    if not len(enemy_array):
        ConsoleLog('Farm COF', 'No enemy detected!')
        return

    ConsoleLog(COF_FARMER, 'Farming...')
    is_farming = True
    bot.config.build_handler.status = DervBuildFarmStatus.Kill

    ConsoleLog(COF_FARMER, 'Killing all! None shall survive!')
    player_id = GLOBAL_CACHE.Player.GetAgentID()

    while True:
        enemy_array = get_enemy_array(custom_range=Range.Spellcast.value)
        if len(enemy_array) == 0:
            ConsoleLog(COF_FARMER, 'Setting to [Loot] status')
            bot.config.build_handler.status = DervBuildFarmStatus.Loot
            yield from Routines.Yield.wait(500)
            yield from loot_items()
            yield from Routines.Yield.wait(500)
            ConsoleLog(COF_FARMER, 'Setting back to [Wait] status')
            bot.config.build_handler.status = DervBuildFarmStatus.Wait
            # log from the last epicenter of the begining of the farm
            break  # all enemies dead

        # Death check
        if GLOBAL_CACHE.Agent.IsDead(player_id):
            # handle death here
            ConsoleLog(COF_FARMER, 'Died fighting, setting back to [Wait], dont block going to outpost')
            bot.config.build_handler.status = DervBuildFarmStatus.Wait
            is_farming = False
            yield from Routines.Yield.Player.Resign()
            yield from Routines.Yield.wait(1000)
            return

        yield from Routines.Yield.wait(100)

    ConsoleLog(COF_FARMER, 'Finished farming.')
    is_farming = False
    yield from Routines.Yield.wait(100)


def loot_items():
    global item_id_blacklist
    filtered_agent_ids = get_valid_salvagable_loot_array(viable_loot=VIABLE_LOOT)
    yield from Routines.Yield.wait(500)  # Wait for a second before starting to loot
    ConsoleLog(COF_FARMER, 'Looting items...')
    failed_items_id = yield from Routines.Yield.Items.LootItemsWithMaxAttempts(filtered_agent_ids, log=True)
    if failed_items_id:
        item_id_blacklist = item_id_blacklist + failed_items_id
    ConsoleLog(COF_FARMER, 'Looting items finished')
    yield


def identify_and_salvage_items():
    yield from Routines.Yield.wait(1500)
    yield from AutoInventoryHandler().IDAndSalvageItems()


def buy_id_kits():
    yield from Routines.Yield.wait(1500)
    kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit)
    sup_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit)
    if (kits_in_inv + sup_kits_in_inv) < 1:
        yield from Routines.Yield.Merchant.BuyIDKits(1)


def buy_salvage_kits():
    yield from Routines.Yield.wait(1500)
    kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit)
    if kits_in_inv < 2:
        yield from Routines.Yield.Merchant.BuySalvageKits(3)


# endregion


# region Helper Methods
def get_enemy_array(custom_range=Range.Area.value * 1.50):
    px, py = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, custom_range)
    return [agent_id for agent_id in enemy_array if GLOBAL_CACHE.Agent.GetModelID(agent_id) not in ENEMY_BLACKLIST]


def reset_looted_areas():
    global item_id_blacklist
    item_id_blacklist = []
    yield


def set_bot_to_setup(bot: Botting):
    bot.config.build_handler.status = DervBuildFarmStatus.Setup  # type: ignore
    yield


def set_bot_to_prepare(bot: Botting):
    bot.config.build_handler.status = DervBuildFarmStatus.Prepare  # type: ignore
    yield


def set_bot_to_loot(bot: Botting):
    bot.config.build_handler.status = DervBuildFarmStatus.Loot  # type: ignore
    yield


def _on_death(bot: Botting):
    ConsoleLog(COF_FARMER, "Waiting for a moment reset...")
    yield from Routines.Yield.wait(1000)
    ident_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit)
    sup_ident_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit)
    salv_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit)
    free_slot_count = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
    fsm = bot.config.FSM
    if (ident_kits_in_inv + sup_ident_kits_in_inv) == 0 or salv_kits_in_inv == 1 or free_slot_count < 2:
        fsm.jump_to_state_by_name("[H]Starting Loop_1")
    else:
        fsm.jump_to_state_by_name("[H]Farm Loop_2")
    fsm.resume()
    yield


def on_death(bot: Botting):
    ConsoleLog(COF_FARMER, "Player is dead. Restarting...")
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))


def is_inventory_ready():
    salv_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit)
    id_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit)
    free_slots = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
    if salv_kits_in_inv < 3 or id_kits_in_inv == 0 or free_slots < 4:
        return False
    return True


# endregion

# region Handlers

def _force_reset(bot: Botting):
    global unmanaged_fail_counter
    unmanaged_fail_counter += 1
    ConsoleLog(COF_FARMER, f"Something went wrong forcing a reset... Attempt: {unmanaged_fail_counter}")
    yield from Routines.Yield.wait(1000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Starting Loop_1")
    yield


def handle_custom_on_unmanaged_fail(bot: Botting):
    global unmanaged_fail_counter

    ConsoleLog(COF_FARMER, "Handling explorable mode unmanaged error...")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("Force Reset", _force_reset(bot))

    if unmanaged_fail_counter > 5:
        return True
    return False


# endregion


def cof_farm_bot(bot: Botting):
    bot.Events.OnDeathCallback(lambda: on_death(bot))
    bot.helpers.Events.set_custom_on_unmanaged_fail(lambda: handle_custom_on_unmanaged_fail(bot))
    # override condition for halting movement

    bot.States.AddHeader('Starting Loop')
    bot.States.AddCustomState(lambda: set_bot_to_loot(bot), "Set bot to loot")
    bot.Map.Travel(target_map_name=DOOMLORE_SHRINE)
    bot.Wait.ForMapLoad(target_map_name=DOOMLORE_SHRINE)
    bot.States.AddCustomState(lambda: load_skill_bar(bot), "Loading Skillbar")

    bot.States.AddCustomState(lambda: set_bot_to_setup(bot), "Setup Resign")
    bot.Move.XY(-18815.00, 17923.00, 'Move to NPC')
    bot.Dialogs.AtXY(-19166.00, 17980.00, 0x7F, "Open Merch")
    bot.States.AddCustomState(sell_non_essential_mats, 'Sell mats')
    bot.States.AddCustomState(buy_id_kits, 'Buying ID Kits')
    bot.States.AddCustomState(buy_salvage_kits, 'Buying Salvage Kits')
    bot.States.AddCustomState(identify_and_salvage_items, 'Salvaging Items')
    bot.Dialogs.AtXY(-19166.00, 17980.00, 0x832101, "Temple of the damned Quest")  # Temple of the damned quest 0x832101
    bot.Dialogs.AtXY(-19166.00, 17980.00, 0x88, "Enter COF Level 1")  # Enter COF Level 1

    # Resign setup
    bot.Wait.ForTime(2000)
    bot.Wait.ForMapLoad(target_map_name=COF_LEVEL_1)
    bot.Move.XY(-19665, -8045, "Setup resign spot")
    bot.Wait.ForMapLoad(target_map_name=DOOMLORE_SHRINE)

    # Actual Farming Loop
    bot.States.AddHeader('Farm Loop')
    bot.Properties.Enable("auto_combat")
    bot.States.AddCustomState(return_to_outpost, "Return to Doomlore if dead")
    bot.Wait.ForTime(2000)
    bot.Wait.ForMapLoad(target_map_name=DOOMLORE_SHRINE)
    bot.Dialogs.AtXY(-19166.00, 17980.00, 0x832101, "Temple of the damned Quest")  # Temple of the damned quest 0x832101
    bot.Dialogs.AtXY(-19166.00, 17980.00, 0x88, "Enter COF Level 1")  # Enter COF Level 1
    bot.Wait.ForMapLoad(target_map_name=COF_LEVEL_1)
    bot.Wait.ForTime(2000)
    bot.Move.XY(-18295.50, -8614.49, "Move towards shrine")
    bot.Dialogs.AtXY(-18250.00, -8595.00, 0x84)

    bot.Move.XY(-16623, -8989, 'Move prep spot')
    bot.States.AddCustomState(lambda: set_bot_to_prepare(bot), "Prepare skills")
    bot.Wait.ForTime(3000)

    bot.Move.XY(-15525, -8923, 'Move spot 1')
    bot.Move.XY(-15737, -9093, 'Move spot 2')
    bot.States.AddCustomState(lambda: farm(bot), "Killing Everything Immediately")
    bot.States.AddCustomState(lambda: set_bot_to_loot(bot), "Set bot to loot")
    bot.States.AddCustomState(reset_looted_areas, "Reset looted areas")
    bot.States.AddCustomState(identify_and_salvage_items, 'Salvaging Items')
    bot.Party.Resign()
    bot.Wait.ForTime(60000)
    bot.Wait.UntilCondition(lambda: GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()))


bot.SetMainRoutine(cof_farm_bot)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE_ICON_PATH)


if __name__ == "__main__":
    main()
