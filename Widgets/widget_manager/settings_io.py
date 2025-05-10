from Py4GWCoreLib import *
from .handler import handler
from . import state

def write_ini():
    if not state.write_timer.HasElapsed(1000):
        return

    if state.current_window_pos != state.window_module.window_pos:
        x, y = map(int, state.current_window_pos)
        state.window_module.window_pos = (x, y)
        handler._write_global_setting(state.module_name, "x", f"{x}")
        handler._write_global_setting(state.module_name, "y", f"{y}")

    if state.current_window_collapsed != state.window_module.collapse:
        state.window_module.collapse = state.current_window_collapsed
        handler._write_global_setting(state.module_name, "collapsed", f"{state.current_window_collapsed}")

    if state.old_enable_all != state.enable_all:
        state.enable_all = state.old_enable_all
        handler._write_global_setting("WidgetManager", "enable_all", str(state.enable_all))

    settings = {
        "enable_all": state.enable_all,
        "show_config_window": state.show_config_window,
        "old_menu": state.old_menu
    }
    for k, v in settings.items():
        handler._write_global_setting("WidgetManager", k, f"{v}")

    dock_settings = {
        "width": state.quick_dock_width,
        "height": state.quick_dock_height,
        "offset_y": state.quick_dock_offset_y,
        "edge": state.quick_dock_edge[0],
        "unlocked": state.quick_dock_unlocked,
        "buttons_per_row": state.buttons_per_row
    }
    for k, v in dock_settings.items():
        handler._write_global_setting("QuickDock", k, f"{v}")

    for i, key in enumerate(("r", "g", "b", "a")):
        handler._write_global_setting("QuickDockColor", key, f"{state.quick_dock_color[i]}")

    state.write_timer.Reset()

def save_account_settings():
    wm_keys = {
        "show_config_window": state.show_config_window,
        "old_menu": state.old_menu,
        "enable_all": state.enable_all
    }
    for k, v in wm_keys.items():
        handler._write_account_setting("WidgetManager", k, f"{v}")

    dock_keys = {
        "enable_quick_dock": state.enable_quick_dock,
        "width": state.quick_dock_width,
        "height": state.quick_dock_height,
        "offset_y": state.quick_dock_offset_y,
        "edge": state.quick_dock_edge[0],
        "unlocked": state.quick_dock_unlocked,
        "buttons_per_row": state.buttons_per_row
    }
    for k, v in dock_keys.items():
        handler._write_account_setting("QuickDock", k, f"{v}")

    for i, key in enumerate(("r", "g", "b", "a")):
        handler._write_account_setting("QuickDockColor", key, f"{state.quick_dock_color[i]}")

    for name, widget in handler.widgets.items():
        data = handler.widget_data_cache.get(name, {})
        handler._write_account_setting(name, "enabled", f"{widget.get('enabled', False)}")
        handler._write_account_setting(name, "category", data.get("category", "Miscellaneous"))
        handler._write_account_setting(name, "subcategory", data.get("subcategory", "Others"))
        handler._write_account_setting(name, "quickdock", str(data.get("quickdock", False)))

    ConsoleLog(state.module_name, "Saved current settings to account INI", Py4GW.Console.MessageType.Info)


def save_global_settings():
    wm_keys = {
        "show_config_window": state.show_config_window,
        "old_menu": state.old_menu,
        "enable_all": state.enable_all
    }
    for k, v in wm_keys.items():
        handler._write_global_setting("WidgetManager", k, f"{v}")

    dock_keys = {
        "enable_quick_dock": state.enable_quick_dock,
        "width": state.quick_dock_width,
        "height": state.quick_dock_height,
        "offset_y": state.quick_dock_offset_y,
        "edge": state.quick_dock_edge[0],
        "unlocked": state.quick_dock_unlocked,
        "buttons_per_row": state.buttons_per_row
    }
    for k, v in dock_keys.items():
        handler._write_global_setting("QuickDock", k, f"{v}")

    for i, key in enumerate(("r", "g", "b", "a")):
        handler._write_global_setting("QuickDockColor", key, f"{state.quick_dock_color[i]}")

    for name, widget in handler.widgets.items():
        data = handler.widget_data_cache.get(name, {})
        handler._write_global_setting(name, "enabled", f"{widget.get('enabled', False)}")
        handler._write_global_setting(name, "category", data.get("category", "Miscellaneous"))
        handler._write_global_setting(name, "subcategory", data.get("subcategory", "Others"))

    ConsoleLog(state.module_name, "Saved current settings to global INI", Py4GW.Console.MessageType.Info)


