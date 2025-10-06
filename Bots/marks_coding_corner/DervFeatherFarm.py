import random

from Bots.marks_coding_corner.utils.loot_utils import VIABLE_LOOT
from Bots.marks_coding_corner.utils.loot_utils import get_valid_loot_array
from Bots.marks_coding_corner.utils.loot_utils import identify_and_salvage_items
from Bots.marks_coding_corner.utils.loot_utils import move_all_crafting_materials_to_storage
from Bots.marks_coding_corner.utils.merch_utils import buy_id_kits
from Bots.marks_coding_corner.utils.merch_utils import buy_salvage_kits
from Bots.marks_coding_corner.utils.merch_utils import sell_non_essential_mats
from Bots.marks_coding_corner.utils.merch_utils import withdraw_gold
from Bots.marks_coding_corner.utils.town_utils import return_to_outpost
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import *
from Py4GWCoreLib.Builds.DervFeatherFarmer import SENSALI_MODEL_IDS
from Py4GWCoreLib.Builds.DervFeatherFarmer import DervBuildFarmStatus
from Py4GWCoreLib.Builds.DervFeatherFarmer import DervFeatherFarmer

FEATHER_FARMER = "Feather Farmer"
SEITUING_HARBOR = "Seitung Harbor"
JAYA_BLUFFS = "Jaya Bluffs"

# handler constants
HANDLE_STUCK = 'handle_stuck'
HANDLE_LOOT = 'handle_loot'
HANDLE_SENSALI_DANGER = 'handle_sensali_danger'
KILL_SPOTS = [
    (-472, -4342, True),
    (-1536, -1686, False),
    (586, -76, False),
    (-1556, 2786, False),
    (-2229, -815, True),
    (-5247, -3290, False),
    (-6994, -2273, False),
    (-5042, -6638, False),
    (-11040, -8577, False),
    (-10860, -2840, False),
    (-14900, -3000, False),
    (-12200, 150, False),
    (-12500, 4000, False),
    (-12111, 1690, False),
    (-10303, 4110, False),
    (-10500, 5500, False),
    (-9700, 2400, False),
]

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
unmanaged_fail_counter = 0
old_player_position = (0, 0)
item_id_blacklist = []
is_farming = False
is_looting = False


# region Direct Bot Actions

def load_skill_bar(bot: Botting):
    yield from bot.config.build_handler.LoadSkillBar()


def ball_sensalis(bot: Botting):
    all_sensali_array = get_sensali_array(custom_range=Range.Earshot.value)
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
    global is_looting
    global is_farming

    if is_farming:
        return

    # Auto detect if sensalis in the area
    sensali_array = get_sensali_array(custom_range=Range.Earshot.value)
    if not len(sensali_array):
        ConsoleLog('Farm Sensalis', 'No Sensali detected!')
        return

    ConsoleLog(FEATHER_FARMER, 'Farming...')
    is_farming = True
    if kill_immediately or get_non_sensali_array(custom_range=Range.Earshot.value):
        bot.config.build_handler.status = DervBuildFarmStatus.Kill
    else:
        yield from ball_sensalis(bot)
        bot.config.build_handler.status = DervBuildFarmStatus.Kill

    ConsoleLog(FEATHER_FARMER, 'Killing all Sensalis! None shall survive!')
    start_time = Utils.GetBaseTimestamp()
    timeout = 120000  # 2 minutes max

    player_id = GLOBAL_CACHE.Player.GetAgentID()

    while True:
        sensali_array = get_sensali_array(custom_range=Range.Earshot.value)
        if len(sensali_array) == 0:
            bot.config.build_handler.status = DervBuildFarmStatus.Move
            break  # all sensalis dead

        # Timeout check
        current_time = Utils.GetBaseTimestamp()
        if timeout > 0 and current_time - start_time > timeout:
            ConsoleLog(FEATHER_FARMER, 'Fight took too long, setting back to [Move] status')
            bot.config.build_handler.status = DervBuildFarmStatus.Move
            yield from Routines.Yield.wait(1000)
            yield from Routines.Yield.Player.Resign()
            return

        # Death check
        if GLOBAL_CACHE.Agent.IsDead(player_id):
            # handle death here
            ConsoleLog(FEATHER_FARMER, 'Died fighting, setting back to [Move] status')
            bot.config.build_handler.status = DervBuildFarmStatus.Move
            return

        yield from Routines.Yield.wait(100)

    ConsoleLog(FEATHER_FARMER, 'Finished farming.')
    is_farming = False
    yield from Routines.Yield.wait(100)


def loot_items():
    global item_id_blacklist
    filtered_agent_ids = get_valid_loot_array(viable_loot=VIABLE_LOOT)
    yield from Routines.Yield.wait(500)  # Wait for a second before starting to loot
    ConsoleLog(FEATHER_FARMER, 'Looting items...')
    failed_items_id = yield from Routines.Yield.Items.LootItemsWithMaxAttempts(filtered_agent_ids, log=True)
    if failed_items_id:
        item_id_blacklist = item_id_blacklist + failed_items_id
    ConsoleLog(FEATHER_FARMER, 'Looting items finished')
    yield


# endregion


# region Helper Methods
def get_sensali_array(custom_range=Range.Area.value * 1.50):
    px, py = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, custom_range)
    return [agent_id for agent_id in enemy_array if GLOBAL_CACHE.Agent.GetModelID(agent_id) in SENSALI_MODEL_IDS]


def get_non_sensali_array(custom_range=Range.Area.value * 1.50):
    px, py = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, custom_range)
    return [agent_id for agent_id in enemy_array if GLOBAL_CACHE.Agent.GetModelID(agent_id) not in SENSALI_MODEL_IDS]


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


def detect_sensali_or_loot():
    global item_id_blacklist
    # 1. Sensali always take priority
    sensali_array = get_sensali_array()
    if sensali_array:
        return True

    # 2. Loot check
    filtered_agent_ids = get_valid_loot_array(viable_loot=VIABLE_LOOT)
    if not filtered_agent_ids:
        return False

    # Apply blacklist filter
    filtered_agent_ids = [agent_id for agent_id in filtered_agent_ids if agent_id not in set(item_id_blacklist)]

    if not filtered_agent_ids:
        return False

    return True


def _on_death(bot: Botting):
    ConsoleLog(FEATHER_FARMER, "Waiting for a moment reset...")
    yield from Routines.Yield.wait(1000)
    ident_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit)
    sup_ident_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit)
    salv_kits_in_inv = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit)
    free_slot_count = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
    fsm = bot.config.FSM
    if (ident_kits_in_inv + sup_ident_kits_in_inv) == 0 or salv_kits_in_inv == 0 or free_slot_count < 2:
        fsm.jump_to_state_by_name("[H]Starting Loop_1")
    else:
        fsm.jump_to_state_by_name("[H]Farm Loop_2")
    fsm.resume()
    yield


def on_death(bot: Botting):
    ConsoleLog(FEATHER_FARMER, "Player is dead. Restarting...")
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
                continue

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
                continue

        yield from Routines.Yield.wait(500)


def handle_sensali_danger(bot: Botting):
    while True:
        # Wait until map is valid
        if not Routines.Checks.Map.MapValid() and not Routines.Checks.Map.IsExplorable():
            yield from Routines.Yield.wait(1000)
            continue

        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            yield from Routines.Yield.wait(1000)
            continue

        if (
            GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName(JAYA_BLUFFS)
            and bot.config.build_handler.status == DervBuildFarmStatus.Move  # type: ignore
        ):
            if bot.config.pause_on_danger_fn() and get_sensali_array(Range.Spellcast.value):
                # Deal with local enemies before resuming
                yield from farm_sensalis(bot)
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
            GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName(JAYA_BLUFFS)
            and bot.config.build_handler.status == DervBuildFarmStatus.Move  # type: ignore
        ):
            if bot.config.pause_on_danger_fn() and get_valid_loot_array(viable_loot=VIABLE_LOOT):
                if not is_looting:
                    is_looting = True
                    ConsoleLog(FEATHER_FARMER, 'Setting to [Loot] status')
                    bot.config.build_handler.status = DervBuildFarmStatus.Loot  # type: ignore
                    yield from Routines.Yield.wait(500)
                    yield from loot_items()
                    yield from Routines.Yield.wait(500)
                    ConsoleLog(FEATHER_FARMER, 'Setting back to [Move] status')
                    bot.config.build_handler.status = DervBuildFarmStatus.Move  # type: ignore
                    # log from the last epicenter of the begining of the farm
                    is_looting = False

        yield from Routines.Yield.wait(500)


def _force_reset(bot: Botting):
    global unmanaged_fail_counter
    unmanaged_fail_counter += 1
    ConsoleLog(FEATHER_FARMER, f"Something went wrong forcing a reset... Attempt: {unmanaged_fail_counter}")
    yield from Routines.Yield.wait(1000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Starting Loop_1")
    fsm.resume()
    yield


def handle_custom_on_unmanaged_fail(bot: Botting):
    global unmanaged_fail_counter

    ConsoleLog(FEATHER_FARMER, "Handling explorable mode unmanaged error...")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("Force Reset", _force_reset(bot))

    if unmanaged_fail_counter > 5:
        return True
    return False


# endregion


def feather_farm_bot(bot: Botting):
    widget_handler = get_widget_handler()
    widget_handler.disable_widget('Return to outpost on defeat')

    bot.Events.OnDeathCallback(lambda: on_death(bot))
    bot.helpers.Events.set_on_unmanaged_fail(lambda: handle_custom_on_unmanaged_fail(bot))
    # override condition for halting movement

    bot.States.AddHeader('Starting Loop')
    bot.Map.Travel(target_map_name=SEITUING_HARBOR)
    bot.States.AddCustomState(lambda: load_skill_bar(bot), "Loading Skillbar")

    bot.Move.XY(17113, 12283, "Move close to Merch")
    bot.Interact.WithNpcAtXY(17290.00, 12426.00, "Interact with Merchant")
    bot.States.AddCustomState(withdraw_gold, "Fill inventory with gold")
    bot.States.AddCustomState(sell_non_essential_mats, "Sell non-essential Materials")
    bot.States.AddCustomState(buy_id_kits, 'Buying ID Kits')
    bot.States.AddCustomState(lambda: buy_salvage_kits(custom_amount=10), 'Buying Salvage Kits')

    bot.States.AddCustomState(identify_and_salvage_items, 'Salvaging Items')
    bot.States.AddCustomState(move_all_crafting_materials_to_storage, "Move crafting materials to storage")

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
    bot.States.AddCustomState(return_to_outpost, "Return to Seitung Harbor if Dead")
    bot.Wait.ForTime(2000)
    bot.Wait.ForMapLoad(target_map_name=SEITUING_HARBOR)
    bot.States.AddManagedCoroutine(HANDLE_STUCK, lambda: handle_stuck(bot))
    bot.States.AddManagedCoroutine(HANDLE_LOOT, lambda: handle_loot(bot))
    bot.States.AddManagedCoroutine(HANDLE_SENSALI_DANGER, lambda: handle_sensali_danger(bot))
    bot.States.AddCustomState(lambda: set_bot_to_move(bot), "Exit Outpost To Farm")
    bot.Move.XY(16570, 17713, "Exit Outpost To Farm")
    bot.Wait.ForMapLoad(target_map_name=JAYA_BLUFFS)

    for index, move_location in enumerate([(9000, -12680), (7588, -10609), (2900, -9700), (1540, -6995)]):
        x, y = move_location
        bot.Move.XY(x, y, f'Run # {index + 1}')

    for index, (x, y, kill_immediately) in enumerate(KILL_SPOTS):
        bot.Move.XY(x, y, f'Move to Kill Spot {index + 1}')
        bot.States.AddCustomState(lambda: farm_sensalis(bot, kill_immediately=kill_immediately), 'Killing Sensalis')

    bot.States.AddCustomState(lambda: set_bot_to_wait(bot), "Waiting to return")

    bot.States.AddHeader('ID and Salvage at the End')
    bot.States.AddCustomState(identify_and_salvage_items, "ID and Salvage loot")
    bot.States.AddCustomState(reset_item_id_blacklist, "Reset looting")

    bot.Party.Resign()
    bot.Wait.ForTime(3000)
    bot.Wait.UntilCondition(lambda: GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()))


bot.SetMainRoutine(feather_farm_bot)


def main():
    bot.Update()
    TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "marks_coding_corner", "textures" , "feather_art.png")
    bot.UI.draw_window(icon_path=TEXTURE)


if __name__ == "__main__":
    main()
