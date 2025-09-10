import os
import pathlib
from Py4GWCoreLib import IconsFontAwesome5, ImGui, PyImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import Utils
from Py4GWCoreLib.enums import SharedCommandType
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology_color import UtilitySkillTypologyColor

script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))
py4gw_root_directory = project_root + f"\\..\\..\\"

@staticmethod
def render():
    constants.DEBUG = PyImGui.checkbox("with debugging logs", constants.DEBUG)

    shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
    if shared_data.is_enabled:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(62, 139, 95, 200)))
        if ImGui.ImageButton(f"disable everything", project_root + f"\\gui\\textures\\all.png", 40, 40):
            CustomBehaviorParty().set_party_is_enabled(False)
        ImGui.show_tooltip("disable everything")
    else:
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 0, 255)))
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
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 0, 255)))
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
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 0, 255)))
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
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 0, 255)))
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
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 0, 255)))
        if ImGui.ImageButton(f"enable chesting", project_root + f"\\gui\\textures\\chesting.png", 40, 40):
            CustomBehaviorParty().set_party_is_chesting_enabled(True)
        ImGui.show_tooltip("enable chesting")
    PyImGui.pop_style_var(1)
    PyImGui.pop_style_color(1)

    PyImGui.separator()

    if shared_data.party_target_id is None:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_CROSSHAIRS} SetPartyCustomTarget"):
            CustomBehaviorParty().set_party_custom_target(GLOBAL_CACHE.Player.GetTargetID())
    else:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_TRASH} ResetPartyCustomTarget"):
            CustomBehaviorParty().set_party_custom_target(None)
        PyImGui.same_line(0, 10)
        PyImGui.text(f"id:{CustomBehaviorParty().get_party_custom_target()}")


    if GLOBAL_CACHE.Map.IsOutpost():
        PyImGui.separator()

        if PyImGui.button(f"{IconsFontAwesome5.ICON_PLANE} SummonToCurrentMap"):
            account_email = GLOBAL_CACHE.Player.GetAccountEmail()
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            for account in accounts:
                if account.AccountEmail == account_email:
                    continue
                print(f"SendMessage {account_email} to {account.AccountEmail}")
                GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.TravelToMap, (self_account.MapID, self_account.MapRegion, self_account.MapDistrict, 0))

    PyImGui.separator()

    PyImGui.text(f"PartyForcedState={CustomBehaviorParty().get_party_forced_state()}")
    if (CustomBehaviorParty().get_party_forced_state() is not None and CustomBehaviorParty().get_party_forced_state().value != BehaviorState.IN_AGGRO.value) or CustomBehaviorParty().get_party_forced_state() is None:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_HAMSA} force to IN_AGGRO"):
            CustomBehaviorParty().set_party_forced_state(BehaviorState.IN_AGGRO)

    if (CustomBehaviorParty().get_party_forced_state() is not None and CustomBehaviorParty().get_party_forced_state().value != BehaviorState.CLOSE_TO_AGGRO.value) or CustomBehaviorParty().get_party_forced_state() is None:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_FEATHER_ALT} force to CLOSE_TO_AGGRO"):
            CustomBehaviorParty().set_party_forced_state(BehaviorState.CLOSE_TO_AGGRO)
            
    if (CustomBehaviorParty().get_party_forced_state() is not None and CustomBehaviorParty().get_party_forced_state().value != BehaviorState.FAR_FROM_AGGRO.value) or CustomBehaviorParty().get_party_forced_state() is None:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_FEATHER_ALT} force to FAR_FROM_AGGRO"):
            CustomBehaviorParty().set_party_forced_state(BehaviorState.FAR_FROM_AGGRO)

    if CustomBehaviorParty().get_party_forced_state() is not None:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_DIZZY} None"):
            CustomBehaviorParty().set_party_forced_state(None)

    PyImGui.separator()
    
    for entry in CustomBehaviorParty().get_shared_lock_manager().get_current_locks():
        PyImGui.text(f"entry={entry.key}-{entry.acquired_at_seconds}-{entry.expires_at_seconds}")


