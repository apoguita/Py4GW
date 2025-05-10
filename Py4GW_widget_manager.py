from Py4GWCoreLib import *
import importlib.util
import os
import types
import sys
import configparser

class WidgetHandler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls is not WidgetHandler:
            raise TypeError("Cannot subclass WidgetHandler")
        return cls._instance or super().__new__(cls)

    def __init__(self, widgets_path="Widgets"):
        if getattr(self, "_initialized", False):
            return

        module_file = getattr(sys.modules.get(__name__), "__file__", None)
        base_dir = os.path.dirname(os.path.abspath(module_file)) if module_file else os.getcwd()
        resolved_path = widgets_path or os.path.join(base_dir, "Widgets")
        self.widgets_path = os.path.abspath(resolved_path)
        
        self.widgets = {}
        self.widget_data_cache = {}
        self.last_write_time = Timer()
        self.last_write_time.Start()
        self.base_path = os.path.join(os.getcwd(), "widgets", "config")
        self.global_ini_path = os.path.join(self.base_path, "global_widget_config.ini")
        
        os.makedirs(self.base_path, exist_ok=True)
        if not os.path.exists(self.global_ini_path):
            open(self.global_ini_path, 'w').close()
            
        self.account_email = Player.GetAccountEmail() or "unknown"
        self.account_path = os.path.join(self.base_path, "account_config", self.account_email)
        self.account_ini_path = os.path.join(self.account_path, "widgets_meta.ini")
        self.account_initialized = False
        
        os.makedirs(self.account_path, exist_ok=True)
        if not os.path.exists(self.account_ini_path):
            open(self.account_ini_path, 'w').close()

        self._load_widget_cache()
        self._last_global_values = {}
        self._last_account_values = {}
        self._initialized = True
        
    def initialize_account_settings(self):
        email = Player.GetAccountEmail()
        if not email or email == "unknown":
            return
        if getattr(self, "_last_initialized_email", None) == email:
            return

        self.account_email = email
        self.account_path = os.path.join(self.base_path, "account_config", email)
        self.account_ini_path = os.path.join(self.account_path, "widgets_meta.ini")

        os.makedirs(self.account_path, exist_ok=True)
        open(self.account_ini_path, "a").close()

        self._last_initialized_email = email
        self.write_account_setting("WidgetManager", "enable_all", "False")
        self.account_initialized = True
    
    def _write_to_ini(self, path, section, key, value):
        parser = configparser.ConfigParser()
        parser.read(path)

        if not parser.has_section(section):
            parser.add_section(section)

        parser.set(section, key, f"{value}")
        with open(path, "w") as f:
            parser.write(f)
    
    def _read_from_ini(self, path, section, key, default=None):
        parser = configparser.ConfigParser()
        parser.read(path)

        if parser.has_section(section) and parser.has_option(section, key):
            return parser.get(section, key)

        return default
    
    def _read_setting(self, section, key, default=None):
        parser = configparser.ConfigParser()

        for path in (self.account_ini_path, self.global_ini_path):
            if path and os.path.exists(path):
                parser.read(path)
                if parser.has_section(section) and parser.has_option(section, key):
                    return parser.get(section, key)

        return default

    def read_setting_bool(self, section, key, default=False):
        val = self._read_setting(section, key, f"{default}")
        return val and val.lower() == "true"

    def read_setting_int(self, section, key, default=0):
        val = self._read_setting(section, key, default)
        if val is None:
            return default
        try:
            return int(val)
        except Exception:
            return default

    def read_setting_float(self, section, key, default=0.0):
        val = self._read_setting(section, key, default)
        if val is None:
            return default
        try:
            return float(val)
        except Exception:
            return default
    
    def read_global_setting(self, section, key, default=None):
        return self._read_from_ini(self.global_ini_path, section, key, default)

    def write_global_setting(self, section, key, value):
        if self._last_global_values.get((section, key)) == value:
            return
        self._write_to_ini(self.global_ini_path, section, key, value)
        self._last_global_values[(section, key)] = value

    def read_account_setting(self, section, key, default=None):
        return self._read_from_ini(self.account_ini_path, section, key, default)

    def write_account_setting(self, section, key, value):
        if self._last_account_values.get((section, key)) == value:
            return
        self._write_to_ini(self.account_ini_path, section, key, value)
        self._last_account_values[(section, key)] = value
    
    def _load_widget_cache(self):
        path = self.account_ini_path if self.account_email != "unknown" else self.global_ini_path
        parser = configparser.ConfigParser()
        parser.read(path)

        for section in parser.sections():
            if section in self.widget_data_cache:
                continue
            get = lambda k, d: parser.get(section, k, fallback=d)
            self.widget_data_cache[section] = {
                "category": get("category", "Miscellaneous"),
                "subcategory": get("subcategory", "General"),
                "enabled": get("enabled", "True").lower() == "true",
                "icon": get("icon", "ICON_CIRCLE"),
                "quickdock": get("quickdock", "False").lower() == "true",
            }

    def save_widget_state(self, widget_name):
        widget = self.widgets.get(widget_name)
        if not widget:
            return

        data = self.widget_data_cache.get(widget_name, {})
        enabled = widget.get("enabled", False)
        category = data.get("category", "")
        subcategory = data.get("subcategory", "")
        icon = data.get("icon", "ICON_CIRCLE")
        quickdock = data.get("quickdock", False)

        for writer in (self.write_account_setting, self.write_global_setting):
            writer(widget_name, "enabled", str(enabled))
            writer(widget_name, "category", category)
            writer(widget_name, "subcategory", subcategory)
            writer(widget_name, "icon", icon)
            writer(widget_name, "quickdock", str(quickdock))
            
        

    def _load_all_from_dir(self):
        if not os.path.isdir(self.widgets_path):
            raise FileNotFoundError(f"Missing widget directory: {self.widgets_path}")

        py_files = [f for f in os.listdir(self.widgets_path) if f.endswith(".py")]

        for file in py_files:
            name = os.path.splitext(file)[0]
            path = os.path.join(self.widgets_path, file)
            try:
                module = self.load_widget(path)
                enabled = self.widget_data_cache.get(name, {}).get("enabled", True)
                self.widgets[name] = {"module": module, "enabled": enabled, "configuring": False}
                ConsoleLog("WidgetHandler", f"Loaded widget: {name}", Py4GW.Console.MessageType.Info)
            except Exception as e:
                ConsoleLog("WidgetHandler", f"Failed to load widget {name}: {e}", Py4GW.Console.MessageType.Error)
                ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

    def discover_widgets(self):
        try:
            self.widget_data_cache.clear()
            self._load_widget_cache()
            self._load_all_from_dir()
        except Exception as e:
            ConsoleLog("WidgetHandler", f"Widget discovery failed: {e}", Py4GW.Console.MessageType.Error)
            ConsoleLog("WidgetHandler", traceback.format_exc(), Py4GW.Console.MessageType.Error)

    def load_widget(self, path):
        spec = importlib.util.spec_from_file_location("widget", path)
        if not spec or not spec.loader:
            raise ValueError(f"Invalid spec from {path}")

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except ImportError as e:
            raise ImportError(f"Widget import failed: {e}")
        except Exception as e:
            raise Exception(f"Widget execution failed: {e}")

        if not all(hasattr(module, attr) for attr in ("main", "configure")):
            raise ValueError("Widget missing required functions: main() and configure()")

        return module
        
    def execute_enabled_widgets(self):
        for name, info in self.widgets.items():
            if not info["enabled"]:
                continue
            try:
                info["module"].main()
            except Exception as e:
                ConsoleLog("WidgetHandler", f"Execution failed: {name} - {e}", Py4GW.Console.MessageType.Error)
                ConsoleLog("WidgetHandler", traceback.format_exc(), Py4GW.Console.MessageType.Error)

    def execute_configuring_widgets(self):
        for name, info in self.widgets.items():
            if not info["configuring"]:
                continue
            try:
                info["module"].configure()
            except Exception as e:
                ConsoleLog("WidgetHandler", f"Configure failed: {name} - {e}", Py4GW.Console.MessageType.Error)
                ConsoleLog("WidgetHandler", traceback.format_exc(), Py4GW.Console.MessageType.Error)
                
    def enable_widget(self, name: str):
        self._set_widget_state(name, True)

    def disable_widget(self, name: str):
        self._set_widget_state(name, False)

    def _set_widget_state(self, name: str, state: bool):
        widget = self.widgets.get(name)
        if not widget:
            ConsoleLog("WidgetHandler", f"Unknown widget: {name}", Py4GW.Console.MessageType.Warning)
            return

        widget["enabled"] = state
        self.save_widget_state(name)

    def is_widget_enabled(self, name: str) -> bool:
        return bool(self.widgets.get(name, {}).get("enabled"))

    def list_enabled_widgets(self) -> list[str]:
        return [name for name, w in self.widgets.items() if w.get("enabled")]

module_name = "WidgetManager"

# Singleton WidgetHandler setup
if "_Py4GW_GLOBAL_WIDGET_HANDLER" not in sys.modules:
    mod = types.ModuleType("_Py4GW_GLOBAL_WIDGET_HANDLER")  # actual module type
    mod.handler = WidgetHandler()  # type: ignore[attr-defined]
    sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"] = mod
handler = sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"].handler

# Global widget configuration
enable_all = handler.read_setting_bool("WidgetManager", "enable_all", False)
old_enable_all = enable_all
show_config_window = handler.read_setting_bool("WidgetManager", "show_config_window", False)
old_menu = handler.read_setting_bool("WidgetManager", "old_menu", False)

# QuickDock persistent config
enable_quick_dock = handler.read_setting_bool("QuickDock", "enable_quick_dock", True)
quick_dock_width = handler.read_setting_int("QuickDock", "width", 10)
quick_dock_height = handler.read_setting_int("QuickDock", "height", 50)
quick_dock_offset_y = handler.read_setting_int("QuickDock", "offset_y", 100)
quick_dock_edge = [handler._read_setting("QuickDock", "edge", "right")]
quick_dock_unlocked = handler.read_setting_bool("QuickDock", "unlocked", False)
buttons_per_row = handler.read_setting_int("QuickDock", "buttons_per_row", 8)
quick_dock_color = [
    handler.read_setting_float("QuickDockColor", "r", 0.6),
    handler.read_setting_float("QuickDockColor", "g", 0.8),
    handler.read_setting_float("QuickDockColor", "b", 1.0),
    handler.read_setting_float("QuickDockColor", "a", 1.0),
]

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
window_x = handler.read_setting_int(module_name, "x", 100)
window_y = handler.read_setting_int(module_name, "y", 100)
window_module.window_pos = (window_x, window_y)
window_module.collapse = handler.read_setting_bool(module_name, "collapsed", True)
current_window_collapsed = window_module.collapse

# Write throttle
write_timer = Timer()
write_timer.Start()
current_window_pos = window_module.window_pos

def write_ini():
    if not write_timer.HasElapsed(1000):
        return

    global enable_all

    if current_window_pos != window_module.window_pos:
        x, y = map(int, current_window_pos)
        window_module.window_pos = (x, y)
        handler.write_global_setting(module_name, "x", f"{x}")
        handler.write_global_setting(module_name, "y", f"{y}")

    if current_window_collapsed != window_module.collapse:
        window_module.collapse = current_window_collapsed
        handler.write_global_setting(module_name, "collapsed", f"{current_window_collapsed}")

    if old_enable_all != enable_all:
        enable_all = old_enable_all
        handler.write_global_setting("WidgetManager", "enable_all", str(enable_all))

    settings = {
        "enable_all": enable_all,
        "show_config_window": show_config_window,
        "old_menu": old_menu
    }
    for k, v in settings.items():
        handler.write_global_setting("WidgetManager", k, f"{v}")

    dock_settings = {
        "width": quick_dock_width,
        "height": quick_dock_height,
        "offset_y": quick_dock_offset_y,
        "edge": quick_dock_edge[0],
        "unlocked": quick_dock_unlocked,
        "buttons_per_row": buttons_per_row
    }
    for k, v in dock_settings.items():
        handler.write_global_setting("QuickDock", k, f"{v}")

    for i, key in enumerate(("r", "g", "b", "a")):
        handler.write_global_setting("QuickDockColor", key, f"{quick_dock_color[i]}")

    write_timer.Reset()

def save_account_settings():
    wm_keys = {
        "show_config_window": show_config_window,
        "old_menu": old_menu,
        "enable_all": enable_all
    }
    for k, v in wm_keys.items():
        handler.write_account_setting("WidgetManager", k, f"{v}")

    dock_keys = {
        "enable_quick_dock": enable_quick_dock,
        "width": quick_dock_width,
        "height": quick_dock_height,
        "offset_y": quick_dock_offset_y,
        "edge": quick_dock_edge[0],
        "unlocked": quick_dock_unlocked,
        "buttons_per_row": buttons_per_row
    }
    for k, v in dock_keys.items():
        handler.write_account_setting("QuickDock", k, f"{v}")

    for i, key in enumerate(("r", "g", "b", "a")):
        handler.write_account_setting("QuickDockColor", key, f"{quick_dock_color[i]}")

    for name, widget in handler.widgets.items():
        data = handler.widget_data_cache.get(name, {})
        handler.write_account_setting(name, "enabled", f"{widget.get('enabled', False)}")
        handler.write_account_setting(name, "category", data.get("category", "Miscellaneous"))
        handler.write_account_setting(name, "subcategory", data.get("subcategory", "Others"))
        handler.write_account_setting(name, "quickdock", str(data.get("quickdock", False)))

    ConsoleLog(module_name, "Saved current settings to account INI", Py4GW.Console.MessageType.Info)

def save_global_settings():
    wm_keys = {
        "show_config_window": show_config_window,
        "old_menu": old_menu,
        "enable_all": enable_all
    }
    for k, v in wm_keys.items():
        handler.write_global_setting("WidgetManager", k, f"{v}")

    dock_keys = {
        "enable_quick_dock": enable_quick_dock,
        "width": quick_dock_width,
        "height": quick_dock_height,
        "offset_y": quick_dock_offset_y,
        "edge": quick_dock_edge[0],
        "unlocked": quick_dock_unlocked,
        "buttons_per_row": buttons_per_row
    }
    for k, v in dock_keys.items():
        handler.write_global_setting("QuickDock", k, f"{v}")

    for i, key in enumerate(("r", "g", "b", "a")):
        handler.write_global_setting("QuickDockColor", key, f"{quick_dock_color[i]}")

    for name, widget in handler.widgets.items():
        data = handler.widget_data_cache.get(name, {})
        handler.write_global_setting(name, "enabled", f"{widget.get('enabled', False)}")
        handler.write_global_setting(name, "category", data.get("category", "Miscellaneous"))
        handler.write_global_setting(name, "subcategory", data.get("subcategory", "Others"))

    ConsoleLog(module_name, "Saved current settings to global INI", Py4GW.Console.MessageType.Info)


def draw_embedded_menu():
    global popup_open, popup_height_known, popup_height, opening_downward, left_side, enable_all
    draw_embedded_widget_config()
    chara_select = Player.InCharacterSelectScreen()
    ingame_frame_id = UIManager.GetFrameIDByHash(1144678641)
    login_frame_id = UIManager.GetChildFrameID(2232987037,[0])

    fullscreen_frame_id = UIManager.GetFrameIDByHash(140452905)
    left, top, right, bottom = UIManager.GetFrameCoords(fullscreen_frame_id)
    screen_w = right - left
    screen_h = bottom - top

    content_frame_id = ingame_frame_id
    
    if chara_select:
        content_frame_id = login_frame_id
    
    frame_left, frame_top, frame_right, frame_bottom = UIManager.GetFrameCoords(content_frame_id) 

    if chara_select:
        button_x = frame_right - 8
        button_y = frame_top - 5
        base     = (0.20, 0.25, 0.32, 1.0)
        hover    = (0.30, 0.35, 0.42, 1.0)
        active   = (0.15, 0.18, 0.24, 1.0)
        border   = (0.50, 0.55, 0.60, 1.0)
    elif UIManager.IsWindowVisible(ingame_frame_id):
        button_x = 20
        button_y = 20
        base   = (0.08, 0.08, 0.08, 1.0)
        hover  = (0.16, 0.16, 0.16, 1.0)
        active = (0.05, 0.05, 0.05, 1.0)
        border = (0.25, 0.25, 0.25, 1.0)
    else:
        button_x = frame_right - 12
        button_y = frame_top - 11
        base     = (0.40, 0.36, 0.33, 1.0)
        hover    = (0.48, 0.44, 0.40, 1.0)
        active   = (0.28, 0.26, 0.23, 1.0)
        border   = (0.85, 0.82, 0.78, 1.0)
    
    window_flags = (PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.AlwaysAutoResize | 
                    PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoMove | 
                    PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoBackground)
    
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        base)
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hover)
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  active)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Border,        border)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 1.0)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameRounding, 3.0)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 1.0, 1.0, 1.0))

    flip_widgets = ((button_x - 80) > screen_w / 2)
    if flip_widgets:
        button_x = frame_left - 90
        left_side = True
    else:
        left_side = False

    PyImGui.set_next_window_pos(button_x, button_y)
    PyImGui.set_next_window_size(100, 0)
    
    if PyImGui.begin("##floating_button", window_flags):
        button_x, button_y = PyImGui.get_window_pos()
        menu_y = button_y + 35 
        menu_x = button_x + 12 

        if popup_open and popup_height_known:
            window_y = button_y
            window_center_y = window_y + 35 / 2
            if window_center_y < screen_h / 2:
                menu_y = button_y + 45  # open downward
                opening_downward = True
            else:
                menu_y = button_y - popup_height # open upward
                opening_downward = False
                
        
        icon = IconsFontAwesome5.ICON_CIRCLE if popup_open else IconsFontAwesome5.ICON_DOT_CIRCLE
            
        if left_side:
            button_label = f"Widgets {icon}##WigetUIButton"
        else:
            button_label = f"{icon} Widgets##WigetUIButton"
        
        if PyImGui.button(button_label, 0, 0):
                PyImGui.open_popup("FloatingMenu")
                popup_open = True
        PyImGui.set_next_window_pos(menu_x, menu_y)
        PyImGui.pop_style_color(5)
        PyImGui.pop_style_var(2)
        
        if PyImGui.begin_popup("FloatingMenu"):
            popup_height = PyImGui.get_window_height()
            popup_height_known = True
            if PyImGui.button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets"):
                ConsoleLog(module_name, "Reloading Widgets...", Py4GW.Console.MessageType.Info)
                initialized = False
                handler.discover_widgets()
                initialized = True
            ImGui.show_tooltip("Reloads all widgets")
            PyImGui.same_line(0.0, 10)
            is_enabled = enable_all
            toggle_label = IconsFontAwesome5.ICON_TOGGLE_ON if enable_all else IconsFontAwesome5.ICON_TOGGLE_OFF
            if is_enabled:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.153, 0.318, 0.929, 1.0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.6, 0.6, 0.9, 1.0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.6, 0.6, 0.6, 1.0))
            if PyImGui.button(toggle_label + "##widget_disable"):
                enable_all = not enable_all
                handler.write_global_setting(module_name, "enable_all", str(enable_all))
            if is_enabled:
                PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Toggle all widgets")
            PyImGui.separator()
            draw_widget_popup_menus()
            PyImGui.end_popup()
        else:
            popup_open = False

    PyImGui.end()
        
def draw_widget_popup_menus():
    categorized_widgets = {}
    for name, info in handler.widgets.items():
        data = handler.widget_data_cache.get(name, {})
        cat = data.get("category", "Miscellaneous")
        sub = data.get("subcategory") or "General"
        categorized_widgets.setdefault(cat, {}).setdefault(sub, []).append(name)

    sub_color = Utils.RGBToNormal(255, 200, 100, 255)
    cat_color = Utils.RGBToNormal(200, 255, 150, 255)

    for cat, subs in categorized_widgets.items():
        if PyImGui.begin_menu(cat):
            for sub, names in subs.items():
                if PyImGui.begin_menu(sub):
                    if not PyImGui.begin_table(f"Widgets_{cat}_{sub}", 2, PyImGui.TableFlags.Borders):
                        PyImGui.end_menu()
                        continue

                    for name in names:
                        info = handler.widgets[name]
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        new_enabled = PyImGui.checkbox(name, info["enabled"])
                        if new_enabled != info["enabled"]:
                            info["enabled"] = new_enabled
                            handler.save_widget_state(name)

                        PyImGui.table_set_column_index(1)
                        if info["enabled"]:
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, cat_color)
                        info["configuring"] = ImGui.toggle_button(IconsFontAwesome5.ICON_COG + f"##Configure{name}", info["configuring"])
                        if info["enabled"]:
                            PyImGui.pop_style_color(1)

                    PyImGui.end_table()
                    PyImGui.end_menu()  # close sub
            PyImGui.end_menu()  # close cat

def draw_embedded_widget_config():
    global show_config_window, old_menu
    
    interface_frame_id = UIManager.GetChildFrameID(1431953425, [1,4294967291])
    options_inner_frame_id = UIManager.GetChildFrameID(1431953425, [1])

    options_inner_left, options_inner_top, options_inner_right, options_inner_bottom = UIManager.GetFrameCoords(options_inner_frame_id) 
    width = options_inner_right - options_inner_left
    height = options_inner_bottom - options_inner_top 
    
    interface_tab_left, interface_tab_top, interface_tab_right, interface_tab_bottom = UIManager.GetFrameCoords(interface_frame_id) 
    button_x = interface_tab_right - 12
    button_y = interface_tab_top - 11
    
    ui_size = UIManager.GetEnumPreference(EnumPreference.InterfaceSize)
    ui_button_size = {
        4294967295: (70, 18),   # Small
        0: (78, 19),   # Medium
        1: (86, 22),   # Large
        2: (94, 24),   # Largest
    }
    ui_button_size_offsets = {
        4294967295: (5, 5),   # Small
        0: (5, 8),   # Normal
        1: (5, 8),   # Large
        2: (5, 10),  # Largest
    }
    ui_offsets = {
        4294967295: (22, 24),  # Small
        0: (25, 25),  # Normal
        1: (29, 29),  # Large
        2: (33, 33),  # Largest
    }
    
    button_flags = (PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.AlwaysAutoResize | 
                    PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoMove | 
                    PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoBackground)
    embedded_window_flags = (PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.AlwaysAutoResize | 
                    PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoMove | 
                    PyImGui.WindowFlags.NoScrollbar)

    label = "Widgets"

    if not UIManager.IsWindowVisible(interface_frame_id):
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.10, 0.10, 0.10, 0.0))        # transparent base
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.25, 0.25, 0.25, 1.0)) # light on hover
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.15, 0.15, 0.15, 1.0))  # darker when clicked
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 1.0, 1.0, 1.0))            # pure white
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameRounding, 4.0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FramePadding , 0)
        x_off, y_off = ui_button_size_offsets.get(ui_size, (5, 6))
        PyImGui.set_next_window_pos(button_x + x_off, button_y + y_off)
        if PyImGui.begin("##floating_config_button", button_flags):
            button_w, button_h = ui_button_size.get(ui_size, (78, 20))
            if PyImGui.button(label, button_w, button_h):
                show_config_window = not show_config_window
        PyImGui.end()
        PyImGui.pop_style_color(4)
        PyImGui.pop_style_var(2)

    if show_config_window:
        if not UIManager.IsWindowVisible(interface_frame_id):
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,4.0)
            # PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg , (0.0, 0.0, 0.0, 1.0))
            PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0.05, 0.05, 0.05, 1.0))
            top_offset, height_offset = ui_offsets.get(ui_size, (25, 23))
            PyImGui.set_next_window_pos(options_inner_left, options_inner_top + top_offset)
            PyImGui.set_next_window_size(width, height - height_offset)
            if PyImGui.begin("##widget_config_content",show_config_window, embedded_window_flags):
                #config options go here
                PyImGui.spacing()
                PyImGui.text_colored("Widget Configuration", (1.0, 0.94, 0.75, 1.0))
                PyImGui.spacing()

                draw_quick_dock_config()
                
                PyImGui.spacing()
                PyImGui.separator()
                PyImGui.spacing()
                
                draw_account_widget_config()
                
                PyImGui.spacing()
                PyImGui.separator()
                PyImGui.spacing()
                
                PyImGui.text("Previous Widget UI Settings")
                PyImGui.spacing()    
                is_old_menu = old_menu
                old_menu = PyImGui.checkbox("Disable Old Floating Menu" if is_old_menu else "Enable Old Floating Menu", old_menu)
                ImGui.show_tooltip("Disable Old Floating Menu" if is_old_menu else "Enable Old Floating Menu")
                
            PyImGui.end()
            PyImGui.pop_style_var(1)
            PyImGui.pop_style_color(1)
        else:
            show_config_window = False

def quick_dock_menu():
    global quick_dock_height, quick_dock_width, quick_dock_color, show_quick_dock_popup, quick_dock_unlocked, quick_dock_offset_y, quick_dock_edge, buttons_per_row, last_popup_size

    fullscreen_frame_id = UIManager.GetFrameIDByHash(140452905)
    left, top, right, bottom = UIManager.GetFrameCoords(fullscreen_frame_id)

    mouse_x, mouse_y = Overlay().GetMouseCoords()
    edge_threshold = 30

    if quick_dock_unlocked and PyImGui.is_mouse_dragging(0, -1.0):
        if mouse_y < top + edge_threshold:
            quick_dock_edge[0] = "top"
        elif mouse_y > bottom - edge_threshold:
            quick_dock_edge[0] = "bottom"
        elif mouse_x < left + edge_threshold:
            quick_dock_edge[0] = "left"
        elif mouse_x > right - edge_threshold:
            quick_dock_edge[0] = "right"

    if quick_dock_edge[0] == "left":
        quick_dock_x = left - 10
        quick_dock_y = max(top + 5, min(bottom - quick_dock_height - 5, quick_dock_offset_y))
    elif quick_dock_edge[0] == "right":
        quick_dock_x = right - quick_dock_width - 10
        quick_dock_y = max(top + 5, min(bottom - quick_dock_height - 5, quick_dock_offset_y))
    elif quick_dock_edge[0] == "top":
        quick_dock_x = max(left + 5, min(right - quick_dock_width - 5, quick_dock_offset_y))
        quick_dock_y = top - 10
    elif quick_dock_edge[0] == "bottom":
        quick_dock_x = max(left + 5, min(right - quick_dock_width - 5, quick_dock_offset_y))
        quick_dock_y = bottom - 20
    else:
        quick_dock_x = right - quick_dock_width - 5
        quick_dock_y = quick_dock_offset_y

    if quick_dock_edge[0] in ("top", "bottom"):
        quick_dock_w = quick_dock_height
        quick_dock_h = quick_dock_width
    else:
        quick_dock_w = quick_dock_width
        quick_dock_h = quick_dock_height

    PyImGui.set_next_window_pos(quick_dock_x, quick_dock_y)
    PyImGui.set_next_window_size(quick_dock_w, quick_dock_h)

    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (quick_dock_color[0], quick_dock_color[1], quick_dock_color[2], quick_dock_color[3]))
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameRounding, 0.0)

    if PyImGui.begin("##quick_dock_toggle", PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoBackground):
        if PyImGui.button("##toggle_ribbon", quick_dock_w, quick_dock_h):
            show_quick_dock_popup = not show_quick_dock_popup
        # PyImGui.show_tooltip("Middle Click to Lock" if quick_dock_unlocked else "Middle Click to Unlock")
        if PyImGui.is_item_hovered() and PyImGui.is_mouse_clicked(2):
            quick_dock_unlocked = not quick_dock_unlocked
        
        
        if quick_dock_unlocked and PyImGui.is_item_active():
            if quick_dock_edge[0] in ("left", "right"):
                quick_dock_offset_y = max(top, min(bottom - quick_dock_height, mouse_y - quick_dock_height // 2))
            else:
                quick_dock_offset_y = max(left, min(right - quick_dock_width, mouse_x - quick_dock_width // 2))
        PyImGui.end()

    PyImGui.pop_style_color(1)
    PyImGui.pop_style_var(1)

    if show_quick_dock_popup:
        popup_w, popup_h = last_popup_size
        if quick_dock_edge[0] == "right":
            panel_x = quick_dock_x - popup_w + 12
            panel_y = max(top + 5, min(bottom - popup_h - 5, quick_dock_y))
        elif quick_dock_edge[0] == "left":
            panel_x = quick_dock_x + quick_dock_w + 12
            panel_y = max(top + 5, min(bottom - popup_h - 5, quick_dock_y))
        elif quick_dock_edge[0] == "top":
            panel_x = max(left + 5, min(right - popup_w - 5, quick_dock_x))
            panel_y = quick_dock_y + quick_dock_h + 12
        elif quick_dock_edge[0] == "bottom":
            panel_x = max(left + 5, min(right - popup_w - 5, quick_dock_x))
            panel_y = quick_dock_y - popup_h + 12
        else:
            panel_x = quick_dock_x + quick_dock_w
            panel_y = quick_dock_y

        PyImGui.set_next_window_pos(panel_x, panel_y)

        button_flags = (
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.AlwaysAutoResize |
            PyImGui.WindowFlags.NoMove |
            PyImGui.WindowFlags.NoScrollbar
        )

        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FramePadding, 0.0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.ItemSpacing, 0.0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowPadding, 0.0)

        if PyImGui.begin("##quick_dock_expanded", button_flags):
            last_popup_size[0], last_popup_size[1] = PyImGui.get_window_size()

            dockable_widgets = [
                (name, data)
                for name, data in handler.widget_data_cache.items()
                if data.get("quickdock", False)
            ]
            button_size = (32, 32)
            for i, (name, data) in enumerate(dockable_widgets):
                icon_name = data.get("icon", "ICON_CIRCLE")
                icon = getattr(IconsFontAwesome5, icon_name, "?")
                widget = handler.widgets.get(name)
                if not widget:
                    continue

                enabled = widget.get("enabled", False)
                label = f"{icon}##dock_toggle_{name}"

                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.Button,
                    (0.2, 0.6, 0.3, 1.0) if enabled else (0.3, 0.3, 0.3, 1.0)
                )

                if PyImGui.button(label, *button_size):
                    widget["enabled"] = not enabled
                    handler.save_widget_state(name)

                if PyImGui.is_item_hovered():
                    PyImGui.begin_tooltip()
                    PyImGui.text(f"{name} [{'Enabled' if enabled else 'Disabled'}]")
                    PyImGui.end_tooltip()

                    if PyImGui.is_mouse_clicked(2):  # Middle click
                        widget["configuring"] = True

                PyImGui.pop_style_color(1)

                if (i + 1) % buttons_per_row != 0:
                    PyImGui.same_line(0, 5)

        PyImGui.end()
        PyImGui.pop_style_var(3)

selected_widget = None
def draw_account_widget_config():
    PyImGui.text("Widget Settings")
    PyImGui.spacing()     
    save_label = "Save to Account Settings"
    save_width = PyImGui.calc_text_size(save_label)[0] + 20
    center = (PyImGui.get_content_region_avail()[0] - save_width) * 0.5
    PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x() + center)
    if PyImGui.button(save_label, save_width, 0):
        save_account_settings()
    PyImGui.same_line(0,-1)
    save_label = "Save to Global Settings"
    if PyImGui.button(save_label, save_width, 0):
        save_global_settings()
    
    global selected_widget
    widget_names = list(handler.widgets.keys())
    selected_index = widget_names.index(selected_widget) if selected_widget in widget_names else 0
    label = "Select Widget:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    selected_index = PyImGui.combo("##selwidg", selected_index, widget_names)
    selected_widget = widget_names[selected_index]

    info = handler.widgets[selected_widget]
    data = handler.widget_data_cache.get(selected_widget, {})
    enabled = info.get("enabled", False)
    category = data.get("category", "Miscellaneous")
    subcategory = data.get("subcategory", "General")
    icon = data.get("icon", "ICON_CIRCLE")

    PyImGui.spacing()
    updated_enabled = PyImGui.checkbox("Enabled", enabled)
    if updated_enabled != enabled:
        info["enabled"] = updated_enabled
        handler.save_widget_state(selected_widget)

    PyImGui.spacing()
    label = "Widget Category:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    new_category = PyImGui.input_text("##cat", category, 100)

    PyImGui.spacing()
    label = "Widget Subcategory:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    new_sub = PyImGui.input_text("##subcat", subcategory, 100)

    PyImGui.spacing()
    icon_names = [name for name in dir(IconsFontAwesome5) if name.startswith("ICON_")]
    current_index = icon_names.index(icon) if icon in icon_names else 0
    label = "Widget Icon:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    new_index = PyImGui.combo("##icon_combo", current_index, icon_names)
    icon_value = getattr(IconsFontAwesome5, icon_names[current_index], "?")
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text("Widget Icon Preview:")
    PyImGui.same_line(0, -1)
    PyImGui.set_cursor_pos(x + 160, y)
    PyImGui.text(f"{icon_value}")
    

    if new_index != current_index:
        data["icon"] = icon_names[new_index]
        handler.save_widget_state(selected_widget)

    if new_category != category or new_sub != subcategory:
        data["category"] = new_category
        data["subcategory"] = new_sub
        handler.save_widget_state(selected_widget)
        
def draw_quick_dock_config():
    global quick_dock_height, quick_dock_width, quick_dock_color, quick_dock_unlocked, buttons_per_row, enable_quick_dock
    #config options go here        
    PyImGui.text("Quick Dock Settings")
    PyImGui.spacing()
    check_label = "Quick Dock Enabled" if enable_quick_dock else "Quick Dock Disabled"
    check_width = PyImGui.calc_text_size(check_label)[0] + 20  # Add padding
    available_width = PyImGui.get_content_region_avail()[0]
    center_pos = (available_width - check_width) * 0.5
    PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x() + center_pos)
    enable_quick_dock = PyImGui.checkbox("Quick Dock Enabled" if enable_quick_dock else "Quick Dock Disabled", enable_quick_dock)
    ImGui.show_tooltip("Enable or Disbale the Widget Dock on the edge of the screen")
    PyImGui.spacing()
    label = "Quick Dock Color:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.set_cursor_pos(x + 160, y)
    full_width = PyImGui.get_content_region_avail()[0]
    slider_width = full_width
    PyImGui.set_next_item_width(slider_width)
    new_color = PyImGui.color_edit4("##rcolor", (quick_dock_color[0], quick_dock_color[1], quick_dock_color[2], quick_dock_color[3]))
    if list(new_color) != quick_dock_color:
        quick_dock_color[:] = new_color
    PyImGui.spacing()   
    label = "Quick Dock Width:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0,-1)
    PyImGui.set_cursor_pos(x + 160, y)
    full_width = PyImGui.get_content_region_avail()[0]
    slider_width = full_width
    PyImGui.set_next_item_width(slider_width)
    quick_dock_width = PyImGui.slider_int("##rwidth", quick_dock_width, 4, 50)
    PyImGui.spacing()   
    label = "Quick Dock Height:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0,-1)
    PyImGui.set_cursor_pos(x + 160, y)
    full_width = PyImGui.get_content_region_avail()[0]
    slider_width = full_width
    PyImGui.set_next_item_width(slider_width)
    quick_dock_height = PyImGui.slider_int("##rheight", quick_dock_height, 20, 150)
    PyImGui.spacing()   
    label = "Buttons Per Row:"
    x, y = PyImGui.get_cursor_pos()
    PyImGui.set_cursor_pos(x, y + 5)
    PyImGui.text(label)
    PyImGui.same_line(0,-1)
    PyImGui.set_cursor_pos(x + 160, y)
    full_width = PyImGui.get_content_region_avail()[0]
    slider_width = full_width
    PyImGui.set_next_item_width(slider_width)
    buttons_per_row = PyImGui.slider_int("##bpr", buttons_per_row, 1, 16)
    PyImGui.spacing()   
    quick_dock_unlocked = PyImGui.checkbox("Lock Quick Dock location" if quick_dock_unlocked else "Unlock Quick Dock location", quick_dock_unlocked)
    ImGui.show_tooltip("You can also Unlock and Lock it by Middle-Clicking the Quick Dock")
    PyImGui.spacing()   
    button_label = "Reset Quick Dock Settings"
    button_width = PyImGui.calc_text_size(button_label)[0] + 20  # Add padding
    available_width = PyImGui.get_content_region_avail()[0]
    center_pos = (available_width - button_width) * 0.5
    PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x() + center_pos)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.0, 0.2, 0.4, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.2, 0.4, 0.6, 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.1, 0.3, 0.5, 1.0))
    if PyImGui.button(button_label, button_width, 0):
        quick_dock_color = [0.6, 0.8, 1.0, 1.0]
        buttons_per_row = 8
        quick_dock_width = 10
        quick_dock_height = 50
    PyImGui.pop_style_color(3)
    
    PyImGui.spacing()
    PyImGui.text("Per-Widget QuickDock Settings")
    PyImGui.spacing()

    if PyImGui.begin_child("QuickDockWidgetList", (0.0, 150.0), True, 0):
        for idx, (name, widget) in enumerate(handler.widgets.items()):
            data = handler.widget_data_cache.get(name, {})
            dock_enabled = data.get("quickdock", False)
            icon_name = data.get("icon", "ICON_CIRCLE")
            icon_char = getattr(IconsFontAwesome5, icon_name, "?")

            PyImGui.text(f"{icon_char} {name}")
            PyImGui.same_line(300, -1)

            new_dock_enabled = PyImGui.checkbox(f"##dock_{idx}", dock_enabled)
            if new_dock_enabled != dock_enabled:
                data["quickdock"] = new_dock_enabled
                handler.save_widget_state(name)
        PyImGui.end_child()

def draw_widget_contents_old():
    categorized_widgets = {}
    for name, info in handler.widgets.items():
        data = handler.widget_data_cache.get(name, {})
        cat = data.get("category", "Miscellaneous")
        sub = data.get("subcategory", "")
        categorized_widgets.setdefault(cat, {}).setdefault(sub, []).append(name)

    sub_color = Utils.RGBToNormal(255, 200, 100, 255)
    cat_color = Utils.RGBToNormal(200, 255, 150, 255)

    for cat, subs in categorized_widgets.items():
        if not PyImGui.collapsing_header(cat):
            continue
        for sub, names in subs.items():
            if not sub:
                continue
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, sub_color)
            if not PyImGui.tree_node(sub):
                PyImGui.pop_style_color(1)
                continue
            PyImGui.pop_style_color(1)
            
            if not PyImGui.begin_table(f"Widgets {cat}{sub}", 2, PyImGui.TableFlags.Borders):
                PyImGui.tree_pop()
                continue
            
            for name in names:
                info = handler.widgets[name]
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                new_enabled = PyImGui.checkbox(name, info["enabled"])
                if new_enabled != info["enabled"]:
                    info["enabled"] = new_enabled
                    handler.save_widget_state(name)
                    
                PyImGui.table_set_column_index(1)
                if info["enabled"]:
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, cat_color)
                info["configuring"] = ImGui.toggle_button(IconsFontAwesome5.ICON_COG + f"##Configure{name}", info["configuring"])
                if info["enabled"]:
                    PyImGui.pop_style_color(1)

            PyImGui.end_table()
            PyImGui.tree_pop()

def draw_widget_ui():
    global enable_all, initialized
    is_enabled = enable_all
    if PyImGui.button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets"):
        ConsoleLog(module_name, "Reloading Widgets...", Py4GW.Console.MessageType.Info)
        initialized = False
        handler.discover_widgets()
        initialized = True
    ImGui.show_tooltip("Reloads all widgets")
    PyImGui.same_line(0.0, 10)
    
    toggle_label = IconsFontAwesome5.ICON_TOGGLE_ON if enable_all else IconsFontAwesome5.ICON_TOGGLE_OFF
    if is_enabled:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.153, 0.318, 0.929, 1.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.6, 0.6, 0.9, 1.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.6, 0.6, 0.6, 1.0))
    if PyImGui.button(toggle_label + "##widget_disable"):
        enable_all = not enable_all
        handler.write_global_setting(module_name, "enable_all", str(enable_all))
    if is_enabled:
        PyImGui.pop_style_color(3)
    ImGui.show_tooltip("Toggle all widgets")
    PyImGui.separator()
    draw_widget_contents_old()

def main():
    global initialized, enable_all, old_enable_all, current_window_pos, current_window_collapsed, enable_quick_dock

    try:
        if not initialized:
            handler.discover_widgets()
            initialized = True

        if window_module.first_run:
            PyImGui.set_next_window_size(*window_module.window_size)
            PyImGui.set_next_window_pos(*window_module.window_pos)
            PyImGui.set_next_window_collapsed(window_module.collapse, 0)
            window_module.first_run = False

        current_window_collapsed = True
        old_enable_all = enable_all

        if old_menu:
            if PyImGui.begin(window_module.window_name, window_module.window_flags):
                current_window_pos = PyImGui.get_window_pos()
                current_window_collapsed = False
                draw_widget_ui()
            PyImGui.end()

        if enable_quick_dock:
            quick_dock_menu()
        
        if (not handler.account_initialized and 
            not Map.IsMapLoading() and 
            not Map.IsInCinematic() and 
            not Player.InCharacterSelectScreen() and 
            Party.IsPartyLoaded()):
            handler.initialize_account_settings()
        
        if Player.InCharacterSelectScreen():
            handler.account_initialized = False
            
        draw_embedded_menu()
        write_ini()

        if enable_all:
            handler.execute_enabled_widgets()
            handler.execute_configuring_widgets()

    except Exception as e:
        err_type = type(e).__name__
        Py4GW.Console.Log(module_name, f"{err_type} encountered: {e}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, traceback.format_exc(), Py4GW.Console.MessageType.Error)

if __name__ == "__main__":
    main()

def get_widget_handler() -> WidgetHandler:
    return sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"].handler  # type: ignore[attr-defined]