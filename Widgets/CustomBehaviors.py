
import pathlib
import sys
from Py4GWCoreLib.Py4GWcorelib import LootConfig, Utils
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

# Iterate through all modules in sys.modules (already imported modules)
# Iterate over all imported modules and reload them
for module_name in list(sys.modules.keys()):
    if module_name not in ("sys", "importlib", "cache_data"):
        try:
            if "behavior" in module_name.lower():
                print(f"Reloading module: {module_name}")
                del sys.modules[module_name]
                # importlib.reload(module_name)
                pass
        except Exception as e:
            print(f"Error reloading module {module_name}: {e}")

from typing import List
from HeroAI.cache_data import CacheData
from Py4GWCoreLib import ImGui, PyImGui, Routines, ActionQueueManager, Player, GLOBAL_CACHE, IconsFontAwesome5, SharedCommandType
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader, MatchResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.gui.current_build import render as current_build_render
from Widgets.CustomBehaviors.gui.party import render as party
from Widgets.CustomBehaviors.gui.debug_skillbars import render as debug_skilbars
from Widgets.CustomBehaviors.gui.debug_execution import render as debug_execution
from Widgets.CustomBehaviors.gui.deamon import deamon as deamon

party_forced_state_combo = 0
DEBUG = True
current_path = pathlib.Path.cwd()
print(f"current_path is : {current_path}")

def gui():
    # PyImGui.set_next_window_size(260, 650)
    # PyImGui.set_next_window_size(460, 800)

    global party_forced_state_combo
    
    window_module = ImGui.WindowModule("Custom behaviors", window_name="Custom behaviors", window_size=(0, 0), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
    shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()

    if PyImGui.begin(window_module.window_name, window_module.window_flags):
        PyImGui.begin_tab_bar("current_build")

        if PyImGui.begin_tab_item("party"):
            party()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("current_build"):
            current_build_render()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("debug_execution"):
            debug_execution()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("debug_skillbars"):
            debug_skilbars()
            PyImGui.end_tab_item()

        PyImGui.end_tab_bar()
    PyImGui.end()
    return

def main():

    if not Routines.Checks.Map.MapValid():
        return

    gui()
    deamon()
    

def configure():
    # gui()
    pass

__all__ = ["main", "configure"]
