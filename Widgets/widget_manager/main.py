from Py4GWCoreLib import Py4GW, Map, Party
import traceback
import sys

from . import state
from .handler import handler
from .ui_floating_menu import draw_floating_menu
from .ui_embedded_config import draw_embedded_widget_config
from .ui_quickdock import quick_dock_menu
from .ui_old_menu import draw_old_widget_ui
from .settings_io import initialize_settings
from .config_scope import is_in_character_select

account_init = False

def main():
    global account_init
    try:
        in_char_select = is_in_character_select()
        
        if not state.initialized:
            handler.discover_widgets()
            state.initialized = True

        if (not account_init and
            not in_char_select and 
            not Map.IsMapLoading() and
            Party.IsPartyLoaded()):
            handler._initialize_account_settings()
            handler._initialize_account_config()
            initialize_settings()
            account_init = True

        if state.old_menu:
            draw_old_widget_ui()


        if state.enable_quick_dock:
            quick_dock_menu()
        
        draw_floating_menu()
             
        draw_embedded_widget_config()
        
        if state.enable_all:
            handler.execute_enabled_widgets()
            handler.execute_configuring_widgets()

    except Exception as e:
        err_type = type(e).__name__
        Py4GW.Console.Log(state.module_name, f"{err_type} encountered: {e}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(state.module_name, traceback.format_exc(), Py4GW.Console.MessageType.Error)

def get_widget_handler():
    return sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"].handler  # type: ignore[attr-defined]