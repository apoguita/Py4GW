from Py4GWCoreLib.Builds.DervFeatherFarmer import SENSALI_MODEL_IDS
from Py4GWCoreLib.Builds.DervFeatherFarmer import DervBuildFarmStatus
from Py4GWCoreLib.Builds.DervFeatherFarmer import DervFeatherFarmer
from Py4GWCoreLib import *

FEATHER_FARMER = "Feather Farmer"
SEITUING_HARBOR = "Seitung Harbor"
VIABLE_LOOT = {
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
    ModelID.Vial_Of_Absinthe,
    ModelID.Witchs_Brew,
    ModelID.Zehtukas_Jug,
    ModelID.Aged_Dwarven_Ale,
    ModelID.Bottle_Of_Grog,
    ModelID.Krytan_Brandy,
    ModelID.Spiked_Eggnog,
}

bot = Botting(
    FEATHER_FARMER,
    custom_build=DervFeatherFarmer(),
    config_movement_timeout=15000,
    config_movement_tolerance=600,  # Can get stuck before it reaches the point, but good enough to fight sensalis in the area
    upkeep_auto_inventory_management_active=False,
    upkeep_auto_loot_active=False,
    upkeep_auto_combat_active=False,
)
stuck_timer = ThrottledTimer(3000)
movement_check_timer = ThrottledTimer(4000)
stuck_counter = 0
old_player_position = (0, 0)
is_looting = False
# Globals for loot detection state
loot_window_timer = ThrottledTimer(5000)  # 5s window
loot_cooldown_timer = ThrottledTimer(5000)  # 5s cooldown
loot_window_active = False
loot_on_cooldown = False


def return_to_outpost():
    yield from Routines.Yield.wait(4000)
    is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
    is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
    is_explorable = GLOBAL_CACHE.Map.IsExplorable()
    is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated()

    if is_map_ready and is_party_loaded and is_explorable and is_party_defeated:
        GLOBAL_CACHE.Party.ReturnToOutpost()
        yield from Routines.Yield.wait(4000)


def get_valid_loot_array():
    loot_array = AgentArray.GetItemArray()
    loot_array = AgentArray.Filter.ByDistance(loot_array, GLOBAL_CACHE.Player.GetXY(), Range.Spellcast.value)

    filtered_agent_ids = []
    for agent_id in loot_array[:]:  # Iterate over a copy to avoid modifying while iterating
        item_data = Agent.GetItemAgent(agent_id)
        item_id = item_data.item_id
        model_id = Item.GetModelID(item_id)
        if model_id in VIABLE_LOOT:
            # Black and White Dyes
            if model_id == ModelID.Vial_Of_Dye and (
                GLOBAL_CACHE.Item.GetDyeColor(item_id) == 10 or GLOBAL_CACHE.Item.GetDyeColor(item_id) == 12
            ):
                filtered_agent_ids.append(agent_id)
            else:
                filtered_agent_ids.append(agent_id)
    return filtered_agent_ids


def detect_sensali_or_loot():
    global loot_window_active, loot_on_cooldown

    filtered_agent_ids = get_valid_loot_array()
    px, py = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, Range.Area.value * 1.50)
    sensali_array = [
        agent_id for agent_id in enemy_array if GLOBAL_CACHE.Agent.GetModelID(agent_id) in SENSALI_MODEL_IDS
    ]

    # Sensali always take priority — return True immediately
    if sensali_array:
        return True

    # --- Handle loot window / cooldown state ---
    if filtered_agent_ids and not loot_on_cooldown and not loot_window_active:
        # Start loot window
        loot_window_active = True
        loot_window_timer.Reset()

    if loot_window_active:
        if loot_window_timer.IsExpired():
            # End loot window, start cooldown
            loot_window_active = False
            loot_on_cooldown = True
            loot_cooldown_timer.Reset()
        else:
            # Still inside loot window (force True)
            return True

    if loot_on_cooldown:
        if loot_cooldown_timer.IsExpired():
            loot_on_cooldown = False
        else:
            # Still in cooldown (force False)
            return False

    # Normal behavior outside window/cooldown
    return bool(filtered_agent_ids)


def ball_sensalis(bot):
    px, py = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, Range.Spellcast.value)
    if not sum(1 for agent_id in enemy_array if GLOBAL_CACHE.Agent.GetModelID(agent_id) in SENSALI_MODEL_IDS):
        return False

    ConsoleLog(FEATHER_FARMER, 'Balling all Sensalis...')
    bot.config.build_handler.status = DervBuildFarmStatus.Ball
    yield from Routines.Yield.wait(100)

    elapsed = 0
    while elapsed < 30:  # 50 * 100ms = 3s
        # Player position
        px, py = GLOBAL_CACHE.Player.GetXY()

        # Enemies nearby
        enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, Range.Adjacent.value)
        player_hp = GLOBAL_CACHE.Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID())
        if player_hp < 0.80:
            return True

        ball_count = sum(1 for agent_id in enemy_array if GLOBAL_CACHE.Agent.GetModelID(agent_id) in SENSALI_MODEL_IDS)

        if ball_count >= 3:
            ConsoleLog(FEATHER_FARMER, 'Sensalis ready to kill!')
            return True  # condition satisfied

        # wait 100ms
        yield from Routines.Yield.wait(100)
        elapsed += 1

    # timeout reached
    return False


def farm_sensalis(bot, kill_immediately=False):
    global is_looting
    # Auto detect if sensalis in the area
    px, py = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, Range.Spellcast.value)
    if not sum(1 for agent_id in enemy_array if GLOBAL_CACHE.Agent.GetModelID(agent_id) in SENSALI_MODEL_IDS):
        return

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
        px, py = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, Range.Spellcast.value)

        sensali_array = [
            agent_id for agent_id in enemy_array if GLOBAL_CACHE.Agent.GetModelID(agent_id) in SENSALI_MODEL_IDS
        ]

        if len(sensali_array) == 0:
            bot.config.build_handler.status = DervBuildFarmStatus.Move
            if not is_looting:  # prevent calling loot_items twice on subsequent farm_sensali calls
                is_looting = True
                bot.Dialogs._disable_auto_combat()
                yield from Routines.Yield.wait(2000)  # Wait for a second before starting to loot
                ConsoleLog(FEATHER_FARMER, 'No more Sensalis, looting')
                yield from loot_items()
                yield from Routines.Yield.wait(2000)
                is_looting = False
                bot.Dialogs._restore_auto_combat()
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
    yield from Routines.Yield.wait(100)


def death_callback(bot):
    bot.Party.Resign()
    bot.States.AddCustomState(return_to_outpost, "Return to Seitung Harbor")
    bot.States.JumpToStepName("[H]Farm Loop_2")


def loot_items():
    yield from Routines.Yield.wait(1500)  # Wait for a second before starting to loot
    filtered_agent_ids = get_valid_loot_array()
    yield from Routines.Yield.Items.LootItems(filtered_agent_ids)


def identify_and_salvage_items():
    yield from Routines.Yield.wait(1500)
    yield from AutoInventoryHandler().IDAndSalvageItems()


def buy_id_kits():
    yield from Routines.Yield.wait(1500)
    kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit)
    print(kits_in_inv)
    if kits_in_inv < 3:
        yield from Routines.Yield.Merchant.BuyIDKits(3)


def buy_salvage_kits():
    yield from Routines.Yield.wait(1500)
    kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit)
    print(kits_in_inv)
    if kits_in_inv <= 3:
        yield from Routines.Yield.Merchant.BuySalvageKits(10)


def is_inventory_ready():
    salv_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit)
    id_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit)
    free_slots = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
    if salv_kits_in_inv < 3 or id_kits_in_inv == 0 or free_slots < 4:
        return False
    return True


def handle_stuck(bot):
    global stuck_timer
    global movement_check_timer
    global old_player_position
    global stuck_counter

    while True:
        # Wait until map is valid
        if not Routines.Checks.Map.MapValid() and Routines.Checks.Map:
            yield from Routines.Yield.wait(1000)
            continue

        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            return

        if GLOBAL_CACHE.Map.GetMapID() == 196 and bot.config.build_handler.status == DervBuildFarmStatus.Move:
            if stuck_timer.IsExpired():
                GLOBAL_CACHE.Player.SendChatCommand("stuck")
                stuck_timer.Reset()

            # Check if character hasn't moved
            if movement_check_timer.IsExpired():
                current_player_pos = GLOBAL_CACHE.Player.GetXY()
                if old_player_position == current_player_pos:
                    stuck_counter += 1
                    player_pos = GLOBAL_CACHE.Player.GetXY()
                    facing_direction = GLOBAL_CACHE.Agent.GetRotationAngle(GLOBAL_CACHE.Player.GetAgentID())

                    enemy_array = Routines.Agents.GetFilteredEnemyArray(
                        player_pos[0], player_pos[1], Range.Spellcast.value
                    )
                    if (
                        sum(
                            1
                            for agent_id in enemy_array
                            if GLOBAL_CACHE.Agent.GetModelID(agent_id) in SENSALI_MODEL_IDS
                        )
                        >= 3
                    ):
                        # Deal with local enemies before resuming
                        yield from farm_sensalis(bot, kill_immediately=True)
                    else:
                        # --- Backpedal (opposite facing direction) ---
                        back_angle = facing_direction + math.pi  # 180° behind
                        back_distance = 200
                        back_offset_x = math.cos(back_angle) * back_distance
                        back_offset_y = math.sin(back_angle) * back_distance

                        backpedal_pos = (player_pos[0] + back_offset_x, player_pos[1] + back_offset_y)
                        for _ in range(3):
                            GLOBAL_CACHE.Player.Move(backpedal_pos[0], backpedal_pos[1])

                        # --- Sidestep (left of facing direction) ---
                        left_angle = facing_direction + math.pi / 2
                        side_distance = 200
                        offset_x = math.cos(left_angle) * side_distance
                        offset_y = math.sin(left_angle) * side_distance

                        sidestep_pos = (player_pos[0] + offset_x, player_pos[1] + offset_y)
                        for _ in range(3):
                            GLOBAL_CACHE.Player.Move(sidestep_pos[0], sidestep_pos[1])

                    yield
                else:
                    old_player_position = current_player_pos
                    stuck_timer.Reset()
                    stuck_counter = 0

                movement_check_timer.Reset()

            # Hard reset if too many consecutive stuck detections
            if stuck_counter >= 10:
                print("Too many stuck detections, forcing reset.")
                stuck_counter = 0
                fsm = bot.config.FSM
                yield from fsm._reset_execution()

        yield from Routines.Yield.wait(500)


def load_skill_bar(bot):
    yield from bot.config.build_handler.LoadSkillBar()


def main_farm(bot):
    # override condition for halting movement
    bot.config.set_pause_on_danger_fn(detect_sensali_or_loot)
    bot.Properties.Enable("auto_combat")
    bot.Properties.Enable("pause_on_danger")
    bot.Events.OnDeathCallback(lambda: death_callback(bot))
    bot.States.AddManagedCoroutine('Stuck handler', lambda: handle_stuck(bot))

    bot.States.AddHeader('Starting Loop')
    map_id = GLOBAL_CACHE.Map.GetMapID()
    if map_id != 250:
        bot.Map.Travel(target_map_name=SEITUING_HARBOR)
        bot.Wait.ForMapLoad(target_map_name=SEITUING_HARBOR)
    bot.States.AddCustomState(lambda: load_skill_bar(bot), "Loading Skillbar")

    if not is_inventory_ready():
        bot.Move.XY(17113, 12283, "Move close to Merch")
        bot.Interact.WithNpcAtXY(17290.00, 12426.00, "Interact with Merchant")
        bot.States.AddCustomState(buy_id_kits, 'Buying ID Kits')
        bot.States.AddCustomState(buy_salvage_kits, 'Buying Salvage Kits')

    bot.States.AddCustomState(identify_and_salvage_items, 'Salvaging Items')

    # Resign setup
    bot.Move.XY(16570, 17713, "Exit Outpost for resign spot")
    bot.Wait.ForMapLoad(target_map_name="Jaya Bluffs")
    bot.Move.XY(11962, -14017, "Setup resign spot")
    bot.Wait.ForMapLoad(target_map_name=SEITUING_HARBOR)

    # Actual Farming Loop
    bot.States.AddHeader('Farm Loop')
    bot.Move.XY(16570, 17713, "Exit Outpost To Farm")
    bot.Wait.ForMapLoad(target_map_name="Jaya Bluffs")

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

    bot.States.AddHeader('ID and Salvage at the End')
    bot.States.AddCustomState(identify_and_salvage_items, "ID and Salvage loot")

    # Manually resign and jumpt to state, instead of lambda
    bot.Party.Resign()
    bot.States.AddCustomState(return_to_outpost, "Return to Seitung Harbor")
    bot.States.JumpToStepName("[H]Farm Loop_2")


bot.SetMainRoutine(main_farm)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path="Feather_art.png")


if __name__ == "__main__":
    main()
