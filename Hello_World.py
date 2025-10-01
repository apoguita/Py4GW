from Py4GWCoreLib import GLOBAL_CACHE
import PyImGui



def Draw_Window():
    dialog = 0x85
    thank_you = 0x86
    if PyImGui.begin("My Skill Farmer", True, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text("This is an example bot that jumps to a step name")
        if PyImGui.button("dialog 0x85"):
            GLOBAL_CACHE.Player.SendDialog(dialog)
            
        if PyImGui.button("dialog 0x86"):
            GLOBAL_CACHE.Player.SendDialog(thank_you)

        PyImGui.end()

def main():

    Draw_Window()



if __name__ == "__main__":
    main()
