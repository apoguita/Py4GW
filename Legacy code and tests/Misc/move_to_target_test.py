# Necessary Imports
from Py4GWCoreLib import *
import PyImGui
# End Necessary Imports

import math
#this is a proof of conept module to test the move to target functionality

module_name = "Move to target Test"

is_moving_to_target = False
has_arrived_to_target = False
distance_threshold = 100


def DrawWindow():
    global module_name
    global is_moving_to_target
    global has_arrived_to_target
    global distance_threshold

    try:
        player_id = Player.GetAgentID()
        target_id = Player.GetTargetID()
        
        if  Agent.GetHealth(Player.GetAgentID()) <=0:
            Py4GW.Console.Log(module_name, "Player Is Dead", Py4GW.Console.MessageType.Error)


        if PyImGui.begin(module_name):
        
            PyImGui.text("Target ID: " + str(target_id))
            PyImGui.separator()
            PyImGui.text("Player Position: " + str(Agent.GetXY(player_id)))
            PyImGui.text("Target Position: " + str(Agent.GetXY(target_id)))
            distance_to_target = Utils.Distance(player_id, target_id)
            if distance_to_target is not None:
                PyImGui.text("Distance to Target: " + str(Utils.Distance(player_id, target_id)))
            # Example usage:

            PyImGui.separator()
            
            if target_id != 0:
                if PyImGui.button("Go To Target"):
                    target_coords = Agent.GetXYZ(target_id)
                    x, y, z = target_coords
                    Player.Move(x,y)
                    is_moving_to_target = True

            if is_moving_to_target:
                if distance_to_target < distance_threshold:
                    has_arrived_to_target = True
                    is_moving_to_target = False
                else:
                    has_arrived_to_target = False

            if is_moving_to_target:
                PyImGui.text("Moving to Target")

            if has_arrived_to_target:
                PyImGui.text("Arrived to Target")
                    
            PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

# main function must exist in every script and is the entry point for your script's execution.
def main():
    global module_name
    try:
        DrawWindow()

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        # Optional: Code that will run whether an exception occurred or not
        #Py4GW.Console.Log(module_name, "Execution of Main() completed", Py4GW.Console.MessageType.Info)
        # Place any cleanup tasks here
        pass

# This ensures that Main() is called when the script is executed directly.
if __name__ == "__main__":
    main()

