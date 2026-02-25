from Py4GWCoreLib import *
import Py4GW
import os

BOT_NAME = "Lightbringer - MirrorOfLyss"
OUTPOST_TO_TRAVEL = 414
EXPLORABLE_TO_TRAVEL = 419
KILLING_PATH:list[tuple[float, float]] = [
    (-13760, -13924),
    (-10600, -12671),
    (-4785, -14912),
    (-2451, -15086),
	(1174,	-13787),
	(6728,	-12014),
	(9554,	-14517),
	(16856, -14068),
	(19428, -13168),
	(16961, -7251),
	(20212, -5510),
	(20373, -580),
	(19778, 2882),
	(19561, 6432),
	(15914, 10322),
	(12116, 7908),
	(12932, 6907),
	(12956, 2637)
]
COORD_TO_EXIT_MAP = (-850, 4700)
COORD_FOR_RESIGN = (-19350.00, -16900.00)

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "ApoSource", "textures", "VQ_Helmet.png")

bot = Botting(BOT_NAME)

def bot_routine(bot: Botting) -> None:
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events

    # Combat preparations
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.Party.SetHardMode(True)
    # Start resign setup
    bot.Move.XY(-850, 4700, "Exit Outpost")
    bot.Wait.ForMapLoad(EXPLORABLE_TO_TRAVEL)
    bot.Move.XY(-19350, -16900, "Enter Outpost")
    bot.Wait.ForMapLoad(OUTPOST_TO_TRAVEL)
    # End resign setup
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Move.XY(-850, 4700, "Exit Outpost")
    bot.Wait.ForMapLoad(EXPLORABLE_TO_TRAVEL)
    bot.Move.XYAndInteractNPC(-20928, -13121) # blessing coords
    bot.Multibox.SendDialogToTarget(0x85) #Get Bounty
    bot.Move.FollowAutoPath(KILLING_PATH)
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(1000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName(f"[H]{BOT_NAME}_loop_3")

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(BOT_NAME + " bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi-account bot to " + BOT_NAME)
    PyImGui.spacing()
    PyImGui.bullet_text("Requirements:")
    PyImGui.bullet_text("- The Kodash Bazaar outpost.")

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Aura")
    PyImGui.bullet_text("Contributors: Wick-Divinus for script template")
    PyImGui.bullet_text("- Wick-Divinus for script template")
    PyImGui.bullet_text("- Kronos for idea and coords")
    PyImGui.end_tooltip()

def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map → jump to recovery step
    bot.States.JumpToStepName("[H]Start Combat_3")
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
