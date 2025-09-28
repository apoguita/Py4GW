import random

from Py4GWCoreLib.Builds.DervDustFarmer import DervBuildFarmStatus
from Py4GWCoreLib.Builds.DervDustFarmer import DervDustFarmer
from Py4GWCoreLib import *

try:
    script_directory = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # __file__ is not defined (e.g. running in interactive mode or embedded interpreter)
    script_directory = os.getcwd()
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))
base_dir = os.path.join(project_root, "marks_coding_corner/textures")

DUST_FARMER = "Dust Farmer"
TOA = "Temple of the Ages"
THE_BLACK_CURTAIN = "The Black Curtain"
VIABLE_LOOT = {
    ModelID.Gold_Coins,
    ModelID.Bone,
    ModelID.Plant_Fiber,
    ModelID.Abnormal_Seed,
    ModelID.Pile_Of_Glittering_Dust,
    ModelID.Feather,
    ModelID.Feathered_Crest,
    ModelID.Bottle_Of_Rice_Wine,
    ModelID.Bottle_Of_Vabbian_Wine,
    ModelID.Dwarven_Ale,
    ModelID.Eggnog,
    ModelID.Hard_Apple_Cider,
    ModelID.Hunters_Ale,
    ModelID.Shamrock_Ale,
    ModelID.Witchs_Brew,
    ModelID.Zehtukas_Jug,
    ModelID.Aged_Dwarven_Ale,
    ModelID.Bottle_Of_Grog,
    ModelID.Krytan_Brandy,
    ModelID.Spiked_Eggnog,
    ModelID.Vial_Of_Dye,
    ModelID.Monstrous_Claw,
    ModelID.Monstrous_Eye,
    ModelID.Shadowy_Remnants,
}
# handler constants
HANDLE_STUCK = 'handle_stuck'
HANDLE_LOOT = 'handle_loot'
HANDLE_FOG_NIGHTMARE_DANGER = 'handle_fog_nightmare_danger'
TEXTURE_ICON_PATH = os.path.join(base_dir, "dust_art.png")

bot = Botting(
    DUST_FARMER,
    custom_build=DervDustFarmer(),
    config_movement_timeout=15000,
    config_movement_tolerance=150,  # Can get stuck before it reaches the point, but good enough to fight fog_nightmares in the area
    upkeep_auto_inventory_management_active=False,
    upkeep_auto_loot_active=False,
)
stuck_timer = ThrottledTimer(3000)
movement_check_timer = ThrottledTimer(6000)
stuck_counter = 0
unstuck_counter = 0
old_player_position = (0, 0)
item_id_blacklist = []
is_farming = False
is_looting = False


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


def farm_fog_nightmares(bot):
    global is_looting
    global is_farming

    if is_farming:
        return

    # Auto detect if fog_nightmares in the area
    fog_nightmare_array = get_fog_nightmare_array(custom_range=Range.Earshot.value)
    if not len(fog_nightmare_array):
        ConsoleLog('Farm Fog Nightmares', 'No Fog Nightmare detected!')
        return

    ConsoleLog(DUST_FARMER, 'Farming...')
    is_farming = True
    bot.config.build_handler.status = DervBuildFarmStatus.Kill

    ConsoleLog(DUST_FARMER, 'Killing all Fog Nightmares! None shall survive!')
    start_time = Utils.GetBaseTimestamp()
    timeout = 120000  # 2 minutes max

    player_id = GLOBAL_CACHE.Player.GetAgentID()

    while True:
        fog_nightmare_array = get_fog_nightmare_array(custom_range=Range.Earshot.value)
        if len(fog_nightmare_array) == 0:
            bot.config.build_handler.status = DervBuildFarmStatus.Move
            break  # all fog_nightmares dead

        # Timeout check
        current_time = Utils.GetBaseTimestamp()
        if timeout > 0 and current_time - start_time > timeout:
            ConsoleLog(DUST_FARMER, 'Fight took too long, setting back to [Move] status')
            bot.config.build_handler.status = DervBuildFarmStatus.Move
            yield from Routines.Yield.wait(1000)
            yield from Routines.Yield.Player.Resign()
            return

        # Death check
        if GLOBAL_CACHE.Agent.IsDead(player_id):
            # handle death here
            ConsoleLog(DUST_FARMER, 'Died fighting, setting back to [Move] status')
            bot.config.build_handler.status = DervBuildFarmStatus.Move
            return

        yield from Routines.Yield.wait(100)

    ConsoleLog(DUST_FARMER, 'Finished farming.')
    is_farming = False
    yield from Routines.Yield.wait(100)


def loot_items():
    global item_id_blacklist
    filtered_agent_ids = get_valid_loot_array()
    yield from Routines.Yield.wait(500)  # Wait for a second before starting to loot
    ConsoleLog(DUST_FARMER, 'Looting items...')
    failed_items_id = yield from Routines.Yield.Items.LootItemsWithMaxAttempts(filtered_agent_ids, log=True)
    if failed_items_id:
        item_id_blacklist = item_id_blacklist + failed_items_id
    ConsoleLog(DUST_FARMER, 'Looting items finished')
    yield


def identify_and_salvage_items():
    yield from Routines.Yield.wait(1500)
    yield from AutoInventoryHandler().IDAndSalvageItems()


def buy_id_kits():
    yield from Routines.Yield.wait(1500)
    kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit)
    if kits_in_inv < 3:
        yield from Routines.Yield.Merchant.BuyIDKits(3)


def buy_salvage_kits():
    yield from Routines.Yield.wait(1500)
    kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit)
    if kits_in_inv <= 3:
        yield from Routines.Yield.Merchant.BuySalvageKits(10)


# endregion


# region Helper Methods
def get_fog_nightmare_array(custom_range=Range.Area.value * 1.50):
    px, py = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, custom_range)
    return [agent_id for agent_id in enemy_array if GLOBAL_CACHE.Agent.GetModelID(agent_id) in {AgentModelID.FOG_NIGHTMARE, AgentModelID.SPINED_ALOE}]


def get_non_fog_nightmare_array(custom_range=Range.Area.value * 1.50):
    px, py = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, custom_range)
    return [agent_id for agent_id in enemy_array if GLOBAL_CACHE.Agent.GetModelID(agent_id) not in {AgentModelID.FOG_NIGHTMARE, AgentModelID.SPINED_ALOE}]


def get_valid_loot_array():
    loot_array = AgentArray.GetItemArray()
    loot_array = AgentArray.Filter.ByDistance(loot_array, GLOBAL_CACHE.Player.GetXY(), Range.Spellcast.value * 3.00)

    def is_valid_item(item_id):
        if not Agent.IsValid(item_id):
            return False
        player_agent_id = Player.GetAgentID()
        owner_id = Agent.GetItemAgentOwnerID(item_id)
        if (owner_id == player_agent_id) or (owner_id == 0):
            return True
        return False

    filtered_agent_ids = []
    for agent_id in loot_array[:]:  # Iterate over a copy to avoid modifying while iterating
        item_data = Agent.GetItemAgent(agent_id)
        item_id = item_data.item_id
        model_id = Item.GetModelID(item_id)
        if model_id in VIABLE_LOOT and is_valid_item(agent_id):
            # Black and White Dyes
            if (
                model_id == ModelID.Vial_Of_Dye
                and (GLOBAL_CACHE.Item.GetDyeColor(item_id) == 10 or GLOBAL_CACHE.Item.GetDyeColor(item_id) == 12)
                or model_id != ModelID.Vial_Of_Dye
            ):
                filtered_agent_ids.append(agent_id)
    return filtered_agent_ids


def reset_item_id_blacklist():
    global item_id_blacklist
    item_id_blacklist = []
    yield


def set_bot_to_move(bot: Botting):
    global is_farming
    is_farming = False
    bot.config.build_handler.status = DervBuildFarmStatus.Move  # type: ignore
    yield


def set_bot_to_wait(bot: Botting):
    global is_farming
    is_farming = False
    bot.config.build_handler.status = DervBuildFarmStatus.Wait  # type: ignore
    yield


def set_bot_to_setup(bot: Botting):
    global is_farming
    is_farming = False
    bot.config.build_handler.status = DervBuildFarmStatus.Setup  # type: ignore
    yield


def detect_fog_nightmare_or_loot():
    global item_id_blacklist
    # 1. Fog Nightmare always take priority
    fog_nightmare_array = get_fog_nightmare_array(custom_range=Range.Earshot.value)
    if fog_nightmare_array:
        return True

    # 2. Loot check
    filtered_agent_ids = get_valid_loot_array()
    if not filtered_agent_ids:
        return False

    # Apply blacklist filter
    filtered_agent_ids = [agent_id for agent_id in filtered_agent_ids if agent_id not in set(item_id_blacklist)]

    if not filtered_agent_ids:
        return False

    return True


def _on_death(bot: Botting):
    ConsoleLog(DUST_FARMER, "Waiting for a moment reset...")
    yield from Routines.Yield.wait(1000)
    ident_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit)
    sup_ident_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit)
    salv_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit)
    fsm = bot.config.FSM
    if (ident_kits_in_inv + sup_ident_kits_in_inv) == 0 or salv_kits_in_inv == 0:
        fsm.jump_to_state_by_name("[H]Starting Loop_1")
    else:
        fsm.jump_to_state_by_name("[H]Farm Loop_2")
    fsm.resume()
    yield


def on_death(bot: Botting):
    ConsoleLog(DUST_FARMER, "Player is dead. Restarting...")
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


def is_within_tolerance(pos1, pos2, tolerance=100):
    dx = pos1[0] - pos2[0]
    dy = pos1[1] - pos2[1]
    distance = math.hypot(dx, dy)  # sqrt(dx^2 + dy^2)
    return distance <= tolerance


# endregion


# region Managed Handlers
def handle_stuck(bot: Botting):
    global stuck_timer
    global movement_check_timer
    global old_player_position
    global stuck_counter
    global unstuck_counter

    while True:
        # Wait until map is valid
        if not Routines.Checks.Map.MapValid() and not Routines.Checks.Map.IsExplorable():
            yield from Routines.Yield.wait(1000)
            continue

        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            yield from Routines.Yield.wait(1000)
            yield from Routines.Yield.Player.Resign()
            continue

        if (
            GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName(THE_BLACK_CURTAIN)
            and bot.config.build_handler.status == DervBuildFarmStatus.Move  # type: ignore
        ):
            if stuck_timer.IsExpired():
                GLOBAL_CACHE.Player.SendChatCommand("stuck")
                stuck_timer.Reset()

            # Check if character hasn't moved
            if movement_check_timer.IsExpired():
                current_player_pos = GLOBAL_CACHE.Player.GetXY()
                if is_within_tolerance(old_player_position, current_player_pos) and not bot.config.pause_on_danger_fn():
                    unstuck_counter += 1
                    ConsoleLog(DUST_FARMER, "Farmer is stuck, attempting unstuck procedure...")
                    stuck_counter += 1
                    GLOBAL_CACHE.Player.SendChatCommand("stuck")
                    player_pos = GLOBAL_CACHE.Player.GetXY()
                    facing_direction = GLOBAL_CACHE.Agent.GetRotationAngle(GLOBAL_CACHE.Player.GetAgentID())
                    # --- Backpedal (opposite facing direction) ---
                    back_angle = facing_direction + math.pi  # 180° behind
                    back_distance = 200
                    back_offset_x = math.cos(back_angle) * back_distance
                    back_offset_y = math.sin(back_angle) * back_distance

                    backpedal_pos = (player_pos[0] + back_offset_x, player_pos[1] + back_offset_y)
                    for _ in range(9):
                        GLOBAL_CACHE.Player.Move(backpedal_pos[0], backpedal_pos[1])

                    # --- Sidestep (random left or right) ---
                    side_direction = random.choice([-1, 1])  # -1 = right, 1 = left
                    side_angle = facing_direction + (side_direction * math.pi / 2)
                    side_distance = 200
                    offset_x = math.cos(side_angle) * side_distance
                    offset_y = math.sin(side_angle) * side_distance

                    sidestep_pos = (player_pos[0] + offset_x, player_pos[1] + offset_y)  # type: ignore
                    for _ in range(9):
                        GLOBAL_CACHE.Player.Move(sidestep_pos[0], sidestep_pos[1])

                    yield
                else:
                    old_player_position = current_player_pos
                    stuck_timer.Reset()
                    stuck_counter = 0

                movement_check_timer.Reset()

            # Hard reset if too many consecutive stuck detections
            if stuck_counter >= 10 or unstuck_counter >= 15:
                stuck_counter = 0
                unstuck_counter = 0
                yield from Routines.Yield.Player.Resign()
                continue

        if (
            GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName(THE_BLACK_CURTAIN)
            and bot.config.build_handler.status == DervBuildFarmStatus.Loot  # type: ignore
        ):
            if movement_check_timer.IsExpired():
                current_player_pos = GLOBAL_CACHE.Player.GetXY()
                if is_within_tolerance(old_player_position, current_player_pos) and not bot.config.pause_on_danger_fn():
                    ConsoleLog(DUST_FARMER, "Looting is stuck, attempting unstuck procedure...")
                    stuck_counter += 1
                    yield
                else:
                    old_player_position = current_player_pos
                    stuck_timer.Reset()
                    stuck_counter = 0

                movement_check_timer.Reset()

            # Hard reset if too many consecutive stuck detections
            if stuck_counter >= 10:
                stuck_counter = 0
                yield from Routines.Yield.Player.Resign()
                continue

        yield from Routines.Yield.wait(500)


def handle_fog_nightmare_danger(bot: Botting):
    while True:
        # Wait until map is valid
        if not Routines.Checks.Map.MapValid() and not Routines.Checks.Map.IsExplorable():
            yield from Routines.Yield.wait(1000)
            continue

        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            yield from Routines.Yield.wait(1000)
            continue

        if (
            GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName(THE_BLACK_CURTAIN)
            and bot.config.build_handler.status == DervBuildFarmStatus.Move  # type: ignore
        ):
            if bot.config.pause_on_danger_fn() and get_fog_nightmare_array(Range.Earshot.value):
                # Deal with local enemies before resuming
                yield from farm_fog_nightmares(bot)
        yield from Routines.Yield.wait(500)


def handle_loot(bot: Botting):
    global is_looting
    while True:
        # Wait until map is valid
        if not Routines.Checks.Map.MapValid() and not Routines.Checks.Map.IsExplorable():
            yield from Routines.Yield.wait(1000)
            continue

        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            yield from Routines.Yield.wait(1000)
            continue

        if (
            GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName(THE_BLACK_CURTAIN)
            and bot.config.build_handler.status == DervBuildFarmStatus.Move  # type: ignore
        ):
            if bot.config.pause_on_danger_fn() and get_valid_loot_array():
                if not is_looting:
                    is_looting = True
                    ConsoleLog(DUST_FARMER, 'Setting to [Loot] status')
                    bot.config.build_handler.status = DervBuildFarmStatus.Loot  # type: ignore
                    yield from Routines.Yield.wait(500)
                    yield from loot_items()
                    yield from Routines.Yield.wait(500)
                    ConsoleLog(DUST_FARMER, 'Setting back to [Move] status')
                    bot.config.build_handler.status = DervBuildFarmStatus.Move  # type: ignore
                    # log from the last epicenter of the begining of the farm
                    is_looting = False

        yield from Routines.Yield.wait(500)


# endregion


def dust_farm_bot(bot: Botting):
    bot.Events.OnDeathCallback(lambda: on_death(bot))
    # override condition for halting movement

    bot.States.AddHeader('Starting Loop')
    bot.Map.Travel(target_map_name=TOA)
    bot.Wait.ForTime(2000)
    bot.Wait.ForMapLoad(target_map_name=TOA)
    bot.States.AddCustomState(lambda: load_skill_bar(bot), "Loading Skillbar")

    bot.Move.XY(-5053.52, 19196.66, "Move close to Merch")
    bot.Interact.WithNpcAtXY(-5048.00, 19468.00, "Interact with Merchant")
    bot.States.AddCustomState(buy_id_kits, 'Buying ID Kits')
    bot.States.AddCustomState(buy_salvage_kits, 'Buying Salvage Kits')

    bot.States.AddCustomState(identify_and_salvage_items, 'Salvaging Items')

    # Resign setup
    bot.States.AddCustomState(lambda: set_bot_to_setup(bot), "Setup Resign")
    bot.Move.XY(-5265, 15913, "Exit Outpost for resign spot")
    bot.Wait.ForMapLoad(target_map_name=THE_BLACK_CURTAIN)
    bot.Move.XY(-5176, 16531, "Setup resign spot")
    bot.Wait.ForMapLoad(target_map_name=TOA)

    # Actual Farming Loop
    bot.States.AddHeader('Farm Loop')
    bot.config.set_pause_on_danger_fn(detect_fog_nightmare_or_loot)
    bot.Properties.Enable("auto_combat")
    bot.Properties.Enable("pause_on_danger")
    bot.States.AddCustomState(return_to_outpost, "Return to Seitung Harbor if Dead")
    bot.Wait.ForTime(2000)
    bot.Wait.ForMapLoad(target_map_name=TOA)
    bot.States.AddManagedCoroutine(HANDLE_STUCK, lambda: handle_stuck(bot))
    bot.States.AddManagedCoroutine(HANDLE_LOOT, lambda: handle_loot(bot))
    bot.States.AddManagedCoroutine(HANDLE_FOG_NIGHTMARE_DANGER, lambda: handle_fog_nightmare_danger(bot))
    bot.States.AddCustomState(lambda: set_bot_to_move(bot), "Exit Outpost To Farm")
    bot.Move.XY(-5265, 15913, "Exit Outpost To Farm")
    bot.Wait.ForMapLoad(target_map_name=THE_BLACK_CURTAIN)

    bot.Move.XY(-4014, 13044, 'Avoid Plant Mobs')
    bot.Move.XY(-5617, 6085, 'Run to spot 1')
    bot.Move.XY(310, 1364, 'Run to spot 2')

    for index, location_kills in enumerate([
        (7725, -2295),
        (7704, -3418),
        (6921, -4925),
        (9625, -4173),
        (11412, -6359),
        (12916, -7558),
        (12211, -4925),
        (13504, -4102),
        (11904, -3596),
        (11857, -2561),
        (13267, -2115),
        (12656, -1221),
        (13773, 771),
        (12626, 1507),
        (10832, 413),
        (10750, 1061),
    ]):
        x, y = location_kills
        bot.Move.XY(x, y, f'Move to Kill Spot {index + 1}')
        bot.States.AddCustomState(lambda: farm_fog_nightmares(bot), "Killing Fog Nightmares")
    bot.States.AddCustomState(lambda: set_bot_to_wait(bot), "Waiting to return")

    bot.States.AddHeader('ID and Salvage at the End')
    bot.States.AddCustomState(identify_and_salvage_items, "ID and Salvage loot")
    bot.States.AddCustomState(reset_item_id_blacklist, "Reset looting")

    bot.Party.Resign()
    bot.Wait.ForTime(3000)
    bot.Wait.UntilCondition(lambda: GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()))


bot.SetMainRoutine(dust_farm_bot)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE_ICON_PATH)


if __name__ == "__main__":
    main()
