# Necessary Imports
import Py4GW
import PyImGui
import PyAgent

import PyParty

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
    PyImGui.text(title)

    # Get the current window size and adjust for margin to calculate content width
    window_width = PyImGui.get_window_size()[0]
    content_width = window_width - margin
    text_block = text_content + "\n" + Py4GW.Console.GetCredits()

    # Split the text content into lines by newline
    lines = text_block.split("\n")
    total_lines = len(lines)

    # Limit total lines to max_lines if provided
    if max_lines is not None:
        total_lines = min(total_lines, max_lines)

    # Get the line height from ImGui
    line_height = PyImGui.get_text_line_height()
    if line_height == 0:
        line_height = 10  # Set default line height if it's not valid

    # Add padding between lines and calculate content height based on visible lines
    content_height = (lines_visible * line_height) + ((lines_visible - 1) * line_padding)

    # Set up the scrollable child window with dynamic width and height
    if PyImGui.begin_child(f"ScrollableTextArea_{title}", size=(content_width, content_height), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):

        # Get the scrolling position and window size for visibility checks
        scroll_y = PyImGui.get_scroll_y()
        scroll_max_y = PyImGui.get_scroll_max_y()
        window_size_y = PyImGui.get_window_size()[1]
        window_pos_y = PyImGui.get_cursor_pos_y()

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
            PyImGui.text_wrapped(line)
            PyImGui.spacing()  # Add spacing between lines for better readability

        # End the scrollable child window
        PyImGui.end_child()


#PyAgent Demo Section
PyAgent_window_state.window_name = "PyAgent DEMO"
PyAgent_window_state.values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

def ShowPyAgentWindow():
    global module_name
    global PyAgent_window_state
    description = "This section demonstrates the use of PyAgent functions in Py4GW. \nPyAgent provides access to in-game entities (agents) such as players, NPCs, gadgets, and items. \nIn this demo, you can see how to create and use PyAgent objects to interact with agents in the game."

    try:     
        if PyImGui.begin(PyAgent_window_state.window_name):
            # Show description text
            DrawTextWithTitle(PyAgent_window_state.window_name, description)

            if not CoreLib.Map.IsMapReady():
                    PyImGui.text_colored("Travel : Map is not ready",(1, 0, 0, 1))

            if CoreLib.Map.IsMapReady():
                # Fetch nearest entities
                nearest_enemy = CoreLib.Agent.GetNearestEnemy()
                nearest_ally = CoreLib.Agent.GetNearestAlly()
                nearest_item = CoreLib.Agent.GetNearestItem()
                nearest_gadget = CoreLib.Agent.GetNearestGadget()
                nearest_npc = CoreLib.Agent.GetNearestNPCMinipet()
                player_id = CoreLib.Player.GetAgentID()

                # Display table headers
                PyImGui.text("Nearest Entities:")
                if PyImGui.begin_table("nearest_entities_table", 6):
                    PyImGui.table_setup_column("Player ID")
                    PyImGui.table_setup_column("Enemy ID")
                    PyImGui.table_setup_column("Ally ID")
                    PyImGui.table_setup_column("NPC ID")
                    PyImGui.table_setup_column("Item ID")
                    PyImGui.table_setup_column("Gadget ID")
                    PyImGui.table_headers_row()

                    # Table row with the closest enemy, ally, item, and gadget
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(str(player_id) if player_id else "N/A")  # Show Player ID
                    PyImGui.table_next_column()
                    PyImGui.text(str(nearest_enemy.id) if nearest_enemy else "N/A")  # Show Enemy ID
                    PyImGui.table_next_column()
                    PyImGui.text(str(nearest_ally.id) if nearest_ally else "N/A")    # Show Ally ID
                    PyImGui.table_next_column()
                    PyImGui.text(str(nearest_npc.id) if nearest_npc else "N/A")    # Show NPC ID
                    PyImGui.table_next_column()
                    PyImGui.text(str(nearest_item.id) if nearest_item else "N/A")    # Show Item ID
                    PyImGui.table_next_column()
                    PyImGui.text(str(nearest_gadget.id) if nearest_gadget else "N/A")  # Show Gadget ID

                    PyImGui.end_table()

            PyImGui.separator()

            # Input field for Agent ID
            PyAgent_window_state.values[0] = PyImGui.input_int("Agent ID", PyAgent_window_state.values[0])
            PyImGui.separator()

            # If an agent ID is entered, display agent details
            if PyAgent_window_state.values[0] != 0:
                agent_instance = PyAgent.PyAgent(PyAgent_window_state.values[0])
                PyImGui.text(f"Agent ID: {agent_instance.id}")
                PyImGui.text(f"Position: ({agent_instance.x}, {agent_instance.y}, {agent_instance.z})")
                PyImGui.text(f"Z Plane: {agent_instance.zplane}")
                PyImGui.text(f"Rotation Angle: {agent_instance.rotation_angle}")
                PyImGui.text(f"Rotation Cosine: {agent_instance.rotation_cos}")
                PyImGui.text(f"Rotation Sine: {agent_instance.rotation_sin}")
                PyImGui.text(f"Velocity X: {agent_instance.velocity_x}")
                PyImGui.text(f"Velocity Y: {agent_instance.velocity_y}")
                PyImGui.text(f"Is Living: {'Yes' if agent_instance.is_living else 'No'}")

            PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in ShowPyAgentWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise





PyMap_Extra_InfoWindow_state.window_name = "PyMap Extra Info DEMO"

def ShowPyImGuiExtraMaplWindow():
    global module_name
    global PyMap_Extra_InfoWindow_state
    description = "This section demonstrates the use of extra map information in PyMap. \nExtra map information includes region types, instance types, and map context. \nIn this demo, you can see how to create and use PyMap objects to interact with the map in the game."

    try:
        width, height = 375,200
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(PyMap_Extra_InfoWindow_state.window_name, PyImGui.WindowFlags.NoResize):
            #DrawTextWithTitle(PyMap_Extra_InfoWindow_state.window_name, description)

            if not CoreLib.Map.IsOutpost():
                PyImGui.text("Get to an Outpost to see this data")
                PyImGui.separator()
    
            if CoreLib.Map.IsOutpost():
                PyImGui.text("Outpost Specific Information")
                if PyImGui.begin_table("OutpostInfoTable", 2, PyImGui.TableFlags.Borders):
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text("Region:")
                    PyImGui.table_set_column_index(1)
                    PyImGui.text(f"{CoreLib.Map.GetRegion()}")

                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text("District:")
                    PyImGui.table_set_column_index(1)
                    PyImGui.text(f"{map_instance.district}")

                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text("Language:")
                    PyImGui.table_set_column_index(1)
                    PyImGui.text(f"{map_instance.language.GetName()}")

                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text("Has Enter Button?")
                    PyImGui.table_set_column_index(1)
                    PyImGui.text(f"{'Yes' if map_instance.has_enter_button else 'No'}")

                    PyImGui.end_table()

                    if not map_instance.has_enter_button:
                        PyImGui.text("Get to an outpost with Enter Button to see this data")


                    if map_instance.has_enter_button:
                        if PyImGui.begin_table("OutpostEnterMissionTable", 2, PyImGui.TableFlags.Borders):
                            PyImGui.table_next_row()
                            PyImGui.table_set_column_index(0)
                            if PyImGui.button("Enter Mission"):
                                map_instance.EnterChallenge()

                            PyImGui.table_set_column_index(1)
                            if PyImGui.button("Cancel Enter"):
                                map_instance.CancelEnterChallenge()
                    
                            PyImGui.end_table()

                PyImGui.separator()

            # Explorable Specific Fields
            if not CoreLib.Map.IsExplorable():
                PyImGui.text("Get to an Explorable Zone to see this data")
                PyImGui.separator()

            if CoreLib.Map.IsExplorable():
                PyImGui.text("Explorable Zone Specific Information")

                party_instance = PyParty.PyParty()
           
                if PyImGui.begin_table("ExplorableNormalTable", 2, PyImGui.TableFlags.Borders):
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    PyImGui.text("Is Vanquishable?")
                    PyImGui.table_set_column_index(1)
                    PyImGui.text(f"{'Yes' if map_instance.is_vanquishable_area else 'No'}")

                    PyImGui.end_table()
                if not party_instance.is_in_hard_mode:
                    PyImGui.text("Enter Hard mode to see this data")

                if party_instance.is_in_hard_mode:
                    PyImGui.separator()
                    if PyImGui.begin_table("ExplorableHMTable", 2, PyImGui.TableFlags.Borders):
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text("Foes Killed:")
                        PyImGui.table_set_column_index(1)
                        PyImGui.text(f"{map_instance.foes_killed}")

                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text("Foes To Kill:")
                        PyImGui.table_set_column_index(1)
                        PyImGui.text(f"{map_instance.foes_to_kill}")



                        PyImGui.end_table()

            PyImGui.end()

    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

PyMap_Travel_Window_state.window_name = "PyMap Travel DEMO"

def ShowPyImGuiTravelWindow():
    global module_name
    global PyMap_Travel_Window_state
    description = "This section demonstrates the use of travel functions in PyMap. \nTravel functions allow you to move between different locations in the game. \nIn this demo, you can see how to use travel functions to move to different districts and outposts."

    try:
        width, height = 375,360
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(PyMap_Travel_Window_state.window_name, PyImGui.WindowFlags.NoResize):
            DrawTextWithTitle(PyMap_Travel_Window_state.window_name, description,8)

            map_instance = PyMap.PyMap()

            if not CoreLib.Map.IsMapReady():
                    PyImGui.text_colored("Travel : Map is not ready",(1, 0, 0, 1))
               
            if CoreLib.Map.IsMapReady():

                PyImGui.text("Travel to default district")
                if PyImGui.button(CoreLib.Map.GetMapName(857)): #Embark Beach
                    success = map_instance.Travel(857)

                PyImGui.text("Travel to specific district")
                if PyImGui.button(CoreLib.Map.GetMapName(248)): #Great Temple of Balthazar
                    success = map_instance.Travel(248, 0, 0)

                PyImGui.text("Travel trough toolbox chat command")
                if PyImGui.button("Eye Of The North"):
                    CoreLib.Player.SendChatCommand("tp eotn")

            PyImGui.end()

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
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(PyMap_window_state.window_name, PyImGui.WindowFlags.NoResize):
            DrawTextWithTitle(PyMap_window_state.window_name, description,8)

            map_instance = PyMap.PyMap()

            # Instance Fields (General map data)
            PyImGui.text("Instance Information")
            if PyImGui.begin_table("InstanceInfoTable", 2, PyImGui.TableFlags.Borders):
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text("Instance ID:")
                PyImGui.table_set_column_index(1)
                PyImGui.text(f"{map_instance.map_id.ToInt()}")

                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text("Instance Name:")
                PyImGui.table_set_column_index(1)
                PyImGui.text(f"{map_instance.map_id.GetName()}")

                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text("Instance Time:")
                PyImGui.table_set_column_index(1)
                #PyImGui.text(f"{map_instance.instance_time}")

                # Convert instance_time from milliseconds to HH:mm:ss
                instance_time_seconds = map_instance.instance_time / 1000  # Convert to seconds
                formatted_time = time.strftime('%H:%M:%S', time.gmtime(instance_time_seconds))
                PyImGui.text(f"{formatted_time} - [{map_instance.instance_time}]")

                PyImGui.end_table()

                if PyImGui.begin_table("MapStatusTable", 4, PyImGui.TableFlags.Borders):
                    # Is Outpost
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    CoreLib.ImGui.toggle_button("In Outpost" if CoreLib.Map.IsOutpost() else "Not in Outpost", CoreLib.Map.IsOutpost())
                    PyImGui.table_set_column_index(1)
                    CoreLib.ImGui.toggle_button("In Explorable" if CoreLib.Map.IsExplorable() else "Not in Explorable", CoreLib.Map.IsExplorable())
                    PyImGui.table_set_column_index(2)
                    CoreLib.ImGui.toggle_button("Map Ready" if CoreLib.Map.IsMapReady() else "Map Not Ready", CoreLib.Map.IsMapReady())
                    PyImGui.table_set_column_index(3)
                    CoreLib.ImGui.toggle_button("Map Loading" if CoreLib.Map.IsMapLoading() else "Map Not Ready", CoreLib.Map.IsMapLoading())

                    PyImGui.end_table()


            PyImGui.separator()

             # Calculate dynamic grid layout based on number of buttons
            total_buttons = len(PyMap_window_state.button_list)
            columns, rows = calculate_grid_layout(total_buttons)

            # Create a table with dynamically calculated columns
            if PyImGui.begin_table("ImGuiButtonTable", columns):  # Dynamic number of columns
                for button_index, button_label in enumerate(PyMap_window_state.button_list):
                    PyImGui.table_next_column()  # Move to the next column

                    selected_button_index = button_index
                    PyMap_window_state.is_window_open[selected_button_index] = CoreLib.ImGui.toggle_button(button_label, PyMap_window_state.is_window_open[selected_button_index])
                    
                    if PyMap_window_state.is_window_open[selected_button_index]:
                        title = PyMap_window_state.button_list[selected_button_index]

                
                PyImGui.end_table()  # End the table
                
            PyImGui.separator()  # Separator between sections

            
            if PyMap_window_state.is_window_open[0]:
                ShowPyImGuiTravelWindow()

            if PyMap_window_state.is_window_open[1]:
                ShowPyImGuiExtraMaplWindow()

            


            PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

                    

#ImGgui DEMO Section
ImGui_misc_window_state.window_name = "PyImGui Miscelaneous DEMO"
ImGui_misc_window_state.values = [
        [0.0, 0.0, 0.0],  # RGB placeholder (3 floats)
        [0.0, 0.0, 0.0, 1.0],  # RGBA placeholder (4 floats)
        0.0  # Progress bar value
    ]

def ShowPyImGuiMiscelaneousWindow():
    global module_name
    global ImGui_misc_window_state
    description = "This section demonstrates the use of miscellaneous functions in PyImGui. \nThese functions include color pickers, progress bars, and tooltips. \nIn this demo, you can see how to create and use these functions in your interface."

    try:  
       width, height = 350,375
       PyImGui.set_next_window_size(width, height)
       if PyImGui.begin(ImGui_misc_window_state.window_name,PyImGui.WindowFlags.NoResize):

            DrawTextWithTitle(ImGui_misc_window_state.window_name, description,8)

            # Color Picker for RGB values
            ImGui_misc_window_state.values[0] = PyImGui.color_edit3("RGB Color Picker", ImGui_misc_window_state.values[0])
            PyImGui.text(f"RGB Color: {ImGui_misc_window_state.values[0]}")
            PyImGui.separator()
            
            # Color Picker for RGBA values
            ImGui_misc_window_state.values[1] = PyImGui.color_edit4("RGBA Color Picker", ImGui_misc_window_state.values[1])
            PyImGui.text(f"RGBA Color: {ImGui_misc_window_state.values[1]}")
            PyImGui.separator()

            # Progress Bar
            ImGui_misc_window_state.values[2] += 0.01  # Increment the progress by a small amount
            if ImGui_misc_window_state.values[2] > 1.0:  # If progress exceeds 1.0 (100%), reset to 0.0
                ImGui_misc_window_state.values[2] = 0.0
            PyImGui.progress_bar(ImGui_misc_window_state.values[2], 100.0, "Progress Bar") 

            # Tooltip
            PyImGui.text("Hover over the button to see a tooltip:")
            PyImGui.same_line(0.0, -1.0)
            
            if PyImGui.button("Hover Me!"):
                Py4GW.Console.Log(module_name,"Button clicked!")
            PyImGui.show_tooltip("This is a tooltip for the button.")

            PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

ImGui_tables_window_state.window_name = "PyImGui Tables DEMO"
ImGui_tables_window_state.values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

def ShowPyImGuiTablesWindow():
    global module_name
    global ImGui_tables_window_state
    description = "This section demonstrates the use of tables in PyImGui. \nTables allow users to display and interact with data in a structured format. \nIn this demo, you can see how to create and use tables in your interface. Tables can be customized with different columns, headers, and rows, can be sorted, and can contain various data types."

    try:   
       width, height = 600,430
       PyImGui.set_next_window_size(width, height)
       if PyImGui.begin(ImGui_tables_window_state.window_name,PyImGui.WindowFlags.NoResize):

            DrawTextWithTitle(ImGui_tables_window_state.window_name, description,8)

            # Table with 3 columns and 5 rows
            if PyImGui.begin_table("Table1", 3):
                PyImGui.table_setup_column("Column 1", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Column 2", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Column 3", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_headers_row()
                for row in range(5):
                    PyImGui.table_next_row()
                    for column in range(3):
                        PyImGui.table_set_column_index(column)
                        PyImGui.text(f"Row {row}, Column {column}")
                PyImGui.end_table()

            PyImGui.separator()

            # Table with 5 columns and 3 rows
            if PyImGui.begin_table("Table2", 5):
                PyImGui.table_setup_column("Column 1", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Column 2", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Column 3", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Column 4", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Column 5", PyImGui.TableColumnFlags.DefaultSort | PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_headers_row()
                for row in range(3):
                    PyImGui.table_next_row()
                    for column in range(5):
                        PyImGui.table_set_column_index(column)
                        PyImGui.text(f"Row {row}, Column {column}")
                PyImGui.end_table()


            PyImGui.end()

    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

ImGui_input_fields_window_state.window_name = "PyImGui Input Fields DEMO"
ImGui_input_fields_window_state.values = [0.0, 0, 0.0, 0, ""]

def ShowPyImGuiInputFieldsWindow():
    global module_name
    global ImGui_input_fields_window_state
    description = "This section demonstrates the use of input \nfields in PyImGui. \nInput fields allow users to input values such \nas numbers, text, and colors. \nIn this demo, you can see how to create \nand use input fields in your interface."

    try: 
       width, height = 310,510
       PyImGui.set_next_window_size(width, height)
       if PyImGui.begin(ImGui_input_fields_window_state.window_name,PyImGui.WindowFlags.NoResize):

            DrawTextWithTitle(ImGui_input_fields_window_state.window_name, description)

            # Slider for float values
            ImGui_input_fields_window_state.values[0] = PyImGui.slider_float("Adjust Float", ImGui_input_fields_window_state.values[0], 0.0, 1.0)
            PyImGui.text(f"Float Value: {ImGui_input_fields_window_state.values[0]:.2f}")
            PyImGui.separator()
            
            # Slider for integer values
            ImGui_input_fields_window_state.values[1] = PyImGui.slider_int("Adjust Int", ImGui_input_fields_window_state.values[1], 0, 100)
            PyImGui.text(f"Int Value: {ImGui_input_fields_window_state.values[1]}")
            PyImGui.separator()

            # Input for float values
            ImGui_input_fields_window_state.values[2] = PyImGui.input_float("Float Input", ImGui_input_fields_window_state.values[2])
            PyImGui.text(f"Float Input: {ImGui_input_fields_window_state.values[2]:.2f}")
            PyImGui.separator()

            # Input for integer values
            ImGui_input_fields_window_state.values[3] = PyImGui.input_int("Int Input", ImGui_input_fields_window_state.values[3])

            PyImGui.text(f"Int Input: {ImGui_input_fields_window_state.values[3]}")
            PyImGui.separator()

            if not isinstance(ImGui_input_fields_window_state.values[4], str):
                ImGui_input_fields_window_state.values[4] = "forced text value"
            # Text Input
            ImGui_input_fields_window_state.values[4] = PyImGui.input_text("Enter Text", ImGui_input_fields_window_state.values[4])
            PyImGui.text(f"Entered Text: {ImGui_input_fields_window_state.values[4]}")
            PyImGui.separator()

            PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

ImGui_selectables_window_state.window_name = "PyImGui Selectables DEMO"
ImGui_selectables_window_state.values = [True, 0, 0]

def ShowPyImGuiSelectablesWindow():
    global module_name
    global ImGui_selectables_window_state
    description = "This section demonstrates the use of selectables in PyImGui. \nSelectables allow users to interact with items by clicking on them. \nIn this demo, you can see how to create and use selectables in your interface."

    try:  
       width, height = 300,425
       PyImGui.set_next_window_size(width, height)
       if PyImGui.begin(ImGui_selectables_window_state.window_name,PyImGui.WindowFlags.NoResize):

            DrawTextWithTitle(ImGui_selectables_window_state.window_name, description, 8)

            ImGui_selectables_window_state.values[0] = PyImGui.checkbox("Check Me!", ImGui_selectables_window_state.values[0])
            PyImGui.text(f"Checkbox is {'checked' if ImGui_selectables_window_state.values[0] else 'unchecked'}")
            PyImGui.separator()
        
             # Radio Buttons with a single integer state variable
            ImGui_selectables_window_state.values[1] = PyImGui.radio_button("Radio Button 1", ImGui_selectables_window_state.values[1], 0)
            ImGui_selectables_window_state.values[1] = PyImGui.radio_button("Radio Button 2", ImGui_selectables_window_state.values[1], 1)
            ImGui_selectables_window_state.values[1] = PyImGui.radio_button("Radio Button 3", ImGui_selectables_window_state.values[1], 2)

            PyImGui.text(f"Selected Radio Button: {ImGui_selectables_window_state.values[1] + 1}")
            PyImGui.separator()
                
            # Combo Box
            items = ["Item 1", "Item 2", "Item 3"]
            ImGui_selectables_window_state.values[2] = PyImGui.combo("Combo Box", ImGui_selectables_window_state.values[2], items)
            PyImGui.text(f"Selected Combo Item: {items[ImGui_selectables_window_state.values[2]]}")
            PyImGui.separator()

            PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


ImGui_window_state.window_name = "PyImGui DEMO"
ImGui_window_state.button_list = ["Selectables", "Input Fields", "Tables", "Miscelaneous", "Official DEMO"]
ImGui_window_state.is_window_open = [False, False, False, False, False]
    
def ShowPyImGuiDemoWindow():
    global module_name
    global ImGui_window_state
    description = "This library has hundreds of functions and demoing each of them is unpractical. \nHere you will find a demo with most useful ImGui functions aswell as an oficial DEMO.\nFor a full detailed list of methods available consult the 'stubs' folder. \nFunctions that are unavailable can be added upon request, \ncontact the autor of the library and request them to be added."

    selected_button_index = 0
    try:
        width, height = 460,340
        PyImGui.set_next_window_size(width, height)

        if PyImGui.begin(ImGui_window_state.window_name,PyImGui.WindowFlags.NoResize):
            DrawTextWithTitle("PyImGui ATTENTION", description)

        
            # ----- Top Section: Dynamic Tileset of Buttons -----
            PyImGui.text("Select a Feature:")

            # Calculate dynamic grid layout based on number of buttons
            total_buttons = len(ImGui_window_state.button_list)
            columns, rows = calculate_grid_layout(total_buttons)

            # Create a table with dynamically calculated columns
            if PyImGui.begin_table("ImGuiButtonTable", columns):  # Dynamic number of columns
                for button_index, button_label in enumerate(ImGui_window_state.button_list):
                    PyImGui.table_next_column()  # Move to the next column

                    selected_button_index = button_index
                    ImGui_window_state.is_window_open[selected_button_index] = CoreLib.ImGui.toggle_button(button_label, ImGui_window_state.is_window_open[selected_button_index])
                    
                    if ImGui_window_state.is_window_open[selected_button_index]:
                        title = ImGui_window_state.button_list[selected_button_index]

                
                PyImGui.end_table()  # End the table
                
            PyImGui.separator()  # Separator between sections

            
            if ImGui_window_state.is_window_open[0]:
                ShowPyImGuiSelectablesWindow()

            if ImGui_window_state.is_window_open[1]:
                ShowPyImGuiInputFieldsWindow()

            if ImGui_window_state.is_window_open[2]:
                ShowPyImGuiTablesWindow()

            if ImGui_window_state.is_window_open[3]:
                ShowPyImGuiMiscelaneousWindow()

            if ImGui_window_state.is_window_open[4]:
                PyImGui.show_demo_window()

            PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


main_window_state.window_name = "Py4GW Lib DEMO"

main_window_state.is_window_open = [False, False, False, False, False, False, False, False, False, False, False, False]

main_window_state.button_list = [
    "PyImGui", "PyMap", "PyAgent", "PyPlayer", "PyParty", 
    "PyItem", "PyInventory", "PySkill", "PySkillbar", "PyMerchant","Py4GW","Py4GWcorelib"
]

main_window_state.description_list = [
    "PyImGui: Provides bindings for creating and managing graphical user interfaces within the game using ImGui. \nIncludes support for text, buttons, tables, sliders, and other GUI elements.",   
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
    "PyImGui": ShowPyImGuiDemoWindow, 
    "LocalFunction": ShowPyImGuiDemoWindow,  
    "PyMap": ShowPyImGuiDemoWindow,
    "PyAgent": ShowPyImGuiDemoWindow,
    "PyPlayer": ShowPyImGuiDemoWindow,
    "PyParty": ShowPyImGuiDemoWindow,
    "PyItem": ShowPyImGuiDemoWindow,
    "PyInventory": ShowPyImGuiDemoWindow,
    "PySkill": ShowPyImGuiDemoWindow,
    "PySkillbar": ShowPyImGuiDemoWindow,
    "PyMerchant": ShowPyImGuiDemoWindow,
    "Py4GWcorelib": ShowPyImGuiDemoWindow
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
        PyImGui.set_next_window_size(width, height)
        if PyImGui.begin(main_window_state.window_name,PyImGui.WindowFlags.NoResize):
        
            # ----- Top Section: Dynamic Tileset of Buttons -----
            PyImGui.text("Select a Feature:")

            # Calculate dynamic grid layout based on number of buttons
            total_buttons = len(main_window_state.button_list)
            columns, rows = calculate_grid_layout(total_buttons)

            # Create a table with dynamically calculated columns
            if PyImGui.begin_table("MainWindowButtonTable", columns):  # Dynamic number of columns
                for button_index, button_label in enumerate(main_window_state.button_list):
                    PyImGui.table_next_column()  # Move to the next column

                    selected_button_index = button_index
                    main_window_state.is_window_open[selected_button_index] = CoreLib.ImGui.toggle_button(button_label, main_window_state.is_window_open[selected_button_index])
                    
                    if main_window_state.is_window_open[selected_button_index]:
                        title = main_window_state.button_list[selected_button_index]
                        explanation_text_content = main_window_state.description_list[selected_button_index]
                        method = main_window_state.method_mapping.get(title, None)

                
                PyImGui.end_table()  # End the table
                
            PyImGui.separator()  # Separator between sections

            DrawTextWithTitle(title, explanation_text_content)
            

            if main_window_state.is_window_open[0]:
                ShowPyImGuiDemoWindow()

            if main_window_state.is_window_open[1]:
                ShowPyMapWindow()

            if main_window_state.is_window_open[2]:
                ShowPyAgentWindow()

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


