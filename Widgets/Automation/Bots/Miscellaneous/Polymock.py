
# Reload imports
import importlib
import os
import PyImGui
from Sources.frenkeyLib.Polymock import gui, combat, state

from Py4GWCoreLib import Map, Routines, ImGui, Color
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer

importlib.reload(gui)
importlib.reload(combat)
importlib.reload(state)

MODULE_NAME = "Polymock"
throttle_timer = ThrottledTimer(250)
script_directory = os.path.dirname(os.path.abspath(__file__))

combat_handler = combat.Combat()
widget_state = state.WidgetState()
ui = gui.UI()

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Polymock Auto-Battler", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A specialized automation suite for the Polymock minigame.")
    PyImGui.text("This widget manages piece selection, ability timing, and")
    PyImGui.text("tactical positioning within the Polymock arenas.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Combat Handler: Intelligent skill priority and interrupt logic for Polymock pieces")
    PyImGui.bullet_text("State Engine: Monitors game progress and transition states automatically")
    PyImGui.bullet_text("Modular UI: Integrated control panel for starting, stopping, and configuring battles")
    PyImGui.bullet_text("Automatic Resets: Handles post-match interactions to streamline the grind")
    PyImGui.bullet_text("Throttled Execution: Optimized 250ms tick rate for responsive yet stable performance")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by frenkey")

    PyImGui.end_tooltip()


def main():    
    if not Routines.Checks.Map.MapValid():
        return    
            
    widget_state.update()
    ui.draw()
    
    if not Map.IsExplorable():
        return                    
                     
    if throttle_timer.IsExpired():
        throttle_timer.Reset()
        
        combat_handler.Fight()
        
        
        

__all__ = ['main']
