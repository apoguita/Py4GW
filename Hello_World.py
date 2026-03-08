import PyImGui
from Py4GWCoreLib import *




def main():


    if PyImGui.begin ("Immediate Window Reference"):
        if PyImGui.button("Toggle UI Window"):
            UIManager.SetWindowVisible(WindowID.WindowID_InventoryBags, False)
    PyImGui.end()


if __name__ == "__main__":
    main()
