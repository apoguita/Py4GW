import os
import pathlib
from Py4GWCoreLib import IconsFontAwesome5, ImGui, PyImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import Utils
from Py4GWCoreLib.enums import SharedCommandType
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.parties.party_commands import PartyCommands
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology_color import UtilitySkillTypologyColor

script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))
py4gw_root_directory = project_root + f"\\..\\..\\"

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
                    CustomBehaviorParty().schedule_action(PartyCommands.resign)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            PyImGui.same_line(0,5)

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PERSON_MILITARY_POINTING} Interract with target"):
                    CustomBehaviorParty().schedule_action(PartyCommands.interract_with_target)
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
                    CustomBehaviorParty().schedule_action(PartyCommands.summon_all_to_current_map)
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
                    CustomBehaviorParty().schedule_action(PartyCommands.invite_all_to_leader_party)
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
                    CustomBehaviorParty().schedule_action(PartyCommands.leave_current_party)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            ImGui.show_tooltip("Ask all other open GW windows to leave their current party.")

            PyImGui.same_line(0, 5)

            if CustomBehaviorParty().is_ready_for_action():
                if PyImGui.button(f"{IconsFontAwesome5.ICON_PERSON_MILITARY_POINTING} Interract with target"):
                    CustomBehaviorParty().schedule_action(PartyCommands.interract_with_target)
            else:
                if PyImGui.button(f"waiting..."):
                    pass
            
            PyImGui.tree_pop()

        # PyImGui.separator()

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

    # PyImGui.separator()

    constants.DEBUG = PyImGui.checkbox("with debugging logs", constants.DEBUG)

    PyImGui.separator()
    
    for entry in CustomBehaviorParty().get_shared_lock_manager().get_current_locks():
        PyImGui.text(f"entry={entry.key}-{entry.acquired_at_seconds}-{entry.expires_at_seconds}")



    


