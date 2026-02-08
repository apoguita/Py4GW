import os

import Py4GW
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import Botting, ConsoleLog, Routines, Agent, Player
from Py4GWCoreLib import Map

BOT_NAME = "Brightclaw Farm 8man"

# Optionnel : ajoute une texture custom si tu veux
# TEXTURE = os.path.join(
#     Py4GW.Console.get_projects_path(), "Bots", "textures", "brightclaw.png"
# )

bot = Botting(BOT_NAME)

KILLING_PATH = [
    (12951.50, 20539.63),
    (10076.71, 18229.31),
    (7715.59, 18963.31),
    (4453.28, 18097.54),
    (3947.94, 18492.72),
    (2433.26, 18725.63),
    (1476.71, 18246.45),
    (1524.68, 19679.80),
    (3659.15, 20559.77)
]


def _on_party_wipe(bot: "Botting"):
    """Gère la mort complète du groupe"""
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalide → libérer FSM et sortir
            bot.config.FSM.resume()
            return

    # Joueur ressuscité → reprendre au combat
    bot.States.JumpToStepName("[H]Start Combat_4")
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    """Callback lors d'un wipe du groupe"""
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


def Routine(bot: Botting) -> None:
    """Routine principale du farm Brightclaw"""
    
    # ===== CONFIGURATION MULTIBOX =====
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')
    
    bot.Templates.Multibox_Aggressive()
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=390)
    # ==================================

    bot.States.AddHeader("Travel to Jade Flats Kurzick")
    bot.Map.Travel(target_map_id=390)
    bot.Party.SetHardMode(False)

    bot.States.AddHeader("Exit Jade Flats Kurzick to Melendru's Hope")
    bot.Move.XYAndExitMap(-7058, -10806, 201)
    bot.Wait.ForMapLoad(target_map_id=201)
    bot.Wait.ForTime(100)

    bot.States.AddHeader("Start Combat")
    bot.Move.FollowAutoPath(KILLING_PATH, "Kill Route")
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Resign Party and Return to Jade Flats Kurzick")
    bot.Multibox.ResignParty()
    bot.Wait.ForMapToChange(target_map_id=390)
    bot.UI.PrintMessageToConsole(BOT_NAME, "Finished routine - Restarting...")
    bot.States.JumpToStepName("[H]Travel to Jade Flats Kurzick_2")


bot.SetMainRoutine(Routine)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Brightclaw Farmer bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("multi-account bot to farm Brightclaw weapon")
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
    # bot.UI.draw_window(icon_path=TEXTURE)  # Si tu as une texture
    bot.UI.draw_window()


if __name__ == "__main__":
    main()