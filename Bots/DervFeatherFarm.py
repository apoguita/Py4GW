import random

from Py4GWCoreLib.Builds.DervFeatherFarmer import SENSALI_MODEL_IDS
from Py4GWCoreLib.Builds.DervFeatherFarmer import DervBuildFarmStatus
from Py4GWCoreLib.Builds.DervFeatherFarmer import DervFeatherFarmer
from Py4GWCoreLib import *

FEATHER_FARMER = "Feather Farmer"
SEITUING_HARBOR = "Seitung Harbor"
JAYA_BLUFFS = "Jaya Bluffs"
VIABLE_LOOT = {
    ModelID.Gold_Coins,
    ModelID.Bone,
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
}
# handler constants
HANDLE_STUCK = 'handle_stuck'
HANDLE_SENSALI_DANGER = 'handle_sensali_danger'

bot = Botting(
    FEATHER_FARMER,
    custom_build=DervFeatherFarmer(),
    config_movement_timeout=15000,
    config_movement_tolerance=150,  # Can get stuck before it reaches the point, but good enough to fight sensalis in the area
    upkeep_auto_inventory_management_active=False,
    upkeep_auto_loot_active=False,
)
stuck_timer = ThrottledTimer(3000)
movement_check_timer = ThrottledTimer(3000)
stuck_counter = 0
unstuck_counter = 0
old_player_position = (0, 0)
looted_areas = []
item_id_blacklist = []
is_farming = False
is_looting = False


# region Direct Bot Actions
def return_to_outpost():
    is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
    is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
    is_explorable = GLOBAL_CACHE.Map.IsExplorable()
    is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated()
    yield from Routines.Yield.wait(3000)

    if is_map_ready and is_party_loaded and is_explorable and is_party_defeated:
        yield from Routines.Yield.Player.Resign()
        yield from Routines.Yield.wait(2000)
        GLOBAL_CACHE.Party.ReturnToOutpost()
        yield from Routines.Yield.wait(4000)
        while GLOBAL_CACHE.Map.GetMapID() != GLOBAL_CACHE.Map.GetMapIDByName(SEITUING_HARBOR):
            GLOBAL_CACHE.Party.ReturnToOutpost()
            yield from Routines.Yield.wait(4000)


def load_skill_bar(bot: Botting):
    yield from bot.config.build_handler.LoadSkillBar()


def ball_sensalis(bot: Botting):
    all_sensali_array = get_sensali_array(custom_range=Range.Spellcast.value)
    if not len(all_sensali_array):
        return False

    ConsoleLog(FEATHER_FARMER, 'Balling all Sensalis...')
    bot.config.build_handler.status = DervBuildFarmStatus.Ball  # type: ignore
    yield from Routines.Yield.wait(100)

    elapsed = 0
    while elapsed < (10 * 10):  # 100 = 10 seconds, 30 = 3 seconds
        # Enemies nearby
        player_hp = GLOBAL_CACHE.Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID())
        if player_hp < 0.80:
            ConsoleLog(FEATHER_FARMER, 'Dying, killing immediately!')
            return True

        all_sensali_array = get_sensali_array(custom_range=Range.Spellcast.value)
        nearby_sensali_array = get_sensali_array(custom_range=Range.Nearby.value)
        ball_count = len(nearby_sensali_array)
        total_count = len(all_sensali_array)

        if ball_count == total_count:
            ConsoleLog(FEATHER_FARMER, 'Sensalis ready to kill!')
            return True  # condition satisfied

        # wait 100ms
        yield from Routines.Yield.wait(100)
        elapsed += 1

    # timeout reached
    return False


def farm_sensalis(bot, kill_immediately=False):
    global looted_areas
    global is_looting
    global is_farming

    if is_farming:
        return

    # Auto detect if sensalis in the area
    sensali_array = get_sensali_array(custom_range=Range.Spellcast.value)
    if not len(sensali_array):
        ConsoleLog('Farm Sensalis', 'No Sensali detected!')
        return

    last_farm_epicenter = GLOBAL_CACHE.Player.GetXY()
    ConsoleLog(FEATHER_FARMER, 'Farming...')
    is_farming = True
    if kill_immediately:
        bot.config.build_handler.status = DervBuildFarmStatus.Kill
    else:
        yield from ball_sensalis(bot)
        bot.config.build_handler.status = DervBuildFarmStatus.Kill

    ConsoleLog(FEATHER_FARMER, 'Killing all Sensalis! None shall survive!')
    start_time = Utils.GetBaseTimestamp()
    timeout = 120000  # 2 minutes max

    player_id = GLOBAL_CACHE.Player.GetAgentID()

    while True:
        sensali_array = get_sensali_array(custom_range=Range.Spellcast.value)
        if len(sensali_array) == 0:
            if not is_looting:
                is_looting = True
                ConsoleLog(FEATHER_FARMER, 'Setting to [Loot] status')
                bot.config.build_handler.status = DervBuildFarmStatus.Loot
                yield from Routines.Yield.wait(500)
                yield from loot_items()
                yield from Routines.Yield.wait(500)
                ConsoleLog(FEATHER_FARMER, 'Setting back to [Move] status')
                bot.config.build_handler.status = DervBuildFarmStatus.Move
                # log from the last epicenter of the begining of the farm
                looted_areas.append(last_farm_epicenter)
                is_looting = False
            break  # all sensalis dead

        # Timeout check
        current_time = Utils.GetBaseTimestamp()
        if timeout > 0 and current_time - start_time > timeout:
            return

        # Death check
        if GLOBAL_CACHE.Agent.IsDead(player_id):
            # handle death here
            return

        yield from Routines.Yield.wait(100)

    ConsoleLog(FEATHER_FARMER, 'Finished farming.')
    is_farming = False
    yield from Routines.Yield.wait(100)


def loot_items():
    global item_id_blacklist
    filtered_agent_ids = get_valid_loot_array()
    yield from Routines.Yield.wait(500)  # Wait for a second before starting to loot
    ConsoleLog(FEATHER_FARMER, 'Looting items...')
    failed_items_id = yield from Routines.Yield.Items.LootItemsWithMaxAttempts(filtered_agent_ids, log=True)
    if failed_items_id:
        item_id_blacklist = item_id_blacklist + failed_items_id
    ConsoleLog(FEATHER_FARMER, 'Looting items finished')
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
def get_sensali_array(custom_range=Range.Area.value * 1.50):
    px, py = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, custom_range)
    return [agent_id for agent_id in enemy_array if GLOBAL_CACHE.Agent.GetModelID(agent_id) in SENSALI_MODEL_IDS]


def get_valid_loot_array():
    loot_array = AgentArray.GetItemArray()
    loot_array = AgentArray.Filter.ByDistance(loot_array, GLOBAL_CACHE.Player.GetXY(), Range.Spellcast.value * 1.50)

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


def is_in_looted_area():
    global looted_areas
    px, py = GLOBAL_CACHE.Player.GetXY()
    for lx, ly in looted_areas:
        dist_sq = (px - lx) ** 2 + (py - ly) ** 2
        if dist_sq <= Range.Earshot.value**2:
            ConsoleLog('ALERT', 'Already looted area!')
            return True
    return False


def reset_looted_areas():
    global looted_areas
    global item_id_blacklist
    looted_areas = []
    item_id_blacklist = []
    yield


def set_bot_to_move(bot: Botting):
    bot.config.build_handler.status = DervBuildFarmStatus.Move  # type: ignore
    yield


def set_bot_to_wait(bot: Botting):
    bot.config.build_handler.status = DervBuildFarmStatus.Wait  # type: ignore
    yield


def set_bot_to_setup(bot: Botting):
    bot.config.build_handler.status = DervBuildFarmStatus.Setup  # type: ignore
    yield


def detect_sensali_or_loot():
    global item_id_blacklist
    # 1. Sensali always take priority
    sensali_array = get_sensali_array()
    if sensali_array:
        return True

    # 2. Loot check
    filtered_agent_ids = get_valid_loot_array()
    if not filtered_agent_ids:
        return False

    # Apply blacklist filter
    filtered_agent_ids = [agent_id for agent_id in filtered_agent_ids if agent_id not in item_id_blacklist]

    if not filtered_agent_ids:
        return False

    return True


def _on_death(bot: "Botting"):
    ConsoleLog(FEATHER_FARMER, "Waiting for a moment reset...")
    yield from Routines.Yield.wait(1000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Farm Loop_2")
    fsm.resume()
    yield


def on_death(bot: "Botting"):
    ConsoleLog(FEATHER_FARMER, "Player is dead. Run Failed, Restarting...")
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
            GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName(JAYA_BLUFFS)
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
                    ConsoleLog(FEATHER_FARMER, "Farmer is stuck, attempting unstuck procedure...")
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

        if (
            GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName(JAYA_BLUFFS)
            and bot.config.build_handler.status == DervBuildFarmStatus.Loot  # type: ignore
        ):
            if movement_check_timer.IsExpired():
                current_player_pos = GLOBAL_CACHE.Player.GetXY()
                if is_within_tolerance(old_player_position, current_player_pos) and not bot.config.pause_on_danger_fn():
                    ConsoleLog(FEATHER_FARMER, "Looting is stuck, attempting unstuck procedure...")
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

        yield from Routines.Yield.wait(500)


def handle_sensali_danger(bot: Botting):
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
            GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName(JAYA_BLUFFS)
            and bot.config.build_handler.status == DervBuildFarmStatus.Move  # type: ignore
        ):
            if bot.config.pause_on_danger_fn() and get_sensali_array(Range.Spellcast.value):
                # Deal with local enemies before resuming
                yield from farm_sensalis(bot)
        yield from Routines.Yield.wait(500)


# endregion


def main_farm(bot: Botting):
    bot.Events.OnDeathCallback(lambda: on_death(bot))
    # override condition for halting movement

    bot.States.AddHeader('Starting Loop')
    if GLOBAL_CACHE.Map.GetMapID() != GLOBAL_CACHE.Map.GetMapIDByName(SEITUING_HARBOR):
        bot.Map.Travel(target_map_name=SEITUING_HARBOR)
        bot.Wait.ForMapLoad(target_map_name=SEITUING_HARBOR)
    bot.States.AddCustomState(lambda: load_skill_bar(bot), "Loading Skillbar")

    bot.Move.XY(17113, 12283, "Move close to Merch")
    bot.Interact.WithNpcAtXY(17290.00, 12426.00, "Interact with Merchant")
    bot.States.AddCustomState(buy_id_kits, 'Buying ID Kits')
    bot.States.AddCustomState(buy_salvage_kits, 'Buying Salvage Kits')

    bot.States.AddCustomState(identify_and_salvage_items, 'Salvaging Items')

    # Resign setup
    bot.States.AddCustomState(lambda: set_bot_to_setup(bot), "Setup Resign")
    bot.Move.XY(16570, 17713, "Exit Outpost for resign spot")
    bot.Wait.ForMapLoad(target_map_name=JAYA_BLUFFS)
    bot.Move.XY(11962, -14017, "Setup resign spot")
    bot.Wait.ForMapLoad(target_map_name=SEITUING_HARBOR)

    # Actual Farming Loop
    bot.States.AddHeader('Farm Loop')
    bot.config.set_pause_on_danger_fn(detect_sensali_or_loot)
    bot.Properties.Enable("auto_combat")
    bot.Properties.Enable("pause_on_danger")
    bot.States.AddCustomState(return_to_outpost, "Return to Seitung Harbor")
    bot.Wait.ForMapLoad(target_map_name=SEITUING_HARBOR)
    bot.States.AddManagedCoroutine(HANDLE_STUCK, lambda: handle_stuck(bot))
    bot.States.AddManagedCoroutine(HANDLE_SENSALI_DANGER, lambda: handle_sensali_danger(bot))
    bot.States.AddCustomState(lambda: set_bot_to_move(bot), "Exit Outpost To Farm")
    bot.Move.XY(16570, 17713, "Exit Outpost To Farm")
    bot.Wait.ForMapLoad(target_map_name=JAYA_BLUFFS)

    bot.Move.XY(9000, -12680, 'Run 1')
    bot.Move.XY(7588, -10609, 'Run 2')

    bot.Move.XY(2900, -9700, 'Move spot 1')
    bot.Move.XY(1540, -6995, 'Move spot 2')

    bot.Move.XY(-472, -4342, 'Move to Kill Spot 1')
    bot.States.AddCustomState(lambda: farm_sensalis(bot, kill_immediately=True), "Killing Sensalis Immediately")

    bot.Move.XY(-1536, -1686, "Move to Kill Spot 2")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(586, -76, "Move to Kill Spot 3")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-1556, 2786, "Move to Kill Spot 4")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-2229, -815, "Move to Kill Spot 5")
    bot.States.AddCustomState(lambda: farm_sensalis(bot, kill_immediately=True), "Killing Sensalis Immediately")

    bot.Move.XY(-5247, -3290, "Move to Kill Spot 6")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-6994, -2273, "Move to Kill Spot 7")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-5042, -6638, "Move to Kill Spot 8")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-11040, -8577, "Move to Kill Spot 9")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-10860, -2840, "Move to Kill Spot 10")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-14900, -3000, "Move to Kill Spot 11")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-12200, 150, "Move to Kill Spot 12")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-12500, 4000, "Move to Kill Spot 13")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-12111, 1690, "Move to Kill Spot 14")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-10303, 4110, "Move to Kill Spot 15")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-10500, 5500, "Move to Kill Spot 16")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.Move.XY(-9700, 2400, "Move to Kill Spot 17")
    bot.States.AddCustomState(lambda: farm_sensalis(bot), "Killing Sensalis")

    bot.States.AddCustomState(lambda: set_bot_to_wait(bot), "Waiting to return")

    bot.States.AddHeader('ID and Salvage at the End')
    bot.States.AddCustomState(identify_and_salvage_items, "ID and Salvage loot")
    bot.States.AddCustomState(reset_looted_areas, "Reset looted areas")

    bot.Party.Resign()
    bot.Wait.ForTime(3000)
    bot.Wait.UntilCondition(lambda: GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()))


bot.SetMainRoutine(main_farm)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path="Feather_art.png")


if __name__ == "__main__":
    main()
