from Py4GWCoreLib import IconsFontAwesome5, PyImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.enums import SharedCommandType
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager


@staticmethod
def render():
    shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
    
    if shared_data.is_enabled:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_TIMES} Disable all"):
            CustomBehaviorParty().set_party_is_enable(False)
    else:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_CHECK} Enable all"):
            CustomBehaviorParty().set_party_is_enable(True)

    PyImGui.separator()

    if shared_data.party_target_id is None:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_CROSSHAIRS} SetPartyCustomTarget"):
            CustomBehaviorParty().set_party_custom_target(GLOBAL_CACHE.Player.GetTargetID())
    else:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_TRASH} ResetPartyCustomTarget"):
            CustomBehaviorParty().set_party_custom_target(None)
        PyImGui.same_line(0, 10)
        PyImGui.text(f"id:{CustomBehaviorParty().get_party_custom_target()}")

    PyImGui.separator()

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
