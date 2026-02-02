from Py4GWCoreLib import Py4GW, Map, Party, ConsoleLog, UIManager
import traceback
import sys

from . import state
from .handler import handler
from .ui_floating_menu import draw_floating_menu
from .settings_io import initialize_settings
from .config_scope import is_in_character_select, character_select

account_init = True
checked = False
def main():
    global account_init, run_once, checked, character_select
    
    try:
        is_loaded = Party.IsPartyLoaded()
        is_loading = Map.IsMapLoading()

        if not state.initialized:
            state.initialized = True
            handler.discover_widgets()

        if not is_loaded and is_loading and not checked:
            character_select = is_in_character_select()
            checked = True

        if is_loaded and not is_loading and checked:
            character_select = is_in_character_select()
            checked = False 

        if account_init and is_loaded and not is_loading:
            account_init = False
            ConsoleLog("WidgetHandler", "Initialize Account Settings", Py4GW.Console.MessageType.Info)
            handler._initialize_account_settings()
            handler._initialize_account_config()
            initialize_settings()

        if state.enable_all:
            handler.execute_enabled_widgets()
            handler.execute_configuring_widgets()

        draw_floating_menu()

    except Exception as e:
        err_type = type(e).__name__
        Py4GW.Console.Log(state.module_name, f"{err_type} encountered: {e}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(state.module_name, traceback.format_exc(), Py4GW.Console.MessageType.Error)

def get_widget_handler():
    return sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"].handler  # type: ignore[attr-defined]