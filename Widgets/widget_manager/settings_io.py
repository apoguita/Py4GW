from Py4GWCoreLib import *
from .handler import handler
from . import state

def write_settings_to_ini():
    if not state.write_timer.HasElapsed(1000):
        return

    # if state.use_account_settings:
    #     # save_account_settings()
    # else:
    #     # save_global_settings()
    
    state.write_timer.Reset()

def restore_global_defaults():
    from .default_settings import global_widget_defaults
    import configparser

    parser = configparser.ConfigParser()

    for section, settings in global_widget_defaults.items():
        parser.add_section(section)
        for key, value in settings.items():
            parser.set(section, key, str(value))

    with open(handler.global_ini_path, "w") as f:
        parser.write(f)

    handler._last_global_values.clear()

def save_all_settings(to_account: bool = False):
    # Always save this to account scope, regardless of flag
    handler._write_account_setting("WidgetManager", "use_account_settings", str(state.use_account_settings))

    wm_keys = {
        "enable_all": state.enable_all,
        "old_menu": state.old_menu,
    }

    for k, v in wm_keys.items():
        handler._write_setting("WidgetManager", k, f"{v}", to_account=to_account, force=True)

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
        handler._write_setting("QuickDock", k, f"{v}", to_account=to_account, force=True)

    for i, key in enumerate(("r", "g", "b", "a")):
        handler._write_setting("QuickDockColor", key, f"{state.quick_dock_color[i]}", to_account=to_account, force=True)

    for name, widget in handler.widgets.items():
        data = handler.widget_data_cache.get(name, {})
        entries = {
            "enabled": widget.get("enabled", False),
            "category": data.get("category", "Miscellaneous"),
            "subcategory": data.get("subcategory", "Others"),
            "icon": data.get("icon", "ICON_CIRCLE"),
            "quickdock": data.get("quickdock", False)
        }
        for k, v in entries.items():
            handler._write_setting(name, k, str(v), to_account=to_account, force=True)

# def save_account_settings():
#     wm_keys = {
#         "enable_all": state.enable_all,
#         "old_menu": state.old_menu,
#         "use_account_settings": str(state.use_account_settings),
#     }
#     for k, v in wm_keys.items():
#         handler._write_account_setting("WidgetManager", k, f"{v}")

#     dock_keys = {
#         "enable_quick_dock": state.enable_quick_dock,
#         "width": state.quick_dock_width,
#         "height": state.quick_dock_height,
#         "offset_y": state.quick_dock_offset_y,
#         "edge": state.quick_dock_edge[0],
#         "unlocked": state.quick_dock_unlocked,
#         "buttons_per_row": state.buttons_per_row
#     }
#     for k, v in dock_keys.items():
#         handler._write_account_setting("QuickDock", k, f"{v}")

#     for i, key in enumerate(("r", "g", "b", "a")):
#         handler._write_account_setting("QuickDockColor", key, f"{state.quick_dock_color[i]}")

#     for name, widget in handler.widgets.items():
#         data = handler.widget_data_cache.get(name, {})
#         for k, v in {
#             "enabled": widget.get("enabled", False),
#             "category": data.get("category", "Miscellaneous"),
#             "subcategory": data.get("subcategory", "Others"),
#             "icon": data.get("icon", "ICON_CIRCLE"),
#             "quickdock": data.get("quickdock", False)
#         }.items():
#             handler._write_setting(name, k, str(v), to_account=True, force=True)

# def save_global_settings():
#     wm_keys = {
#         "enable_all": state.enable_all,
#         "old_menu": state.old_menu,
#     }
#     for k, v in wm_keys.items():
#         handler._write_global_setting("WidgetManager", k, f"{v}")

#     dock_keys = {
#         "enable_quick_dock": state.enable_quick_dock,
#         "width": state.quick_dock_width,
#         "height": state.quick_dock_height,
#         "offset_y": state.quick_dock_offset_y,
#         "edge": state.quick_dock_edge[0],
#         "unlocked": state.quick_dock_unlocked,
#         "buttons_per_row": state.buttons_per_row
#     }
#     for k, v in dock_keys.items():
#         handler._write_global_setting("QuickDock", k, f"{v}")

#     for i, key in enumerate(("r", "g", "b", "a")):
#         handler._write_global_setting("QuickDockColor", key, f"{state.quick_dock_color[i]}")

#     for name, widget in handler.widgets.items():
#         data = handler.widget_data_cache.get(name, {})
#         handler._write_global_setting(name, "enabled", f"{widget.get('enabled', False)}")
#         handler._write_global_setting(name, "quickdock", str(data.get("quickdock", False)))

def initialize_settings():
    if state.selected_settings_scope == 1:
        load_account_settings()
    else:
        load_global_settings()

def load_account_settings():
    state.enable_all = handler._read_setting_bool("WidgetManager", "enable_all", False, force_account=True)
    state.old_menu = handler._read_setting_bool("WidgetManager", "old_menu", True, force_account=True)
    state.use_account_settings = handler._read_setting_bool("WidgetManager", "use_account_settings", True, force_account=True)

    state.old_menu_window_pos = (
        handler._read_setting_int("WidgetManager", "omx", 100, force_account=True),
        handler._read_setting_int("WidgetManager", "omy", 100, force_account=True),
    )
    state.old_menu_window_collapsed = handler._read_setting_bool("WidgetManager", "collapsed", False, force_account=True)

    state.enable_quick_dock = handler._read_setting_bool("QuickDock", "enable_quick_dock", True, force_account=True)
    state.quick_dock_width = handler._read_setting_int("QuickDock", "width", 10, force_account=True)
    state.quick_dock_height = handler._read_setting_int("QuickDock", "height", 50, force_account=True)
    state.quick_dock_offset_y = handler._read_setting_int("QuickDock", "offset_y", 0, force_account=True)
    state.quick_dock_edge[0] = handler._read_setting("QuickDock", "edge", "left", force_account=True)
    state.quick_dock_unlocked = handler._read_setting_bool("QuickDock", "unlocked", False, force_account=True)
    state.buttons_per_row = handler._read_setting_int("QuickDock", "buttons_per_row", 8, force_account=True)

    state.quick_dock_color = [
        handler._read_setting_float("QuickDockColor", "r", 0.6, force_account=True),
        handler._read_setting_float("QuickDockColor", "g", 0.8, force_account=True),
        handler._read_setting_float("QuickDockColor", "b", 1.0, force_account=True),
        handler._read_setting_float("QuickDockColor", "a", 1.0, force_account=True)
    ]
    
def load_global_settings():
    state.enable_all = handler._read_setting_bool("WidgetManager", "enable_all", False, force_global=True)
    state.old_menu = handler._read_setting_bool("WidgetManager", "old_menu", True, force_global=True)
    state.use_account_settings = handler._read_setting_bool("WidgetManager", "use_account_settings", True, force_global=True)

    state.old_menu_window_pos = (
        handler._read_setting_int("WidgetManager", "omx", 100, force_global=True),
        handler._read_setting_int("WidgetManager", "omx", 100, force_global=True),
    )
    state.old_menu_window_collapsed = handler._read_setting_bool("WidgetManager", "collapsed", False, force_global=True)

    state.enable_quick_dock = handler._read_setting_bool("QuickDock", "enable_quick_dock", True, force_global=True)
    state.quick_dock_width = handler._read_setting_int("QuickDock", "width", 10, force_global=True)
    state.quick_dock_height = handler._read_setting_int("QuickDock", "height", 50, force_global=True)
    state.quick_dock_offset_y = handler._read_setting_int("QuickDock", "offset_y", 0, force_global=True)
    state.quick_dock_edge[0] = handler._read_setting("QuickDock", "edge", "left", force_global=True)
    state.quick_dock_unlocked = handler._read_setting_bool("QuickDock", "unlocked", False, force_global=True)
    state.buttons_per_row = handler._read_setting_int("QuickDock", "buttons_per_row", 8, force_global=True)

    state.quick_dock_color = [
        handler._read_setting_float("QuickDockColor", "r", 0.6, force_global=True),
        handler._read_setting_float("QuickDockColor", "g", 0.8, force_global=True),
        handler._read_setting_float("QuickDockColor", "b", 1.0, force_global=True),
        handler._read_setting_float("QuickDockColor", "a", 1.0, force_global=True)
    ]