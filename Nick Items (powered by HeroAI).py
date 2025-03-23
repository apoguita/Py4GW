from Py4GWCoreLib import *
from HeroAI.shared_memory_manager import *
from HeroAI.game_option import *


MODULE_NAME = "tester for everything"

fog = False

def DrawWindow():
    """ImGui draw function that runs every frame."""
    global fog
    try:
        flags = PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.AlwaysAutoResize
        if PyImGui.begin("Py4GW", flags):

            if PyImGui.button("Toggle Fog"):
                Py4GW.Game.SetFog(fog)
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)

def main():
    """Runs every frame."""
    DrawWindow()

if __name__ == "__main__":
    main()
