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
from Py4GWCoreLib import Map, Agent, Player

BOT_NAME = "Asterius Scythe Farm"
TEXTURE = os.path.join(
    Py4GW.Console.get_projects_path(), "Bots", "marks_coding_corner", "textures", "asterius_scythe.png"
)
OUTPOST_TO_TRAVEL = Map.GetMapIDByName('Olafstead')
VARAJAR_FELLS_MAP_ID = 553
ASTERIUS_MODEL_ID = 6458

TRAVEL_PATH: list[tuple[float, float]] = [
    (-3357, -741),
    (-2572, -3393),
    (-5767, -4300),
    (-8149, -2815),
    (-9563, -2276),
    (-12105, -868),
    (-15445, -4605),
]

is_asterius_spotted = False
is_asterius_killed = False
asterius_agent_id = -1
elapsed = 0

bot = Botting(BOT_NAME)


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
        if not Agent.IsDead(asterius_agent_id):
            return False
        is_asterius_killed = True

    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByCondition(
        enemy_array,
        lambda agent_id: Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id))
        <= Range.SafeCompass.value,
    )
    enemy_array = AgentArray.Filter.ByCondition(
        enemy_array, lambda agent_id: Player.GetAgentID() != agent_id
    )
    for enemy_id in enemy_array:
        if Agent.GetModelID(enemy_id) == ASTERIUS_MODEL_ID:
            is_asterius_spotted = True
            asterius_agent_id = enemy_id
    return False


def reset_farm_flags():
    global is_asterius_killed
    global is_asterius_spotted
    global asterius_agent_id
    global elapsed

    is_asterius_spotted = False
    is_asterius_killed = False
    asterius_agent_id = -1
    elapsed = 0


def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
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


def handle_asterius_killed_en_route():
    global is_asterius_killed
    global is_asterius_spotted
    global asterius_agent_id

    while True:
        if not Map.IsExplorable():
            yield from Routines.Yield.wait(1000)
            continue

        if is_asterius_killed:
            yield from Routines.Yield.wait(1000)
            continue

        if is_asterius_spotted and asterius_agent_id:
            yield from Routines.Yield.wait(1000)
            if Agent.IsDead(asterius_agent_id):
                is_asterius_killed = True
            continue

        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id))
            <= Range.SafeCompass.value,
        )
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array, lambda agent_id: Player.GetAgentID() != agent_id
        )
        for enemy_id in enemy_array:
            if Agent.GetModelID(enemy_id) == ASTERIUS_MODEL_ID:
                is_asterius_spotted = True
                asterius_agent_id = enemy_id
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
    bot.Properties.Disable("auto_inventory_management")

    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.Party.SetHardMode(True)
    bot.States.AddManagedCoroutine('Detect en route Asterius kill', handle_asterius_killed_en_route)

    bot.States.AddHeader('Exit To Farm')
    bot.Properties.Disable('pause_on_danger')
    bot.Move.XYAndExitMap(-2166, 861, target_map_id=VARAJAR_FELLS_MAP_ID)
    bot.Wait.ForTime(4000)
    bot.Properties.Enable('pause_on_danger')

    bot.States.AddHeader("Start Combat")
    bot.Move.FollowAutoPath(TRAVEL_PATH, "Kill Route")
    bot.Wait.UntilCondition(
        is_asterius_killed_or_time_elapsed, duration=1000
    )  # check every second until boss is killed
    bot.Wait.ForTime(10000)  # allow to loot
    bot.Multibox.ResignParty()
    bot.States.AddCustomState(reset_farm_flags, "Reset Farm detections")
    bot.Wait.UntilOnOutpost()
    bot.Wait.ForTime(10000)
    bot.States.JumpToStepName("[H]Exit To Farm_3")


bot.SetMainRoutine(farm_scythes)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Asterius Scythe Farmer bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("multi-account bot to farm Asterius Scythe")
    PyImGui.spacing()
    PyImGui.bullet_text("Requirements:")
    PyImGui.bullet_text("- 6-8 well-geared accounts")
    PyImGui.bullet_text("- Hero AI widget enabled on all accounts")
    PyImGui.bullet_text("- Launch the script on the party leader only")
    PyImGui.bullet_text("Designed for Normal Mode (NM) for faster and easy run, but can be change editing True or False in the code.")
    
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Mark")
    PyImGui.end_tooltip()

def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE)


if __name__ == "__main__":
    main()
