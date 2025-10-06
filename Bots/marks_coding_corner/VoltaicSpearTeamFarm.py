import os
import math

import Py4GW
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Botting
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Widgets.CombatPrep import CombatPrep
from HeroAI.cache_data import CacheData


BOT_NAME = "Voltaic Spear Farm"
TEXTURE = os.path.join(
    Py4GW.Console.get_projects_path(), "Bots", "marks_coding_corner", "textures", "voltaic_spear.png"
)
OUTPOST_TO_TRAVEL = GLOBAL_CACHE.Map.GetMapIDByName('Umbral Grotto')
VERDANT_CASCADES_MAP_ID = 566
SALVERS_EXILE_MAP_ID = 577
JUSTICIAR_THOMMIS_ROOM_MAP_ID = 620

VERDANT_CASCADES_TRAVEL_PATH: list[tuple[float, float]] = [
    (-19887, 6074),
    (-10273, 3251),
    (-6878, -329),
    (-3041, -3446),
    (3571, -9501),
    (10764, -6448),
    (13063, -4396),
    (18054, -3275),
    (20966, -6476),
    (25298, -9456),
]

ENTER_DUNGEON_PATH: list[tuple[float, float]] = [
    (-16797, 9251),
    (-17835, 12524),
]

SALVERS_EXILE_TRAVEL_PATH_1: list[tuple[float, float]] = [
    (-13500, -15750),
    (-12500, -15000),
    (-10400, -14800),
    (-11500, -13300),
    (-13400, -11500),
    (-13700, -9550),
    (-14100, -8600),
    (-15000, -7500),
    (-16500, -8000),
    (-18500, -8000),
]

SALVERS_EXILE_TRAVEL_PATH_2: list[tuple[float, float]] = [
    (-18500, -11500),
    (-17700, -12500),
    (-17500, -14250),
]


bot = Botting(BOT_NAME)
cache_data = CacheData()
combat_prep = CombatPrep(cache_data, '60', 'row')  # Use Widget class to flag heroes
is_party_flagged = False
last_flagged_x_y = (0, 0)
last_flagged_map_id = VERDANT_CASCADES_MAP_ID


def _on_party_wipe(bot: "Botting"):
    while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
        yield from bot.helpers.Wait._for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    player_x, player_y = GLOBAL_CACHE.Player.GetXY()

    shrine_1_x, shrine_1_y = (-18673, -7701)

    # Compute distances
    dist_to_shrine_1 = math.hypot(player_x - shrine_1_x, player_y - shrine_1_y)

    # Check if within earshot
    if dist_to_shrine_1 <= Range.Earshot.value:
        ConsoleLog("Res Check", "Player is near Shrine 1 (Res Point 1)")
        bot.States.JumpToStepName("[H]Make way to Justiciar Tommis part 2_7")

    else:
        ConsoleLog("Res Check", "Player is not near any shrine.")
        bot.States.JumpToStepName("[H]Make way to Justiciar Tommis part 1_6")

    # Player revived on same map → jump to recovery step
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


def handle_on_danger_flagging(bot: Botting):
    global combat_prep
    global is_party_flagged
    global last_flagged_x_y
    global last_flagged_map_id

    spread_formation = [[-200, -200], [200, -200], [-200, 0], [200, 0], [-200, 300], [0, 300], [200, 300]]

    while True:
        player_x, player_y = GLOBAL_CACHE.Player.GetXY()
        map_id = GLOBAL_CACHE.Map.GetMapID()

        if Routines.Checks.Agents.InDanger() and bot.config.pause_on_danger_fn():
            # If not yet flagged, or re-flagging in a new area
            if not is_party_flagged:
                last_flagged_x_y = (player_x, player_y)
                last_flagged_map_id = map_id
                combat_prep.cb_set_formation(spread_formation, False)
                is_party_flagged = True
            else:
                # Check distance to last flagged location
                if last_flagged_map_id == map_id:
                    last_x, last_y = last_flagged_x_y
                    dx = player_x - last_x
                    dy = player_y - last_y
                    dist_sq = dx * dx + dy * dy
                    max_dist = (Range.Area.value * 1.5) ** 2

                    if dist_sq > max_dist:
                        last_flagged_x_y = (player_x, player_y)
                        combat_prep.cb_set_formation(spread_formation, False)
        else:
            if is_party_flagged:
                combat_prep.cb_set_formation([], True)
                is_party_flagged = False
                last_flagged_x_y = (0, 0)
                last_flagged_map_id = VERDANT_CASCADES_MAP_ID
        yield from Routines.Yield.wait(1000)


def farm_dungeon(bot: Botting) -> None:
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')

    # events
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    # end events

    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Set("party_member_behind_threshold", 1500)
    bot.States.AddManagedCoroutine('handle_on_danger_flagging', lambda: handle_on_danger_flagging(bot))

    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.Party.SetHardMode(True)

    bot.States.AddHeader('Exit To Farm')
    bot.Properties.Disable('pause_on_danger')
    bot.Move.XYAndExitMap(-22735, 6339, target_map_id=VERDANT_CASCADES_MAP_ID)
    bot.Properties.Enable('pause_on_danger')

    bot.States.AddHeader("Enter Dungeon")
    bot.Move.FollowAutoPath(VERDANT_CASCADES_TRAVEL_PATH, "To the dungeon route")
    bot.Move.XYAndExitMap(25729, -9360, target_map_id=SALVERS_EXILE_MAP_ID)

    bot.States.AddHeader("Enter Dungeon Room")
    bot.Move.FollowAutoPath(ENTER_DUNGEON_PATH, "To the dungeon room route")
    bot.Move.XYAndExitMap(-18300, 12527, target_map_id=JUSTICIAR_THOMMIS_ROOM_MAP_ID)

    bot.States.AddHeader("Make way to Justiciar Tommis part 1")
    bot.Multibox.UsePConSet()
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("auto_inventory_management")
    bot.Move.FollowAutoPath(SALVERS_EXILE_TRAVEL_PATH_1, "Part 1 killing route")

    bot.States.AddHeader("Make way to Justiciar Tommis part 2")
    bot.Move.FollowAutoPath(SALVERS_EXILE_TRAVEL_PATH_2, "Part 2 killing route")
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Disable('pause_on_danger')

    bot.Wait.ForTime(20000)
    bot.Interact.WithGadgetAtXY(-17461.00, -14258.00, "Main runner claim rewards")
    bot.Multibox.InteractWithTargetDungeonChest()  # Bots should auto loot

    bot.Wait.ForTime(10000)
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName('[H]Exit To Farm_3')


bot.SetMainRoutine(farm_dungeon)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE)


if __name__ == "__main__":
    main()
