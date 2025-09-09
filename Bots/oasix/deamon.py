import sys

import PyImGui

from Bots.oasix.areas.planter_fiber import PlantFiber
from Bots.oasix.areas.simple_bot_4_steps import SimpleBot4Steps
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Py4GWcorelib import LootConfig
from Py4GWCoreLib.enums import Range

# Iterate through all modules in sys.modules (already imported modules)
# Iterate over all imported modules and reload them
for module_name in list(sys.modules.keys()):
    if module_name not in ("sys", "importlib", "cache_data"):
        try:
            if "oasix_nicky" in module_name.lower():
                print(f"Reloading module: {module_name}")
                del sys.modules[module_name]
                # importlib.reload(module_name)
                pass
        except Exception as e:
            print(f"Error reloading module {module_name}: {e}")

from typing import Any, List
from HeroAI.cache_data import CacheData

bot:SimpleBot4Steps = PlantFiber()
generator = bot.act()

def main():

    if not Routines.Checks.Map.MapValid():
        return

    gui()
    next(generator)

def gui():
    PyImGui.begin("ooooasiiix", PyImGui.WindowFlags.AlwaysAutoResize)
    PyImGui.text(f"POC custom-behavior with botting")
    PyImGui.end()

def configure():
    pass

__all__ = ["main", "configure"]
