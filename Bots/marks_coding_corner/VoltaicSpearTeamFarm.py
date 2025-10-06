import os

import Py4GW
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import Botting
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Utils

BOT_NAME = "Voltaic Spear Farm"
TEXTURE = os.path.join(
    Py4GW.Console.get_projects_path(), "Bots", "marks_coding_corner", "textures", "voltaic_spear.png"
)
OUTPOST_TO_TRAVEL = GLOBAL_CACHE.Map.GetMapIDByName('Umbral Grotto')
VERDANT_CASCADES_MAP_ID = 566
SALVERS_EXILE_MAP_ID = 577
JUSTICIAR_THOMAS_ROOM_MAP_ID = 620

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


def _on_party_wipe(bot: "Botting"):
    while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
        yield from bot.helpers.Wait._for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    # Check if in slavers exile

    # Check if in res point 1

    # Check if in res point 2

    # Player revived on same map → jump to recovery step
    # bot.States.JumpToStepName("[H]Start Combat_4")
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


def rest_of_party_claim_rewards(bot: Botting):
    pass


def farm_dungeon(bot: Botting) -> None:
    print(GLOBAL_CACHE.Map.GetMapID())
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')

    # events
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    # end events

    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("auto_inventory_management")

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
    bot.Move.XYAndExitMap(-18300, 12527, target_map_id=JUSTICIAR_THOMAS_ROOM_MAP_ID)

    bot.States.AddHeader("Make way to Justiciar Tommis part 1")
    bot.Move.FollowAutoPath(SALVERS_EXILE_TRAVEL_PATH_1, "Part 1 killing route")

    bot.States.AddHeader("Make way to Justiciar Tommis part 2")
    bot.Move.FollowAutoPath(SALVERS_EXILE_TRAVEL_PATH_2, "Part 2 killing route")
    bot.Properties.Disable('pause_on_danger')

    bot.Interact.WithGadgetAtXY(-17461.00, -14258.00, "Main runner claim rewards")
    bot.Multibox.InteractWithTargetDungeonChest()  # Bots should auto loot

    bot.Wait.ForTime(10000)


bot.SetMainRoutine(farm_dungeon)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE)


if __name__ == "__main__":
    main()
