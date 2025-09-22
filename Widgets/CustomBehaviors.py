
import pathlib
import sys

import Py4GW
from Py4GWCoreLib.Py4GWcorelib import LootConfig, ThrottledTimer, Utils
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.fps_monitor import FPSMonitor
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.widget_monitor import WidgetMonitor

# Iterate through all modules in sys.modules (already imported modules)
# Iterate over all imported modules and reload them
for module_name in list(sys.modules.keys()):
    if module_name not in ("sys", "importlib", "cache_data"):
        try:
            if "behavior" in module_name.lower():
                Py4GW.Console.Log("CustomBehaviors", f"Reloading module: {module_name}")
                del sys.modules[module_name]
                # importlib.reload(module_name)
                pass
        except Exception as e:
            Py4GW.Console.Log("CustomBehaviors", f"Error reloading module {module_name}: {e}")

from typing import List
from HeroAI.cache_data import CacheData
from Py4GWCoreLib import ImGui, PyImGui, Routines, ActionQueueManager, Player, GLOBAL_CACHE, IconsFontAwesome5, SharedCommandType
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader, MatchResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.gui.current_build import render as current_build_render
from Widgets.CustomBehaviors.gui.party import render as party
from Widgets.CustomBehaviors.gui.debug_skillbars import render as debug_skilbars
from Widgets.CustomBehaviors.gui.debug_execution import render as debug_execution
from Widgets.CustomBehaviors.gui.debug_sharedlocks import render as debug_sharedlocks
from Widgets.CustomBehaviors.gui.debug_eventbus import render as debug_eventbus
from Widgets.CustomBehaviors.gui.auto_mover import render as auto_mover
from Widgets.CustomBehaviors.gui.daemon import daemon as daemon
from Widgets.CustomBehaviors.gui.botting import render as botting
from Widgets.CustomBehaviors.gui.daemon_botting import daemon_botting

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
    
    window_module:ImGui.WindowModule = ImGui.WindowModule("Custom behaviors", window_name="Custom behaviors - Multiboxing over utility-ai algorithm.", window_size=(0, 0), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
    shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()

    if PyImGui.begin(window_module.window_name, window_module.window_flags):
        widget_window_size = PyImGui.get_window_size()
        widget_window_pos = PyImGui.get_window_pos()
        
        PyImGui.text(f"{monitor.fps_stats()[1]}")
        PyImGui.text(f"{monitor.frame_stats()[1]}")

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

        if PyImGui.begin_tab_item("botting"):
            botting()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("debug"):
                
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
map_change_throttler = ThrottledTimer(250)

def main():
    global previous_map_status, monitor, widget_window_size, widget_window_pos

    daemon_botting(widget_window_size, widget_window_pos) # botting deamon is fully autonomous, no throttling or map check

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
        gui()
        daemon()

def configure():
    # gui()
    pass

__all__ = ["main", "configure"]
