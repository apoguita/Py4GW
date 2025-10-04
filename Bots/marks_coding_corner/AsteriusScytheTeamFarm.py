from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import Botting
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Range
from Py4GWCoreLib import Utils
from Bots.marks_coding_corner.utils.town_utils import return_to_outpost
import Py4GW

BOT_NAME = "Asterius Scythe Farm"
TEXTURE = Py4GW.Console.get_projects_path() + "//Vanquished_Helmet.png"
OUTPOST_TO_TRAVEL = GLOBAL_CACHE.Map.GetMapIDByName('Olafstead')
VARAJAR_FELLS_MAP_ID = 553
ASTERIUS_MODEL_ID = 6458

TRAVEL_PATH: list[tuple[float, float]] = [
    (-3357.584716796875, -741.2806396484375),
    (-2572.929443359375, -3393.46875),
    (-5767.3828125, -4300.8720703125),
    (-8149.3349609375, -2815.1455078125),
    (-9563.5947265625, -2276.733642578125),
    (-12105.3779296875, -868.0400390625),
    (-15445.7314453125, -4605.25244140625),
]

is_asterius_spotted = False
is_asterius_killed = False
asterius_agent_id = -1
elapsed = 0

bot = Botting(BOT_NAME, upkeep_auto_inventory_management_active=False, upkeep_honeycomb_active=True)


def bot_routine(bot: Botting) -> None:
    global Vanquish_Path
    # events
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    # end events

    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)

    bot.States.AddHeader('Exit To Farm')
    bot.Party.SetHardMode(True)
    bot.Move.XYAndExitMap(-2166, 861, VARAJAR_FELLS_MAP_ID)
    bot.Wait.ForTime(4000)
    bot.States.AddHeader("Start Combat")

    bot.Move.FollowAutoPath(TRAVEL_PATH, "Kill Route")
    bot.Wait.UntilCondition(
        is_asterius_killed_or_time_elapsed, duration=1000
    )  # check every second until boss is killed

    bot.Wait.ForTime(10000)
    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    bot.Wait.ForTime(20000)
    bot.States.JumpToStepName("[H]Asterius Scythe Farm_1")


def is_asterius_killed_or_time_elapsed():
    global is_asterius_killed
    global is_asterius_spotted
    global asterius_agent_id
    global elapsed

    elapsed += 1
    # Cap at 3 minutes to wait for Asterius on the final spot
    if elapsed > 180:
        return True

    if is_asterius_killed:
        return True

    if is_asterius_spotted and asterius_agent_id:
        if not GLOBAL_CACHE.Agent.IsDead(asterius_agent_id):
            return False
        is_asterius_killed = True

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
        if GLOBAL_CACHE.Agent.GetModelID(enemy_id) == ASTERIUS_MODEL_ID:
            is_asterius_spotted = True
            asterius_agent_id = enemy_id
    return False


def _on_party_wipe(bot: "Botting"):
    yield from return_to_outpost()
    bot.States.JumpToStepName("[H]Exit To Farm_3")
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


bot.SetMainRoutine(bot_routine)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE)


if __name__ == "__main__":
    main()
