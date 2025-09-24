from __future__ import annotations
from typing import List, Tuple

import PyImGui
from Py4GWCoreLib import (GLOBAL_CACHE, Keystroke, Key, Py4GW, UIManager, ControlAction, Botting,
                          AutoPathing, ImGui)

started = False
toggle = False
last_toggle = False  # remember the previous state

def main():
    global toggle, last_toggle, started

    try:
        if PyImGui.begin("key sender"):
            if PyImGui.button("send key"):
                toggle = not toggle

            if PyImGui.button("send keypress/release"):
                UIManager.Keypress(ControlAction.ControlAction_MoveBackward.value, 0)
                #Keystroke.PressAndRelease(Key.S.value)


            # Only act if the toggle value changed
            if toggle != last_toggle:
                if toggle:
                    UIManager.Keydown(ControlAction.ControlAction_MoveBackward.value, 0)
                    #Keystroke.Press(Key.S.value)
                else:
                    UIManager.Keyup(ControlAction.ControlAction_MoveBackward.value, 0)
                    #Keystroke.Release(Key.S.value)
                last_toggle = toggle

    except Exception as e:
        Py4GW.Console.Log("send key", f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()
