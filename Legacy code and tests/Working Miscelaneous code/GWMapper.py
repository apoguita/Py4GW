"""
GWMapper
Note: Python 3.12 (32 bit) is required for this script to work.
Instructions:
1. Install dependencies if needed: "pip install plotly", the script will attempt to install if missing (Plotly)
2. Run PY4GW.dll as plugin from within GWToolbox
3. Navigate to GWMapper.py from PY4GW
4. Run
5. Logs and Maps will save to /Coordinate_Logs/MAP_NAME

"""
import logging
from Py4GWCoreLib import *
from datetime import datetime
import os
import subprocess
import sys

try:
    import plotly
except ImportError:
    Py4GW.Console.Log("GWMapper", "Plotly not installed...Installing...", Py4GW.Console.MessageType.Error)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly"])
import plotly.graph_objects as go

module_name = "GWMapper"

player_y=0
player_x=0
activate_coords = False
timer_check = 0
timer=Py4GW.Timer()
update_frequency= 3
enemy_xy ={}
ally_xy ={}
player_id = Player.GetAgentID()
player_xy= []
cart_xy = []
custom_xy = []
custom_name="custom_name"
player_update_distance= 300
enemy_update_distance= 500



def GetTimer():
    global timer_check
    if timer_check == 0 and timer.get_elapsed_time() == 0:
        return True
    if timer_check != 0 and timer.get_elapsed_time() > 0:
        if timer.has_elapsed(timer_check):
            # Py4GW.Console.Log(bot_vars.window_module.module_name, f"Stopping timer. Elapsed_time = {FSM_vars.casting_timer.get_elapsed_time()}", Py4GW.Console.MessageType.Info)
            player_timer_check = 0
            timer.reset()
            return True

    return False

def TimerFunctions():
    global timer_check, timer

    if GetTimer():
        GetPlayerCoords()
        GetEnemyCoords()
        GetAllyCoords()

        timer_check = update_frequency * 1000
        timer.reset()

def GetPlayerCoords():
    global timer
    global player_x, player_y
    global player_xy
    # Update the player coordinates
    player_x, player_y = Player.GetXY()
    # Round the coordinates to 1 decimal place
    rounded_x, rounded_y = round(player_x, 1), round(player_y, 1)

    # Create the new coordinate tuple
    new_coord = (rounded_x, rounded_y)

    # Check if this is the first coordinate or if the new coordinate is far enough from the last one
    if not player_xy or (
            abs(new_coord[0] - player_xy[-1][0]) >= 300 or
            abs(new_coord[1] - player_xy[-1][1]) >= 300
    ):
        # Add the new coordinate to the list (maintains order)
        player_xy.append(new_coord)

    # Debug log to track coordinates
    Py4GW.Console.Log("GWMapper", f"New player coordinates: {new_coord}", Py4GW.Console.MessageType.Info)



def GetEnemyCoords():
    global enemy_array, enemy_xy, alive_enemies


     # Update the enemy coordinates
    enemy_array = AgentArray.GetEnemyArray()
    alive_enemies = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    if not alive_enemies:
        Py4GW.Console.Log("Enemy Array", "No enemies found.", Py4GW.Console.MessageType.Warning)
        return  # Stop the function if no enemies

    # Generate a list of (agent_id, x, y) tuples using list comprehension
    #enemy_xy = {agent_id: Agent.GetXY(agent_id) for agent_id in enemy_array}
    for agent_id in alive_enemies:
        # Get the current coordinates (assuming valid (x, y) values)
        x, y = Agent.GetXY(agent_id)

        # Round the coordinates to 1 decimal place
        x, y = round(x, 1), round(y, 1)

        # Create the coordinate tuple
        coord_tuple = (x, y)

        # Check if the agent already has coordinates stored
        if agent_id in enemy_xy:
            last_coord = enemy_xy[agent_id][-1]  # Get the most recent coordinate

            # Calculate the difference in x and y
            delta_x = abs(coord_tuple[0] - last_coord[0])
            delta_y = abs(coord_tuple[1] - last_coord[1])

            # Only add the new coordinate if it differs by 500 or more units
            if delta_x >= 500 or delta_y >= 500:
                enemy_xy[agent_id].append(coord_tuple)
        else:
            # Initialize the list with the first set of coordinates
            enemy_xy[agent_id] = [coord_tuple]




    Py4GW.Console.Log("Enemy Array", f"Enemies: {enemy_xy}", Py4GW.Console.MessageType.Info)


def GetAllyCoords():
    global ally_xy, ally_array

    # Update Ally agent coordinates
    ally_array = AgentArray.GetAllyArray()

    if not ally_array:
        Py4GW.Console.Log("Ally Array", "No Ally NPC found.", Py4GW.Console.MessageType.Warning)
        return  # Stop the function if no enemies

    # Generate a list of (agent_id, x, y) tuples using list comprehension

    for agent_id in ally_array:
        # Get the current coordinates (assuming valid (x, y) values)
        x, y = Agent.GetXY(agent_id)

        # Round the coordinates to 1 decimal place
        x, y = round(x, 1), round(y, 1)

        # Create the coordinate tuple
        coord_tuple = (x, y)

        # Check if the agent already has coordinates stored
        if agent_id in ally_xy:
            last_coord = ally_xy[agent_id][-1]  # Get the most recent coordinate

            # Calculate the difference in x and y
            delta_x = abs(coord_tuple[0] - last_coord[0])
            delta_y = abs(coord_tuple[1] - last_coord[1])

            # Only add the new coordinate if it differs by 20 or more units
            if delta_x >= 500 or delta_y >= 500:
                ally_xy[agent_id].append(coord_tuple)
        else:
            # Initialize the list with the first set of coordinates
            ally_xy[agent_id] = [coord_tuple]



def GetCartoCoords():
    global cart_xy

    # Initialize cart_xy as an empty list if it doesn't exist
    if 'cart_xy' not in globals() or not isinstance(cart_xy, list):
        cart_xy = []

    # Get the current player's coordinates
    cart_x, cart_y = Player.GetXY()

    # Round the coordinates to 2 decimal places
    cart_x, cart_y = round(cart_x, 2), round(cart_y, 2)

    # Create the coordinate tuple
    new_coord = (cart_x, cart_y)

    # Add the new coordinate to the list (maintains all coordinates)
    cart_xy.append(new_coord)

    # Debug log to track coordinates
    Py4GW.Console.Log("GWMapper", f"New Cartography coordinates: {new_coord}", Py4GW.Console.MessageType.Info)

def GetCustomCoords():
    global custom_xy
    global custom_name
    # Initialize cart_xy as an empty list if it doesn't exist
    if 'custom_xy' not in globals() or not isinstance(custom_xy, list):
        custom_xy = []

    # Get the current player's coordinates
    custom_x, custom_y = Player.GetXY()

    # Round the coordinates to 2 decimal places
    custom_x, custom_y = round(custom_x, 2), round(custom_y, 2)

    # Create the coordinate tuple
    new_coord = (custom_x, custom_y)

    # Add the new coordinate to the list (maintains all coordinates)
    custom_xy.append(new_coord)

    # Debug log to track coordinates
    Py4GW.Console.Log("GWMapper", f"New {custom_name} coordinates: {new_coord}", Py4GW.Console.MessageType.Info)






def CoordLogger(log_type, log_name, data, header="GWMapper"):
    global map_name

    """
    A template function to log data to a specific log type folder (e.g., 'enemy', 'player', 'custom').

    Parameters:
        log_type (str): The type of log (e.g., 'enemy', 'player', 'custom').
        log_name (str): The base name for the log file.
        data (list): The data to be logged (e.g., list of coordinates).
        header (str): A header message to include in the log file. Defaults to 'Custom Coords'.
    """


    # Generate a timestamp (e.g., '20241026_2235')
    timestamp = datetime.now().strftime('%Y%m%d_%H')

    # Create the subfolder for the log type (e.g., 'logs/enemy/')
    log_folder = os.path.join('Coordinate_Logs', map_name)
    os.makedirs(log_folder, exist_ok=True)  # Create the subfolder if it doesn't exist

    # Create the full path with the timestamped filename
    file_path = os.path.join(log_folder, f"{map_name}_{log_name[:-4]}_{timestamp}.txt")

    try:
        # Open the file using the generated path
        with open(file_path, 'a') as log_file:
            # Write the header and metadata
            log_file.write(f"Log Type: {log_type.capitalize()}\n")
            log_file.write(f"Log File: {os.path.basename(file_path)}\n\n")
            log_file.write(f"{header}:\n")

            # Write the data to the log file
            for item in data:
                log_file.write(f" {item}\n")

        # Log success message to the console
        Py4GW.Console.Log(
            "GWMapper",
            f"{log_type.capitalize()} data logged to {file_path}",
            Py4GW.Console.MessageType.Info
        )
    except Exception as e:
        # Log any error that occurs
        Py4GW.Console.Log(
            "GWMapper",
            f"Failed to log {log_type} data: {str(e)}",
            Py4GW.Console.MessageType.Error
        )

def CoordMapper():
    global player_x, player_y, player_xy, cart_xy, custom_xy, custom_name, enemy_xy, ally_xy

    import plotly.graph_objects as go
    map_timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    enemy_traces = []
    ally_traces = []
    save_dir = f"./Coordinate_Logs/{map_name}"
    file_name = f"{map_name}_{map_timestamp}).html"
    full_path = os.path.join(save_dir, file_name)

    # Step 2: Create the directory if it doesn't exist
    try:
        os.makedirs(save_dir, exist_ok=True)  # Create directories as needed
        Py4GW.Console.Log("GWMapper", f"Directory created or already exists: {save_dir}", Py4GW.Console.MessageType.Info)
    except Exception as e:
        Py4GW.Console.Log("GWMapper", f"Error creating directory: {save_dir}", Py4GW.Console.MessageType.Error)

    # Step 3: Verify that the directory exists
    if os.path.exists(save_dir):
        Py4GW.Console.Log("GWMapper", f"Directory verified: {save_dir}", Py4GW.Console.MessageType.Info)
    else:
        Py4GW.Console.Log("GWMapper", f"Directory does not exist: {save_dir}", Py4GW.Console.MessageType.Error)

    # Create the plot
    fig = go.Figure()
    if player_xy:
        Py4GW.Console.Log("Coordinate Logger", "Mapping player coordinates...", Py4GW.Console.MessageType.Info)
        fig.add_trace(go.Scatter(
            x=[coord[0] for coord in player_xy],
            y=[coord[1] for coord in player_xy],
            mode='markers+lines',
            marker=dict(size=10, color='blue'),
            name='Player'
        ))

    # Add enemy coordinates (check if dictionary is not empty)
    if enemy_xy:
        Py4GW.Console.Log("Coordinate Logger", "Mapping enemy coordinates...", Py4GW.Console.MessageType.Info)
        for agent_id, coords in enemy_xy.items():
            if coords:
                fig.add_trace(go.Scatter(
                    x=[coord[0] for coord in coords],
                    y=[coord[1] for coord in coords],
                    mode='markers+lines',
                    marker=dict(size=10, color='red'),
                    name=f'Enemy {agent_id}'
                ))
                enemy_traces.append(len(fig.data) - 1)
            else:
                Py4GW.Console.Log("Coordinate Logger", f"Skipping empty coordinates for enemy {agent_id}",
                                  Py4GW.Console.MessageType.Error)

    # Add ally coordinates (check if dictionary is not empty)
    if ally_xy:
        Py4GW.Console.Log("Coordinate Logger", "Mapping ally coordinates...", Py4GW.Console.MessageType.Info)
        for agent_id, coords in ally_xy.items():
            if coords:
                fig.add_trace(go.Scatter(
                    x=[coord[0] for coord in coords],
                    y=[coord[1] for coord in coords],
                    mode='markers+lines',
                    marker=dict(size=10, color='green'),
                    name=f'Ally {agent_id}'
                ))
                ally_traces.append(len(fig.data) - 1)
            else:
                Py4GW.Console.Log("Coordinate Logger", f"Skipping empty coordinates for ally {agent_id}",
                                  Py4GW.Console.MessageType.Error)

    # Add cartography coordinates (check if list is not empty)
    if cart_xy:
        Py4GW.Console.Log("Coordinate Logger", "Adding cartography coordinates...", Py4GW.Console.MessageType.Info)
        fig.add_trace(go.Scatter(
            x=[coord[0] for coord in cart_xy],
            y=[coord[1] for coord in cart_xy],
            mode='markers',
            marker=dict(size=10, color='purple'),
            name='Cartography'
        ))

    # Add custom coordinates (check if list is not empty)
    if custom_xy:
        Py4GW.Console.Log("Coordinate Logger", "Adding custom coordinates...", Py4GW.Console.MessageType.Info)
        fig.add_trace(go.Scatter(
            x=[coord[0] for coord in custom_xy],
            y=[coord[1] for coord in custom_xy],
            mode='markers',
            marker=dict(size=10, color='orange'),
            name='Custom'
        ))

    all_visible = [True] * len(fig.data)
    enemies_hidden = [i not in enemy_traces for i in range(len(fig.data))]
    allies_hidden = [i not in ally_traces for i in range(len(fig.data))]

    # Configure layout with buttons
    fig.update_layout(
        title='GWMapper Coordinates',
        xaxis_title='X Coordinate',
        yaxis_title='Y Coordinate',
        legend=dict(title='Coordinate Types', x=1, y=1, traceorder='normal'),
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                showactive=True,
                buttons=[
                    dict(
                        label="Show All",
                        method="update",
                        args=[{"visible": all_visible}],
                    ),
                    dict(
                        label="Hide All Enemies",
                        method="update",
                        args=[{"visible": enemies_hidden}],
                    ),
                    dict(
                        label="Hide All Allies",
                        method="update",
                        args=[{"visible": allies_hidden}],
                    )
                ],
                pad={"r": 10, "t": 10},
                x=0.5,
                xanchor="left",
                y=-0.2,
                yanchor="top"
            )
        ]
    )
    # Save the plot as HTML

    fig.write_html(str(full_path))  # Convert Path to string for compatibility



# Example of additional utility function
def DrawWindow():
    global module_name,custom_name
    global main_window_state
    global player_x, player_y
    global activate_coords
    global title
    global timer
    global update_frequency, enemy_array
    global player_xy, enemy_xy, cart_xy, ally_xy, custom_name, custom_xy
    global map_name
    global player_update_distance, enemy_update_distance
    map_name = Map.GetMapName()
    columns = 3  # Number of columns grids
    selected_button_index = 0
    try:
        width, height = 600,300
        PyImGui.set_next_window_size(width, height)

        if PyImGui.begin("GWMapper", PyImGui.WindowFlags.NoCollapse):


            PyImGui.text(f"Current Map: {map_name}\r")
            PyImGui.text(f"Player Coordinates: ({player_x:.2f}, {player_y:.2f})")
            if PyImGui.begin_table("Activate Table", columns):  # Start table layout
                # Render the "Clear All Coords" button
                PyImGui.table_next_column()
                activate_coords = PyImGui.checkbox("Activate", activate_coords)
                if activate_coords:
                    TimerFunctions()

                PyImGui.table_next_column()
                PyImGui.table_next_column()

                if PyImGui.button("Add Carto Coord"):
                    GetCartoCoords()

                PyImGui.table_next_column()

                PyImGui.text("Click to activate.")

                PyImGui.table_next_column()
                PyImGui.table_next_column()

                if PyImGui.button("Add Custom Coord"):
                    GetCustomCoords()

                PyImGui.table_next_column()

                if PyImGui.button("Write Coords to File"):
                    CoordLogger("Player", "Player", player_xy, "GWMapper- Player Coordinates")
                    CoordLogger("Enemy", "Enemy", enemy_xy.items(), "GWMapper- Enemy Coordinates")
                    CoordLogger("Allys", "Allys", ally_xy.items(), "GWMapper- Ally Coordinates")
                    CoordLogger("Cartography", "Carto", cart_xy, "GWMapper- Cartography Coordinates")
                    CoordLogger(custom_name, custom_name, custom_xy, f"GWMapper- {custom_name} Coordinates")
                    CoordMapper()

                PyImGui.table_next_column()

                if PyImGui.button("Clear All Coords"):
                    player_x = 0
                    player_y = 0
                    player_xy.clear()
                    enemy_xy.clear()
                    ally_xy.clear()
                    cart_xy.clear()
                    custom_xy.clear()

                PyImGui.end_table()








            if PyImGui.collapsing_header("Clear Coordinates"):
                if PyImGui.begin_table("ClearButtonTable", columns):  # Start table layout
                    # Render the "Clear All Coords" button
                    PyImGui.table_next_column()
                    if PyImGui.button("Clear All Coords"):
                        player_x = 0
                        player_y = 0
                        player_xy.clear()
                        enemy_xy.clear()
                        ally_xy.clear()
                        cart_xy.clear()
                        custom_xy.clear()

                    # Render the "Clear Player Coords" button
                    PyImGui.table_next_column()
                    if PyImGui.button("Clear Player Coords"):
                        player_x = 0
                        player_y = 0
                        player_xy.clear()

                    # Render the "Clear Enemy Coords" button
                    PyImGui.table_next_column()
                    if PyImGui.button("Clear Enemy Coords"):
                        enemy_xy.clear()

                    # Render the "Clear Ally Coords" button
                    PyImGui.table_next_column()
                    if PyImGui.button("Clear Ally Coords"):
                        ally_xy.clear()

                    # Render the "Clear Carto Coords" button
                    PyImGui.table_next_column()
                    if PyImGui.button("Clear Carto Coords"):
                        cart_xy.clear()

                    # Render the "Clear Custom Coords" button
                    PyImGui.table_next_column()
                    if PyImGui.button("Clear Custom Coords"):
                        custom_xy.clear()

                    # Render the "Carto Coord" button
                    PyImGui.table_next_column()


                    PyImGui.end_table()  # End the table layout


            if PyImGui.collapsing_header("Custom Coordinates"):
                PyImGui.text("Name of Custom Coordinates")
                custom_name = PyImGui.input_text(" ", custom_name)



            if PyImGui.collapsing_header("Advanced Settings"):
                player_update_distance = PyImGui.slider_int("Player Log Update Distance", player_update_distance, 1, 2500)
                enemy_update_distance = PyImGui.slider_int("Enemy Log Update Distance", enemy_update_distance, 1, 2500)
                update_frequency = PyImGui.slider_int("Update Frequency", update_frequency, 0, 20)

            if PyImGui.collapsing_header("How to Use"):
                PyImGui.text_wrapped("Click to activate, while active the following coordinates will update: Player, Enemy, and Ally.")
                PyImGui.text_wrapped("Click Add Carto Coord to add a cartography coordinate at the players current position")
                PyImGui.text_wrapped("Click Add Custom Coord to add a cartography coordinate at the players current position, you can also change the name")
                PyImGui.text_wrapped("Click Write Coords to File to log all coordinates since last clear. ")
                PyImGui.text_wrapped("Click Clear All Coords to clear all coordinates, you can also clear coordinate types specifically")
                PyImGui.text_wrapped("Advanced Settings: ")
                PyImGui.text_wrapped("Player Log Update Distance: How far the player has to travel in order to log a coordinate. ")
                PyImGui.text_wrapped("Enemy Log Update Distance: How far the enemy has to travel in order to log a coordinate. ")
                PyImGui.text_wrapped("Update Frequency: How often to check for new coordinates.")



            PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise




# main function must exist in every script and is the entry point for your script's execution.
def main():
    global module_name
    try:
        if Map.IsMapReady():
            DrawWindow()
        else:
            Py4GW.Console.Log(module_name, f"Map not ready", Py4GW.Console.MessageType.Error)

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
        # Py4GW.Console.Log(module_name, "Execution of Main() completed", Py4GW.Console.MessageType.Info)
        # Place any cleanup tasks here
        pass


# This ensures that Main() is called when the script is executed directly.
if __name__ == "__main__":
    main()


