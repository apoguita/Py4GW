from collections import deque
from typing import Any, Callable, Dict, Generator
from Py4GWCoreLib import IconsFontAwesome5, Map, PyImGui, Player
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.auto_mover.auto_follow_agent import AutoFollowAgent
from Sources.oazix.CustomBehaviors.primitives.auto_mover.auto_follow_path import AutoFollowPath
from Sources.oazix.CustomBehaviors.primitives.auto_mover.waypoint_builder import WaypointBuilder
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility

shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
edit_flags: Dict[int, bool] = {}

@staticmethod
def render():

    PyImGui.text(f"auto-moving from map coords [U] require [MissionMap+ - Widget]")
    PyImGui.text(f"such feature will inject additionnal utility skills,")
    PyImGui.text(f"so the leader account will be able to act as a bot - fully autonomous")
    PyImGui.separator()

    if not custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader():
        PyImGui.text(f"feature restricted to party leader.")
        return

    # Render editable text box for coords
    instance: CustomBehaviorBaseUtility | None = CustomBehaviorLoader().custom_combat_behavior

    if instance is None: return
    auto_follow_path = AutoFollowPath()
    auto_follow_agent = AutoFollowAgent()

    if auto_follow_path.is_movement_running():
        if PyImGui.tree_node_ex("Follow path & fight", PyImGui.TreeNodeFlags.DefaultOpen):

            PyImGui.text(f"Running {auto_follow_path.get_movement_progress()}%")
            
            if PyImGui.button("STOP"):
                auto_follow_path.stop_movement()

            if not auto_follow_path.is_movement_paused():
                PyImGui.same_line(0,5)
                if PyImGui.button("PAUSE"):
                    auto_follow_path.pause_movement()

            if auto_follow_path.is_movement_paused():
                PyImGui.same_line(0,5)
                if PyImGui.button("RESUME"):
                    auto_follow_path.resume_movement()

            PyImGui.tree_pop()


    if PyImGui.tree_node_ex("Waypoint builder", PyImGui.TreeNodeFlags.DefaultOpen):

        if not Map.MissionMap.IsWindowOpen():
            PyImGui.text_colored(f"To manage waypoints & path, you must have MissionMap+ openned", Utils.ColorToTuple(Utils.RGBToColor(131, 250, 146, 255)))

        if Map.MissionMap.IsWindowOpen():
            PyImGui.text_colored(f"Right click on MissionMap+ to start build a path.", Utils.ColorToTuple(Utils.RGBToColor(131, 250, 146, 255)))

            auto_follow_path.render()

            if len(auto_follow_path.get_list_of_waypoints()) == 0:
                if PyImGui.button("or paste an array of tuple[float, float] from clipboard"):
                    clipboard_array:str = PyImGui.get_clipboard_text()
                    auto_follow_path.try_inject_waypoint_coordinates_from_clipboard(clipboard_array)
                
            if PyImGui.button("or paste a 'float, float' from clipboard"):
                    clipboard_tuple:str = PyImGui.get_clipboard_text()
                    auto_follow_path.try_inject_waypoint_coordinate_from_clipboard(clipboard_tuple)

            if len(auto_follow_path.get_list_of_waypoints()) >0:
                if PyImGui.button("Remove last waypoint from the list"):
                    auto_follow_path.remove_last_waypoint_from_the_list()
                PyImGui.same_line(0,5)
                if PyImGui.button("clear list"):
                    auto_follow_path.clear_list_of_waypoints()

                table_flags = PyImGui.TableFlags.Sortable | PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg
                if PyImGui.begin_table("Waypoints", 6, table_flags):
                    # Setup columns
                    PyImGui.table_setup_column("index", PyImGui.TableColumnFlags.NoSort)
                    PyImGui.table_setup_column("coordinate", PyImGui.TableColumnFlags.WidthFixed, 90)
                    PyImGui.table_setup_column("edit", PyImGui.TableColumnFlags.WidthFixed, 150)
                    PyImGui.table_setup_column("ctrl", PyImGui.TableColumnFlags.NoSort)
                    PyImGui.table_setup_column("remove", PyImGui.TableColumnFlags.NoSort)
                    PyImGui.table_setup_column("follow", PyImGui.TableColumnFlags.NoSort)
                    PyImGui.table_headers_row()

                    waypoints = auto_follow_path.get_list_of_waypoints()

                    for index, point in enumerate(waypoints):
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        PyImGui.text(f"{index}")
                        PyImGui.table_next_column()
                        int_point = (int(point[0]), int(point[1]))
                        PyImGui.text(f"{int_point}")
                        PyImGui.table_next_column()

                        if edit_flags.get(index, False):
                            if PyImGui.button(f"HIDE_{index}"):
                                edit_flags[index] = not edit_flags.get(index, False)
                        else:
                            if PyImGui.button(f"{IconsFontAwesome5.ICON_EDIT}##edit_{index}"):
                                edit_flags[index] = not edit_flags.get(index, False)
                        
                        if edit_flags.get(index, False):
                            min_x, min_y, max_x, max_y = Map.GetMapBoundaries()
                            # sliders for X/Y (in game units)
                            edit_x = point[0]
                            edit_y = point[1]
                            edit_x = PyImGui.slider_float(f"X##X_{index}", float(edit_x), float(min_x), float(max_x))
                            edit_y = PyImGui.slider_float(f"Y##Y_{index}", float(edit_y), float(min_y), float(max_y))
                            PyImGui.text(f"increments")

                            waypoints[index] = (edit_x, edit_y)
                            if PyImGui.small_button(f"+10 x ##+X_{index}"):
                                waypoints[index] = waypoints[index] = (waypoints[index][0]+20, waypoints[index][1])
                            PyImGui.same_line(0,5)
                            if PyImGui.small_button(f"-10 x ##-X_{index}"):
                                waypoints[index] = waypoints[index] = (waypoints[index][0]-20, waypoints[index][1])
                            if PyImGui.small_button(f"+10 y ##+Y_{index}"):
                                waypoints[index] = waypoints[index] = (waypoints[index][0], waypoints[index][1]+20)
                            PyImGui.same_line(0,5)
                            if PyImGui.small_button(f"-10 y ##-Y_{index}"):
                                waypoints[index] = waypoints[index] = (waypoints[index][0], waypoints[index][1]-20)
                        
                        PyImGui.table_next_column()

                        if PyImGui.button(f"{IconsFontAwesome5.ICON_COPY}##copy_{index}"):
                            PyImGui.set_clipboard_text(f"({int(point[0])}, {int(point[1])})")
                        PyImGui.show_tooltip("Copy waypoint coordinates")

                        PyImGui.same_line(0,5)
                        if PyImGui.button(f"{IconsFontAwesome5.ICON_PASTE}##paste_{index}"):
                            clipboard_text = PyImGui.get_clipboard_text()
                            coordinate = WaypointBuilder.parse_coordinate_from_text(clipboard_text)
                            if coordinate is not None:
                                waypoints[index] = coordinate
                        PyImGui.show_tooltip("Paste waypoint coordinates")

                        PyImGui.same_line(0,5)
                        if PyImGui.button(f"{IconsFontAwesome5.ICON_ARROW_UP}##up_{index}"):
                            if index > 0:
                                waypoints[index], waypoints[index-1] = waypoints[index-1], waypoints[index]
                                # Also swap edit flags if they exist
                                edit_flag_current = edit_flags.get(index, False)
                                edit_flag_above = edit_flags.get(index-1, False)
                                edit_flags[index] = edit_flag_above
                                edit_flags[index-1] = edit_flag_current
                        PyImGui.show_tooltip("Move waypoint up")
                        

                        PyImGui.same_line(0,5)
                        if PyImGui.button(f"{IconsFontAwesome5.ICON_ARROW_DOWN}##down_{index}"):
                            if index < len(waypoints) - 1:
                                waypoints[index], waypoints[index+1] = waypoints[index+1], waypoints[index]
                                # Also swap edit flags if they exist
                                edit_flag_current = edit_flags.get(index, False)
                                edit_flag_below = edit_flags.get(index+1, False)
                                edit_flags[index] = edit_flag_below
                                edit_flags[index+1] = edit_flag_current
                        PyImGui.show_tooltip("Move waypoint down")

                        PyImGui.same_line(0,5)
                        if PyImGui.button(f"{IconsFontAwesome5.ICON_PLUS}new##new_{index}"):
                            waypoints.insert(index + 1, (0,0))
                        PyImGui.show_tooltip("Add new waypoint just after")

                        PyImGui.table_next_column()

                        if PyImGui.button(f"{IconsFontAwesome5.ICON_TIMES}##REMOVE_{index}"):
                            auto_follow_path.remove_waypoint(index)
                            edit_flags.pop(index, None)
                            pass
                        PyImGui.show_tooltip("Remove waypoint")
                        
                        PyImGui.table_next_column()
                        if not auto_follow_path.is_movement_running():
                            if PyImGui.button(f"Start moving from point:{index} to the end"):
                                auto_follow_path.start_movement(start_at_waypoint_index=index)

                    # End the nested ControlTable
                    PyImGui.end_table()

                if PyImGui.button("Copy waypoints coordinates"):
                    points = auto_follow_path.get_list_of_waypoints()
                    if points:
                        # Format coordinates as [ (xxx, xxx), (xxx, xxx), etc ] - cast as INT
                        formatted_coords = ", ".join([f"({int(point[0])}, {int(point[1])})" for point in points])
                        coordinates = f"[ {formatted_coords} ]"
                        PyImGui.set_clipboard_text(coordinates)
                PyImGui.same_line(0,5)
                if PyImGui.button("Copy autopathing coordinates"):
                    points = auto_follow_path.get_final_path()
                    # Format coordinates as [ (xxx, xxx), (xxx, xxx), etc ]
                    formatted_coords = ", ".join([f"({int(point[0])}, {int(point[1])})" for point in points])
                    coordinates = f"[ {formatted_coords} ]"
                    PyImGui.set_clipboard_text(coordinates)

        if True:
            PyImGui.text(f"CurrentMap: {Map.GetMapID()}")
            coordinate = Player.GetXY()
            PyImGui.text(f"CurrentPos: {int(coordinate[0])}, {int(coordinate[1])}") 
            PyImGui.same_line(0,5)
            if PyImGui.small_button("Copy"):
                PyImGui.set_clipboard_text(f"({int(coordinate[0])}, {int(coordinate[1])})")

            PyImGui.same_line(0,5)

            if PyImGui.small_button("Insert as waypoint"):
                coordinate = Player.GetXY()
                auto_follow_path.add_raw_waypoint(coordinate)

        PyImGui.tree_pop()

        # PyImGui.separator()

    PyImGui.separator()

    if PyImGui.tree_node_ex("Follow agent_id", 0):
        PyImGui.text("This will follow an agent_id, and stop when the agent_id is no longer valid")
        PyImGui.text("This is useful for following a quest NPC, or a merchant")
        PyImGui.text("This will NOT work for enemies, as they are not valid targets for movement")
        PyImGui.separator()

        # Show status if following is active
        if auto_follow_agent.is_running():
            PyImGui.text(f"Following agent_id: {auto_follow_agent.get_target_agent_id()}")
            PyImGui.text(f"Progress: {auto_follow_agent.get_movement_progress():.1f}%")

            # Show agent name and position if available
            agent_name = auto_follow_agent.get_target_agent_name()
            if agent_name:
                PyImGui.text(f"Agent name: {agent_name}")
            agent_pos = auto_follow_agent.get_target_agent_position()
            if agent_pos != (0.0, 0.0):
                PyImGui.text(f"Agent position: ({int(agent_pos[0])}, {int(agent_pos[1])})")

            if PyImGui.button("STOP##follow_agent"):
                auto_follow_agent.stop()

            if not auto_follow_agent.is_paused():
                PyImGui.same_line(0, 5)
                if PyImGui.button("PAUSE##follow_agent"):
                    auto_follow_agent.pause()

            if auto_follow_agent.is_paused():
                PyImGui.same_line(0, 5)
                if PyImGui.button("RESUME##follow_agent"):
                    auto_follow_agent.resume()
        else:
            # Agent ID input
            PyImGui.text("Agent ID to follow:")
            selected_id = auto_follow_agent.get_selected_agent_id()
            new_id = PyImGui.input_int("##agent_id_input", selected_id)
            if new_id != selected_id:
                auto_follow_agent.set_selected_agent_id(new_id)

            PyImGui.same_line(0, 5)
            if PyImGui.small_button("Get from current target"):
                if not auto_follow_agent.set_agent_from_current_target():
                    PyImGui.text_colored("No valid target selected", Utils.ColorToTuple(Utils.RGBToColor(255, 100, 100, 255)))

            PyImGui.same_line(0, 5)
            if PyImGui.small_button("Get from mouse over"):
                if not auto_follow_agent.set_agent_from_mouse_over():
                    PyImGui.text_colored("No valid agent under mouse", Utils.ColorToTuple(Utils.RGBToColor(255, 100, 100, 255)))

            # Show agent info if valid
            if auto_follow_agent.is_selected_agent_valid():
                agent_name = auto_follow_agent.get_selected_agent_name()
                if agent_name:
                    PyImGui.text_colored(f"Agent: {agent_name}", Utils.ColorToTuple(Utils.RGBToColor(131, 250, 146, 255)))
                agent_pos = auto_follow_agent.get_selected_agent_position()
                PyImGui.text(f"Position: ({int(agent_pos[0])}, {int(agent_pos[1])})")
            elif auto_follow_agent.get_selected_agent_id() != 0:
                PyImGui.text_colored("Invalid agent_id", Utils.ColorToTuple(Utils.RGBToColor(255, 100, 100, 255)))

            # Follow distance input
            PyImGui.text("Follow distance (stop when within this range):")
            selected_distance = auto_follow_agent.get_selected_follow_distance()
            new_distance = PyImGui.slider_float("##follow_distance", selected_distance, 100.0, 1000.0)
            if new_distance != selected_distance:
                auto_follow_agent.set_selected_follow_distance(new_distance)

            # Start button
            if PyImGui.button("Start following"):
                if not auto_follow_agent.start_following_selected():
                    PyImGui.text_colored("Cannot start: Invalid agent_id", Utils.ColorToTuple(Utils.RGBToColor(255, 100, 100, 255)))

        PyImGui.tree_pop()
