import Py4GW
from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

x =0.0
y = 0.0

def main():
    global x,y
    try:
        window_flags=PyImGui.WindowFlags.AlwaysAutoResize #| PyImGui.WindowFlags.MenuBar
        if PyImGui.begin("move", window_flags):
            
            current_x, current_y = Player.GetXY()
            PyImGui.text(f"Current Position: x={current_x}, y={current_y}")
            PyImGui.separator()
            x = PyImGui.input_float("x", x)
            y = PyImGui.input_float("y", y)
            if PyImGui.button("Move"):
                Player.Move(x, y)
                            
            if PyImGui.button("Move trough ActionQueue"):
                GLOBAL_CACHE.Player.Move(x, y)
           
            
        PyImGui.end()
        


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
if __name__ == "__main__":
    main()
