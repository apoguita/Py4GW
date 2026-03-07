import os

import Py4GW
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import Botting, ConsoleLog, Routines, Agent, Player

BOT_NAME = "Rajazan's Fervor"
MODULE_ICON = "Textures\\Module_Icons\\Rajazan's Fervor.png"
bot = Botting(BOT_NAME)

KILLING_PATH = [
    (3573.0, 1788),
    (4670, 2949),
    (4731, 4260),
    (3939, 5265),
    (3116, 5570),
    (1409, 5723),
    (861, 2827),
    (2324, 725),
    (3878, 176),
    (5310, 450),
    (6926, 1304),
    (8602, 4138),
    (7779, 5905),
    (5006, 8008),
    (526, 8222),
    (-1485, 7155),
    (-3618, 6180),
    (-6605, 5235),
    (-8708, 3955),
    (-9104, 2126),
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
    """Rajazan's Fervor"""
    
    # ===== CONFIGURATION MULTIBOX =====
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')
    
    bot.Templates.Multibox_Aggressive()
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=277)
    bot.Properties.Disable("auto_inventory_management")
    bot.Party.SetHardMode(False)
    # ==================================

    bot.States.AddHeader("Exit Outpost")
    bot.Move.XYAndExitMap(3200, 2499, target_map_id=227)
    bot.Wait.ForMapLoad(227)
    bot.Wait.ForTime(3000)

    bot.States.AddHeader("Combat")
    bot.Move.FollowAutoPath(KILLING_PATH, "Rajazan's Fervor Kill Route")
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(8000)

    bot.States.AddHeader("Resign and Return to Outpost")
    bot.Multibox.ResignParty()
    bot.Wait.ForMapToChange(target_map_id=277)
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
    PyImGui.text_colored("Rajazan's Fervor Farmer bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("multi-account bot to farm Rajazan's Fervor weapon")
    PyImGui.spacing()
    PyImGui.bullet_text("Requirements:")
    PyImGui.bullet_text("- 6-8 well-geared accounts")
    PyImGui.bullet_text("- Hero AI widget enabled on all accounts")
    PyImGui.bullet_text("- Launch the script on the party leader only")
    PyImGui.bullet_text("Designed for Normal Mode (NM) for faster and easy run, but can be change editing True or False in the code.")
    
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Xan")
    PyImGui.bullet_text("Contriutors: LeZgw")
    PyImGui.end_tooltip()


def main():
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()