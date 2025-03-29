from Py4GWCoreLib import *
import time
import sys
import os



MODULE_NAME = "tester for everything"

item_id = 0
item_name = ""


def DrawWindow():
    """ImGui draw function that runs every frame."""
    global item_id
    global item_name
    try:
        if PyImGui.begin("tester"):
                account_name = Player.GetAccountName()

                PyImGui.text(f"account_name: {account_name}")

        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)

def main():
    """Runs every frame."""
    DrawWindow()

if __name__ == "__main__":
    main()
