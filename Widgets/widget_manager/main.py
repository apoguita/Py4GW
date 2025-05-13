from Py4GWCoreLib import *
import traceback
import sys

from . import state
from .handler import handler
from .ui_floating_menu import draw_floating_menu
from .ui_embedded_config import draw_embedded_widget_config
from .ui_quickdock import quick_dock_menu
from .ui_old_menu import draw_old_widget_ui
from .settings_io import initialize_settings

def main():
    try:
        # sort_frame = UIManager.IsWindowVisible(UIManager.GetChildFrameID(2232987037,[0]))
        # menu_frame = UIManager.IsWindowVisible(UIManager.GetFrameIDByHash(1144678641))
        
        # if ((sort_frame and menu_frame) or ((Map.GetDescriptionID() == 39684 and Map.GetMapID() == 514) or Map.IsInCinematic())):
        #     return
        
        if not state.initialized:
            handler.discover_widgets()
            state.initialized = True

        if (not handler.account_initialized and
            not Player.InCharacterSelectScreen() and
            Party.IsPartyLoaded()):
            handler._initialize_account_settings()
            handler._initialize_account_config()
            initialize_settings()

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