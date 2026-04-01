import os
from Py4GWCoreLib import IconsFontAwesome5, ImGui, PyImGui
from Py4GWCoreLib.Overlay import Overlay

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import Utils
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums import SharedCommandType
from Py4GWCoreLib.enums_src.GameData_enums import ProfessionShort, ProfessionShort_Names
from Sources.Nikon_Scripts import Enemies
from Sources.oazix.CustomBehaviors.PathLocator import PathLocator
from Sources.oazix.CustomBehaviors.gui.flag_panel.flag_panel import FlagPanel
from Sources.oazix.CustomBehaviors.gui.flag_panel.flag_custom_grid_placement import FlagCustomGridPlacement
from Sources.oazix.CustomBehaviors.gui.flag_panel.flag_backward_grid_placement import FlagBackwardGridPlacement
from Sources.oazix.CustomBehaviors.gui.flag_panel.flag_stacked_placement import FlagStackedPlacement
from Sources.oazix.CustomBehaviors.gui.following_panel.following_panel import FollowingPanel
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.following_behavior_priority import FollowingBehaviorPriority
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers, custom_behavior_helpers_party
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants
from Sources.oazix.CustomBehaviors.primitives.parties.party_flagging_manager import PartyFlaggingManager
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology_color import UtilitySkillTypologyColor
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager

# Create expandable sections for different UI panels
project_root = PathLocator.get_custom_behaviors_root_directory()
icon_size = 35

def draw_party_target_vertical_line() -> None:
    """Draw a vertical indicator for the Party Custom Target only:
    - 3D pillar at the target position (world-space)
    - Screen-space vertical line aligned with the target's screen X, clamped to screen edges
    Draws nothing if no party custom target is set or it's invalid.
    """
    target_id = custom_behavior_helpers.CustomBehaviorHelperParty.get_party_custom_target()
    if not target_id or not Agent.IsValid(target_id):
        return

    try:
        tx, ty, _ = Agent.GetXYZ(target_id)

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
    if PyImGui.begin_table("party_top_controls", 9, PyImGui.TableFlags.NoSavedSettings | PyImGui.TableFlags.SizingStretchProp):
        PyImGui.table_setup_column("All",          PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("SepAfterAll",  PyImGui.TableColumnFlags.WidthFixed,   12.0)
        PyImGui.table_setup_column("Combat",       PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("Following",    PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("Looting",      PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("Chesting",     PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("Blessing",     PyImGui.TableColumnFlags.WidthFixed,   46.0)
        PyImGui.table_setup_column("Inventory",    PyImGui.TableColumnFlags.WidthFixed,   46.0)

        PyImGui.table_setup_column("FlagClear",    PyImGui.TableColumnFlags.WidthFixed,   46.0)

        PyImGui.table_next_row(PyImGui.TableRowFlags.NoFlag, 42.0)


        # All
        PyImGui.table_next_column()
        if shared_data.is_enabled:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(62, 139, 95, 200)))
            if ImGui.ImageButton(f"disable everything", project_root + f"\\gui\\textures\\all.png", icon_size, icon_size):
                CustomBehaviorParty().set_party_is_enabled(False)
            ImGui.show_tooltip("disable everything")
        else:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
            if ImGui.ImageButton(f"enable everything", project_root + f"\\gui\\textures\\all.png", icon_size, icon_size):
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
            if ImGui.ImageButton(f"disable combat", project_root + f"\\gui\\textures\\combat.png", icon_size, icon_size):
                CustomBehaviorParty().set_party_is_combat_enabled(False)
            ImGui.show_tooltip("disable combat")
        else:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
            if ImGui.ImageButton(f"enable combat", project_root + f"\\gui\\textures\\combat.png", icon_size, icon_size):
                CustomBehaviorParty().set_party_is_combat_enabled(True)
            ImGui.show_tooltip("enable combat")
        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(1)

        # Following
        PyImGui.table_next_column()
        if shared_data.is_following_enabled:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.FOLLOWING_COLOR)
            if ImGui.ImageButton(f"disable following", project_root + f"\\gui\\textures\\following.png", icon_size, icon_size):
                CustomBehaviorParty().set_party_is_following_enabled(False)
            ImGui.show_tooltip("disable following")
        else:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
            if ImGui.ImageButton(f"enable following", project_root + f"\\gui\\textures\\following.png", icon_size, icon_size):
                CustomBehaviorParty().set_party_is_following_enabled(True)
            ImGui.show_tooltip("enable following")
        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(1)

        # Looting
        PyImGui.table_next_column()
        if shared_data.is_looting_enabled:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.LOOTING_COLOR)
            if ImGui.ImageButton(f"disable looting", project_root + f"\\gui\\textures\\loot.png", icon_size, icon_size):
                CustomBehaviorParty().set_party_is_looting_enabled(False)
            ImGui.show_tooltip("disable looting")
        else:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
            if ImGui.ImageButton(f"enable looting", project_root + f"\\gui\\textures\\loot.png", icon_size, icon_size):
                CustomBehaviorParty().set_party_is_looting_enabled(True)
            ImGui.show_tooltip("enable looting")
        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(1)

        # Chesting
        PyImGui.table_next_column()
        if shared_data.is_chesting_enabled:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.CHESTING_COLOR)
            if ImGui.ImageButton(f"disable chesting", project_root + f"\\gui\\textures\\chesting.png", icon_size, icon_size):
                CustomBehaviorParty().set_party_is_chesting_enabled(False)
            ImGui.show_tooltip("disable chesting")
        else:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
            if ImGui.ImageButton(f"enable chesting", project_root + f"\\gui\\textures\\chesting.png", icon_size, icon_size):
                CustomBehaviorParty().set_party_is_chesting_enabled(True)
            ImGui.show_tooltip("enable chesting")
        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(1)

        # Blessing
        PyImGui.table_next_column()
        if shared_data.is_blessing_enabled:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.BLESSING_COLOR)
            if ImGui.ImageButton(f"disable blessing", project_root + f"\\gui\\textures\\blessing.png", icon_size, icon_size):
                CustomBehaviorParty().set_party_is_blessing_enabled(False)
            ImGui.show_tooltip("disable blessing")
        else:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
            if ImGui.ImageButton(f"enable blessing", project_root + f"\\gui\\textures\\blessing.png", icon_size, icon_size):
                CustomBehaviorParty().set_party_is_blessing_enabled(True)
            ImGui.show_tooltip("enable blessing")
        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(1)

        # Inventory
        PyImGui.table_next_column()
        if shared_data.is_inventory_enabled:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.INVENTORY_COLOR)
            if ImGui.ImageButton(f"disable inventory management", project_root + f"\\gui\\textures\\inventory.png", icon_size, icon_size):
                CustomBehaviorParty().set_party_is_inventory_enabled(False)
            ImGui.show_tooltip("disable inventory management")
        else:
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 30, 0, 255)))
            if ImGui.ImageButton(f"enable inventory management", project_root + f"\\gui\\textures\\inventory.png", icon_size, icon_size):
                CustomBehaviorParty().set_party_is_inventory_enabled(True)
            ImGui.show_tooltip("enable inventory management")
        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(1)
        PyImGui.end_table()


    PyImGui.separator()

    # [EXPLORABLE] Feature across party :
    if Map.IsExplorable() or True:
        if True:

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
                    CustomBehaviorParty().set_party_custom_target(Player.GetTargetID())
            else:
                if PyImGui.button(f"{IconsFontAwesome5.ICON_TRASH} ResetPartyCustomTarget | id:{shared_data.party_target_id}"):
                    CustomBehaviorParty().set_party_custom_target(None)

    PyImGui.separator()

    if Map.IsOutpost() or True:
        if True:

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PLANE} Map"):
                    CustomBehaviorParty().schedule_action(PartyCommandConstants.summon_all_to_current_map)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            ImGui.show_tooltip("Ask all other open GW windows to travel to current map.")
            ImGui.show_tooltip(f"----------------------------")

            account_email = Player.GetAccountEmail()
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
            count_in_map = 0
            total_count = 0
            if self_account is not None:
                for account in accounts:
                    if account.AccountEmail == account_email:
                        continue
                    total_count += 1
                    is_in_map = (self_account.AgentData.Map.MapID == account.AgentData.Map.MapID and self_account.AgentData.Map.Region == account.AgentData.Map.Region and self_account.AgentData.Map.District == account.AgentData.Map.District)
                    if is_in_map :
                        ImGui.show_tooltip(f"{account.AgentData.CharacterName} - In the current map")
                        count_in_map+=1
                    else : ImGui.show_tooltip(f"{account.AgentData.CharacterName} - In {Map.GetMapName(account.AgentData.Map.MapID)}")

            ImGui.show_tooltip(f"----------------------------")
            ImGui.show_tooltip(f"{count_in_map}/{total_count} in current map")

            PyImGui.same_line(0, 5)

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PLANE_ARRIVAL} GH"):
                    CustomBehaviorParty().schedule_action(PartyCommandConstants.travel_gh)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            ImGui.show_tooltip("Ask to all other open GW windows to travel to Guild Hall.")
            
            PyImGui.same_line(0, 5)

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PERSON_CIRCLE_PLUS} Join"):
                    CustomBehaviorParty().schedule_action(PartyCommandConstants.invite_all_to_leader_party)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            ImGui.show_tooltip("Ask all other open GW windows to current join sender party.")

            ImGui.show_tooltip(f"--------------Eligibles--------------")

            account_email = Player.GetAccountEmail()
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
            if self_account is not None:
                for account in accounts:
                    if account.AccountEmail == account_email:
                        continue
                    is_in_map = (self_account.AgentData.Map.MapID == account.AgentData.Map.MapID and self_account.AgentData.Map.Region == account.AgentData.Map.Region and self_account.AgentData.Map.District == account.AgentData.Map.District)
                    if is_in_map:
                        ImGui.show_tooltip(f"{account.AgentData.CharacterName} - In the current map")

                ImGui.show_tooltip(f"--------------Not eligible--------------")

                for account in accounts:
                    if account.AccountEmail == account_email:
                        continue
                    is_in_map = (self_account.AgentData.Map.MapID == account.AgentData.Map.MapID and self_account.AgentData.Map.Region == account.AgentData.Map.Region and self_account.AgentData.Map.District == account.AgentData.Map.District)
                    if not is_in_map:
                        ImGui.show_tooltip(f"{account.AgentData.CharacterName} - Not eligible (not in the current map)")

            PyImGui.same_line(0, 5)

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PERSON_CIRCLE_XMARK} Leave"):
                    CustomBehaviorParty().schedule_action(PartyCommandConstants.leave_current_party)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            ImGui.show_tooltip("Ask all other open GW windows to leave their current party.")

            PyImGui.same_line(0, 5)

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PERSON_MILITARY_POINTING} Interract"):
                    CustomBehaviorParty().schedule_action(PartyCommandConstants.interract_with_target)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            ImGui.show_tooltip("Ask all other open GW windows to interact with current target.")

            PyImGui.same_line(0, 5)

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PEN_FANCY} Rename"):
                    CustomBehaviorParty().schedule_action(PartyCommandConstants.rename_gw_windows)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            ImGui.show_tooltip("Rename all GW windows to their character name.")
            
    PyImGui.separator()

    if True:
        if PyImGui.tree_node_ex("[MANAGE] Enforce the main state machine for all party members :", 0):

            ImGui.push_font("Italic", 12)
            PyImGui.text(f"using such force mode manually can be usefull to pre-cast, stop the combat, fallback, ect")
            ImGui.pop_font()

            green_color = Utils.ColorToTuple(Utils.RGBToColor(41, 144, 69, 255))
            light_blue_color = Utils.ColorToTuple(Utils.RGBToColor(100, 150, 255, 150))

            # Get forced state and current actual state
            forced_state = CustomBehaviorParty().get_party_forced_state()
            current_state = None
            if forced_state is None and CustomBehaviorLoader().custom_combat_behavior is not None:
                current_state = CustomBehaviorLoader().custom_combat_behavior.get_state()

            # IN_AGGRO button
            should_highlight = (forced_state == BehaviorState.IN_AGGRO) or (forced_state is None and current_state == BehaviorState.IN_AGGRO)
            if forced_state == BehaviorState.IN_AGGRO:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, green_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, green_color)
            elif forced_state is None and current_state == BehaviorState.IN_AGGRO:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, light_blue_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, light_blue_color)
            if PyImGui.button(f"{IconsFontAwesome5.ICON_FIST_RAISED} IN_AGGRO"):
                CustomBehaviorParty().set_party_forced_state(BehaviorState.IN_AGGRO)
            ImGui.show_tooltip("IN_AGGRO : enemy is combat range")
            if should_highlight:
                PyImGui.pop_style_color(2)

            PyImGui.same_line(0,5)

            # CLOSE_TO_AGGRO button
            should_highlight = (forced_state == BehaviorState.CLOSE_TO_AGGRO) or (forced_state is None and current_state == BehaviorState.CLOSE_TO_AGGRO)
            if forced_state == BehaviorState.CLOSE_TO_AGGRO:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, green_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, green_color)
            elif forced_state is None and current_state == BehaviorState.CLOSE_TO_AGGRO:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, light_blue_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, light_blue_color)
            if PyImGui.button(f"{IconsFontAwesome5.ICON_HAMSA} CLOSE_TO_AGGRO"):
                CustomBehaviorParty().set_party_forced_state(BehaviorState.CLOSE_TO_AGGRO)
            ImGui.show_tooltip("CLOSE_TO_AGGRO : enemy close to combat range")
            if should_highlight:
                PyImGui.pop_style_color(2)

            PyImGui.same_line(0,5)

            # FAR_FROM_AGGRO button
            should_highlight = (forced_state == BehaviorState.FAR_FROM_AGGRO) or (forced_state is None and current_state == BehaviorState.FAR_FROM_AGGRO)
            if forced_state == BehaviorState.FAR_FROM_AGGRO:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, green_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, green_color)
            elif forced_state is None and current_state == BehaviorState.FAR_FROM_AGGRO:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, light_blue_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, light_blue_color)
            if PyImGui.button(f"{IconsFontAwesome5.ICON_HIKING} FAR_FROM_AGGRO"):
                CustomBehaviorParty().set_party_forced_state(BehaviorState.FAR_FROM_AGGRO)
            ImGui.show_tooltip("CLOSE_TO_AGGRO : nothing close to fight")
            if should_highlight:
                PyImGui.pop_style_color(2)

            PyImGui.same_line(0,5)

            # IDLE button
            should_highlight = (forced_state == BehaviorState.IDLE) or (forced_state is None and current_state == BehaviorState.IDLE)
            if forced_state == BehaviorState.IDLE:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, green_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, green_color)
            elif forced_state is None and current_state == BehaviorState.IDLE:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, light_blue_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, light_blue_color)
            if PyImGui.button(f"{IconsFontAwesome5.ICON_HOURGLASS} IDLE"):
                CustomBehaviorParty().set_party_forced_state(BehaviorState.IDLE)
            ImGui.show_tooltip("IDLE : town, dead, loading, ect...")
            if should_highlight:
                PyImGui.pop_style_color(2)

            if forced_state is not None:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, Utils.ColorToTuple(Utils.RGBToColor(200, 30, 30, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, Utils.ColorToTuple(Utils.RGBToColor(240, 10, 0, 255)))
                if PyImGui.button(f"{IconsFontAwesome5.ICON_TIMES}"):
                    CustomBehaviorParty().set_party_forced_state(None)
                ImGui.show_tooltip("Remove forced state")
                PyImGui.pop_style_color(2)

                PyImGui.same_line(0,5)
                PyImGui.text(f"Party forced state is ")
                PyImGui.same_line(0,0)
                PyImGui.text(f"{forced_state}")

            PyImGui.tree_pop()

    PyImGui.separator()

    if PyImGui.tree_node_ex("[FOLLOWING - IN_AGGRO] Define how followers should follow the leader :", PyImGui.TreeNodeFlags.DefaultOpen):

        ImGui.push_font("Italic", 12)
        PyImGui.text(f"customize how followers should follow the leader when IN_AGGRO")
        PyImGui.same_line(0,5)

        # Help button with tooltip
        if PyImGui.small_button("[?]"):
            pass
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            PyImGui.text(f"those button are presets. but you can further customize the forces activation per account in the following panel below.")
            PyImGui.text(f"3 forces are in play : attraction to leader, repulsion from allies, repulsion from enemies")
            PyImGui.text(f"flagging is always prioritized over any other movement")
            PyImGui.text(f"NONE was the existing default behavior.")
            PyImGui.end_tooltip()

        ImGui.pop_font()

        current_behavior = CustomBehaviorParty().get_party_following_behavior()
        light_blue_color = Utils.ColorToTuple(Utils.RGBToColor(100, 150, 255, 150))

        # DONT_SPREAD button
        if current_behavior == FollowingBehaviorPriority.HIGH_PRIORITY:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, light_blue_color)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, light_blue_color)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_ANGLE_DOUBLE_UP} HIGH_PRIORITY"):
            CustomBehaviorParty().set_party_following_behavior_priority(FollowingBehaviorPriority.HIGH_PRIORITY)
        if current_behavior == FollowingBehaviorPriority.HIGH_PRIORITY:
            PyImGui.pop_style_color(2)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("When IN_AGGRO, followers will prioritize movement at all cost.")

            
        PyImGui.same_line(0,5)

        if current_behavior == FollowingBehaviorPriority.HIGH_PRIORITY_WITH_THROTTLE:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, light_blue_color)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, light_blue_color)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_ANGLE_DOUBLE_UP} HIGH_PRIORITY_THROTTLE"):
            CustomBehaviorParty().set_party_following_behavior_priority(FollowingBehaviorPriority.HIGH_PRIORITY_WITH_THROTTLE)
        if current_behavior == FollowingBehaviorPriority.HIGH_PRIORITY_WITH_THROTTLE:
            PyImGui.pop_style_color(2)
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            PyImGui.set_tooltip("When IN_AGGRO, followers will prioritize movement at all cost - but with a few seconds throttle between each movements.")
            PyImGui.end_tooltip()

        PyImGui.same_line(0,5)


        if current_behavior == FollowingBehaviorPriority.LOW_PRIORITY:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, light_blue_color)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, light_blue_color)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_ANGLE_UP} LOW_PRIORITY"):
            CustomBehaviorParty().set_party_following_behavior_priority(FollowingBehaviorPriority.LOW_PRIORITY)
        if current_behavior == FollowingBehaviorPriority.LOW_PRIORITY:
            PyImGui.pop_style_color(2)
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            PyImGui.set_tooltip("When IN_AGGRO, followers will only move if nothing else to do.")
            PyImGui.end_tooltip()

        PyImGui.same_line(0,5)

        PyImGui.same_line(0,5)

        if current_behavior == FollowingBehaviorPriority.NONE:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, light_blue_color)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, light_blue_color)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_ANCHOR} NONE"):
            CustomBehaviorParty().set_party_following_behavior_priority(FollowingBehaviorPriority.NONE)
        if current_behavior == FollowingBehaviorPriority.NONE:
            PyImGui.pop_style_color(2)
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            PyImGui.set_tooltip("When IN_AGGRO, movement is only initiated but your character's skills.")
            PyImGui.end_tooltip()

        FollowingPanel.render_configuration()

        PyImGui.tree_pop()

    PyImGui.separator()

    if PyImGui.tree_node_ex("[FLAGGING] Define party flags :", PyImGui.TreeNodeFlags.DefaultOpen):

        # Set Flags at Leader Position (Preset 0: Grid)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.FLAG_COLOR)
        clicked_p0 = ImGui.ImageButton(f"Set Flags at Leader Position##preset0", project_root + f"\\gui\\textures\\flag.png", icon_size, icon_size)
        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(1)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("PRESET 0 (Custom Grid): Apply custom grid assignments to flag positions based on grid configuration (manual-assign)")

        if clicked_p0:
            FlagCustomGridPlacement.apply_grid_to_flag_manager()

        PyImGui.same_line(0,5)

        # Set Flags at Leader Position (Preset 1: GridBackWard Leader)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.FLAG_COLOR)
        clicked_p1 = ImGui.ImageButton(f"Set Flags at Leader Position##preset1", project_root + f"\\gui\\textures\\flag.png", icon_size, icon_size)
        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(1)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("PRESET 1 (AutoGrid BackWard Leader): Apply auto-grid assignments based on leader's position and facing (auto-assign)")
        if clicked_p1:
            FlagBackwardGridPlacement.apply_backward_grid_to_flag_manager()

        PyImGui.same_line(0,5)

        # Preset 2: Stacked flags at leader position (separate column)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.FLAG_COLOR)
        clicked_p2 = ImGui.ImageButton(f"Set Flags (Stacked)##preset2", project_root + f"\\gui\\textures\\flag.png", icon_size, icon_size)
        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(1)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("PRESET 2 (Stacked): Stack all flags at the leader's position (auto-assign)")
        if clicked_p2:
            FlagStackedPlacement.apply_stacked_to_flag_manager()

        # Clear Flag Positions
        if flag_manager.are_flags_defined():
            PyImGui.same_line(0,5)

            drop_btn_color = (0.8, 0.0, 0.0, 1.0)  # Red color
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, drop_btn_color)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (min(1.0, drop_btn_color[0] + 0.15), min(1.0, drop_btn_color[1] + 0.15), min(1.0, drop_btn_color[2] + 0.15), drop_btn_color[3]))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (max(0.0, drop_btn_color[0] - 0.1), max(0.0, drop_btn_color[1] - 0.1), max(0.0, drop_btn_color[2] - 0.1), drop_btn_color[3]))
            if PyImGui.button(f"{IconsFontAwesome5.ICON_TIMES}##drop_all_flags", 30, 30):
                flag_manager.clear_all_flag_positions()
            PyImGui.pop_style_color(3)
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Remove all flags from map")

        FlagPanel.render_configuration()
        PyImGui.tree_pop()

    PyImGui.separator()

    if custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader():
        
        if PyImGui.tree_node_ex("[TEAM] Management :", 0):

            from Sources.oazix.CustomBehaviors.primitives.hero_ai_wrapping.hero_ai_wrapping import HeroAiWrapping
            hero_ai = HeroAiWrapping()
            heroai_ui_visible = hero_ai.is_heroai_ui_visible()
            new_state = PyImGui.checkbox("Show HeroUI Panels", heroai_ui_visible)
            if new_state != heroai_ui_visible:
                hero_ai.change_heroai_ui_visibility(is_visible=new_state)

            PyImGui.text(f"Default PartyLeader is {GLOBAL_CACHE.Party.GetPartyLeaderID()}")
            PyImGui.text(f"Overriden PartyLeader is {custom_behavior_helpers.CustomBehaviorHelperParty.get_party_leader_id()}")
            if PyImGui.small_button("Reset PartyLeader"):
                CustomBehaviorParty().set_party_leader_email(None)

            # if CustomBehaviorParty.get_party_leader_email() is not None:
            #     PyImGui.text(f"CharacterName {GLOBAL_CACHE.ShMem.GetAccountDataFromEmail()).AgentData.CharacterName}")

            # Table listing all players from shared memory
            account_email = Player.GetAccountEmail()
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)

            if accounts and len(accounts) > 0:
                if PyImGui.begin_table("party_players_table", 5, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg):
                    PyImGui.table_setup_column("Character Name", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_setup_column("PartyID", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_setup_column("Invite", PyImGui.TableColumnFlags.WidthFixed, 80.0)
                    PyImGui.table_headers_row()

                    for account in accounts:

                        character_name = account.AgentData.CharacterName if account.AgentData.CharacterName else "Unknown"

                        # Get profession short names (e.g., "Me/Mo")
                        primary_prof_id = account.AgentData.Profession[0] if account.AgentData.Profession else 0
                        secondary_prof_id = account.AgentData.Profession[1] if account.AgentData.Profession else 0
                        primary_short = ProfessionShort_Names.get(ProfessionShort(primary_prof_id), "?") if primary_prof_id > 0 else "?"
                        secondary_short = ProfessionShort_Names.get(ProfessionShort(secondary_prof_id), "") if secondary_prof_id > 0 else ""
                        class_text = f"{primary_short}/{secondary_short}" if secondary_short else primary_short

                        PyImGui.table_next_row()
                        # Highlight current player's row with light blue background
                        if account.AccountEmail == account_email:
                            light_blue = Utils.RGBToColor(100, 150, 255, 80)
                            PyImGui.table_set_bg_color(2, light_blue, -1)
                        PyImGui.table_next_column()
                        # Show yellow crown icon if this account is the party leader
                        party_leader_email = custom_behavior_helpers_party.CustomBehaviorHelperParty._get_party_leader_email()
                        if party_leader_email and account.AccountEmail == party_leader_email:
                            PyImGui.text_colored(f"{IconsFontAwesome5.ICON_CROWN}", (1.0, 0.85, 0.0, 1.0))  # Yellow crown
                            PyImGui.same_line(0, 5)
                        PyImGui.text(f"[{class_text}] {character_name}")

                        PyImGui.table_next_column()
                        PyImGui.text(f"{account.AgentPartyData.PartyID} / AgentId {account.AgentData.AgentID} / PartyLeader {GLOBAL_CACHE.Party.GetPartyLeaderID()}")

                        PyImGui.table_next_column()
                        if PyImGui.button(f"Focus window##{account.AccountEmail}"):
                            CustomBehaviorParty().schedule_action(lambda email=account.AccountEmail: PartyCommandConstants.focus_window(email))

                        PyImGui.table_next_column()
                        if PyImGui.button(f"Invite##{account.AccountEmail}"):
                            if character_name and character_name != "Unknown":
                                CustomBehaviorParty().schedule_action(lambda email=account.AccountEmail, name=character_name: PartyCommandConstants.invite_player(email, name))

                        PyImGui.table_next_column()
                        if PyImGui.button(f"Promote as leader##{account.AccountEmail}"):
                            CustomBehaviorParty().set_party_leader_email(account.AccountEmail)
                            pass

                    PyImGui.end_table()
            else:
                PyImGui.text("No players in shared memory")

            PyImGui.tree_pop()

    PyImGui.separator()


    for entry in CustomBehaviorParty().get_shared_lock_manager().get_current_locks():
        PyImGui.text(f"entry={entry.key}-{entry.acquired_at_seconds}-{entry.expires_at_seconds}-{entry.lock_type}")

    # Always draw a vertical indicator for the (custom or current) target
    draw_party_target_vertical_line()

    # Draw the flagging overlay last so it appears on top
    FlagPanel.render_overlay()
    FollowingPanel.render_overlay()

