import math
from typing import List
from typing import Tuple

import Py4GW
from Bots.marks_coding_corner.utils.loot_utils import VIABLE_LOOT
from Bots.marks_coding_corner.utils.loot_utils import get_valid_loot_array
from Bots.marks_coding_corner.utils.loot_utils import move_all_crafting_materials_to_storage
from Bots.marks_coding_corner.utils.loot_utils import set_autoloot_options_for_custom_bots
from Bots.marks_coding_corner.utils.merch_utils import sell_non_essential_mats
from Bots.marks_coding_corner.utils.merch_utils import withdraw_gold
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import Botting
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import Utils
from Py4GWCoreLib.BuildMgr import BuildMgr
from Py4GWCoreLib.Builds import SF_Ass_vaettir
from Py4GWCoreLib.Builds import SF_Mes_vaettir
from Py4GWCoreLib.enums import ModelID
from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.enums import TitleID

VAETTIR_FARM_BY_MARK = "Vaettir By Mark"
HANDLE_STUCK_JAGA_MORAINE = "HandleStuckJagaMoraine"

bot = Botting(
    VAETTIR_FARM_BY_MARK,
    upkeep_birthday_cupcake_restock=1,
    config_movement_tolerance=200,
    upkeep_salvage_kits_restock=10,
    upkeep_identify_kits_restock=1,
)
item_id_blacklist = []
unmanaged_fail_counter = 0


def create_bot_routine(bot: Botting) -> None:
    town_routines(bot)
    traverse_bjora_marches(bot)
    jaga_moraine_farm_routine(bot)
    reset_farm_loop(bot)


def initialize_bot(bot: Botting) -> None:
    widget_handler = get_widget_handler()
    widget_handler.disable_widget('Return to outpost on defeat')
    set_autoloot_options_for_custom_bots(salvage_golds=True, module_active=False)

    bot.helpers.Events.set_on_unmanaged_fail(lambda: handle_custom_on_unmanaged_fail(bot))
    bot.Events.OnDeathCallback(lambda: on_death(bot))
    bot.States.AddHeader("Initialize Bot")
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Disable("auto_loot")
    bot.Properties.Disable("hero_ai")
    bot.Properties.Enable("auto_combat")
    bot.Properties.Disable("pause_on_danger")
    bot.Properties.Enable("halt_on_death")
    bot.Properties.Set("movement_timeout", value=-1)
    bot.Properties.Enable("birthday_cupcake")
    bot.Properties.Enable("identify_kits")
    bot.Properties.Enable("salvage_kits")


def town_routines(bot: Botting) -> None:
    bot.States.AddHeader("Town Routines")
    bot.Map.Travel(target_map_name="Longeyes Ledge")
    initialize_bot(bot)
    bot.States.AddCustomState(lambda: equip_skillbar(bot), "Equip SkillBar")
    handle_inventory(bot)
    bot.States.AddHeader("Exit to Bjora Marches")
    bot.Party.SetHardMode(True)  # set hard mode on
    bot.Move.XYAndExitMap(-26375, 16180, target_map_name="Bjora Marches")


def traverse_bjora_marches(bot: Botting) -> None:
    bot.States.AddHeader("Traverse Bjora Marches")
    bot.Player.SetTitle(TitleID.Norn.value)
    path_points_to_traverse_bjora_marches: List[Tuple[float, float]] = [
        (17810, -17649),
        (17516, -17270),
        (17166, -16813),
        (16862, -16324),
        (16472, -15934),
        (15929, -15731),
        (15387, -15521),
        (14849, -15312),
        (14311, -15101),
        (13776, -14882),
        (13249, -14642),
        (12729, -14386),
        (12235, -14086),
        (11748, -13776),
        (11274, -13450),
        (10839, -13065),
        (10572, -12590),
        (10412, -12036),
        (10238, -11485),
        (10125, -10918),
        (10029, -10348),
        (9909, -9778),
        (9599, -9327),
        (9121, -9009),
        (8674, -8645),
        (8215, -8289),
        (7755, -7945),
        (7339, -7542),
        (6962, -7103),
        (6587, -6666),
        (6210, -6226),
        (5834, -5788),
        (5457, -5349),
        (5081, -4911),
        (4703, -4470),
        (4379, -3990),
        (4063, -3507),
        (3773, -3031),
        (3452, -2540),
        (3117, -2070),
        (2678, -1703),
        (2115, -1593),
        (1541, -1614),
        (960, -1563),
        (388, -1491),
        (-187, -1419),
        (-770, -1426),
        (-1343, -1440),
        (-1922, -1455),
        (-2496, -1472),
        (-3073, -1535),
        (-3650, -1607),
        (-4214, -1712),
        (-4784, -1759),
        (-5278, -1492),
        (-5754, -1164),
        (-6200, -796),
        (-6632, -419),
        (-7192, -300),
        (-7770, -306),
        (-8352, -286),
        (-8932, -258),
        (-9504, -226),
        (-10086, -201),
        (-10665, -215),
        (-11247, -242),
        (-11826, -262),
        (-12400, -247),
        (-12979, -216),
        (-13529, -53),
        (-13944, 341),
        (-14358, 743),
        (-14727, 1181),
        (-15109, 1620),
        (-15539, 2010),
        (-15963, 2380),
        (-18048, 4223),
        (-19196, 4986),
        (-20000, 5595),
        (-20300, 5600),
    ]
    bot.Move.FollowPathAndExitMap(path_points_to_traverse_bjora_marches, target_map_name="Jaga Moraine")


def jaga_moraine_farm_routine(bot: Botting) -> None:
    def _follow_and_wait(path_points: List[Tuple[float, float]], wait_state_name: str, cycle_timeout: int = 150):
        bot.Move.FollowPath(path_points)
        bot.States.AddCustomState(
            lambda: wait_for_ball(bot, wait_state_name, cycle_timeout), f"Wait for {wait_state_name}"
        )

    bot.States.AddHeader("Jaga Moraine Farm Routine")
    initialize_bot(bot)
    bot.States.AddCustomState(lambda: assign_build(bot), "Assign Build")
    bot.Move.XY(13372.44, -20758.50)
    bot.Dialogs.AtXY(13367, -20771, 0x84)
    bot.States.AddManagedCoroutine(HANDLE_STUCK_JAGA_MORAINE, lambda: handle_stuck_jaga_moraine(bot))
    path: List[Tuple[float, float]] = [
        (13367, -20771),
        (11375, -22761),
        (10925, -23466),
        (10917, -24311),
        (10280, -24620),
        (10280, -24620),
        (9640, -23175),
        (7815, -23200),
        (6626.51, -23167.24),
    ]
    _follow_and_wait(path, "Inner Packs", cycle_timeout=75)

    path: List[Tuple[float, float]] = [
        (7765, -22940),
        (8213, -22829),
        (8740, -22475),
        (8880, -21384),
        (8684, -20833),
        (8982, -20576),
    ]
    bot.States.AddHeader("Wait for Left Aggro Ball")
    _follow_and_wait(path, "Left Aggro Ball")

    path: List[Tuple[float, float]] = [
        (10196, -20124),
        (10123, -19529),
        (10049, -18933),
    ]
    _follow_and_wait(path, "log side packs", cycle_timeout=75)
    path: List[Tuple[float, float]] = [
        (9976, -18338),
        (11316, -18056),
        (10392, -17512),
        (10114, -16948),
    ]
    _follow_and_wait(path, "Big Pack")

    path = [
        (10729, -16273),
        (10505, -14750),
        (10815, -14790),
        (11090, -15345),
        (11670, -15457),
        (12604, -15320),
        (12450, -14800),
        (12725, -14850),
        (12476, -16157),
    ]
    _follow_and_wait(path, "Right Aggro Ball")

    bot.Properties.Set("movement_tolerance", value=25)
    bot.Move.XY(13070, -16911, "Start Killing ball")
    bot.States.AddCustomState(
        lambda: wait_for_right_aggro_ball(bot, use_hos_after=False), "Wait for Right Aggro Ball Again"
    )
    path_points_to_killing_spot: List[Tuple[float, float]] = [
        (12938, -17081),
        (12790, -17201),
        (12747, -17220),
        (12703, -17239),
        (12684, -17184),
        (12485.18, -17260.41),
    ]
    bot.Move.FollowPath(path_points_to_killing_spot)
    bot.Properties.ResetTodefault("movement_tolerance")
    bot.States.AddHeader("Kill Enemies")
    bot.States.AddCustomState(lambda: kill_enemies(bot), "Kill Enemies")
    bot.Properties.Disable("auto_combat")
    bot.States.RemoveManagedCoroutine(HANDLE_STUCK_JAGA_MORAINE)
    bot.States.AddHeader("Loot Items")
    bot.States.AddCustomState(loot_items, "Custom Loot Items")
    bot.Items.AutoIDAndSalvageItems()
    bot.States.AddCustomState(lambda: needs_inventory_management(bot), "Needs Inventory Management")
    bot.Move.XYAndExitMap(15850, -20550, target_map_name="Bjora Marches")


def loot_items():
    global item_id_blacklist
    filtered_agent_ids = get_valid_loot_array(viable_loot=VIABLE_LOOT, loot_salvagables=False)
    yield from Routines.Yield.wait(500)  # Wait for a second before starting to loot
    ConsoleLog(VAETTIR_FARM_BY_MARK, 'Looting items...')
    failed_items_id = yield from Routines.Yield.Items.LootItemsWithMaxAttempts(filtered_agent_ids, log=True)
    if failed_items_id:
        item_id_blacklist = item_id_blacklist + failed_items_id
    ConsoleLog(VAETTIR_FARM_BY_MARK, 'Looting items finished')
    yield


def _reset_to_town(bot: Botting):
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Town Routines_1")
    fsm.resume()
    yield


def needs_inventory_management(bot: Botting):
    free_slots_in_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
    count_of_id_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value)
    count_of_salvage_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value)

    if free_slots_in_inventory < 4 or count_of_id_kits == 0 or count_of_salvage_kits == 0:
        ActionQueueManager().ResetAllQueues()
        fsm = bot.config.FSM
        fsm.pause()
        fsm.AddManagedCoroutine("ResetToTown", _reset_to_town(bot))
    yield


def reset_farm_loop(bot: Botting) -> None:
    bot.States.AddHeader("Reset Farm Loop")
    bot.Move.XYAndExitMap(-20300, 5600, target_map_name="Jaga Moraine")
    bot.States.JumpToStepName("[H]Jaga Moraine Farm Routine_6")


def kill_enemies(bot: Botting):
    global in_killing_routine
    in_killing_routine = True
    build = bot.config.build_handler
    if isinstance(build, SF_Ass_vaettir) or isinstance(build, SF_Mes_vaettir):
        build.SetKillingRoutine(in_killing_routine)

    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.Spellcast.value)

    start_time = Utils.GetBaseTimestamp()
    timeout = 120000

    while len(enemy_array) > 0:  # sometimes not all enemies are killed
        current_time = Utils.GetBaseTimestamp()
        delta = current_time - start_time
        if delta > timeout and timeout > 0:
            ConsoleLog("Killing Routine", "Timeout reached, restarting.", Py4GW.Console.MessageType.Error)
            fsm = bot.config.FSM
            fsm.jump_to_state_by_name("[H]Town Routines_1")
            return

        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            ConsoleLog("Killing Routine", "Player is dead, restarting.", Py4GW.Console.MessageType.Warning)
            fsm = bot.config.FSM
            fsm.jump_to_state_by_name("[H]Town Routines_1")
        yield from Routines.Yield.wait(1000)
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.Spellcast.value)

    in_killing_routine = False
    finished_routine = True
    if isinstance(build, SF_Ass_vaettir) or isinstance(build, SF_Mes_vaettir):
        build.SetKillingRoutine(False)
        build.SetRoutineFinished(finished_routine)
    ConsoleLog("Killing Routine", "Finished Killing Routine", Py4GW.Console.MessageType.Info)
    yield from Routines.Yield.wait(1000)  # Wait a bit to ensure the enemies are dead


def assign_build(bot: Botting):
    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    match profession:
        case "Assassin":
            bot.OverrideBuild(SF_Ass_vaettir())
        case "Mesmer":
            bot.OverrideBuild(SF_Mes_vaettir())  # Placeholder for Mesmer build
        case _:
            ConsoleLog(
                "Unsupported Profession",
                f"The profession '{profession}' is not supported by this bot.",
                Py4GW.Console.MessageType.Error,
            )
            bot.Stop()
            return
    yield


def equip_skillbar(bot: Botting):
    yield from assign_build(bot)
    yield from bot.config.build_handler.LoadSkillBar()


def handle_inventory(bot: Botting) -> None:
    bot.States.AddHeader("Inventory Handling")
    bot.Items.AutoIDAndSalvageItems()  # sort bags, auto id, salvage, deposit to bank
    bot.Move.XYAndInteractNPC(-23110, 14942)  # Merchant in Longeyes Ledge
    bot.Wait.ForTime(500)
    bot.States.AddCustomState(withdraw_gold, "Fill inventory with gold")
    bot.States.AddCustomState(sell_non_essential_mats, "Sell non-essential Materials")
    bot.Merchant.Restock.IdentifyKits()  # restock identify kits
    bot.Merchant.Restock.SalvageKits()  # restock salvage kits
    bot.Items.AutoIDAndSalvageItems()  # sort bags again to make sure everything is deposited
    bot.States.AddCustomState(sell_non_essential_mats, "Sell non-essential Materials")
    bot.States.AddCustomState(move_all_crafting_materials_to_storage, "Move materials to inventory")
    bot.Merchant.Restock.IdentifyKits()  # restock identify kits
    bot.Merchant.Restock.SalvageKits()  # restock salvage kits
    bot.Items.Restock.BirthdayCupcake()  # restock birthday cupcake


def _wait_for_aggro_ball(bot: Botting, side_label: str, cycle_timeout: int = 150):
    """
    Shared logic for waiting until enemies have balled up.
    side_label is just used for logging ("Left" / "Right").
    """
    global in_waiting_routine
    ConsoleLog(
        f"Waiting for {side_label} Aggro Ball", "Waiting for enemies to ball up.", Py4GW.Console.MessageType.Info
    )

    in_waiting_routine = True
    elapsed = 0
    build = bot.config.build_handler

    try:
        while elapsed < cycle_timeout:  # 150 * 100ms = 15s max
            yield from Routines.Yield.wait(100)
            elapsed += 1

            # hard exit if player dies
            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                ConsoleLog(
                    f"{side_label} Aggro Ball Wait", "Player is dead, exiting wait.", Py4GW.Console.MessageType.Warning
                )
                yield
                return

            # Get player position
            px, py = GLOBAL_CACHE.Player.GetXY()

            # Get enemies within earshot
            enemies_ids = Routines.Agents.GetFilteredEnemyArray(px, py, Range.Earshot.value)

            # Check if all enemies are within Adjacent range
            all_in_adjacent = True
            for enemy_id in enemies_ids:
                enemy = GLOBAL_CACHE.Agent.GetAgent(enemy_id)
                if enemy is None:
                    continue
                dx, dy = enemy.x - px, enemy.y - py
                if dx * dx + dy * dy > (Range.Adjacent.value**2):
                    all_in_adjacent = False
                    break

            if all_in_adjacent:
                ConsoleLog(
                    f"{side_label} Aggro Ball Wait", "Enemies balled up successfully.", Py4GW.Console.MessageType.Info
                )
                break  # exit early

        else:
            # ← executes only if loop ran full timeout
            ConsoleLog(
                f"{side_label} Aggro Ball Wait",
                f"Timeout reached {cycle_timeout * 100}ms, exiting without ball.",
                Py4GW.Console.MessageType.Warning,
            )

    finally:
        # Always reset, no matter why we exited
        in_waiting_routine = False

        # Resume build if applicable
        if isinstance(build, SF_Ass_vaettir) or isinstance(build, SF_Mes_vaettir):
            yield from build.CastHeartOfShadow()


def wait_for_ball(bot: Botting, side_label: str, cycle_timeout: int = 150):
    yield from _wait_for_aggro_ball(bot, side_label, cycle_timeout)


def wait_for_right_aggro_ball(bot: Botting, use_hos_after=True):
    global in_waiting_routine
    ConsoleLog("Waiting for Right Aggro Ball", "Waiting for enemies to ball up.", Py4GW.Console.MessageType.Info)

    in_waiting_routine = True

    elapsed = 0
    build = bot.config.build_handler

    while elapsed < 150:  # 150 * 100ms = 15s max
        yield from Routines.Yield.wait(100)
        elapsed += 1

        # Get player position
        px, py = GLOBAL_CACHE.Player.GetXY()

        # Get enemies within earshot
        enemies_ids = Routines.Agents.GetFilteredEnemyArray(px, py, Range.Earshot.value)

        # Check if all enemies are within Adjacent range
        all_in_adjacent = True
        for enemy_id in enemies_ids:
            enemy = GLOBAL_CACHE.Agent.GetAgent(enemy_id)
            if enemy is None:
                continue
            dx, dy = enemy.x - px, enemy.y - py
            if dx * dx + dy * dy > (Range.Adjacent.value**2):
                all_in_adjacent = False
                break

        player_hp = GLOBAL_CACHE.Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID())
        if all_in_adjacent and player_hp > 0.45:
            break  # Exit early if enemies are balled up

    in_waiting_routine = False

    # Resume build
    if isinstance(build, SF_Ass_vaettir) or isinstance(build, SF_Mes_vaettir) and use_hos_after:
        yield from build.CastHeartOfShadow()


# region Events
def _on_death(bot: Botting):
    ConsoleLog(VAETTIR_FARM_BY_MARK, "Waiting for a moment reset...")
    yield from Routines.Yield.wait(1000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Town Routines_1")
    fsm.resume()
    yield


def on_death(bot: Botting):
    ConsoleLog(VAETTIR_FARM_BY_MARK, "Player is dead. Restarting...")
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))


# region Handlers
in_waiting_routine = False
finished_routine = False
stuck_counter = 0
stuck_timer = ThrottledTimer(3000)
stuck_timer.Start()
BJORA_MARCHES = GLOBAL_CACHE.Map.GetMapIDByName("Bjora Marches")
JAGA_MORAINE = GLOBAL_CACHE.Map.GetMapIDByName("Jaga Moraine")
movement_check_timer = ThrottledTimer(5000)
old_player_position = (0, 0)
in_killing_routine = False


def handle_stuck_jaga_moraine(bot: Botting):
    global in_waiting_routine
    global finished_routine
    global stuck_counter
    global stuck_timer
    global movement_check_timer
    global old_player_position
    global in_killing_routine

    ConsoleLog("Stuck Detection", "Starting Stuck Detection Coroutine.", Py4GW.Console.MessageType.Info, True)

    def is_within_tolerance(pos1, pos2, tolerance=100):
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        distance = math.hypot(dx, dy)  # sqrt(dx^2 + dy^2)
        return distance <= tolerance

    while True:
        if not Routines.Checks.Map.MapValid():
            ConsoleLog("Stuck Detection", "Map is not valid, waiting...", Py4GW.Console.MessageType.Debug, False)
            yield from Routines.Yield.wait(1000)
            continue

        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            ConsoleLog(
                "Stuck Detection", "Player is dead, exiting stuck handler.", Py4GW.Console.MessageType.Debug, False
            )
            yield from Routines.Yield.wait(1000)
            continue

        build: BuildMgr = bot.config.build_handler

        instance_time = GLOBAL_CACHE.Map.GetInstanceUptime() / 1000  # Convert ms to seconds
        if instance_time > 7 * 60:  # 7 minutes in seconds
            ConsoleLog(
                "HandleStuck",
                "Instance time exceeded 7 minutes, force resigning.",
                Py4GW.Console.MessageType.Debug,
                True,
            )
            stuck_counter = 0
            if isinstance(build, SF_Ass_vaettir) or isinstance(build, SF_Mes_vaettir):
                build.SetStuckSignal(stuck_counter)

            GLOBAL_CACHE.Player.SendChatCommand("resign")

            yield from Routines.Yield.wait(500)
            return

        # Waiting routine check
        if in_waiting_routine:
            ConsoleLog(
                "Stuck Detection",
                "In waiting routine, resetting stuck counter.",
                Py4GW.Console.MessageType.Debug,
                False,
            )
            stuck_counter = 0
            if isinstance(build, SF_Ass_vaettir) or isinstance(build, SF_Mes_vaettir):
                build.SetStuckSignal(stuck_counter)
            stuck_timer.Reset()
            yield from Routines.Yield.wait(1000)
            continue

        # Finished routine check
        if finished_routine:
            ConsoleLog(
                "Stuck Detection", "Finished routine, resetting stuck counter.", Py4GW.Console.MessageType.Debug, False
            )
            stuck_counter = 0
            if isinstance(build, SF_Ass_vaettir) or isinstance(build, SF_Mes_vaettir):
                build.SetStuckSignal(stuck_counter)
            stuck_timer.Reset()
            yield from Routines.Yield.wait(1000)
            continue

        # Killing routine check
        if in_killing_routine:
            ConsoleLog(
                "Stuck Detection",
                "In killing routine, resetting stuck counter.",
                Py4GW.Console.MessageType.Debug,
                False,
            )
            stuck_counter = 0
            if isinstance(build, SF_Ass_vaettir) or isinstance(build, SF_Mes_vaettir):
                build.SetStuckSignal(stuck_counter)
            stuck_timer.Reset()
            yield from Routines.Yield.wait(1000)
            continue

        # Jaga Moraine map check
        if GLOBAL_CACHE.Map.GetMapID() == JAGA_MORAINE:
            if stuck_timer.IsExpired():
                ConsoleLog(
                    "Stuck Detection",
                    "Stuck timer expired, sending /stuck command.",
                    Py4GW.Console.MessageType.Debug,
                    False,
                )
                GLOBAL_CACHE.Player.SendChatCommand("stuck")
                stuck_timer.Reset()

            if movement_check_timer.IsExpired():
                current_player_pos = GLOBAL_CACHE.Player.GetXY()
                ConsoleLog(
                    "Stuck Detection",
                    f"Checking movement. Old pos: {old_player_position}, Current pos: {current_player_pos}",
                    Py4GW.Console.MessageType.Debug,
                    False,
                )

                if is_within_tolerance(old_player_position, current_player_pos, 50):
                    ConsoleLog(
                        "Stuck Detection", "Player is stuck, sending /stuck command.", Py4GW.Console.MessageType.Warning
                    )
                    GLOBAL_CACHE.Player.SendChatCommand("stuck")
                    stuck_counter += 1
                    ConsoleLog(
                        "Stuck Detection",
                        f"Stuck counter incremented to {stuck_counter}.",
                        Py4GW.Console.MessageType.Debug,
                        False,
                    )
                    if isinstance(build, SF_Ass_vaettir) or isinstance(build, SF_Mes_vaettir):
                        build.SetStuckSignal(stuck_counter)
                    stuck_timer.Reset()
                else:
                    old_player_position = current_player_pos
                    ConsoleLog(
                        "Stuck Detection",
                        "Player moved, resetting stuck counter to 0.",
                        Py4GW.Console.MessageType.Info,
                        False,
                    )
                    stuck_counter = 0
                    if isinstance(build, SF_Ass_vaettir) or isinstance(build, SF_Mes_vaettir):
                        build.SetStuckSignal(stuck_counter)

                movement_check_timer.Reset()

            if stuck_counter >= 10:
                ConsoleLog(
                    "Stuck Detection", "Unrecoverable stuck detected, resetting.", Py4GW.Console.MessageType.Error
                )
                stuck_counter = 0
                if isinstance(build, SF_Ass_vaettir) or isinstance(build, SF_Mes_vaettir):
                    build.SetStuckSignal(stuck_counter)
                GLOBAL_CACHE.Player.SendChatCommand("resign")
                continue
        else:
            ConsoleLog("Stuck Detection", "Not in Jaga Moraine", Py4GW.Console.MessageType.Info, False)
            yield from Routines.Yield.wait(1000)
            continue

        ConsoleLog("Stuck Detection", "waiting for next check.", Py4GW.Console.MessageType.Info, False)
        yield from Routines.Yield.wait(500)
        continue


def _force_reset(bot: Botting):
    global unmanaged_fail_counter
    unmanaged_fail_counter += 1
    ConsoleLog(VAETTIR_FARM_BY_MARK, f"Something went wrong forcing a reset... Attempt: {unmanaged_fail_counter}")
    yield from Routines.Yield.wait(1000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Town Routines_1")
    fsm.resume()
    yield


def handle_custom_on_unmanaged_fail(bot: Botting):
    global unmanaged_fail_counter

    ConsoleLog(VAETTIR_FARM_BY_MARK, "Handling explorable mode unmanaged error...")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("Force Reset", _force_reset(bot))

    if unmanaged_fail_counter > 5:
        return True
    return False


bot.SetMainRoutine(create_bot_routine)


def configure():
    global bot
    bot.UI.draw_configure_window()


def main():
    bot.Update()
    projects_path = Py4GW.Console.get_projects_path()
    widgets_path = projects_path + "\\Bots\\marks_coding_corner\\textures\\"
    bot.UI.draw_window(icon_path=widgets_path + "vaettir_icon.png")


if __name__ == "__main__":
    main()
