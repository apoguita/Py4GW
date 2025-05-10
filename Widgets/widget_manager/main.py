from Py4GWCoreLib import *
import traceback
import sys

from . import state
from .handler import handler
from .ui_floating_menu import draw_floating_menu
from .ui_quickdock import quick_dock_menu
from .ui_old_menu import draw_widget_ui
from .settings_io import write_ini

def main():
    try:
        if not state.initialized:
            handler.discover_widgets()
            state.initialized = True

        if state.window_module.first_run:
            PyImGui.set_next_window_size(*state.window_module.window_size)
            PyImGui.set_next_window_pos(*state.window_module.window_pos)
            PyImGui.set_next_window_collapsed(state.window_module.collapse, 0)
            state.window_module.first_run = False

        state.current_window_collapsed = True
        state.old_enable_all = state.enable_all

        if state.old_menu:
            if PyImGui.begin(state.window_module.window_name, state.window_module.window_flags):
                state.current_window_pos = PyImGui.get_window_pos()
                state.current_window_collapsed = False
                draw_widget_ui()
            PyImGui.end()

        if state.enable_quick_dock:
            quick_dock_menu()
        
        if (not handler.account_initialized and 
            not Map.IsMapLoading() and 
            not Map.IsInCinematic() and 
            not Player.InCharacterSelectScreen() and 
            Party.IsPartyLoaded()):
            handler._initialize_account_settings()
            handler._initialize_account_config()
        
        if Player.InCharacterSelectScreen():
            handler.account_initialized = False
            
        draw_floating_menu()
        write_ini()

        if state.enable_all:
            handler.execute_enabled_widgets()
            handler.execute_configuring_widgets()

    except Exception as e:
        err_type = type(e).__name__
        Py4GW.Console.Log(state.module_name, f"{err_type} encountered: {e}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(state.module_name, traceback.format_exc(), Py4GW.Console.MessageType.Error)

def get_widget_handler():
    return sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"].handler  # type: ignore[attr-defined]