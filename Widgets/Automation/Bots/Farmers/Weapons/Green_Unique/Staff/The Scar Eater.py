import os

import Py4GW
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import Botting, ConsoleLog, Routines, Agent, Player

BOT_NAME = "Scar Eater Farm"
bot = Botting(BOT_NAME)

KILLING_PATH = [
    (15204.0, 1321),
    (14314, -769),
    (14097, -1194),
    (12216, -1054),
    (12831, -3230),
    (14683, -3208),
    (17338, -2931),
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
    """Routine principale du farm Scar Eater"""
    
    # ===== CONFIGURATION MULTIBOX =====
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')
    
    bot.Templates.Multibox_Aggressive()
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=130)
    bot.Properties.Disable("auto_inventory_management")
    bot.Party.SetHardMode(False)
    # ==================================

    bot.States.AddHeader("Exit Outpost")
    bot.Move.XYAndExitMap(18046, 1734, target_map_id=128)
    bot.Wait.ForMapLoad(128)
    bot.Wait.ForTime(3000)

    bot.States.AddHeader("Combat")
    bot.Move.FollowAutoPath(KILLING_PATH, "Scar Eater Kill Route")
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(8000)

    bot.States.AddHeader("Resign and Return to Outpost")
    bot.Multibox.ResignParty()
    bot.Wait.ForMapToChange(target_map_id=130)
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
    PyImGui.text_colored("Scar Eater Farmer bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("multi-account bot to farm Scar Eater weapon")
    PyImGui.spacing()
    PyImGui.bullet_text("Requirements:")
    PyImGui.bullet_text("- 6-8 well-geared accounts")
    PyImGui.bullet_text("- Hero AI widget enabled on all accounts")
    PyImGui.bullet_text("- Launch the script on the party leader only")
    PyImGui.bullet_text("Designed for Normal Mode (NM) for faster and easy run, but can be change editing True or False in the code.")
    
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by LeZgw")
    PyImGui.end_tooltip()


def main():
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()