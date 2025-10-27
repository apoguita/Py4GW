import os
import pathlib
from Py4GWCoreLib import IconsFontAwesome5, ImGui, PyImGui
from Py4GWCoreLib.Overlay import Overlay

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import Utils
from Py4GWCoreLib.enums import SharedCommandType
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants
from Widgets.CustomBehaviors.primitives.parties.party_following_manager import PartyFollowingManager
from Widgets.CustomBehaviors.primitives.parties.party_flagging_manager import PartyFlaggingManager
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology_color import UtilitySkillTypologyColor

script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))
py4gw_root_directory = project_root + f"\\..\\..\\"

def draw_party_target_vertical_line() -> None:
    """Draw a vertical indicator for the Party Custom Target only:
    - 3D pillar at the target position (world-space)
    - Screen-space vertical line aligned with the target's screen X, clamped to screen edges
    Draws nothing if no party custom target is set or it's invalid.
    """
    try:
        target_id = CustomBehaviorParty().get_party_custom_target()
        if not target_id or not GLOBAL_CACHE.Agent.IsValid(target_id):
            return

        tx, ty, _ = GLOBAL_CACHE.Agent.GetXYZ(target_id)

        ov = Overlay()
        ov.BeginDraw()
        color = Utils.RGBToColor(255, 255, 0, 200)  # semi-opaque yellow

        # 1) 3D vertical pillar (from ground Z upwards)
        gz = Overlay().FindZ(tx, ty, 0)
        ov.DrawLine3D(tx, ty, gz, tx, ty, gz - 250, color, thickness=3.0)

        # 2) Screen-space vertical line.
        sx, _ = Overlay.WorldToScreen(tx, ty, gz)
        disp_w, disp_h = ov.GetDisplaySize()
        try:
            sx_i = int(sx)
        except Exception:
            sx_i = 0
        if disp_w is None or disp_h is None:
            disp_w, disp_h = 1920, 1080  # fallback
        if sx_i < 0:
            sx_i = 0
        elif sx_i >= disp_w:
            sx_i = disp_w - 1
        ov.DrawLine(sx_i, 0, sx_i, disp_h, color, thickness=3.0)

        ov.EndDraw()
    except Exception:
        pass

@staticmethod
def render():
    PyImGui.text(f"[COMMON] Toggle party capabilities :")

    shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
    if shared_data.is_enabled:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(62, 139, 95, 200)))
        if ImGui.ImageButton(f"disable everything", project_root + f"\\gui\\textures\\all.png", 40, 40):
            CustomBehaviorParty().set_party_is_enabled(False)
        ImGui.show_tooltip("disable everything")
    else:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
        if ImGui.ImageButton(f"enable everything", project_root + f"\\gui\\textures\\all.png", 40, 40):
            CustomBehaviorParty().set_party_is_enabled(True)
        ImGui.show_tooltip("enable everything")
    PyImGui.pop_style_var(1)
    PyImGui.pop_style_color(1)

    PyImGui.same_line(0, 10)

    if shared_data.is_combat_enabled:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.COMBAT_COLOR)
        if ImGui.ImageButton(f"disable combat", project_root + f"\\gui\\textures\\combat.png", 40, 40):
            CustomBehaviorParty().set_party_is_combat_enabled(False)
        ImGui.show_tooltip("disable combat")
    else:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
        if ImGui.ImageButton(f"enable combat", project_root + f"\\gui\\textures\\combat.png", 40, 40):
            CustomBehaviorParty().set_party_is_combat_enabled(True)
        ImGui.show_tooltip("enable combat")
    PyImGui.pop_style_var(1)
    PyImGui.pop_style_color(1)

    PyImGui.same_line(0, 10)

    if shared_data.is_following_enabled:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.FOLLOWING_COLOR)
        if ImGui.ImageButton(f"disable following", project_root + f"\\gui\\textures\\following.png", 40, 40):
            CustomBehaviorParty().set_party_is_following_enabled(False)
        ImGui.show_tooltip("disable following")
    else:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
        if ImGui.ImageButton(f"enable following", project_root + f"\\gui\\textures\\following.png", 40, 40):
            CustomBehaviorParty().set_party_is_following_enabled(True)
        ImGui.show_tooltip("enable following")
    PyImGui.pop_style_var(1)
    PyImGui.pop_style_color(1)

    PyImGui.same_line(0, 10)

    if shared_data.is_looting_enabled:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.LOOTING_COLOR)
        if ImGui.ImageButton(f"disable looting", project_root + f"\\gui\\textures\\loot.png", 40, 40):
            CustomBehaviorParty().set_party_is_looting_enabled(False)
        ImGui.show_tooltip("disable looting")
    else:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
        if ImGui.ImageButton(f"enable looting", project_root + f"\\gui\\textures\\loot.png", 40, 40):
            CustomBehaviorParty().set_party_is_looting_enabled(True)
        ImGui.show_tooltip("enable looting")
    PyImGui.pop_style_var(1)
    PyImGui.pop_style_color(1)

    PyImGui.same_line(0, 10)

    if shared_data.is_chesting_enabled:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.CHESTING_COLOR)
        if ImGui.ImageButton(f"disable chesting", project_root + f"\\gui\\textures\\chesting.png", 40, 40):
            CustomBehaviorParty().set_party_is_chesting_enabled(False)
        ImGui.show_tooltip("disable chesting")
    else:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
        if ImGui.ImageButton(f"enable chesting", project_root + f"\\gui\\textures\\chesting.png", 40, 40):
            CustomBehaviorParty().set_party_is_chesting_enabled(True)
        ImGui.show_tooltip("enable chesting")
    PyImGui.pop_style_var(1)
    PyImGui.pop_style_color(1)

    PyImGui.same_line(0, 10)

    if shared_data.is_blessing_enabled:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.BLESSING_COLOR)
        if ImGui.ImageButton(f"disable blessing", project_root + f"\\gui\\textures\\blessing.png", 40, 40):
            CustomBehaviorParty().set_party_is_blessing_enabled(False)
        ImGui.show_tooltip("disable blessing")
    else:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
        if ImGui.ImageButton(f"enable blessing", project_root + f"\\gui\\textures\\blessing.png", 40, 40):
            CustomBehaviorParty().set_party_is_blessing_enabled(True)
        ImGui.show_tooltip("enable blessing")
    PyImGui.pop_style_var(1)
    PyImGui.pop_style_color(1)

    PyImGui.same_line(0, 10)

    if shared_data.is_inventory_enabled:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.INVENTORY_COLOR)
        if ImGui.ImageButton(f"disable inventory management", project_root + f"\\gui\\textures\\inventory.png", 40, 40):
            CustomBehaviorParty().set_party_is_inventory_enabled(False)
        ImGui.show_tooltip("disable inventory management")
    else:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
        if ImGui.ImageButton(f"enable inventory management", project_root + f"\\gui\\textures\\inventory.png", 40, 40):
            CustomBehaviorParty().set_party_is_inventory_enabled(True)
        ImGui.show_tooltip("enable inventory management")
    PyImGui.pop_style_var(1)
    PyImGui.pop_style_color(1)

    PyImGui.separator()

    if GLOBAL_CACHE.Map.IsExplorable():

        if PyImGui.tree_node_ex("[EXPLORABLE] Feature across party :", PyImGui.TreeNodeFlags.DefaultOpen):

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PERSON_FALLING} Resign"):
                    CustomBehaviorParty().schedule_action(PartyCommandConstants.resign)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            PyImGui.same_line(0,5)

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PERSON_MILITARY_POINTING} Interract with target"):
                    CustomBehaviorParty().schedule_action(PartyCommandConstants.interract_with_target)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            PyImGui.same_line(0,5)

            if shared_data.party_target_id is None:
                if PyImGui.button(f"{IconsFontAwesome5.ICON_CROSSHAIRS} SetPartyCustomTarget"):
                    CustomBehaviorParty().set_party_custom_target(GLOBAL_CACHE.Player.GetTargetID())
            else:
                if PyImGui.button(f"{IconsFontAwesome5.ICON_TRASH} ResetPartyCustomTarget"):
                    CustomBehaviorParty().set_party_custom_target(None)
                PyImGui.same_line(0, 10)
                PyImGui.text(f"id:{CustomBehaviorParty().get_party_custom_target()}")



            PyImGui.tree_pop()

            # PyImGui.separator()

    if GLOBAL_CACHE.Map.IsOutpost():
        if PyImGui.tree_node_ex("[OUTPOST] Feature across party :", PyImGui.TreeNodeFlags.DefaultOpen):

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PLANE} summon all to current map"):
                    CustomBehaviorParty().schedule_action(PartyCommandConstants.summon_all_to_current_map)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            ImGui.show_tooltip("Ask all other open GW windows to travel to current map.")
            ImGui.show_tooltip(f"----------------------------")

            account_email = GLOBAL_CACHE.Player.GetAccountEmail()
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
            count_in_map = 0
            total_count = 0
            if self_account is not None:
                for account in accounts:
                    if account.AccountEmail == account_email:
                        continue
                    total_count += 1
                    is_in_map = (self_account.MapID == account.MapID and self_account.MapRegion == account.MapRegion and self_account.MapDistrict == account.MapDistrict)
                    if is_in_map :
                        ImGui.show_tooltip(f"{account.CharacterName} - In the current map")
                        count_in_map+=1
                    else : ImGui.show_tooltip(f"{account.CharacterName} - In {GLOBAL_CACHE.Map.GetMapName(account.MapID)}")

            ImGui.show_tooltip(f"----------------------------")
            ImGui.show_tooltip(f"{count_in_map}/{total_count} in current map")

            PyImGui.same_line(0, 5)

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PERSON_CIRCLE_PLUS} Invite all to leader party"):
                    CustomBehaviorParty().schedule_action(PartyCommandConstants.invite_all_to_leader_party)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            ImGui.show_tooltip("Ask all other open GW windows to current join sender party.")

            ImGui.show_tooltip(f"--------------Eligibles--------------")

            account_email = GLOBAL_CACHE.Player.GetAccountEmail()
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
            if self_account is not None:
                for account in accounts:
                    if account.AccountEmail == account_email:
                        continue
                    is_in_map = (self_account.MapID == account.MapID and self_account.MapRegion == account.MapRegion and self_account.MapDistrict == account.MapDistrict)
                    if is_in_map:
                        ImGui.show_tooltip(f"{account.CharacterName} - In the current map")

                ImGui.show_tooltip(f"--------------Not eligible--------------")

                for account in accounts:
                    if account.AccountEmail == account_email:
                        continue
                    is_in_map = (self_account.MapID == account.MapID and self_account.MapRegion == account.MapRegion and self_account.MapDistrict == account.MapDistrict)
                    if not is_in_map:
                        ImGui.show_tooltip(f"{account.CharacterName} - Not eligible (not in the current map)")

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PERSON_CIRCLE_XMARK} Leave current party"):
                    CustomBehaviorParty().schedule_action(PartyCommandConstants.leave_current_party)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            ImGui.show_tooltip("Ask all other open GW windows to leave their current party.")

            PyImGui.same_line(0, 5)

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PERSON_MILITARY_POINTING} Interract with target"):
                    CustomBehaviorParty().schedule_action(PartyCommandConstants.interract_with_target)
            else:
                if PyImGui.button(f"waiting..."):
                    pass

            PyImGui.tree_pop()

        # PyImGui.separator()

    if GLOBAL_CACHE.Map.IsExplorable() and True:

        if PyImGui.tree_node_ex("[EXPLORABLE] Following & Spreading settings :", 0):

            # Get the singleton manager
            manager = PartyFollowingManager()

            # Set narrower width for sliders to make labels more readable
            PyImGui.push_item_width(200.0)

            # Debug overlay toggle
            new_overlay_value = PyImGui.checkbox("Enable Debug Overlay", manager.enable_debug_overlay)
            if new_overlay_value != manager.enable_debug_overlay:
                manager.enable_debug_overlay = new_overlay_value

            PyImGui.same_line(0.0, -1.0)
            PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Show visual overlay with formation circles, distances, and movement vectors")

            # Force overlay rendering when enabled - this ensures overlays are always drawn
            if manager.enable_debug_overlay:
                    # Get the behavior instance and call overlay renderers
                    behavior = CustomBehaviorLoader().custom_combat_behavior
                    if behavior is not None:
                        skills_list = behavior.get_skills_final_list()
                        current_state = behavior.get_final_state()

                        # Import the utilities
                        from Widgets.CustomBehaviors.skills.following.follow_party_leader_only_utility import FollowPartyLeaderOnlyUtility
                        from Widgets.CustomBehaviors.skills.following.spread_during_combat_utility import SpreadDuringCombatUtility

                        # Render overlays for both utilities if they exist
                        for skill_utility in skills_list:
                            if isinstance(skill_utility, FollowPartyLeaderOnlyUtility):
                                skill_utility.draw_overlay(current_state)
                            elif isinstance(skill_utility, SpreadDuringCombatUtility):
                                skill_utility.draw_overlay(current_state)

            PyImGui.separator()

            # Configuration is now handled by individual utilities
            PyImGui.text_colored("Following & Spreading Configuration:", (0.0, 1.0, 1.0, 1.0))
            PyImGui.text_colored("Note: Configuration is managed by individual utilities", (0.7, 0.7, 0.7, 1.0))
            PyImGui.bullet_text("Follow Party Leader: Configured in follow_party_leader_only_utility")
            PyImGui.bullet_text("Spread During Combat: Configured in spread_during_combat_utility")
            PyImGui.text_colored("Enable debug overlay above to see detailed configuration panels", (0.7, 0.7, 0.7, 1.0))

            PyImGui.tree_pop()

    if GLOBAL_CACHE.Map.IsExplorable():
        if PyImGui.tree_node_ex("[FORMATION] Manage party flag formation :", 0):

            # Get the singleton manager
            flag_manager = PartyFlaggingManager()

            # Configuration sliders
            PyImGui.text_colored("Formation Configuration:", (0.0, 1.0, 1.0, 1.0))

            # Spacing radius slider
            new_spacing = PyImGui.slider_float("Spacing Radius", flag_manager.spacing_radius, 50.0, 300.0)
            if new_spacing != flag_manager.spacing_radius:
                flag_manager.spacing_radius = new_spacing

            PyImGui.same_line(0.0, -1.0)
            PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Distance between flag positions in the formation (game units)")

            PyImGui.separator()

            # Button 1: Set flags at leader position
            if PyImGui.button(f"{IconsFontAwesome5.ICON_FLAG} Set Flags at Leader Position"):
                # Update positions for currently assigned flags without changing assignments
                leader_x, leader_y = GLOBAL_CACHE.Player.GetXY()
                leader_agent_id = GLOBAL_CACHE.Player.GetAgentID()
                leader_angle = GLOBAL_CACHE.Agent.GetRotationAngle(leader_agent_id)
                flag_manager.update_formation_positions(leader_x, leader_y, leader_angle, "preset_1")

            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Update flag positions based on leader's current position and facing direction (keeps current assignments)")

            PyImGui.same_line(0, 10)

            # Button 2: Clear all flag positions
            if PyImGui.button(f"{IconsFontAwesome5.ICON_TRASH} Clear Flag Positions"):
                flag_manager.clear_all_flag_positions()
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Remove flags from map (keeps dropdown assignments)")

            PyImGui.separator()

            # Debug overlay toggle
            new_overlay_value = PyImGui.checkbox("Enable Flag Overlay", flag_manager.enable_debug_overlay)
            if new_overlay_value != flag_manager.enable_debug_overlay:
                flag_manager.enable_debug_overlay = new_overlay_value

            PyImGui.same_line(0.0, -1.0)
            PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Show visual overlay with flag positions on the map")

            # Force overlay rendering when enabled - this ensures overlays are always drawn
            if flag_manager.enable_debug_overlay:
                # Get the behavior instance and call overlay renderer
                behavior = CustomBehaviorLoader().custom_combat_behavior
                if behavior is not None:
                    skills_list = behavior.get_skills_final_list()
                    current_state = behavior.get_final_state()

                    # Import the utility
                    from Widgets.CustomBehaviors.skills.following.follow_flag_utility_new import FollowFlagUtilityNew

                    # Render overlay if the utility exists
                    for skill_utility in skills_list:
                        if isinstance(skill_utility, FollowFlagUtilityNew):
                            skill_utility.draw_overlay(current_state)
                            break

            PyImGui.separator()

            # Manual flag assignment grid
            PyImGui.text_colored("Manual Flag Assignment Grid:", (0.0, 1.0, 1.0, 1.0))
            PyImGui.text_colored("(Leader facing forward, flags behind)", (0.7, 0.7, 0.7, 1.0))

            # Leader position indicator (centered above grid)
            PyImGui.spacing()
            PyImGui.indent(220)  # Center the leader indicator
            PyImGui.text_colored(f"{IconsFontAwesome5.ICON_USER} LEADER", (0.0, 1.0, 0.0, 1.0))
            PyImGui.unindent(220)
            PyImGui.text_colored("        |", (0.5, 0.5, 0.5, 1.0))
            PyImGui.text_colored("        v", (0.5, 0.5, 0.5, 1.0))
            PyImGui.spacing()

            # Get all party members for dropdown
            account_email = GLOBAL_CACHE.Player.GetAccountEmail()
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
                    is_in_map = (my_account.MapID == account.MapID and
                               my_account.MapRegion == account.MapRegion and
                               my_account.MapDistrict == account.MapDistrict)
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
                leader_x, leader_y = GLOBAL_CACHE.Player.GetXY()
                leader_agent_id = GLOBAL_CACHE.Player.GetAgentID()
                leader_angle = GLOBAL_CACHE.Agent.GetRotationAngle(leader_agent_id)
                flag_manager.update_formation_positions(leader_x, leader_y, leader_angle, "preset_1")
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Automatically assign all party members to flags in order (Flag 1 → first member, Flag 2 → second member, etc.)")

            PyImGui.spacing()

            # Grid layout: Perfect 3x4 grid (12 flags)
            # Flag positions in formation (leader at top, flags below):
            # Row 1 (closest to leader): Flag 1, Flag 2, Flag 3
            # Row 2: Flag 4, Flag 5, Flag 6
            # Row 3: Flag 7, Flag 8, Flag 9
            # Row 4 (furthest from leader): Flag 10, Flag 11, Flag 12

            grid_layout = [
                [0, 1, 2],     # Row 1: Flag 1, Flag 2, Flag 3 (closest)
                [3, 4, 5],     # Row 2: Flag 4, Flag 5, Flag 6
                [6, 7, 8],     # Row 3: Flag 7, Flag 8, Flag 9
                [9, 10, 11],   # Row 4: Flag 10, Flag 11, Flag 12 (furthest)
            ]

            # Get current leader position for applying changes
            leader_x, leader_y = GLOBAL_CACHE.Player.GetXY()
            leader_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            leader_angle = GLOBAL_CACHE.Agent.GetRotationAngle(leader_agent_id)

            # Draw the grid
            for row_idx, row in enumerate(grid_layout):
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
                                import math
                                spacing = flag_manager.spacing_radius
                                if spacing == 0.0:
                                    spacing = 100.0

                                # Formation offsets (same as in assign_formation_preset_1)
                                formation_offsets = [
                                    (-spacing, -spacing),      # Flag 1
                                    (-spacing, 0),             # Flag 2
                                    (-spacing, spacing),       # Flag 3
                                    (-spacing * 2, -spacing),  # Flag 4
                                    (-spacing * 2, 0),         # Flag 5
                                    (-spacing * 2, spacing),   # Flag 6
                                    (-spacing * 3, -spacing),  # Flag 7
                                    (-spacing * 3, 0),         # Flag 8
                                    (-spacing * 3, spacing),   # Flag 9
                                    (-spacing * 4, -spacing),  # Flag 10
                                    (-spacing * 4, 0),         # Flag 11
                                    (-spacing * 4, spacing),   # Flag 12
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

            PyImGui.tree_pop()

    if PyImGui.tree_node_ex("[MANAGE] Enforce the main state machine for all party members :", PyImGui.TreeNodeFlags.DefaultOpen):

        ImGui.push_font("Italic", 12)
        PyImGui.text(f"using such force mode manually can be usefull to pre-cast, stop the combat, fallback, ect")
        ImGui.pop_font()

        green_color = Utils.ColorToTuple(Utils.RGBToColor(41, 144, 69, 255))

        if CustomBehaviorParty().get_party_forced_state() == BehaviorState.IN_AGGRO:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, green_color)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, green_color)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_FIST_RAISED} IN_AGGRO"):
            CustomBehaviorParty().set_party_forced_state(BehaviorState.IN_AGGRO)
        ImGui.show_tooltip("IN_AGGRO : enemy is combat range")
        if CustomBehaviorParty().get_party_forced_state() == BehaviorState.IN_AGGRO:
            PyImGui.pop_style_color(2)


        PyImGui.same_line(0,5)
        if CustomBehaviorParty().get_party_forced_state() == BehaviorState.CLOSE_TO_AGGRO:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, green_color)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, green_color)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_HAMSA} CLOSE_TO_AGGRO"):
            CustomBehaviorParty().set_party_forced_state(BehaviorState.CLOSE_TO_AGGRO)
        ImGui.show_tooltip("CLOSE_TO_AGGRO : enemy close to combat range")
        if CustomBehaviorParty().get_party_forced_state() == BehaviorState.CLOSE_TO_AGGRO:
            PyImGui.pop_style_color(2)


        PyImGui.same_line(0,5)
        if CustomBehaviorParty().get_party_forced_state() == BehaviorState.FAR_FROM_AGGRO:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, green_color)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, green_color)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_HIKING} FAR_FROM_AGGRO"):
            CustomBehaviorParty().set_party_forced_state(BehaviorState.FAR_FROM_AGGRO)
        ImGui.show_tooltip("CLOSE_TO_AGGRO : nothing close to fight")
        if CustomBehaviorParty().get_party_forced_state() == BehaviorState.FAR_FROM_AGGRO:
            PyImGui.pop_style_color(2)


        PyImGui.same_line(0,5)
        if CustomBehaviorParty().get_party_forced_state() == BehaviorState.IDLE:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, green_color)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, green_color)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_HOURGLASS} IDLE"):
            CustomBehaviorParty().set_party_forced_state(BehaviorState.IDLE)
        ImGui.show_tooltip("IDLE : town, dead, loading, ect...")
        if CustomBehaviorParty().get_party_forced_state() == BehaviorState.IDLE:
            PyImGui.pop_style_color(2)

        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, Utils.ColorToTuple(Utils.RGBToColor(200, 30, 30, 255)))
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, Utils.ColorToTuple(Utils.RGBToColor(240, 10, 0, 255)))
        if PyImGui.button(f"{IconsFontAwesome5.ICON_TIMES}"):
            CustomBehaviorParty().set_party_forced_state(None)
        ImGui.show_tooltip("Remove forced state")
        PyImGui.pop_style_color(2)

        PyImGui.same_line(0,5)
        PyImGui.text(f"Party forced state is ")
        PyImGui.same_line(0,0)
        PyImGui.text(f"{CustomBehaviorParty().get_party_forced_state()}")

        PyImGui.tree_pop()

    PyImGui.separator()

    constants.DEBUG = PyImGui.checkbox("with debugging logs", constants.DEBUG)
    PyImGui.same_line(0,5)

    if CustomBehaviorParty().is_ready_for_action():
        if PyImGui.button(f"{IconsFontAwesome5.ICON_HOUSE_CHIMNEY_WINDOW} Rename GW windows"):
            CustomBehaviorParty().schedule_action(PartyCommandConstants.rename_gw_windows)
    else:
        if PyImGui.button(f"waiting..."):
            pass

    PyImGui.separator()

    for entry in CustomBehaviorParty().get_shared_lock_manager().get_current_locks():
        PyImGui.text(f"entry={entry.key}-{entry.acquired_at_seconds}-{entry.expires_at_seconds}")




    # Always draw a vertical indicator for the (custom or current) target
    draw_party_target_vertical_line()

