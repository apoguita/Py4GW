from Py4GWCoreLib import Player
from Py4GWCoreLib import Map
import Py4GW
import PyImGui
from Py4GWCoreLib import ImGui, Color

MODULE_NAME = "Window Renamer"
MODULE_ICON = "Textures/Module_Icons/Rename.png"
_last_char_name: str = ""

def main():
    global _last_char_name
    if not Map.IsMapReady():
        return
    char_name = Player.GetName()
    if not char_name or char_name == _last_char_name:
        return
    _last_char_name = char_name
    Py4GW.Console.set_window_title(char_name)

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Window Renamer", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    #ellaborate a better description 
    PyImGui.text("Renames game windows to character names")
    
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Renames game windows on character change")
    PyImGui.bullet_text("Sets window title to character name")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by PinkMusen")

    PyImGui.end_tooltip()

if __name__ == "__main__":
    main()
