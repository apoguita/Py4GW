from __future__ import annotations
from typing import List, Tuple

import PyImGui
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui)


    
dialog = 0x84



def main():
    global dialog

    try:
        if PyImGui.begin("dialog sender"):
            dialog = PyImGui.input_int("dialog id", dialog)
            if PyImGui.button("send dialog"):
                GLOBAL_CACHE.Player.SendDialog(dialog)
    except Exception as e:
        Py4GW.Console.Log("send dialog", f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()
