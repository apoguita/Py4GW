from Py4GWCoreLib import ImGui, PyImGui
from .handler import handler

module_name = "WidgetManager"

# Global widget configuration
enable_all = handler._read_setting_bool("WidgetManager", "enable_all", False)
old_enable_all = enable_all
old_menu = handler._read_setting_bool("WidgetManager", "old_menu", False)
initialized = False
settings_scope_options = ["Global.ini", "Account.ini"]

show_config_window = False

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
quick_dock_hovering_button = False
cached_quickdock_widgets = []
last_quickdock_cache_id = None
last_written_quick_dock_edge = None
last_written_offset_y = None

# Ui Elements
selected_widget = ""
show_hidden_widgets = False
scroll_pos = 0.0

# Floating menu popup state
popup_open = False
popup_height_known = False
popup_height = 220
opening_downward = True
left_side = False
show_quick_dock_popup = False
last_popup_size = [200.0, 100.0]
floating_attachment_index = handler._read_setting_int("FloatingMenu", "floating_attachment_index", 0)
floating_attachment_options = ["Menu Button", "District Selector", "Skill Bar", "Free Move"]
floating_drag_locked = handler._read_setting_bool("FloatingMenu", "floating_drag_locked", True)
is_dragging_floating_button = False
floating_button_offset = (0, 0)
hovering_floating_button = False
focused_floating_button = False
floating_menu_pos = (20.0, 100.0)
floating_district_pos = (20.0, 100.0)
floating_skill_pos = (20.0, 100.0)
fmx = handler._read_setting_int("FloatingMenu", "fmx", 100)
fmy = handler._read_setting_int("FloatingMenu", "fmy", 100)
floating_window_pos = (fmx, fmy)
floating_write_pending = False
floating_write_timer = 0
reopen_floating_menu = False
floating_custom_colors_enabled = handler._read_setting_bool("FloatingMenu", "use_custom_colors", False)
floating_custom_colors = {
    "base": (
        handler._read_setting_float("FloatingMenu", "base_r", 0.10),
        handler._read_setting_float("FloatingMenu", "base_g", 0.10),
        handler._read_setting_float("FloatingMenu", "base_b", 0.10),
        handler._read_setting_float("FloatingMenu", "base_a", 1.00)
    ),
    "hover": (
        handler._read_setting_float("FloatingMenu", "hover_r", 0.15),
        handler._read_setting_float("FloatingMenu", "hover_g", 0.15),
        handler._read_setting_float("FloatingMenu", "hover_b", 0.15),
        handler._read_setting_float("FloatingMenu", "hover_a", 1.00)
    ),
    "active": (
        handler._read_setting_float("FloatingMenu", "active_r", 0.05),
        handler._read_setting_float("FloatingMenu", "active_g", 0.05),
        handler._read_setting_float("FloatingMenu", "active_b", 0.05),
        handler._read_setting_float("FloatingMenu", "active_a", 1.00)
    ),
    "border": (
        handler._read_setting_float("FloatingMenu", "border_r", 0.30),
        handler._read_setting_float("FloatingMenu", "border_g", 0.30),
        handler._read_setting_float("FloatingMenu", "border_b", 0.30),
        handler._read_setting_float("FloatingMenu", "border_a", 1.00)
    )
}

# Menu window and layout state
window_module = ImGui.WindowModule(module_name, window_name="Widgets", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
window_x = handler._read_setting_int(module_name, "omx", 100)
window_y = handler._read_setting_int(module_name, "omy", 100)
window_module.window_pos = (window_x, window_y)
window_module.collapse = handler._read_setting_bool(module_name, "collapsed", True)
old_menu_window_collapsed = window_module.collapse
old_menu_window_pos = window_module.window_pos
    