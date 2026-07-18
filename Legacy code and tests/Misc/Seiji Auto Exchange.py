import Py4GW
from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

npc_name = "Seiji"

frame_id= 0

def exchange ():
    global frame_id
    while True:
        UIManager.FrameClick(frame_id)
        yield from Routines.Yield.wait(25)

def main():
    global frame_id
    try:
        window_flags=PyImGui.WindowFlags.AlwaysAutoResize #| PyImGui.WindowFlags.MenuBar
        if PyImGui.begin("move", window_flags):

            
            if PyImGui.button("start exchange"):
                frame_id = UIManager.GetChildFrameID(3613855137,[0,0,6])
                GLOBAL_CACHE.Coroutines.append(exchange())
              
            if PyImGui.button("stop exchange"):
                GLOBAL_CACHE.Coroutines.clear()  
            
                
            
        PyImGui.end()
        


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
if __name__ == "__main__":
    main()
