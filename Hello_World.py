from Py4GWCoreLib import ImGui, GLOBAL_CACHE, TitleID
import PyImGui, Py4GW
import os

MODULE_NAME = "Window Manipulator"


def Draw_Window():  
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        pass
    PyImGui.end()


def main():
    Draw_Window()


if __name__ == "__main__":
    main()
