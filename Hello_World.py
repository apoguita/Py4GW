from Py4GWCoreLib import (ActionQueueManager, GLOBAL_CACHE, Console, ConsoleLog, Routines, ThrottledTimer,
                          Keystroke, Key, FrameInfo, CHAR_MAP
                          )
import PyImGui
from typing import Generator, Any
import ctypes



def draw_window():
    if PyImGui.begin("Adress tester"):
        if PyImGui.button("Execute call instruction"):
            GLOBAL_CACHE.Coroutines.append(Routines.Yield.RerollCharacter.DeleteAndCreateCharacter("Dialoguer Test","Dialoguer Main","Nightfall","Dervish",timeout_ms=25000,log=True))
            
        if PyImGui.button("Create Character"):
            GLOBAL_CACHE.Coroutines.append(Routines.Yield.RerollCharacter.CreateCharacter("Dialoguer Test","Nightfall","Dervish",timeout_ms=25000,log=True))
        
    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()
