# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import ImGui_Py     #ImGui wrapper
import PyAgent      #Agent functions and classes
import PyPlayer     #Player functions and classes
import traceback    #traceback to log stack traces
# End Necessary Imports

import math
#this is a proof of conept module to test the move to target functionality

module_name = "Move to target Test"

is_moving_to_target = False
has_arrived_to_target = False
distance_threshold = 100


def GetAgentLivingData(agent_id):
    """
    Fetch and return the living agent data for a given agent ID.
    
    Args:
        agent_id (int): The ID of the agent whose living data is to be retrieved.
        
    Returns:
        living_agent (PyAgent.LivingAgent): The living agent data if the agent exists and is living.
        None: If the agent doesn't exist or isn't a living agent.
    """
    agent_instance = PyAgent.PyAgent(agent_id)
    
    # Check if the agent exists and is a living agent
    if agent_instance and agent_instance.is_living:
        return agent_instance.living_agent
    else:
        Py4GW.Console.Log(module_name, f"Agent ID {agent_id} is either non-existent or not a living agent.")
        return None


def GetAgentCoords(agent_id):
    """
    Fetch and return the x, y, z coordinates of a given agent.
    
    Args:
        agent_id (int): The ID of the agent whose position is to be retrieved.
        
    Returns:
        tuple: (x, y, z) coordinates of the agent if it exists.
        None: If the agent doesn't exist.
    """
    agent_instance = PyAgent.PyAgent(agent_id)
    
    # Check if the agent exists
    if agent_instance:
        return (agent_instance.x, agent_instance.y, agent_instance.z)
    else:
        Py4GW.Console.Log(module_name, f"Agent ID {agent_id} does not exist.")
        return None

def GetDistance(agent_id_1, agent_id_2):
    """
    Calculate and return the Euclidean distance between two agents based on their (x, y, z) coordinates.
    
    Args:
        agent_id_1 (int): The ID of the first agent.
        agent_id_2 (int): The ID of the second agent.
        
    Returns:
        float: The distance between the two agents.
    """
    # Get the positions of both agents
    position_1 = GetAgentCoords(agent_id_1)
    position_2 = GetAgentCoords(agent_id_2)
    
    if position_1 and position_2:
        # Unpack the x, y, z values for both agents
        x1, y1, z1 = position_1
        x2, y2, z2 = position_2
        
        # Calculate the Euclidean distance
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)
        return distance
    else:
        Py4GW.Console.Log(module_name, "One or both agents' positions could not be retrieved.")
        return None


def GetPlayerHP():
    player = PyPlayer.PyPlayer()
    agent_instance = PyAgent.PyAgent(player.id)
    agent_living = GetAgentLivingData(agent_instance.id)
    return agent_living.hp



def DrawWindow():
    global module_name
    global is_moving_to_target
    global has_arrived_to_target
    global distance_threshold

    try:
        player = PyPlayer.PyPlayer()
        agent_instance = PyAgent.PyAgent(player.id)
        agent_living = agent_instance.living_agent
        target_id = player.target_id
        
        if  GetPlayerHP() <=0:
            Py4GW.Console.Log(module_name, "Player Is Dead", Py4GW.Console.MessageType.Error)


        if ImGui_Py.begin(module_name):
        
            ImGui_Py.text("Target ID: " + str(target_id))
            ImGui_Py.separator()
            ImGui_Py.text("Player Position: " + str(GetAgentCoords(player.id)))
            ImGui_Py.text("Target Position: " + str(GetAgentCoords(target_id)))
            distance_to_target = GetDistance(player.id, target_id)
            if distance_to_target is not None:
                ImGui_Py.text("Distance to Target: " + str(GetDistance(player.id, target_id)))
            # Example usage:

            ImGui_Py.separator()
            
            if target_id != 0:
                if ImGui_Py.button("Go To Target"):
                    target_coords = GetAgentCoords(target_id)
                    x, y, z = target_coords
                    player.Move(x,y)
                    is_moving_to_target = True

            if is_moving_to_target:
                if distance_to_target < distance_threshold:
                    has_arrived_to_target = True
                    is_moving_to_target = False
                else:
                    has_arrived_to_target = False

            if is_moving_to_target:
                ImGui_Py.text("Moving to Target")

            if has_arrived_to_target:
                ImGui_Py.text("Arrived to Target")
                    
            ImGui_Py.end()
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

