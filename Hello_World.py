from Py4GWCoreLib import (UIManager, GLOBAL_CACHE, Console, ConsoleLog, Routines, ThrottledTimer,
                          Keystroke, Key, FrameInfo, CHAR_MAP
                          )
import PyImGui
import Py4GW

from datetime import datetime, timedelta
BOOT_TIME = datetime.now() - timedelta(milliseconds=Py4GW.Game.get_tick_count64())

def draw_window():
    if PyImGui.begin("Address tester"):
        
        PyImGui.text(f"is on loading screen: {GLOBAL_CACHE.Player.InCharacterSelectScreen()}")
            

    PyImGui.end()



def main():
    draw_window()
    target = GLOBAL_CACHE.Player.GetTargetID()
    model = GLOBAL_CACHE.Agent.GetModelID(target)


if __name__ == "__main__":
    main()
