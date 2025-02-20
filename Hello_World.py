from Py4GWCoreLib import *
import re
import sys

MODULE_NAME = "chat logger"


def DrawWindow():
    try:
        if PyImGui.begin("Async data Tester"):
            if PyImGui.button("travel to GH"):
                Map.TravelGH()
                             
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)






def main():
    DrawWindow()


if __name__ == "__main__":
    main()
