
from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, AutoPathing, Py4GW, FSM, ConsoleLog, Color, DXOverlay
from typing import List, Tuple, Any, Generator, Callable
import PyImGui




selected_step = 0

#dialog = 0x0000008A #get bow
dialog = 0x63E #enter quest
def main():
    global selected_step

    if PyImGui.begin("PathPlanner Test", PyImGui.WindowFlags.AlwaysAutoResize):
        
        if PyImGui.button("interact"):
            GLOBAL_CACHE.Player.SendDialog(dialog)
            

    PyImGui.end()


if __name__ == "__main__":
    main()
