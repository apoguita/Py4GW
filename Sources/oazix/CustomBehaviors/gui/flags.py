from Py4GWCoreLib import PyImGui
from Sources.oazix.CustomBehaviors.gui.flags_grid import FlagGridUI
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Py4GWCoreLib import Agent, Player
import math

from Sources.oazix.CustomBehaviors.primitives.parties.party_flagging_manager import PartyFlaggingManager


class FlagsUI:
    _persistence = PersistenceLocator().flagging
    _spacing_initialized: bool = False

    @staticmethod
    def render_configuration() -> None:
        """
        Render the configurable flags/formation UI.
        Note: The caller should check if the section is expanded before calling this method.
        """
        flag_manager = PartyFlaggingManager()

        # Load spacing from INI on first render
        if not FlagsUI._spacing_initialized:
            saved_spacing = FlagsUI._persistence.read_spacing_radius()
            flag_manager.spacing_radius = saved_spacing
            FlagsUI._spacing_initialized = True

        PyImGui.separator()
        PyImGui.text("[FLAGGING] configure party flag formation :")
        # Always enable overlay; remove UI toggle
        flag_manager.enable_debug_overlay = True

        # Tabs for configuration
        if PyImGui.begin_tab_bar("flag_config_tabs"):

            # Grid layout with FlagGridUI
            if PyImGui.begin_tab_item("Grid Layout"):
                FlagsUI._render_grid_layout()
                PyImGui.end_tab_item()

            # Preset 2: Stacked
            if PyImGui.begin_tab_item("Stacked"):
                PyImGui.text("All flags are stacked at the leader position.\nNo additional configuration is needed here.")
                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

    @staticmethod
    def _render_grid_layout() -> None:
        """Render the grid layout using FlagGridUI bound to PartyFlaggingManager."""
        flag_manager = PartyFlaggingManager()

        # Spacing radius slider
        current_spacing = flag_manager.spacing_radius
        new_spacing = PyImGui.slider_float("Spacing Radius", current_spacing, 50.0, 300.0)
        PyImGui.same_line(0.0, -1.0)
        PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Distance between flags in the grid formation (game units)")
        if new_spacing != current_spacing:
            flag_manager.spacing_radius = new_spacing
            # Save to INI when changed
            FlagsUI._persistence.write_spacing_radius(new_spacing)

        PyImGui.spacing()

        # Render the FlagGridUI
        FlagGridUI.render_configuration()

    @staticmethod
    def apply_grid_to_flag_manager() -> None:
        """Apply the current grid assignments to PartyFlaggingManager with calculated positions."""
        flag_manager = PartyFlaggingManager()

        # Get grid assignments from FlagGridUI (grid_index -> email)
        assignments = FlagGridUI.get_assignments_dict()

        # Clear all flags first
        flag_manager.clear_all_flags()

        if not assignments:
            return

        # Get leader position and angle for calculating world positions
        leader_x, leader_y = Player.GetXY()
        leader_agent_id = Player.GetAgentID()
        leader_angle = Agent.GetRotationAngle(leader_agent_id)
        leader_email = Player.GetAccountEmail()

        spacing = flag_manager.spacing_radius
        if spacing == 0.0:
            spacing = 100.0

        # Calculate rotation
        cos_angle = math.cos(leader_angle)
        sin_angle = math.sin(leader_angle)

        # Find leader's grid position
        grid_size = 5
        leader_grid_index: int | None = None
        for grid_index, email in assignments.items():
            if email == leader_email:
                leader_grid_index = grid_index
                break

        # If leader not in grid, use center of grid as reference
        if leader_grid_index is None:
            leader_row, leader_col = grid_size // 2, grid_size // 2
        else:
            leader_row = leader_grid_index // grid_size
            leader_col = leader_grid_index % grid_size

        # Assign to flag manager (max 12 flags)
        flag_index = 0
        for grid_index, email in sorted(assignments.items(), key=lambda x: x[0]):
            if flag_index >= 12:  # Max 12 flags in PartyFlaggingManager
                break

            # Calculate row and column from grid_index
            row = grid_index // grid_size
            col = grid_index % grid_size

            # Calculate offset RELATIVE to leader's grid position
            row_delta = row - leader_row  # Positive = further back from leader
            col_delta = col - leader_col  # Positive = right of leader

            # Forward/backward: negative row_delta means in front, positive means behind
            forward_offset = -spacing * row_delta  # Negative = behind leader
            right_offset = spacing * col_delta

            # Transform from local (forward/right) to world coordinates
            world_x = leader_x + (forward_offset * cos_angle + right_offset * sin_angle)
            world_y = leader_y + (forward_offset * sin_angle - right_offset * cos_angle)

            # Set flag data
            flag_manager.set_flag_data(flag_index, email, world_x, world_y)
            flag_index += 1


    @staticmethod
    def render_overlay() -> None:
        flag_manager = PartyFlaggingManager()
        # Force overlay always on from UI perspective
        flag_manager.enable_debug_overlay = True
        if flag_manager.enable_debug_overlay:
            behavior = CustomBehaviorLoader().custom_combat_behavior
            if behavior is not None:
                skills_list = behavior.get_skills_final_list()
                current_state = behavior.get_final_state()
                from Sources.oazix.CustomBehaviors.skills.following.follow_flag_utility_new import (
                    FollowFlagUtilityNew,
                )
                for skill_utility in skills_list:
                    if isinstance(skill_utility, FollowFlagUtilityNew):
                        skill_utility.draw_overlay(current_state)
                        break