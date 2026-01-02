import os
import pathlib
from Py4GWCoreLib import IconsFontAwesome5, ImGui, PyImGui
from Py4GWCoreLib.Overlay import Overlay

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import Utils
from Py4GWCoreLib.Map import Map
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
from Widgets.CustomBehaviors.gui.flags import FlagsUI


script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))
py4gw_root_directory = project_root + f"\\..\\..\\"


def draw_party_target_vertical_line() -> None:
    """Draw a vertical indicator for the Party Custom Target only:
    - 3D pillar at the target position (world-space)
    - Screen-space vertical line aligned with the target's screen X, clamped to screen edges
    Draws nothing if no party custom target is set or it's invalid.
    """
    target_id = CustomBehaviorParty().get_party_custom_target()
    if not target_id or not GLOBAL_CACHE.Agent.IsValid(target_id):
        return

    try:
        tx, ty, _ = GLOBAL_CACHE.Agent.GetXYZ(target_id)

        ov = Overlay()
        ov.BeginDraw()
        try:
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
        finally:
            # Always call EndDraw to properly close the overlay context
            ov.EndDraw()
    except Exception:
        pass

@staticmethod
def render():
    PyImGui.text(f"[COMMON] Toggle party capabilities :")

    shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
    # Table layout for top controls
    flag_manager = PartyFlaggingManager()
    if PyImGui.begin_table("party_top_controls", 12, PyImGui.TableFlags.NoSavedSettings | PyImGui.TableFlags.SizingStretchProp):
        PyImGui.table_setup_column("All",          PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("SepAfterAll",  PyImGui.TableColumnFlags.WidthFixed,   12.0)
        PyImGui.table_setup_column("Combat",       PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("Following",    PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("Looting",      PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("Chesting",     PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("Blessing",     PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("Inventory",    PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("|",            PyImGui.TableColumnFlags.WidthFixed,   12.0)
        PyImGui.table_setup_column("FlagSet",      PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("FlagSet2",     PyImGui.TableColumnFlags.WidthFixed,   46.0)

        PyImGui.table_setup_column("FlagClear",    PyImGui.TableColumnFlags.WidthFixed,   46.0)

        PyImGui.table_next_row(PyImGui.TableRowFlags.NoFlag, 42.0)

        # All
        PyImGui.table_next_column()
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

        # Vertical spacer after ALL
        PyImGui.table_next_column()
        sep_x, sep_y = PyImGui.get_cursor_screen_pos()
        mid_x = sep_x + 6.0
        PyImGui.draw_list_add_line(mid_x, sep_y, mid_x, sep_y + 42.0, Utils.RGBToColor(200, 200, 200, 255), 2.0)
        PyImGui.dummy(12, 42)



        # Combat
        PyImGui.table_next_column()
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

        # Following
        PyImGui.table_next_column()
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
        if PyImGui.small_button(f"[+]##expand_following"):
            pass

        # Looting
        PyImGui.table_next_column()
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

        # Chesting
        PyImGui.table_next_column()
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

        # Blessing
        PyImGui.table_next_column()
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

        # Inventory
        PyImGui.table_next_column()
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

        # Separator
        PyImGui.table_next_column()
        sep_x, sep_y = PyImGui.get_cursor_screen_pos()
        mid_x = sep_x + 6.0
        PyImGui.draw_list_add_line(mid_x, sep_y, mid_x, sep_y + 42.0, Utils.RGBToColor(200, 200, 200, 255), 2.0)
        PyImGui.dummy(12, 42)

        # Set Flags at Leader Position (Preset 1: Grid)
        PyImGui.table_next_column()
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.FLAG_COLOR)
        clicked_p1 = ImGui.ImageButton(f"Set Flags at Leader Position", project_root + f"\\gui\\textures\\flag.png", 40, 40)
        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(1)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Preset 1 (Grid): Update flag positions based on leader's position and facing; auto-assign if none")

        if clicked_p1:
            flag_manager.auto_assign_emails_if_none_assigned()
            leader_x, leader_y = GLOBAL_CACHE.Player.GetXY()
            leader_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            leader_angle = GLOBAL_CACHE.Agent.GetRotationAngle(leader_agent_id)
            flag_manager.update_formation_positions(leader_x, leader_y, leader_angle, "preset_1")

        # Toggle expand/collapse using FlagsUI state (no module-level globals)
        FlagsUI.render_expand_toggle("", "expand_flagging_top")

        # Preset 2: Stacked flags at leader position (separate column)
        PyImGui.table_next_column()
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.FLAG_COLOR)
        clicked_p2 = ImGui.ImageButton(f"Set Flags (Stacked)##preset2", project_root + f"\\gui\\textures\\flag2.png", 40, 40)
        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(1)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Preset 2 (Stacked): Stack all assigned flags at the leader's position; auto-assign if none")
        if clicked_p2:
            flag_manager.auto_assign_emails_if_none_assigned()
            leader_x, leader_y = GLOBAL_CACHE.Player.GetXY()
            leader_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            leader_angle = GLOBAL_CACHE.Agent.GetRotationAngle(leader_agent_id)
            flag_manager.update_formation_positions(leader_x, leader_y, leader_angle, "preset_2")

        # Clear Flag Positions
        PyImGui.table_next_column()
        if flag_manager.are_flags_defined():
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(200, 30, 0, 255)))
            if ImGui.ImageButton(f"Clear Flag Positions", project_root + f"\\gui\\textures\\unflag.png", 40, 40):
                flag_manager.clear_all_flag_positions()
            PyImGui.pop_style_var(1)
            PyImGui.pop_style_color(1)
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Remove flags from map (keeps dropdown assignments)")

        PyImGui.end_table()


    PyImGui.separator()

    if Map.IsExplorable():

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
                if PyImGui.button(f"{IconsFontAwesome5.ICON_TRASH} ResetPartyCustomTarget | id:{shared_data.party_target_id}"):
                    CustomBehaviorParty().set_party_custom_target(None)

            PyImGui.tree_pop()
            #PyImGui.separator()

    if Map.IsOutpost():
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
                    else : ImGui.show_tooltip(f"{account.CharacterName} - In {Map.GetMapName(account.MapID)}")

            ImGui.show_tooltip(f"----------------------------")
            ImGui.show_tooltip(f"{count_in_map}/{total_count} in current map")

            PyImGui.same_line(0, 5)

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PLANE} summon to GH"):
                    CustomBehaviorParty().schedule_action(PartyCommandConstants.travel_gh)
            else:
                if PyImGui.button(f"waiting..."):
                    pass

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

    if Map.IsExplorable() and False:

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

        if CustomBehaviorParty().get_party_forced_state() is not None:
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

    for entry in CustomBehaviorParty().get_shared_lock_manager().get_current_locks():
        PyImGui.text(f"entry={entry.key}-{entry.acquired_at_seconds}-{entry.expires_at_seconds}")

    if FlagsUI.is_expanded():
        if PyImGui.begin_child("flags_panel", size=(0, 500), border=True, flags=PyImGui.WindowFlags.AlwaysAutoResize):
            FlagsUI.render_configuration()
            PyImGui.end_child()

    # Always draw a vertical indicator for the (custom or current) target
    draw_party_target_vertical_line()

    # Draw the flagging overlay last so it appears on top
    FlagsUI.render_overlay()

