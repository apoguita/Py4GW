# Necessary Imports
import inspect
import os
import Py4GW
import ImGui_Py
import PyMap
import PyAgent
import PyPlayer
import PyParty
import PyItem
import PyInventory
import PySkill
import PySkillbar
import PyMerchant
import PyEffects
# End Necessary Imports
import Py4GWcorelib as CoreLib

import traceback
import math
import time

#This script is intended to be a showcase of every Methos and all the data that can be accessed from Py4GW
#current status, not complete

module_name = "Py4GW DEMO"

class WindowState:
    def __init__(self):
        self.window_name = ""
        self.is_window_open =[]
        self.button_list = []
        self.description_list = []
        self.method_mapping = {}
        self.values = []

main_window_state = WindowState()
ImGui_window_state = WindowState()
ImGui_selectables_window_state = WindowState()
ImGui_input_fields_window_state = WindowState()
ImGui_tables_window_state = WindowState()
ImGui_misc_window_state = WindowState()

PyMap_window_state = WindowState()
PyMap_Travel_Window_state = WindowState()
PyMap_Extra_InfoWindow_state = WindowState()
PyAgent_window_state = WindowState()

def calculate_grid_layout(total_buttons):
    # Find the smallest perfect square greater than or equal to total_buttons
    next_square = math.ceil(math.sqrt(total_buttons)) ** 2  # Next perfect square
    columns = int(math.sqrt(next_square))  # Number of columns is the square root of next_square
    rows = math.ceil(total_buttons / columns)  # Calculate number of rows needed
    return columns, rows

def DrawTextWithTitle(title, text_content, lines_visible=10):
    """
    Function to display a title and multi-line text in a scrollable and configurable area.
    Width is based on the main window's width with a margin.
    Height is based on the number of lines_visible.
    """
    margin = 20
    max_lines = 10
    line_padding = 4  # Add a bit of padding for readability

    # Display the title first
    ImGui_Py.text(title)

    # Get the current window size and adjust for margin to calculate content width
    window_width = ImGui_Py.get_window_size()[0]
    content_width = window_width - margin
    text_block = text_content + "\n" + Py4GW.Console.GetCredits()

    # Split the text content into lines by newline
    lines = text_block.split("\n")
    total_lines = len(lines)

    # Limit total lines to max_lines if provided
    if max_lines is not None:
        total_lines = min(total_lines, max_lines)

    # Get the line height from ImGui
    line_height = ImGui_Py.get_text_line_height()
    if line_height == 0:
        line_height = 10  # Set default line height if it's not valid

    # Add padding between lines and calculate content height based on visible lines
    content_height = (lines_visible * line_height) + ((lines_visible - 1) * line_padding)

    # Set up the scrollable child window with dynamic width and height
    if ImGui_Py.begin_child(f"ScrollableTextArea_{title}", size=(content_width, content_height), border=True, flags=ImGui_Py.WindowFlags.HorizontalScrollbar):

        # Get the scrolling position and window size for visibility checks
        scroll_y = ImGui_Py.get_scroll_y()
        scroll_max_y = ImGui_Py.get_scroll_max_y()
        window_size_y = ImGui_Py.get_window_size()[1]
        window_pos_y = ImGui_Py.get_cursor_pos_y()

        # Display each line only if it's visible based on scroll position
        for index, line in enumerate(lines):
            # Calculate the Y position of the line based on index
            line_start_y = window_pos_y + (index * (line_height + line_padding))

            # Calculate visibility boundaries
            line_end_y = line_start_y + line_height

            # Skip rendering if the line is above or below the visible area
            if line_end_y < scroll_y or line_start_y > scroll_y + window_size_y:
                continue

            # Render the line if it's within the visible scroll area
            ImGui_Py.text_wrapped(line)
            ImGui_Py.spacing()  # Add spacing between lines for better readability

        # End the scrollable child window
        ImGui_Py.end_child()


#PyAgent Demo Section
PyAgent_window_state.window_name = "PyAgent DEMO"
PyAgent_window_state.values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

def ShowPyAgentWindow():
    global module_name
    global PyAgent_window_state
    description = "This section demonstrates the use of PyAgent functions in Py4GW. \nPyAgent provides access to in-game entities (agents) such as players, NPCs, gadgets, and items. \nIn this demo, you can see how to create and use PyAgent objects to interact with agents in the game."

    try:     
        if ImGui_Py.begin(PyAgent_window_state.window_name):
            # Show description text
            DrawTextWithTitle(PyAgent_window_state.window_name, description)

            if not CoreLib.Map.IsMapReady():
                    ImGui_Py.text_colored("Travel : Map is not ready",(1, 0, 0, 1))

            if CoreLib.Map.IsMapReady():
                # Fetch nearest entities
                nearest_enemy = CoreLib.Agent.GetNearestEnemy()
                nearest_ally = CoreLib.Agent.GetNearestAlly()
                nearest_item = CoreLib.Agent.GetNearestItem()
                nearest_gadget = CoreLib.Agent.GetNearestGadget()
                nearest_npc = CoreLib.Agent.GetNearestNPCMinipet()
                player_id = CoreLib.Player.GetPlayerID()

                # Display table headers
                ImGui_Py.text("Nearest Entities:")
                if ImGui_Py.begin_table("nearest_entities_table", 6):
                    ImGui_Py.table_setup_column("Player ID")
                    ImGui_Py.table_setup_column("Enemy ID")
                    ImGui_Py.table_setup_column("Ally ID")
                    ImGui_Py.table_setup_column("NPC ID")
                    ImGui_Py.table_setup_column("Item ID")
                    ImGui_Py.table_setup_column("Gadget ID")
                    ImGui_Py.table_headers_row()

                    # Table row with the closest enemy, ally, item, and gadget
                    ImGui_Py.table_next_row()
                    ImGui_Py.table_next_column()
                    ImGui_Py.text(str(player_id) if player_id else "N/A")  # Show Player ID
                    ImGui_Py.table_next_column()
                    ImGui_Py.text(str(nearest_enemy.id) if nearest_enemy else "N/A")  # Show Enemy ID
                    ImGui_Py.table_next_column()
                    ImGui_Py.text(str(nearest_ally.id) if nearest_ally else "N/A")    # Show Ally ID
                    ImGui_Py.table_next_column()
                    ImGui_Py.text(str(nearest_npc.id) if nearest_npc else "N/A")    # Show NPC ID
                    ImGui_Py.table_next_column()
                    ImGui_Py.text(str(nearest_item.id) if nearest_item else "N/A")    # Show Item ID
                    ImGui_Py.table_next_column()
                    ImGui_Py.text(str(nearest_gadget.id) if nearest_gadget else "N/A")  # Show Gadget ID

                    ImGui_Py.end_table()

            ImGui_Py.separator()

            # Input field for Agent ID
            PyAgent_window_state.values[0] = ImGui_Py.input_int("Agent ID", PyAgent_window_state.values[0])
            ImGui_Py.separator()

            # If an agent ID is entered, display agent details
            if PyAgent_window_state.values[0] != 0:
                agent_instance = PyAgent.PyAgent(PyAgent_window_state.values[0])
                ImGui_Py.text(f"Agent ID: {agent_instance.id}")
                ImGui_Py.text(f"Position: ({agent_instance.x}, {agent_instance.y}, {agent_instance.z})")
                ImGui_Py.text(f"Z Plane: {agent_instance.zplane}")
                ImGui_Py.text(f"Rotation Angle: {agent_instance.rotation_angle}")
                ImGui_Py.text(f"Rotation Cosine: {agent_instance.rotation_cos}")
                ImGui_Py.text(f"Rotation Sine: {agent_instance.rotation_sin}")
                ImGui_Py.text(f"Velocity X: {agent_instance.velocity_x}")
                ImGui_Py.text(f"Velocity Y: {agent_instance.velocity_y}")
                ImGui_Py.text(f"Is Living: {'Yes' if agent_instance.is_living else 'No'}")

            ImGui_Py.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowPyAgentWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise





PyMap_Extra_InfoWindow_state.window_name = "PyMap Extra Info DEMO"

def ShowImGui_PyExtraMaplWindow():
    global module_name
    global PyMap_Extra_InfoWindow_state
    description = "This section demonstrates the use of extra map information in PyMap. \nExtra map information includes region types, instance types, and map context. \nIn this demo, you can see how to create and use PyMap objects to interact with the map in the game."

    try:
        width, height = 375,200
        ImGui_Py.set_next_window_size(width, height)
        if ImGui_Py.begin(PyMap_Extra_InfoWindow_state.window_name, ImGui_Py.WindowFlags.NoResize):
            #DrawTextWithTitle(PyMap_Extra_InfoWindow_state.window_name, description)

            map_instance = PyMap.PyMap()
            map_instance.GetContext()

            if not CoreLib.Map.IsOutpost():
                ImGui_Py.text("Get to an Outpost to see this data")
                ImGui_Py.separator()
    
            if CoreLib.Map.IsOutpost():
                ImGui_Py.text("Outpost Specific Information")
                if ImGui_Py.begin_table("OutpostInfoTable", 2, ImGui_Py.TableFlags.Borders):
                    ImGui_Py.table_next_row()
                    ImGui_Py.table_set_column_index(0)
                    ImGui_Py.text("Region:")
                    ImGui_Py.table_set_column_index(1)
                    ImGui_Py.text(f"{map_instance.server_region.GetName()}")

                    ImGui_Py.table_next_row()
                    ImGui_Py.table_set_column_index(0)
                    ImGui_Py.text("District:")
                    ImGui_Py.table_set_column_index(1)
                    ImGui_Py.text(f"{map_instance.district}")

                    ImGui_Py.table_next_row()
                    ImGui_Py.table_set_column_index(0)
                    ImGui_Py.text("Language:")
                    ImGui_Py.table_set_column_index(1)
                    ImGui_Py.text(f"{map_instance.language.GetName()}")

                    ImGui_Py.table_next_row()
                    ImGui_Py.table_set_column_index(0)
                    ImGui_Py.text("Has Enter Button?")
                    ImGui_Py.table_set_column_index(1)
                    ImGui_Py.text(f"{'Yes' if map_instance.has_enter_button else 'No'}")

                    ImGui_Py.end_table()

                    if not map_instance.has_enter_button:
                        ImGui_Py.text("Get to an outpost with Enter Button to see this data")


                    if map_instance.has_enter_button:
                        if ImGui_Py.begin_table("OutpostEnterMissionTable", 2, ImGui_Py.TableFlags.Borders):
                            ImGui_Py.table_next_row()
                            ImGui_Py.table_set_column_index(0)
                            if ImGui_Py.button("Enter Mission"):
                                map_instance.EnterChallenge()

                            ImGui_Py.table_set_column_index(1)
                            if ImGui_Py.button("Cancel Enter"):
                                map_instance.CancelEnterChallenge()
                    
                            ImGui_Py.end_table()

                ImGui_Py.separator()

            # Explorable Specific Fields
            if not CoreLib.Map.IsExplorable():
                ImGui_Py.text("Get to an Explorable Zone to see this data")
                ImGui_Py.separator()

            if CoreLib.Map.IsExplorable():
                ImGui_Py.text("Explorable Zone Specific Information")

                party_instance = PyParty.PyParty()
           
                if ImGui_Py.begin_table("ExplorableNormalTable", 2, ImGui_Py.TableFlags.Borders):
                    ImGui_Py.table_next_row()
                    ImGui_Py.table_set_column_index(0)
                    ImGui_Py.text("Is Vanquishable?")
                    ImGui_Py.table_set_column_index(1)
                    ImGui_Py.text(f"{'Yes' if map_instance.is_vanquishable_area else 'No'}")

                    ImGui_Py.end_table()
                if not party_instance.is_in_hard_mode:
                    ImGui_Py.text("Enter Hard mode to see this data")

                if party_instance.is_in_hard_mode:
                    ImGui_Py.separator()
                    if ImGui_Py.begin_table("ExplorableHMTable", 2, ImGui_Py.TableFlags.Borders):
                        ImGui_Py.table_next_row()
                        ImGui_Py.table_set_column_index(0)
                        ImGui_Py.text("Foes Killed:")
                        ImGui_Py.table_set_column_index(1)
                        ImGui_Py.text(f"{map_instance.foes_killed}")

                        ImGui_Py.table_next_row()
                        ImGui_Py.table_set_column_index(0)
                        ImGui_Py.text("Foes To Kill:")
                        ImGui_Py.table_set_column_index(1)
                        ImGui_Py.text(f"{map_instance.foes_to_kill}")



                        ImGui_Py.end_table()

            ImGui_Py.end()

    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

PyMap_Travel_Window_state.window_name = "PyMap Travel DEMO"

def ShowImGui_PyTravelWindow():
    global module_name
    global PyMap_Travel_Window_state
    description = "This section demonstrates the use of travel functions in PyMap. \nTravel functions allow you to move between different locations in the game. \nIn this demo, you can see how to use travel functions to move to different districts and outposts."

    try:
        width, height = 375,360
        ImGui_Py.set_next_window_size(width, height)
        if ImGui_Py.begin(PyMap_Travel_Window_state.window_name, ImGui_Py.WindowFlags.NoResize):
            DrawTextWithTitle(PyMap_Travel_Window_state.window_name, description,8)

            map_instance = PyMap.PyMap()

            if not CoreLib.Map.IsMapReady():
                    ImGui_Py.text_colored("Travel : Map is not ready",(1, 0, 0, 1))
               
            if CoreLib.Map.IsMapReady():

                ImGui_Py.text("Travel to default district")
                if ImGui_Py.button(CoreLib.Map.GetMapName(857)): #Embark Beach
                    success = map_instance.Travel(857)

                ImGui_Py.text("Travel to specific district")
                if ImGui_Py.button(CoreLib.Map.GetMapName(248)): #Great Temple of Balthazar
                    success = map_instance.Travel(248, 0, 0)

                ImGui_Py.text("Travel trough toolbox chat command")
                if ImGui_Py.button("Eye Of The North"):
                    CoreLib.Player.SendChatCommand("tp eotn")

            ImGui_Py.end()

    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


#PyMap Demo Section
PyMap_window_state.window_name = "PyMap DEMO"
PyMap_window_state.button_list = ["Travel", "Extra Info"]
PyMap_window_state.is_window_open = [False, False]

def ShowPyMapWindow():
    global module_name
    global PyMap_window_state
    description = "This section demonstrates the use of PyMap functions in Py4GW. \nPyMap provides access to map-related data such as region types, instance types, and map context. \nIn this demo, you can see how to create and use PyMap objects to interact with the map in the game."

    try:
        width, height = 375,370
        ImGui_Py.set_next_window_size(width, height)
        if ImGui_Py.begin(PyMap_window_state.window_name, ImGui_Py.WindowFlags.NoResize):
            DrawTextWithTitle(PyMap_window_state.window_name, description,8)

            map_instance = PyMap.PyMap()

            # Instance Fields (General map data)
            ImGui_Py.text("Instance Information")
            if ImGui_Py.begin_table("InstanceInfoTable", 2, ImGui_Py.TableFlags.Borders):
                ImGui_Py.table_next_row()
                ImGui_Py.table_set_column_index(0)
                ImGui_Py.text("Instance ID:")
                ImGui_Py.table_set_column_index(1)
                ImGui_Py.text(f"{map_instance.map_id.ToInt()}")

                ImGui_Py.table_next_row()
                ImGui_Py.table_set_column_index(0)
                ImGui_Py.text("Instance Name:")
                ImGui_Py.table_set_column_index(1)
                ImGui_Py.text(f"{map_instance.map_id.GetName()}")

                ImGui_Py.table_next_row()
                ImGui_Py.table_set_column_index(0)
                ImGui_Py.text("Instance Time:")
                ImGui_Py.table_set_column_index(1)
                #ImGui_Py.text(f"{map_instance.instance_time}")

                # Convert instance_time from milliseconds to HH:mm:ss
                instance_time_seconds = map_instance.instance_time / 1000  # Convert to seconds
                formatted_time = time.strftime('%H:%M:%S', time.gmtime(instance_time_seconds))
                ImGui_Py.text(f"{formatted_time} - [{map_instance.instance_time}]")

                ImGui_Py.end_table()

                if ImGui_Py.begin_table("MapStatusTable", 4, ImGui_Py.TableFlags.Borders):
                    # Is Outpost
                    ImGui_Py.table_next_row()
                    ImGui_Py.table_set_column_index(0)
                    CoreLib.ImGui.toggle_button("In Outpost" if CoreLib.Map.IsOutpost() else "Not in Outpost", CoreLib.Map.IsOutpost())
                    ImGui_Py.table_set_column_index(1)
                    CoreLib.ImGui.toggle_button("In Explorable" if CoreLib.Map.IsExplorable() else "Not in Explorable", CoreLib.Map.IsExplorable())
                    ImGui_Py.table_set_column_index(2)
                    CoreLib.ImGui.toggle_button("Map Ready" if CoreLib.Map.IsMapReady() else "Map Not Ready", CoreLib.Map.IsMapReady())
                    ImGui_Py.table_set_column_index(3)
                    CoreLib.ImGui.toggle_button("Map Loading" if CoreLib.Map.IsMapLoading() else "Map Not Ready", CoreLib.Map.IsMapLoading())

                    ImGui_Py.end_table()


            ImGui_Py.separator()

             # Calculate dynamic grid layout based on number of buttons
            total_buttons = len(PyMap_window_state.button_list)
            columns, rows = calculate_grid_layout(total_buttons)

            # Create a table with dynamically calculated columns
            if ImGui_Py.begin_table("ImGuiButtonTable", columns):  # Dynamic number of columns
                for button_index, button_label in enumerate(PyMap_window_state.button_list):
                    ImGui_Py.table_next_column()  # Move to the next column

                    selected_button_index = button_index
                    PyMap_window_state.is_window_open[selected_button_index] = CoreLib.ImGui.toggle_button(button_label, PyMap_window_state.is_window_open[selected_button_index])
                    
                    if PyMap_window_state.is_window_open[selected_button_index]:
                        title = PyMap_window_state.button_list[selected_button_index]

                
                ImGui_Py.end_table()  # End the table
                
            ImGui_Py.separator()  # Separator between sections

            
            if PyMap_window_state.is_window_open[0]:
                ShowImGui_PyTravelWindow()

            if PyMap_window_state.is_window_open[1]:
                ShowImGui_PyExtraMaplWindow()

            


            ImGui_Py.end()

    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

                    

#ImGgui DEMO Section
ImGui_misc_window_state.window_name = "ImGui_Py Miscelaneous DEMO"
ImGui_misc_window_state.values = [
        [0.0, 0.0, 0.0],  # RGB placeholder (3 floats)
        [0.0, 0.0, 0.0, 1.0],  # RGBA placeholder (4 floats)
        0.0  # Progress bar value
    ]

def ShowImGui_PyMiscelaneousWindow():
    global module_name
    global ImGui_misc_window_state
    description = "This section demonstrates the use of miscellaneous functions in ImGui_Py. \nThese functions include color pickers, progress bars, and tooltips. \nIn this demo, you can see how to create and use these functions in your interface."

    try:  
       width, height = 350,375
       ImGui_Py.set_next_window_size(width, height)
       if ImGui_Py.begin(ImGui_misc_window_state.window_name,ImGui_Py.WindowFlags.NoResize):

            DrawTextWithTitle(ImGui_misc_window_state.window_name, description,8)

            # Color Picker for RGB values
            ImGui_misc_window_state.values[0] = ImGui_Py.color_edit3("RGB Color Picker", ImGui_misc_window_state.values[0])
            ImGui_Py.text(f"RGB Color: {ImGui_misc_window_state.values[0]}")
            ImGui_Py.separator()
            
            # Color Picker for RGBA values
            ImGui_misc_window_state.values[1] = ImGui_Py.color_edit4("RGBA Color Picker", ImGui_misc_window_state.values[1])
            ImGui_Py.text(f"RGBA Color: {ImGui_misc_window_state.values[1]}")
            ImGui_Py.separator()

            # Progress Bar
            ImGui_misc_window_state.values[2] += 0.01  # Increment the progress by a small amount
            if ImGui_misc_window_state.values[2] > 1.0:  # If progress exceeds 1.0 (100%), reset to 0.0
                ImGui_misc_window_state.values[2] = 0.0
            ImGui_Py.progress_bar(ImGui_misc_window_state.values[2], 100.0, "Progress Bar") 

            # Tooltip
            ImGui_Py.text("Hover over the button to see a tooltip:")
            ImGui_Py.same_line(0.0, -1.0)
            
            if ImGui_Py.button("Hover Me!"):
                Py4GW.Console.Log(module_name,"Button clicked!")
            ImGui_Py.show_tooltip("This is a tooltip for the button.")

            ImGui_Py.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

ImGui_tables_window_state.window_name = "ImGui_Py Tables DEMO"
ImGui_tables_window_state.values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

def ShowImGui_PyTablesWindow():
    global module_name
    global ImGui_tables_window_state
    description = "This section demonstrates the use of tables in ImGui_Py. \nTables allow users to display and interact with data in a structured format. \nIn this demo, you can see how to create and use tables in your interface. Tables can be customized with different columns, headers, and rows, can be sorted, and can contain various data types."

    try:   
       width, height = 600,430
       ImGui_Py.set_next_window_size(width, height)
       if ImGui_Py.begin(ImGui_tables_window_state.window_name,ImGui_Py.WindowFlags.NoResize):

            DrawTextWithTitle(ImGui_tables_window_state.window_name, description,8)

            # Table with 3 columns and 5 rows
            if ImGui_Py.begin_table("Table1", 3):
                ImGui_Py.table_setup_column("Column 1", ImGui_Py.TableColumnFlags.DefaultSort | ImGui_Py.TableColumnFlags.WidthStretch)
                ImGui_Py.table_setup_column("Column 2", ImGui_Py.TableColumnFlags.DefaultSort | ImGui_Py.TableColumnFlags.WidthStretch)
                ImGui_Py.table_setup_column("Column 3", ImGui_Py.TableColumnFlags.DefaultSort | ImGui_Py.TableColumnFlags.WidthStretch)

                ImGui_Py.table_headers_row()
                for row in range(5):
                    ImGui_Py.table_next_row()
                    for column in range(3):
                        ImGui_Py.table_set_column_index(column)
                        ImGui_Py.text(f"Row {row}, Column {column}")
                ImGui_Py.end_table()

            ImGui_Py.separator()

            # Table with 5 columns and 3 rows
            if ImGui_Py.begin_table("Table2", 5):
                ImGui_Py.table_setup_column("Column 1", ImGui_Py.TableColumnFlags.DefaultSort | ImGui_Py.TableColumnFlags.WidthStretch)
                ImGui_Py.table_setup_column("Column 2", ImGui_Py.TableColumnFlags.DefaultSort | ImGui_Py.TableColumnFlags.WidthStretch)
                ImGui_Py.table_setup_column("Column 3", ImGui_Py.TableColumnFlags.DefaultSort | ImGui_Py.TableColumnFlags.WidthStretch)
                ImGui_Py.table_setup_column("Column 4", ImGui_Py.TableColumnFlags.DefaultSort | ImGui_Py.TableColumnFlags.WidthStretch)
                ImGui_Py.table_setup_column("Column 5", ImGui_Py.TableColumnFlags.DefaultSort | ImGui_Py.TableColumnFlags.WidthStretch)

                ImGui_Py.table_headers_row()
                for row in range(3):
                    ImGui_Py.table_next_row()
                    for column in range(5):
                        ImGui_Py.table_set_column_index(column)
                        ImGui_Py.text(f"Row {row}, Column {column}")
                ImGui_Py.end_table()


            ImGui_Py.end()

    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

ImGui_input_fields_window_state.window_name = "ImGui_Py Input Fields DEMO"
ImGui_input_fields_window_state.values = [0.0, 0, 0.0, 0, ""]

def ShowImGui_PyInputFieldsWindow():
    global module_name
    global ImGui_input_fields_window_state
    description = "This section demonstrates the use of input \nfields in ImGui_Py. \nInput fields allow users to input values such \nas numbers, text, and colors. \nIn this demo, you can see how to create \nand use input fields in your interface."

    try: 
       width, height = 310,510
       ImGui_Py.set_next_window_size(width, height)
       if ImGui_Py.begin(ImGui_input_fields_window_state.window_name,ImGui_Py.WindowFlags.NoResize):

            DrawTextWithTitle(ImGui_input_fields_window_state.window_name, description)

            # Slider for float values
            ImGui_input_fields_window_state.values[0] = ImGui_Py.slider_float("Adjust Float", ImGui_input_fields_window_state.values[0], 0.0, 1.0)
            ImGui_Py.text(f"Float Value: {ImGui_input_fields_window_state.values[0]:.2f}")
            ImGui_Py.separator()
            
            # Slider for integer values
            ImGui_input_fields_window_state.values[1] = ImGui_Py.slider_int("Adjust Int", ImGui_input_fields_window_state.values[1], 0, 100)
            ImGui_Py.text(f"Int Value: {ImGui_input_fields_window_state.values[1]}")
            ImGui_Py.separator()

            # Input for float values
            ImGui_input_fields_window_state.values[2] = ImGui_Py.input_float("Float Input", ImGui_input_fields_window_state.values[2])
            ImGui_Py.text(f"Float Input: {ImGui_input_fields_window_state.values[2]:.2f}")
            ImGui_Py.separator()

            # Input for integer values
            ImGui_input_fields_window_state.values[3] = ImGui_Py.input_int("Int Input", ImGui_input_fields_window_state.values[3])

            ImGui_Py.text(f"Int Input: {ImGui_input_fields_window_state.values[3]}")
            ImGui_Py.separator()

            if not isinstance(ImGui_input_fields_window_state.values[4], str):
                ImGui_input_fields_window_state.values[4] = "forced text value"
            # Text Input
            ImGui_input_fields_window_state.values[4] = ImGui_Py.input_text("Enter Text", ImGui_input_fields_window_state.values[4])
            ImGui_Py.text(f"Entered Text: {ImGui_input_fields_window_state.values[4]}")
            ImGui_Py.separator()

            ImGui_Py.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

ImGui_selectables_window_state.window_name = "ImGui_Py Selectables DEMO"
ImGui_selectables_window_state.values = [True, 0, 0]

def ShowImGui_PySelectablesWindow():
    global module_name
    global ImGui_selectables_window_state
    description = "This section demonstrates the use of selectables in ImGui_Py. \nSelectables allow users to interact with items by clicking on them. \nIn this demo, you can see how to create and use selectables in your interface."

    try:  
       width, height = 300,425
       ImGui_Py.set_next_window_size(width, height)
       if ImGui_Py.begin(ImGui_selectables_window_state.window_name,ImGui_Py.WindowFlags.NoResize):

            DrawTextWithTitle(ImGui_selectables_window_state.window_name, description, 8)

            ImGui_selectables_window_state.values[0] = ImGui_Py.checkbox("Check Me!", ImGui_selectables_window_state.values[0])
            ImGui_Py.text(f"Checkbox is {'checked' if ImGui_selectables_window_state.values[0] else 'unchecked'}")
            ImGui_Py.separator()
        
             # Radio Buttons with a single integer state variable
            ImGui_selectables_window_state.values[1] = ImGui_Py.radio_button("Radio Button 1", ImGui_selectables_window_state.values[1], 0)
            ImGui_selectables_window_state.values[1] = ImGui_Py.radio_button("Radio Button 2", ImGui_selectables_window_state.values[1], 1)
            ImGui_selectables_window_state.values[1] = ImGui_Py.radio_button("Radio Button 3", ImGui_selectables_window_state.values[1], 2)

            ImGui_Py.text(f"Selected Radio Button: {ImGui_selectables_window_state.values[1] + 1}")
            ImGui_Py.separator()
                
            # Combo Box
            items = ["Item 1", "Item 2", "Item 3"]
            ImGui_selectables_window_state.values[2] = ImGui_Py.combo("Combo Box", ImGui_selectables_window_state.values[2], items)
            ImGui_Py.text(f"Selected Combo Item: {items[ImGui_selectables_window_state.values[2]]}")
            ImGui_Py.separator()

            ImGui_Py.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


ImGui_window_state.window_name = "ImGui_Py DEMO"
ImGui_window_state.button_list = ["Selectables", "Input Fields", "Tables", "Miscelaneous", "Official DEMO"]
ImGui_window_state.is_window_open = [False, False, False, False, False]
    
def ShowImGui_PyDemoWindow():
    global module_name
    global ImGui_window_state
    description = "This library has hundreds of functions and demoing each of them is unpractical. \nHere you will find a demo with most useful ImGui functions aswell as an oficial DEMO.\nFor a full detailed list of methods available consult the 'stubs' folder. \nFunctions that are unavailable can be added upon request, \ncontact the autor of the library and request them to be added."

    selected_button_index = 0
    try:
        width, height = 460,340
        ImGui_Py.set_next_window_size(width, height)

        if ImGui_Py.begin(ImGui_window_state.window_name,ImGui_Py.WindowFlags.NoResize):
            DrawTextWithTitle("ImGui_Py ATTENTION", description)

        
            # ----- Top Section: Dynamic Tileset of Buttons -----
            ImGui_Py.text("Select a Feature:")

            # Calculate dynamic grid layout based on number of buttons
            total_buttons = len(ImGui_window_state.button_list)
            columns, rows = calculate_grid_layout(total_buttons)

            # Create a table with dynamically calculated columns
            if ImGui_Py.begin_table("ImGuiButtonTable", columns):  # Dynamic number of columns
                for button_index, button_label in enumerate(ImGui_window_state.button_list):
                    ImGui_Py.table_next_column()  # Move to the next column

                    selected_button_index = button_index
                    ImGui_window_state.is_window_open[selected_button_index] = CoreLib.ImGui.toggle_button(button_label, ImGui_window_state.is_window_open[selected_button_index])
                    
                    if ImGui_window_state.is_window_open[selected_button_index]:
                        title = ImGui_window_state.button_list[selected_button_index]

                
                ImGui_Py.end_table()  # End the table
                
            ImGui_Py.separator()  # Separator between sections

            
            if ImGui_window_state.is_window_open[0]:
                ShowImGui_PySelectablesWindow()

            if ImGui_window_state.is_window_open[1]:
                ShowImGui_PyInputFieldsWindow()

            if ImGui_window_state.is_window_open[2]:
                ShowImGui_PyTablesWindow()

            if ImGui_window_state.is_window_open[3]:
                ShowImGui_PyMiscelaneousWindow()

            if ImGui_window_state.is_window_open[4]:
                ImGui_Py.show_demo_window()

            ImGui_Py.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


main_window_state.window_name = "Py4GW Lib DEMO"

main_window_state.is_window_open = [False, False, False, False, False, False, False, False, False, False, False, False]

main_window_state.button_list = [
    "ImGui_Py", "PyMap", "PyAgent", "PyPlayer", "PyParty", 
    "PyItem", "PyInventory", "PySkill", "PySkillbar", "PyMerchant","Py4GW","Py4GWcorelib"
]

main_window_state.description_list = [
    "ImGui_Py: Provides bindings for creating and managing graphical user interfaces within the game using ImGui. \nIncludes support for text, buttons, tables, sliders, and other GUI elements.",   
    "PyMap: Manages map-related functions such as handling travel, region data, instance types, and map context. \nIncludes functionality for interacting with server regions, campaigns, and continents.",    
    "PyAgent: Handles in-game entities (agents) such as players, NPCs, gadgets, and items. \nProvides methods for manipulating and interacting with agents, including movement, targeting, and context updates.",    
    "PyPlayer: Provides access to the player-specific operations.\nIncludes functionality for interacting with agents, changing targets, issuing chat commands, and other player-related actions such as moving or interacting with the game environment.",   
    "PyParty: Manages party composition and party-related actions.\n This includes adding/kicking party members (players, heroes, henchmen), flagging heroes, and responding to party requests.\nAllows access to party details like members, size, and mode (e.g., Hard Mode).",   
    "PyItem: Provides functions for handling in-game items.\nThis includes retrieving item information (modifiers, rarity, type), context updates, and operations like dyeing or identifying items.",
    "PyInventory: Manages the player's inventory, including Xunlai storage interactions, item manipulation (pick up, drop, equip, destroy), and salvage operations. \nAlso includes functions for managing gold and moving items between inventory bags.", 
    "PySkill: Handles in-game skills and their properties.\nProvides access to skill-related data such as skill effects, costs (energy, health, adrenaline), and professions.\nIncludes methods for interacting with individual skills and loading skill templates.",
    "PySkillbar: Manages the player's skillbar, including loading skill templates, using skills in specific slots, and refreshing the skillbar context. \nEach skill in the skillbar can be interacted with or updated.",
    "PyMerchant: Manages interactions with in-game merchants, including buying and selling items, requesting price quotes, and checking transaction status. \nProvides methods to handle trade-related actions and merchant-specific functionality.",
    "Py4GW: Provides core functionality for Py4GW scripts, including logging, error handling, and message types. \nIncludes functions for logging messages, errors, and warnings to the console or log file.",
    "Py4GWcorelib: Provides utility functions and common functionality for Py4GW scripts.\nIncludes functions for logging, error handling, and GUI elements like text display and button creation."
]

main_window_state.method_mapping = {
    "ImGui_Py": ShowImGui_PyDemoWindow, 
    "LocalFunction": ShowImGui_PyDemoWindow,  
    "PyMap": ShowImGui_PyDemoWindow,
    "PyAgent": ShowImGui_PyDemoWindow,
    "PyPlayer": ShowImGui_PyDemoWindow,
    "PyParty": ShowImGui_PyDemoWindow,
    "PyItem": ShowImGui_PyDemoWindow,
    "PyInventory": ShowImGui_PyDemoWindow,
    "PySkill": ShowImGui_PyDemoWindow,
    "PySkillbar": ShowImGui_PyDemoWindow,
    "PyMerchant": ShowImGui_PyDemoWindow,
    "Py4GWcorelib": ShowImGui_PyDemoWindow
}

main_window_state.is_window_open = [False, False, False, False, False, False, False, False, False, False, False, False]

title = "Welcome"
explanation_text_content = "Select a feature to see its details here."

test_button = False

# Example of additional utility function
def DrawWindow():
    global module_name
    global main_window_state

    global title
    global explanation_text_content
    global test_button

    selected_button_index = 0
    try:
        width, height = 400,360
        ImGui_Py.set_next_window_size(width, height)
        if ImGui_Py.begin(main_window_state.window_name,ImGui_Py.WindowFlags.NoResize):
        
            # ----- Top Section: Dynamic Tileset of Buttons -----
            ImGui_Py.text("Select a Feature:")

            # Calculate dynamic grid layout based on number of buttons
            total_buttons = len(main_window_state.button_list)
            columns, rows = calculate_grid_layout(total_buttons)

            # Create a table with dynamically calculated columns
            if ImGui_Py.begin_table("MainWindowButtonTable", columns):  # Dynamic number of columns
                for button_index, button_label in enumerate(main_window_state.button_list):
                    ImGui_Py.table_next_column()  # Move to the next column

                    selected_button_index = button_index
                    main_window_state.is_window_open[selected_button_index] = CoreLib.ImGui.toggle_button(button_label, main_window_state.is_window_open[selected_button_index])
                    
                    if main_window_state.is_window_open[selected_button_index]:
                        title = main_window_state.button_list[selected_button_index]
                        explanation_text_content = main_window_state.description_list[selected_button_index]
                        method = main_window_state.method_mapping.get(title, None)

                
                ImGui_Py.end_table()  # End the table
                
            ImGui_Py.separator()  # Separator between sections

            DrawTextWithTitle(title, explanation_text_content)
            

            if main_window_state.is_window_open[0]:
                ShowImGui_PyDemoWindow()

            if main_window_state.is_window_open[1]:
                ShowPyMapWindow()

            if main_window_state.is_window_open[2]:
                ShowPyAgentWindow()

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


