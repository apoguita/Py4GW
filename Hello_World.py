from Py4GWCoreLib import *
import time
import sys
import os



MODULE_NAME = "tester for everything"

action_queue = ActionQueueNode(75)

def DrawWindow():
    """ImGui draw function that runs every frame."""
    try:
        flags = PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.AlwaysAutoResize
        if PyImGui.begin("Py4GW", flags):

            if PyImGui.button("Travet To GH"):
                action_queue.add_action(Map.TravelGH)
                

        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)

def main():
    global action_queue
    """Runs every frame."""
    DrawWindow()

    if action_queue.action_queue_timer.HasElapsed(action_queue.action_queue_time):
        action_queue.execute_next()
        
if __name__ == "__main__":
    main()
