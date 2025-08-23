
from Py4GWCoreLib import *


selected_step = 0

#dialog = 0x0000008A #get bow
#dialog = 0x63E #enter quest

WARRIOR = 0x813D0B
RANGER = 0x813D0F
MONK = 0x813D0D
NECROMANCER = 0x813D0C
MESMER = 0x813D0E
ELEMENTALIST = 0x813D09
ASSASSIN = 0x813D08
RITUALIST = 0x813D0A


def main():
    global selected_step
    

    if PyImGui.begin("PathPlanner Test", PyImGui.WindowFlags.AlwaysAutoResize):
        
        if PyImGui.button("Proceed to Shing Jea"):
            GLOBAL_CACHE.Player.SendDialog(0x85)

        if PyImGui.button("Unlock Warrior Secondary"):
            GLOBAL_CACHE.Player.SendDialog(WARRIOR)

        if PyImGui.button("Unlock Ranger Secondary"):
            GLOBAL_CACHE.Player.SendDialog(RANGER)

        if PyImGui.button("Unlock Monk Secondary"):
            GLOBAL_CACHE.Player.SendDialog(MONK)

        if PyImGui.button("Unlock Necromancer Secondary"):
            GLOBAL_CACHE.Player.SendDialog(NECROMANCER)

        if PyImGui.button("Unlock Mesmer Secondary"):
            GLOBAL_CACHE.Player.SendDialog(MESMER)

        if PyImGui.button("Unlock Elementalist Secondary"):
            GLOBAL_CACHE.Player.SendDialog(ELEMENTALIST)

        if PyImGui.button("Unlock Assassin Secondary"):
            GLOBAL_CACHE.Player.SendDialog(ASSASSIN)

        if PyImGui.button("Unlock Ritualist Secondary"):
            GLOBAL_CACHE.Player.SendDialog(RITUALIST)

    PyImGui.end()


if __name__ == "__main__":
    main()
