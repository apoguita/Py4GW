import Py4GW
import os
from Py4GWCoreLib import *

BOT_NAME = "Survivor Title - Kath Hammers"
MODULE_NAME = "Survivor Title - Kath Hammers"
MODULE_ICON = "Textures\\Module_Icons\\Survivor Title - Kath Hammers.png"
bot = Botting(BOT_NAME)
loop = 179

def routine(bot: Botting) -> None:

    ### exit to sacnoth ###
    bot.States.AddHeader("Exit to Sacnoth")
    bot.Move.XYAndExitMap(18600, -21000, target_map_id=651)
    bot.Wait.ForTime(100)

    ### get quest ###
    bot.States.AddHeader("Talking to Swithin Nye")
    bot.Dialogs.AtXY(18392, -18153, 0x832501) # 0x8 + "quest ID hex" + 01 for accept / 07 for reward
    bot.Wait.ForTime(100)
    
    ### turn in quest ###
    bot.Dialogs.AtXY(18392, -18153, 0x832507)
    bot.Wait.ForTime(100)
    ### zone to catacombs ###

    bot.States.AddHeader("Exit to Catacombs")
    bot.Move.XYAndExitMap(19750, -16000, target_map_id=570)
    bot.Wait.ForTime(100)

    bot.States.JumpToStepName("[H]Exit to Sacnoth_1")
        
bot.SetMainRoutine(routine)

def main():
    bot.Update()
    IMAGE = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "Item Models", "22374-Hammer_of_Kathandrax.png")
    bot.UI.draw_window(icon_path=IMAGE)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Kath Hammers Bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Exchanges Kath Hammers for Survivor Title")
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by yellya")
    PyImGui.end_tooltip()
    
if __name__ == "__main__":
    for i in range(loop):
        main()
        loop -= 1