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

BOT_NAME = "Birahn's Shield Farm"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Vanquished_Helmet.png")
OUTPOST_TO_TRAVEL = GLOBAL_CACHE.Map.GetMapIDByName('The Kodash Bazaar')
MIRROR_OF_LYSS_MAP_ID = 419
BRIAHNS_MODEL_ID = 5518

HONUR_HILL_TRAVEL_PATH: list[tuple[float, float]] = [
    (21500.25390625, -15467.0126953125),
    (18896.490234375, -15838.85546875),
    (13516.6240234375, -13918.5712890625),
    (10773.3056640625, -15054.142578125),
    (4464.98046875, -12559.630859375),
    (1649.0672607421875, -13868.5439453125),
    (-6889.783203125, -14858.8115234375),
    (-10354.7958984375, -12134.3203125),
    (-13278.0712890625, -11623.4765625),
    (-16952.267578125, -11470.740234375),
    (-18884.419921875, -13176.1279296875),
    (-19154.185546875, -14973.0166015625),
]

KODASH_TRAVEL_PATH: list[tuple[float, float]] = [
    (-19218.529296875, -15411.8349609375),
    (-18553.06640625, -12571.8193359375),
    (-17381.486328125, -11511.1630859375),
    (-14303.0224609375, -11338.306640625),
    (-11115.97265625, -11649.5283203125),
    (-8877.7490234375, -12748.3525390625),
    (-5999.94287109375, -14982.9384765625),
    (-1239.8211669921875, -14970.0205078125),
    (1620.1793212890625, -13476.8798828125),
    (5151.92724609375, -12421.8955078125),
    (8309.7099609375, -13429.748046875),
    (13531.5361328125, -14155.5751953125),
]

is_briahn_spotted = False
is_briahn_killed = False
briahn_agent_id = -1
elapsed = 0

bot = Botting(BOT_NAME)


def is_briahn_killed_or_time_elapsed():
    global is_briahn_killed
    global is_briahn_spotted
    global briahn_agent_id
    global elapsed

    elapsed += 1
    # Cap at 30 seconds to wait for Briahn on the final spot
    if elapsed > 30:
        return True

    if is_briahn_killed:
        return True

    if is_briahn_spotted and briahn_agent_id:
        if not GLOBAL_CACHE.Agent.IsDead(briahn_agent_id):
            return False
        is_briahn_killed = True

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByCondition(
        enemy_array,
        lambda agent_id: Utils.Distance(GLOBAL_CACHE.Player.GetXY(), GLOBAL_CACHE.Agent.GetXY(agent_id))
        <= Range.SafeCompass.value,
    )
    enemy_array = AgentArray.Filter.ByCondition(
        enemy_array, lambda agent_id: GLOBAL_CACHE.Player.GetAgentID() != agent_id
    )
    for enemy_id in enemy_array:
        if GLOBAL_CACHE.Agent.GetModelID(enemy_id) == BRIAHNS_MODEL_ID:
            is_briahn_spotted = True
            briahn_agent_id = enemy_id
    return False


def reset_farm_flags():
    global is_briahn_killed
    global is_briahn_spotted
    global briahn_agent_id
    global elapsed

    is_briahn_spotted = False
    is_briahn_killed = False
    briahn_agent_id = -1
    elapsed = 0


def _on_party_wipe(bot: "Botting"):
    while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
        yield from bot.helpers.Wait._for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map → jump to recovery step
    bot.States.JumpToStepName("[H]Start Combat_4")
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


def handle_briahn_killed_en_route():
    global is_briahn_killed
    global is_briahn_spotted
    global briahn_agent_id

    while True:
        if not GLOBAL_CACHE.Map.IsExplorable():
            yield from Routines.Yield.wait(1000)
            continue

        if is_briahn_killed:
            yield from Routines.Yield.wait(1000)
            continue

        if is_briahn_spotted and briahn_agent_id:
            yield from Routines.Yield.wait(1000)
            if GLOBAL_CACHE.Agent.IsDead(briahn_agent_id):
                is_briahn_killed = True
            continue

        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: Utils.Distance(GLOBAL_CACHE.Player.GetXY(), GLOBAL_CACHE.Agent.GetXY(agent_id))
            <= Range.SafeCompass.value,
        )
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array, lambda agent_id: GLOBAL_CACHE.Player.GetAgentID() != agent_id
        )
        for enemy_id in enemy_array:
            if GLOBAL_CACHE.Agent.GetModelID(enemy_id) == BRIAHNS_MODEL_ID:
                is_briahn_spotted = True
                briahn_agent_id = enemy_id
                yield from Routines.Yield.wait(1000)
        yield from Routines.Yield.wait(1000)


def farm_scythes(bot: Botting) -> None:
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')

    # events
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    # end events

    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.Party.SetHardMode(True)
    bot.Move.XYAndExitMap(
        -572, 7489, target_map_id=MIRROR_OF_LYSS_MAP_ID
    )  # setup resign
    bot.Move.XYAndExitMap(-19366, -17899, target_map_id=OUTPOST_TO_TRAVEL)  # Enter back to Kodash
    bot.States.AddManagedCoroutine('Detect en route Briahn kill', handle_briahn_killed_en_route)

    bot.States.AddHeader('Exit To Farm')
    bot.Properties.Disable('pause_on_danger')
    bot.Move.XYAndExitMap(
        -572, 7489, target_map_id=MIRROR_OF_LYSS_MAP_ID
    )  # -572, 7489 Kodash exit, -20980, 21010 Honur Hill Exit
    bot.Wait.ForTime(4000)
    bot.Properties.Enable('pause_on_danger')

    bot.States.AddHeader("Start Combat")
    bot.Move.FollowAutoPath(KODASH_TRAVEL_PATH, "Kill Route")
    bot.Wait.UntilCondition(is_briahn_killed_or_time_elapsed, duration=1000)  # check every second until boss is killed
    bot.Wait.ForTime(10000)  # allow to loot
    bot.Multibox.ResignParty()
    bot.States.AddCustomState(reset_farm_flags, "Reset Farm detections")
    bot.Wait.UntilOnOutpost()
    bot.Wait.ForTime(10000)
    bot.States.JumpToStepName("[H]Exit To Farm_3")


bot.SetMainRoutine(farm_scythes)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE)


if __name__ == "__main__":
    main()
