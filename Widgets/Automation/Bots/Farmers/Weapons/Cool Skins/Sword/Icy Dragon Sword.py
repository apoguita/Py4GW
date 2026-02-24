import os

import Py4GW
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import Botting, ConsoleLog, Routines, Agent, Player

BOT_NAME = "Ice Dragon Sword Farm"
MODULE_ICON = "Textures\\Module_Icons\\Icy Dragon Sword.png"
bot = Botting(BOT_NAME)

# Path dans Tasca's Demise (map 92)
KILLING_PATH_TASCAS = [
    (-6576.98, 21048.42),
    (-4737.67, 20476.49),
    (-3444.01, 18646.93),
    (-2375.25, 17811.89),
    (1292.36, 17196.85),
    (1101.62, 20333.49),
    (3086.33, 21293.39),
    (6841.67, 21317.61),
    (4550.62, 25867.70),
    (4832.05, 26894.38),
    (5013.66, 27914.02),
    (6961.32, 29165.35),
    (7924.16, 29574.07), # Point avant changement de carte
]

# Path dans Mineral Springs (map 96)
KILLING_PATH_MINERAL = [
    (-20556.10, -9186.23),
    (-22756.70, -4507.07),
    (-20906.48, 2409.70),
    (-20782.31, 3384.65),
    (-20583.18, 4757.61),
    (-20428.73, 5702.45),
    (-19472.12, 10160.58),
    (-15779.47, 9496.85),
    (-14663.69, 8700.60),
    (-13337.59, 7392.53),
    (-11807.39, 7248.12),
    (-10152.40, 8320.35),
    (-8695.75, 8883.15),
    (-7196.33, 9044.85),
    (-4886.48, 6504.34),
    (-3582.45, 6419.53),
    (-2378.46, 4700.92),
    (-1063.20, 6314.70),
    (1109.05, 6120.64),
    (1109.05, 6120.64),
    (1906.27, 4478.43),
    (5132.52, 4244.47),
    (8973.27, 5460.31),
    (13804.43, 9271.58),
    (16914.31, 9953.56),
    (16914.31, 9953.56),
    (20678, 8860),
    (23289, 8262),
    (24880, 8838),
    (24304, 5820),
    (24880, 8838),
    (25511, 4559)
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
    """Routine principale du farm Ice Dragon Sword"""
    
    # ===== CONFIGURATION MULTIBOX =====
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')
    
    bot.Templates.Multibox_Aggressive()
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=156)
    bot.Properties.Disable("auto_inventory_management")
    bot.Party.SetHardMode(False)
    # ==================================

    bot.States.AddHeader("Exit Outpost")
    bot.Move.XYAndExitMap(-9916, 19020, target_map_id=92)
    bot.Wait.ForMapLoad(92)
    bot.Wait.ForTime(3000)

    bot.States.AddHeader("Combat - Tasca's Demise")
    bot.Move.FollowAutoPath(KILLING_PATH_TASCAS, "Tasca's Demise Route")
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(2000)

    bot.States.AddHeader("Map Change - Enter Mineral Springs")
    bot.Move.XYAndExitMap(7924.16, 29574.07, target_map_id=96)
    bot.Wait.ForMapLoad(96)
    bot.Wait.ForTime(3000)

    bot.States.AddHeader("Combat - Mineral Springs")
    bot.Move.FollowAutoPath(KILLING_PATH_MINERAL, "Mineral Springs Route")
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(8000)

    bot.States.AddHeader("Resign and Return to Outpost")
    bot.Multibox.ResignParty()
    bot.Wait.ForMapToChange(target_map_id=156)
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
    PyImGui.text_colored("Icy Dragon Sword Farmer bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("multi-account bot to farm Icy Dragon Sword")
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