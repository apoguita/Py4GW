import os

import Py4GW
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import Botting, ConsoleLog, Routines, Agent, Player

BOT_NAME = "Ice Breaker Farm"
MODULE_ICON = "Textures\\Module_Icons\\The Ice Breaker.png"
bot = Botting(BOT_NAME)

KILLING_PATH = [
    (-21836.37, 15600.12),
    (-22630.61, 13523.55),
    (-20800.78, 13247.58),
    (-18927.65, 14829.27),
    (-18313.14, 12205.53),
    (-16212.95, 10640.76),
    (-14645.55, 10270.77),
    (-12738.45, 9654.81),
    (-13882.84, 14651.44),
    (-11230.53, 16500.39),
    (-9226.18, 14034.68),
    (-6594.39, 15729.20),
    (-4177.07, 15850.13),
    (-2378.74, 15625.52),
    (1615.12, 14791.13),
    (2790.79, 14775.57),
    (3902.81, 14059.60),
    (5074.49, 14427.69),
    (7194.55, 14765.60),
    (9113.74, 14959.46),
    (10939.60, 14962.41),
    (12161.31, 14508.19)
]

# =========================
# WIPE HANDLING
# =========================

def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return
    # Quand le joueur est ressuscité, reprendre au combat
    bot.States.JumpToStepName("[H]Combat_3")
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "party wipe detected")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


# =========================
# MAIN ROUTINE
# =========================

def Routine(bot: Botting) -> None:
    """Routine principale du farm Ice Breaker"""
    
    # ===== CONFIGURATION MULTIBOX =====
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')
    
    bot.Templates.Multibox_Aggressive()
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=155)
    bot.Properties.Disable("auto_inventory_management")
    bot.Party.SetHardMode(False)
    # ==================================

    bot.States.AddHeader("Exit Outpost")
    bot.Move.XYAndExitMap(7589, -45014, target_map_id=26)
    bot.Wait.ForMapLoad(26)
    bot.Wait.ForTime(3000)

    bot.States.AddHeader("Combat")
    bot.Move.FollowAutoPath(KILLING_PATH, "Ice Breaker Kill Route")
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(8000)

    bot.States.AddHeader("Resign and Return to Outpost")
    bot.Multibox.ResignParty()
    bot.Wait.ForMapToChange(target_map_id=155)
    bot.UI.PrintMessageToConsole(BOT_NAME, "Finished routine - Restarting...")
    bot.States.JumpToStepName("[H]Exit Outpost_2")


bot.SetMainRoutine(Routine)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Ice Breaker Farmer bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("multi-account bot to farm Ice Breaker")
    PyImGui.spacing()
    PyImGui.bullet_text("Requirements:")
    PyImGui.bullet_text("- 6-8 well-geared accounts")
    PyImGui.bullet_text("- Hero AI widget enabled on all accounts")
    PyImGui.bullet_text("- Launch the script on the party leader only")
    PyImGui.bullet_text("Designed for Normal Mode (NM) for faster and easy run, but can be change editing True or False in the code.")
    
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by XLeek")
    PyImGui.end_tooltip()
def main():
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()