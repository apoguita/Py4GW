from Py4GWCoreLib import GLOBAL_CACHE
import PyImGui
import Py4GW

def draw_window():
    if PyImGui.begin("Address tester"):
        characters = GLOBAL_CACHE.Player.GetLoginCharacters()
        for char in characters:
            PyImGui.text(f"Char ID: {char.player_name} Campaign: {char.campaign}")
            

    PyImGui.end()



def main():
    draw_window()

if __name__ == "__main__":
    main()
