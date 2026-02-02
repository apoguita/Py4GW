from Py4GWCoreLib import IconsFontAwesome5, PyImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Py4GWCoreLib import Agent, Player
import math

from Sources.oazix.CustomBehaviors.primitives.parties.party_flagging_manager import PartyFlaggingManager


class FlagsUI:
    @staticmethod
    def render_configuration() -> None:
        """
        Render the configurable flags/formation UI.
        Note: The caller should check if the section is expanded before calling this method.
        """
        flag_manager = PartyFlaggingManager()

        PyImGui.separator()
        PyImGui.text("[FLAGGING] configure party flag formation :")
        # Always enable overlay; remove UI toggle
        flag_manager.enable_debug_overlay = True

        # Tabs for configuration
        if PyImGui.begin_tab_bar("flag_config_tabs"):

            # Preset 1: Grid layout
            if PyImGui.begin_tab_item("preset1 : grid layout"):
                FlagsUI._render_preset1_grid()
                PyImGui.end_tab_item()

            # Preset 2: Stacked
            if PyImGui.begin_tab_item("preset2 : stacked"):
                PyImGui.text("All flags are stacked at the leader position.\nNo additional configuration is needed here.")
                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()
            
    @staticmethod
    def _render_preset1_grid() -> None:
        flag_manager = PartyFlaggingManager()

        # Manual flag assignment grid
        PyImGui.text_colored("Manual Flag Assignment Grid:", (0.0, 1.0, 1.0, 1.0))
        PyImGui.text_colored("(Leader facing forward, flags behind)", (0.7, 0.7, 0.7, 1.0))

        # Spacing radius (Preset 1)
        current_spacing = flag_manager.spacing_radius
        new_spacing = PyImGui.slider_float("Spacing Radius", current_spacing, 50.0, 300.0)
        PyImGui.same_line(0.0, -1.0)
        PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Distance between flags in the grid preset (game units)")
        if new_spacing != current_spacing:
            flag_manager.spacing_radius = new_spacing
            leader_x, leader_y = Player.GetXY()
            leader_agent_id = Player.GetAgentID()
            leader_angle = Agent.GetRotationAngle(leader_agent_id)
            flag_manager.update_formation_positions(leader_x, leader_y, leader_angle, "preset_1")


        # Leader position indicator (centered above grid)
        PyImGui.spacing()
        PyImGui.indent(220)  # Center the leader indicator
        PyImGui.text_colored(f"{IconsFontAwesome5.ICON_USER} LEADER", (0.0, 1.0, 0.0, 1.0))
        PyImGui.unindent(220)
        PyImGui.text_colored("        |", (0.5, 0.5, 0.5, 1.0))
        PyImGui.text_colored("        v", (0.5, 0.5, 0.5, 1.0))
        PyImGui.spacing()

        # Get all party members for dropdown
        account_email = Player.GetAccountEmail()
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()

        # Build list of available party members (same map)
        # Store both display names and emails
        available_members_display = ["<None>"]  # Display names
        available_members_emails = [""]  # Corresponding emails (empty for <None>)

        my_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        if my_account is not None:
            for account in all_accounts:
                if account.AccountEmail == account_email:
                    continue  # Skip leader
                is_in_map = (
                    my_account.MapID == account.MapID
                    and my_account.MapRegion == account.MapRegion
                    and my_account.MapDistrict == account.MapDistrict
                )
                if is_in_map:
                    # Use character name for display, store email for lookup
                    char_name = account.CharacterName if account.CharacterName else account.AccountEmail
                    available_members_display.append(char_name)
                    available_members_emails.append(account.AccountEmail)

        # Auto-assign button
        if PyImGui.button(f"{IconsFontAwesome5.ICON_MAGIC} Auto-Assign Characters to Grid"):
            # Auto-assign party members to flags in order (Flag 1, 2, 3, ...)
            for i, email in enumerate(available_members_emails[1:]):  # Skip <None> at index 0
                if i >= 12:  # Max 12 flags
                    break
                flag_manager.set_flag_account_email(i, email)
            # Also place flags at leader position so overlay updates immediately
            leader_x, leader_y = Player.GetXY()
            leader_agent_id = Player.GetAgentID()
            leader_angle = Agent.GetRotationAngle(leader_agent_id)
            flag_manager.update_formation_positions(leader_x, leader_y, leader_angle, "preset_1")
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip(
                "Automatically assign all party members to flags in order (Flag 1 \u2192 first member, Flag 2 \u2192 second member, etc.)"
            )

        PyImGui.spacing()

        # Grid layout: Perfect 3x4 grid (12 flags)
        # Flag positions in formation (leader at top, flags below):
        # Row 1 (closest to leader): Flag 1, Flag 2, Flag 3
        # Row 2: Flag 4, Flag 5, Flag 6
        # Row 3: Flag 7, Flag 8, Flag 9
        # Row 4 (furthest from leader): Flag 10, Flag 11, Flag 12

        grid_layout = [
            [0, 1, 2],  # Row 1: Flag 1, Flag 2, Flag 3 (closest)
            [3, 4, 5],  # Row 2: Flag 4, Flag 5, Flag 6
            [6, 7, 8],  # Row 3: Flag 7, Flag 8, Flag 9
            [9, 10, 11],  # Row 4: Flag 10, Flag 11, Flag 12 (furthest)
        ]

        # Get current leader position for applying changes
        leader_x, leader_y = Player.GetXY()
        leader_agent_id = Player.GetAgentID()
        leader_angle = Agent.GetRotationAngle(leader_agent_id)

        # Draw the grid
        for row in grid_layout:
            for col_idx, flag_index in enumerate(row):
                if flag_index == -1:
                    # Empty slot
                    PyImGui.text("     ")
                else:
                    flag_number = flag_index + 1

                    # Get current assignment
                    current_email = flag_manager.get_flag_account_email(flag_index)

                    # Find current selection index by matching email
                    if current_email:
                        try:
                            current_idx = available_members_emails.index(current_email)
                        except ValueError:
                            current_idx = 0  # Not found, default to <None>
                    else:
                        current_idx = 0

                    # Draw flag number label
                    PyImGui.text(f"Flag {flag_number}:")
                    PyImGui.same_line(0, 5)

                    # Draw combo box with display names
                    PyImGui.push_item_width(150)
                    new_idx = PyImGui.combo(f"##{flag_number}", current_idx, available_members_display)
                    PyImGui.pop_item_width()

                    # Handle selection change
                    if new_idx != current_idx:
                        if new_idx == 0:
                            # Clear this flag
                            flag_manager.clear_flag(flag_index)
                        else:
                            # Assign this flag - calculate position based on formation
                            selected_email = available_members_emails[new_idx]

                            # Calculate formation position for this specific flag
                            spacing = flag_manager.spacing_radius
                            if spacing == 0.0:
                                spacing = 100.0

                            # Formation offsets (same as in assign_formation_preset_1)
                            formation_offsets = [
                                (-spacing, -spacing),  # Flag 1
                                (-spacing, 0),  # Flag 2
                                (-spacing, spacing),  # Flag 3
                                (-spacing * 2, -spacing),  # Flag 4
                                (-spacing * 2, 0),  # Flag 5
                                (-spacing * 2, spacing),  # Flag 6
                                (-spacing * 3, -spacing),  # Flag 7
                                (-spacing * 3, 0),  # Flag 8
                                (-spacing * 3, spacing),  # Flag 9
                                (-spacing * 4, -spacing),  # Flag 10
                                (-spacing * 4, 0),  # Flag 11
                                (-spacing * 4, spacing),  # Flag 12
                            ]

                            forward_offset, right_offset = formation_offsets[flag_index]

                            # Transform to world coordinates
                            cos_angle = math.cos(leader_angle)
                            sin_angle = math.sin(leader_angle)
                            world_x = leader_x + (forward_offset * cos_angle + right_offset * sin_angle)
                            world_y = leader_y + (forward_offset * sin_angle - right_offset * cos_angle)

                            # Set this specific flag without clearing others
                            flag_manager.set_flag_data(flag_index, selected_email, world_x, world_y)
                # Add spacing between columns (except last column)
                if col_idx < len(row) - 1:
                    PyImGui.same_line(0, 10)

            # Add small vertical spacing between rows
            PyImGui.spacing()


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