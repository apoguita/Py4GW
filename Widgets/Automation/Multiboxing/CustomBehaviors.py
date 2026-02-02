
import pathlib
import sys

import Py4GW
from Py4GWCoreLib import ImGui, Map, PyImGui, Routines, Color
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.UIManager import UIManager
from Widgets.Config.CustomBehaviors.primitives import constants
from Widgets.Config.CustomBehaviors.primitives.fps_monitor import FPSMonitor
from Widgets.Config.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.Config.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.Config.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.Config.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.Config.CustomBehaviors.primitives.widget_monitor import WidgetMonitor

# Iterate through all modules in sys.modules (already imported modules)
# Iterate over all imported modules and reload them
for module_name in list(sys.modules.keys()):
    if module_name not in ("sys", "importlib", "cache_data"):
        try:
            if "behavior" in module_name.lower():
                # Py4GW.Console.Log("CustomBehaviors", f"Reloading module: {module_name}")
                del sys.modules[module_name]
                # importlib.reload(module_name)
                pass
        except Exception as e:
            Py4GW.Console.Log("CustomBehaviors", f"Error reloading module {module_name}: {e}")

from Widgets.Config.CustomBehaviors.daemon import daemon
from Widgets.Config.CustomBehaviors.primitives import constants
from Widgets.Config.CustomBehaviors.primitives.fps_monitor import FPSMonitor
from Widgets.Config.CustomBehaviors.primitives.widget_monitor import WidgetMonitor
from Widgets.Config.CustomBehaviors.gui.current_build import render as current_build_render
from Widgets.Config.CustomBehaviors.gui.party import render as party
from Widgets.Config.CustomBehaviors.gui.debug_skillbars import render as debug_skilbars
from Widgets.Config.CustomBehaviors.gui.debug_execution import render as debug_execution
from Widgets.Config.CustomBehaviors.gui.debug_sharedlocks import render as debug_sharedlocks
from Widgets.Config.CustomBehaviors.gui.debug_eventbus import render as debug_eventbus
from Widgets.Config.CustomBehaviors.gui.auto_mover import render as auto_mover
from Widgets.Config.CustomBehaviors.gui.teambuild import render as teambuild
from Widgets.Config.CustomBehaviors.gui.botting import render as botting

party_forced_state_combo = 0
current_path = pathlib.Path.cwd()
monitor = FPSMonitor(history=300)
widget_monitor = WidgetMonitor()
# print(f"current_path is : {current_path}")
widget_window_size:tuple[float, float] = (0,0)
widget_window_pos:tuple[float, float] = (0,0)

def gui():
    # PyImGui.set_next_window_size(260, 650)
    # PyImGui.set_next_window_size(460, 800)

    global party_forced_state_combo, monitor, widget_window_size, widget_window_pos
    
    # window_module:ImGui.WindowModule = ImGui.WindowModule("Custom behaviors", window_name="Custom behaviors - Multiboxing over utility-ai algorithm.", window_size=(0, 600), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

    if PyImGui.begin("Custom behaviors - Multiboxing over utility-ai algorithm.", PyImGui.WindowFlags.AlwaysAutoResize):
        widget_window_size = PyImGui.get_window_size()
        widget_window_pos = PyImGui.get_window_pos()

        PyImGui.begin_tab_bar("tabs")
        if PyImGui.begin_tab_item("party"):
            party()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("player"):
            current_build_render()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("waypoint builder / auto_mover"):
            auto_mover()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("teambuild"):
            teambuild()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("botting"):
            botting()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("debug"):
                
                PyImGui.text(f"{monitor.fps_stats()[1]}")
                PyImGui.text(f"{monitor.frame_stats()[1]}")
                constants.DEBUG = PyImGui.checkbox("with debugging logs", constants.DEBUG)
                
                PyImGui.begin_tab_bar("debug_tab_bar")
                
                if PyImGui.begin_tab_item("debug_execution"):
                    debug_execution()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("debug_sharedlock"):
                    debug_sharedlocks()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("debug_eventbus"):
                    debug_eventbus()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("debug_loader"):
                    PyImGui.text(f"History (newest on top) : ")
                    debug_skilbars()
                    PyImGui.end_tab_item()

                PyImGui.end_tab_bar()

        PyImGui.end_tab_bar()
    PyImGui.end()
    return

previous_map_status = False
map_change_throttler = ThrottledTimer(1_500)

def main():
    global previous_map_status, monitor, widget_window_size, widget_window_pos

    monitor.tick()
    widget_monitor.act()

    if Routines.Checks.Map.MapValid() and previous_map_status == False:
        map_change_throttler.Reset()
        if constants.DEBUG: print("map changed detected - we will throttle.")

    previous_map_status = Routines.Checks.Map.MapValid()
    
    if not Routines.Checks.Map.MapValid():
        return
    
    if not map_change_throttler.IsExpired():
        if constants.DEBUG: print("map changed - throttling.")

    if map_change_throttler.IsExpired():
        show_ui = not UIManager.IsWorldMapShowing() and not Map.IsInCinematic() and not Map.Pregame.InCharacterSelectScreen() and Py4GW.Console.is_window_active()
        if show_ui:
            gui()

        daemon()

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Custom Behaviors: Utility AI", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A specialized combat engine that utilizes Utility AI (Scoring)")
    PyImGui.text("logic rather than fixed trees. This system evaluates the current")
    PyImGui.text("game state to choose the most mathematically optimal action.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Utility Scoring: Dynamically weights skills and behaviors based on priority")
    PyImGui.bullet_text("Advanced Party Sync: Real-time coordination via Shared Memory (SMM)")
    PyImGui.bullet_text("Behavior Injection: Modular system for custom skill and party routines")
    PyImGui.bullet_text("Diagnostic Suite: Integrated FPS monitoring and Skillbar debugging")
    PyImGui.bullet_text("Automated Handling: Built-in NPC interaction and loot management")
    PyImGui.bullet_text("Event Bus Architecture: Decoupled communication for reactive combat states")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Oazix")

    PyImGui.end_tooltip()

__all__ = ["main"]
