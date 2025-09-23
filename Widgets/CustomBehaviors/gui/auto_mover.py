from collections import deque
from typing import Any, Callable, Dict, Generator
from Py4GWCoreLib import IconsFontAwesome5, Map, PyImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.auto_mover.auto_mover import AutoMover
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader, MatchResult
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology_color import UtilitySkillTypologyColor
from Widgets.CustomBehaviors.skills.botting.move_if_stuck import MoveIfStuckUtility
from Widgets.CustomBehaviors.skills.botting.move_to_distant_chest_if_path_exists import MoveToDistantChestIfPathExistsUtility
from Widgets.CustomBehaviors.skills.botting.move_to_enemy_if_close_enough import MoveToEnemyIfCloseEnoughUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_dead import MoveToPartyMemberIfDeadUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_in_aggro import MoveToPartyMemberIfInAggroUtility
from Widgets.CustomBehaviors.skills.botting.resign_if_needed import ResignIfNeededUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_in_aggro import WaitIfInAggroUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_mana_too_low import WaitIfPartyMemberManaTooLowUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_needs_to_loot import WaitIfPartyMemberNeedsToLootUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility

shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
edit_flags: Dict[int, bool] = {}

@staticmethod
def render():

    PyImGui.text(f"auto-moving from map coords [U] require [MissionMap+ - Widget]")
    PyImGui.text(f"such feature will inject additionnal utility skills,")
    PyImGui.text(f"so the leader account will be able to act as a bot - fully autonomous")
    PyImGui.separator()

    if not GLOBAL_CACHE.Party.IsPartyLeader():
        PyImGui.text(f"feature restricted to party leader.")
        return

    # Render editable text box for coords
    instance: CustomBehaviorBaseUtility | None = CustomBehaviorLoader().custom_combat_behavior

    if instance is None: return
    root = AutoMover()

    if root.is_movement_running():
        PyImGui.text(f"Running {root.get_movement_progress()}%")
        
        if PyImGui.button("STOP"):
            root.stop_movement()

        if not root.is_movement_paused():
            if PyImGui.button("PAUSE"):
                root.pause_movement()

    if root.is_movement_paused():
        if PyImGui.button("RESUME"):
            root.resume_movement()
    
    PyImGui.text(f"Waypoint builder")

    if not Map.MissionMap.IsWindowOpen():
        PyImGui.text_colored(f"To manage waypoints & path, you must have MissionMap+ openned", Utils.ColorToTuple(Utils.RGBToColor(131, 250, 146, 255)))

    if Map.MissionMap.IsWindowOpen():
        root.render()

        current_value = root.is_waypoint_recording_activated()
        result:bool = PyImGui.checkbox("is waypoint recorded on map click", current_value)
        root.set_waypoint_recording_activated(result)

        if len(root.get_list_of_waypoints()) >0:
            if PyImGui.button("Remove last waypoint from the list"):
                root.remove_last_waypoint_from_the_list()
            PyImGui.same_line(0,5)
            if PyImGui.button("clear list"):
                root.clear_list_of_waypoints()

            table_flags = PyImGui.TableFlags.Sortable | PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg
            if PyImGui.begin_table("Waypoints", 5, table_flags):
                # Setup columns
                PyImGui.table_setup_column("index", PyImGui.TableColumnFlags.NoSort)
                PyImGui.table_setup_column("coordinate", PyImGui.TableColumnFlags.WidthFixed, 90)
                PyImGui.table_setup_column("edit", PyImGui.TableColumnFlags.WidthFixed, 250)
                PyImGui.table_setup_column("remove", PyImGui.TableColumnFlags.NoSort)
                PyImGui.table_setup_column("follow", PyImGui.TableColumnFlags.NoSort)
                PyImGui.table_headers_row()

                waypoints = root.get_list_of_waypoints()

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
                        if PyImGui.button(f"EDIT_{index}"):
                            edit_flags[index] = not edit_flags.get(index, False)
                    
                    if edit_flags.get(index, False):
                        min_x, min_y, max_x, max_y = Map.GetMapBoundaries()
                        # sliders for X/Y (in game units)
                        edit_x = point[0]
                        edit_y = point[1]
                        edit_x = PyImGui.slider_float(f"X_{index}", float(edit_x), float(min_x), float(max_x))
                        edit_y = PyImGui.slider_float(f"Y_{index}", float(edit_y), float(min_y), float(max_y))
                        waypoints[index] = (edit_x, edit_y)

                    PyImGui.table_next_column()

                    if PyImGui.button(f"REMOVE_{index}"):
                        root.remove_waypoint(index)
                        edit_flags.pop(index, None)
                        pass
                    
                    PyImGui.table_next_column()
                    if not root.is_movement_running():
                        if PyImGui.button(f"Start moving from point:{index} to the end"):
                            root.start_movement(start_at_waypoint_index=index)

                # End the nested ControlTable
                PyImGui.end_table()

            if PyImGui.button("Copy waypoints coordinates"):
                points = root.get_list_of_waypoints()
                if points:
                    # Format coordinates as [ (xxx, xxx), (xxx, xxx), etc ] - cast as INT
                    formatted_coords = ", ".join([f"({int(point[0])}, {int(point[1])})" for point in points])
                    coordinates = f"[ {formatted_coords} ]"
                    PyImGui.set_clipboard_text(coordinates)
            PyImGui.same_line(0,5)
            if PyImGui.button("Copy autopathing coordinates"):
                points = root.get_final_path()
                # Format coordinates as [ (xxx, xxx), (xxx, xxx), etc ]
                formatted_coords = ", ".join([f"({int(point[0])}, {int(point[1])})" for point in points])
                coordinates = f"[ {formatted_coords} ]"
                PyImGui.set_clipboard_text(coordinates)
            
        if len(root.get_list_of_waypoints()) ==0:
            PyImGui.text_colored(f"click on MissionMap+ to start build a path.", Utils.ColorToTuple(Utils.RGBToColor(131, 250, 146, 255)))
            if PyImGui.button("or paste an array of tuple[float, float] from clipboard"):

                clipboard:str = PyImGui.get_clipboard_text()
                root.try_inject_waypoint_coordinate_from_clipboard(clipboard)


    if True:
        PyImGui.text(f"CurrentMap: {GLOBAL_CACHE.Map.GetMapID()}")
        PyImGui.text(f"CurrentPos: {GLOBAL_CACHE.Player.GetXY()}") 
        PyImGui.same_line(0,5)
        if PyImGui.small_button("Copy"):
            coordinate = GLOBAL_CACHE.Player.GetXY()
            PyImGui.set_clipboard_text(f"({coordinate[0]}, {coordinate[1]})")

        PyImGui.separator()

