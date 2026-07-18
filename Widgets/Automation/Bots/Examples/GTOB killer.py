
from Py4GWCoreLib import *

bot = Botting("GTOB Killer")

def Routine(bot: Botting) -> None:
    bot.Templates.Aggressive(enable_imp=False)
    bot.Map.Travel(target_map_id=248) #gtob
    bot.Move.XYAndExitMap(-6062, -2688, target_map_id=280, step_name="Exit Outpost") #gtob

    path_to_master_of_healing = [(-2566.19, -1185.40),
                                 (816.17, -1323.48),
                                 (37.09, 488.95)]
           
    bot.Move.FollowAutoPath(points=path_to_master_of_healing, step_name="To Master Of Healing")                       

    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(3531.49, 3936.87, "Master Of Hexes")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(1832.22, 9710.28, "Master Of Enchantments")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(5870.76, 8822.76, "Master Of Axes")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(8603.14, 6247.41, "Master Of Hammers")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(6527.84, 1637.41, "Master Of Lighting")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7873.69, -1941.89, "Master Of Energy Denial")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(3354.89, -7001.23, "Master Of Interrupts")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(3071.38, -2879.04, "Master Of Spirits")
    bot.Wait.UntilOutOfCombat()
    bot.UI.PrintMessageToConsole("GTOB Killer", "Finished routine")

bot.SetMainRoutine(Routine)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("GTOB Killer Bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Single Account, kill all GTOB masters")
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")
    PyImGui.end_tooltip()


def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()
