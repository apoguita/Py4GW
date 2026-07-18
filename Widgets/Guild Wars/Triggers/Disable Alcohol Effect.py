import Py4GW
import PyImGui

from Py4GWCoreLib.Effect import Effects
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer


MODULE_ICON = "Textures/Module_Icons/Disable Alcohol Effect.png"
MODULE_NAME = "Disable Alcohol Effect"
title_color = Color(255, 200, 100, 255)

throttle = ThrottledTimer(1000)

def tooltip():
    PyImGui.set_next_window_size((400, 0))
    PyImGui.begin_tooltip()

    # Title
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    
    #description
    PyImGui.text_wrapped("This module disables the alcohol effect, allowing you to see clearly even after consuming alcohol in the game.")

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by frenkey")

    PyImGui.end_tooltip()


def main():
    if throttle.IsExpired():
        throttle.Reset()
        
        if not Routines.Checks.Map.IsMapReady():
            return

        current_alcohol_level = Effects.GetAlcoholLevel()
        if current_alcohol_level > 0:
            Effects.ApplyDrunkEffect(0, 0)