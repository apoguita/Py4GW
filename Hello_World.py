from Py4GWCoreLib import GLOBAL_CACHE
import PyImGui
import PyPlayer


dialog = 0x000AA

def draw_window():
    global dialog
    
    if PyImGui.begin("dialog tester"):

        if PyImGui.button("dialog trough GLOBAL_CACHE"):
            GLOBAL_CACHE.Player.SendDialog(dialog)
            
        if PyImGui.button("dialog directly"):
            player_instance = PyPlayer.PyPlayer()
            player_instance.SendDialog(dialog)
            

    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()
