from Py4GWCoreLib import *
from .handler import handler

module_name = "WidgetManager"

# Global widget configuration
enable_all = handler._read_setting_bool("WidgetManager", "enable_all", False)
old_enable_all = enable_all
show_config_window = handler._read_setting_bool("WidgetManager", "show_config_window", False)
old_menu = handler._read_setting_bool("WidgetManager", "old_menu", False)

# QuickDock persistent config
enable_quick_dock = handler._read_setting_bool("QuickDock", "enable_quick_dock", True)
quick_dock_width = handler._read_setting_int("QuickDock", "width", 10)
quick_dock_height = handler._read_setting_int("QuickDock", "height", 50)
quick_dock_offset_y = handler._read_setting_int("QuickDock", "offset_y", 100)
quick_dock_edge = [handler._read_setting("QuickDock", "edge", "right")]
quick_dock_unlocked = handler._read_setting_bool("QuickDock", "unlocked", False)
buttons_per_row = handler._read_setting_int("QuickDock", "buttons_per_row", 8)
quick_dock_color = [
    handler._read_setting_float("QuickDockColor", "r", 0.6),
    handler._read_setting_float("QuickDockColor", "g", 0.8),
    handler._read_setting_float("QuickDockColor", "b", 1.0),
    handler._read_setting_float("QuickDockColor", "a", 1.0),
]

# Ui Elements
selected_widget = ""
show_hidden_widgets = False

# Floating menu popup state
popup_open = False
popup_height_known = False
popup_height = 220
opening_downward = True
left_side = False
show_quick_dock_popup = False
last_popup_size = [200.0, 100.0]

# ImGui window and layout state
initialized = False
window_module = ImGui.WindowModule(module_name, window_name="Widgets", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
window_x = handler._read_setting_int(module_name, "x", 100)
window_y = handler._read_setting_int(module_name, "y", 100)
window_module.window_pos = (window_x, window_y)
window_module.collapse = handler._read_setting_bool(module_name, "collapsed", True)
current_window_collapsed = window_module.collapse

# Write throttle
write_timer = Timer()
write_timer.Start()
current_window_pos = window_module.window_pos

