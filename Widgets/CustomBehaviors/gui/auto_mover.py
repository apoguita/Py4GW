from collections import deque
from typing import Any, Callable, Generator
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
coords_input_buffer = ["0, 0"]  # Mutable object to persist between frames

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

    if not root.is_movement_running():

        if PyImGui.button("Follow path"):
            root.follow_path()

    PyImGui.text_colored(f"follow path will generate a valid path to the target.", Utils.ColorToTuple(Utils.RGBToColor(131, 250, 146, 255)))
    PyImGui.text_colored(f"no need to precise intermediary points if not needed", Utils.ColorToTuple(Utils.RGBToColor(131, 250, 146, 255)))

    if root.is_movement_running():
        PyImGui.text(f"Running {root.get_movement_progress()}%")
        if PyImGui.button("STOP"):
            root.stop_movement()
    
    PyImGui.separator()

    # missing feature, 
    # - edit current path

    PyImGui.text(f"Path builder")

    if not Map.MissionMap.IsWindowOpen():
        PyImGui.text(f"To manage path, you must have MissionMap+ openned")

    if Map.MissionMap.IsWindowOpen():
        root.render()

        if len(root.get_list_of_points()) >0:
            if PyImGui.button("Remove last point from the list"):
                root.remove_last_point_from_the_list()
            PyImGui.same_line(0,5)
            if PyImGui.button("clear list"):
                root.clear_list()
            if PyImGui.begin_child("x", size=(400, 200),border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
                for point in root.get_list_of_points():
                    PyImGui.text(f"{point}")
            PyImGui.end_child()

            if PyImGui.button("Copy waypoints coordinates"):
                points = root.get_list_of_points()
                if points:
                    # Format coordinates as [ (xxx, xxx), (xxx, xxx), etc ]
                    formatted_coords = ", ".join([f"({point[0]}, {point[1]})" for point in points])
                    coordinates = f"[ {formatted_coords} ]"
                    PyImGui.set_clipboard_text(coordinates)
            PyImGui.same_line(0,5)
            if PyImGui.button("Copy autopathing coordinates"):
                points = root.get_final_path()
                # Format coordinates as [ (xxx, xxx), (xxx, xxx), etc ]
                formatted_coords = ", ".join([f"({point[0]}, {point[1]})" for point in points])
                coordinates = f"[ {formatted_coords} ]"
                PyImGui.set_clipboard_text(coordinates)
            
        if len(root.get_list_of_points()) ==0:
            PyImGui.text(f"click on MissionMap+ to start build a path.")


    
