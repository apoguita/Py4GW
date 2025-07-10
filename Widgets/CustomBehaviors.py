
import sys
from Py4GWCoreLib.Py4GWcorelib import Utils
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

# Iterate through all modules in sys.modules (already imported modules)
# Iterate over all imported modules and reload them
for module_name in list(sys.modules.keys()):
    if module_name not in ("sys", "importlib", "cache_data"):
        try:
            if "behavior" in module_name.lower():
                print(f"Reloading module: {module_name}")
                del sys.modules[module_name]
                # importlib.reload(module_name)
                pass
        except Exception as e:
            print(f"Error reloading module {module_name}: {e}")

from typing import List
from HeroAI.cache_data import CacheData
from Py4GWCoreLib import ImGui, PyImGui, Routines, ActionQueueManager, Player, GLOBAL_CACHE, IconsFontAwesome5, SharedCommandType
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader, MatchResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.gui.current_build import render as current_build_render
from Widgets.CustomBehaviors.gui.party import render as party
from Widgets.CustomBehaviors.gui.skillbars import render as all_templates_render
from Widgets.CustomBehaviors.gui.deamon import deamon as deamon

party_forced_state_combo = 0
DEBUG = True

def gui():
    # PyImGui.set_next_window_size(260, 650)
    # PyImGui.set_next_window_size(460, 800)

    global party_forced_state_combo
    PyImGui.begin("Custom behaviors", PyImGui.WindowFlags.AlwaysAutoResize)
    shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()

    PyImGui.begin_tab_bar("current_build")

    if PyImGui.begin_tab_item("party"):
        party()
        PyImGui.end_tab_item()

    if PyImGui.begin_tab_item("current_build"):
        current_build_render()
        PyImGui.end_tab_item()

    if PyImGui.begin_tab_item("debug_templates"):
        all_templates_render()
        PyImGui.end_tab_item()

    PyImGui.end_tab_bar()

    PyImGui.end()
    return

    # if DEBUG:
    #     PyImGui.text(f"is_enabled {shared_data.is_enabled}")
    #     PyImGui.text(f"party_target_id {shared_data.party_target_id}")
    #     PyImGui.text(f"party_forced_state {shared_data.party_forced_state}")
    #     PyImGui.text(f"party_forced_state {BehaviorState(shared_data.party_forced_state) if shared_data.party_forced_state is not None else None}")
    #     PyImGui.separator()

    PyImGui.text(f"{IconsFontAwesome5.ICON_USERS} CROSS ACCOUNT ACTIONS")
    if shared_data.is_enabled:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_TIMES} Disable all"):
            CustomBehaviorParty().set_party_is_enable(False)
    else:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_CHECK} Enable all"):
            CustomBehaviorParty().set_party_is_enable(True)

    # PyImGui.same_line(0, 10)

    if shared_data.party_target_id is None:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_CROSSHAIRS} SetPartyCustomTarget"):
            CustomBehaviorParty().set_party_custom_target(GLOBAL_CACHE.Player.GetTargetID())
    else:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_TRASH} ResetPartyCustomTarget"):
            CustomBehaviorParty().set_party_custom_target(None)
        PyImGui.same_line(0, 10)
        PyImGui.text(f"id:{CustomBehaviorParty().get_party_custom_target()}")


    if GLOBAL_CACHE.Map.IsOutpost():
        if PyImGui.button(f"{IconsFontAwesome5.ICON_PLANE} SummonToCurrentMap"):
            account_email = GLOBAL_CACHE.Player.GetAccountEmail()
            self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            for account in accounts:
                if account.AccountEmail == account_email:
                    continue
                print(f"SendMessage {account_email} to {account.AccountEmail}")
                GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.TravelToMap, (self_account.MapID, self_account.MapRegion, self_account.MapDistrict, 0))
        # PyImGui.same_line(0, 10)

    if PyImGui.button(f"{IconsFontAwesome5.ICON_ARROW_ALT_CIRCLE_RIGHT} TakeDialogWithTarget"):
        account_email = GLOBAL_CACHE.Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        for account in accounts:
            if account.AccountEmail == account_email:
                continue

            print(f"SendMessage {account_email} to {account.AccountEmail}")
            target_id = GLOBAL_CACHE.Player.GetTargetID()
            GLOBAL_CACHE.ShMem.SendMessage(account_email, account.AccountEmail, SharedCommandType.TakeDialogWithTarget, (target_id, ))

        # messaging stuff
        pass

    # items: list[str] = ["None"] + [state.name for state in BehaviorState]
    # party_forced_state_combo = PyImGui.combo("", party_forced_state_combo , items)
    # PyImGui.text(f"State : {items[party_forced_state_combo]} | {CustomBehaviorParty().get_party_forced_state()}")
    # # PyImGui.same_line(0, 10)
    # if PyImGui.button("Apply"):
    #     if items[party_forced_state_combo] == "None":
    #         CustomBehaviorParty().set_party_forced_state(None)
    #     else:
    #         state_string = items[party_forced_state_combo]
    #         state:BehaviorState = BehaviorState[state_string]
    #         CustomBehaviorParty().set_party_forced_state(state)
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

    PyImGui.text(f"{IconsFontAwesome5.ICON_USER_ALT} CURRENT ACCOUNT ACTIONS")
    if DEBUG:
        PyImGui.text(f"PlayerId : {Player.GetAgentID()}")
        # PyImGui.same_line(0, 10)
    PyImGui.text(f"HasLoaded : {CustomBehaviorLoader()._has_loaded}")
    # PyImGui.same_line(0, 10)
    PyImGui.text(f"Selected behavior : {CustomBehaviorLoader().custom_combat_behavior.__class__.__name__}")
    if CustomBehaviorLoader().custom_combat_behavior is not None:
        PyImGui.text(f"Account state:{CustomBehaviorLoader().custom_combat_behavior.get_state()}")
        PyImGui.text(f"Final state:{CustomBehaviorLoader().custom_combat_behavior.get_final_state()}")
    

        if CustomBehaviorLoader().custom_combat_behavior.get_is_enabled():
            if PyImGui.button(f"{IconsFontAwesome5.ICON_TIMES} Disable"):
                CustomBehaviorLoader().custom_combat_behavior.disable()
        else:
            if PyImGui.button(f"{IconsFontAwesome5.ICON_CHECK} Enable"):
                CustomBehaviorLoader().custom_combat_behavior.enable()
        pass

    PyImGui.end()

def main():

    if not Routines.Checks.Map.MapValid():
        return

    gui()
    deamon()
    

def configure():
    # gui()
    pass

__all__ = ["main", "configure"]
