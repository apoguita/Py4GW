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
        flags = PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.AlwaysAutoResize
        if PyImGui.begin("Py4GW", flags):
            hovered_item = Inventory.GetHoveredItemID()
            
            if hovered_item != 0:
                if item_id != hovered_item:
                    item_id = hovered_item
                    temp_item_name = Item.RequestName(item_id)
                    
            if item_id != 0:
                temp_item_name = Item.GetName(item_id)
                if temp_item_name != "":
                    item_name = temp_item_name

                item_model = Item.GetModelID(item_id)
                
                PyImGui.text(f"Item Name: {item_name}")
                PyImGui.text(f"Item Model ID: {item_model}")

        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)

def main():
    """Runs every frame."""
    DrawWindow()

if __name__ == "__main__":
    main()
