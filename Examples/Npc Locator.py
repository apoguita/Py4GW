import Py4GW
from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

npc_name = "Seiji"

def select_npc (npc_name):
    yield from Routines.Yield.Agents.TargetAgentByName(npc_name)
    
    
def main():
    global npc_name
    try:
        window_flags=PyImGui.WindowFlags.AlwaysAutoResize #| PyImGui.WindowFlags.MenuBar
        if PyImGui.begin("move", window_flags):
            
            npc_name = PyImGui.input_text("NPC Name", npc_name)
            
            if PyImGui.button("Move to NPC"):
                GLOBAL_CACHE.Coroutines.append(select_npc(npc_name))
                
            
        PyImGui.end()
        


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
if __name__ == "__main__":
    main()
