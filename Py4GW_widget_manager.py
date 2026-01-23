from typing import Callable
from types import ModuleType
from PyImGui import StyleConfig
from Py4GWCoreLib import *
import importlib.util
import os
import types
import sys

module_name = "Widget Manager"
ini_file_location = "Py4GW.ini"
ini_handler = IniHandler(ini_file_location)

class Widget:
    def __init__(self, name : str, module: ModuleType, widget_data: dict):
        self.name : str = name
        self.module : ModuleType = module
        self.configuring : bool = False
        self.enabled : bool = bool(widget_data.get("enabled", True))
        self.optional : bool = bool(module.__dict__.get("OPTIONAL", True))
                    
        self.category : str = str(widget_data.get("category", "Miscellaneous"))
        self.subcategory : str = str(widget_data.get("subcategory", "Others"))

        self.main : Callable  = lambda: None
        self.minimal : Callable  = lambda: None
        self.configure : Callable  = lambda: None
        self.on_enable : Callable  = lambda: None
        self.on_disable : Callable  = lambda: None

        main = getattr(module, "main", None)
        if callable(main):
            self.main = main
            
        minimal = getattr(module, "minimal", None)
        if callable(minimal):
            self.minimal = minimal
            
        configure = getattr(module, "configure", None)
        if callable(configure):
            self.configure = configure

        on_enable = getattr(module, "on_enable", None)
        if callable(on_enable):
            self.on_enable = on_enable
            
        on_disable = getattr(module, "on_disable", None)
        if callable(on_disable):
            self.on_disable = on_disable
            
    def __getitem__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")
    
    def __setitem__(self, key, value):
        if key in self.__dict__:
            self.__dict__[key] = value
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")
    
    def save_widget_state(self):
        ini_handler.write_key(self.name, "enabled", str(self.enabled))

class WidgetHandler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, widgets_path="Widgets"):
        if getattr(self, "_initialized", False):
            return

        import sys
        try:
            module_file = sys.modules[__name__].__file__
        except (KeyError, AttributeError):
            module_file = None

        base_dir = os.path.dirname(os.path.abspath(module_file)) if module_file else os.getcwd()
        resolved_path = widgets_path or os.path.join(base_dir, "Widgets")
        self.widgets_path = os.path.abspath(resolved_path)
        self.__show_widget_ui = True
        self.__pause_optional_widgets = False

        self.widgets : dict[str, Widget] = {}
        self.widget_data_cache = {}
        self.last_write_time = Timer()
        self.last_write_time.Start()
        self._load_widget_cache()
        self._initialized = True
    
    @property
    def pause_optional_widgets(self):
        return self.__pause_optional_widgets
    
    @property
    def show_widget_ui(self):
        return self.__show_widget_ui

    def _load_widget_cache(self):
        for section in ini_handler.list_sections():
            if section in self.widget_data_cache:
                continue
            
            self.widget_data_cache[section] = {
                "category": ini_handler.read_key(section, "category", "Miscellaneous"),
                "subcategory": ini_handler.read_key(section, "subcategory", "Others"),
                "enabled": ini_handler.read_bool(section, "enabled", True),
            }

    def _load_all_from_dir(self):
        if not os.path.isdir(self.widgets_path):
            raise FileNotFoundError(f"Widget directory missing: {self.widgets_path}")
        for file in os.listdir(self.widgets_path):
            if not file.endswith(".py"):
                continue

            widget_name = os.path.splitext(file)[0]
            widgets_path = os.path.join(self.widgets_path, file)

            try:
                module = self.load_widget(widgets_path)
                widget = self.widgets[widget_name] = Widget(
                    name=widget_name,
                    module=module,
                    widget_data=self.widget_data_cache.get(widget_name, {})
                )

                if widget.enabled and widget.on_enable is not None:
                    try:
                        widget.on_enable()

                    except Exception as e:
                        ConsoleLog("WidgetHandler", f"Error during on_enable of widget {widget.name}: {str(e)}", Py4GW.Console.MessageType.Error)
                        ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

                ConsoleLog("WidgetHandler", f"Loaded widget: {widget.name}", Py4GW.Console.MessageType.Info)

            except Exception as e:
                ConsoleLog("WidgetHandler", f"Failed to load widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    
    def discover_widgets(self):
        try:
            self.widget_data_cache.clear()
            self._load_widget_cache()
            self._load_all_from_dir()
            
        except Exception as e:
            ConsoleLog("WidgetHandler", f"Unexpected error during widget discovery: {str(e)}", Py4GW.Console.MessageType.Error)
            ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

    def load_widget(self, widget_path):
        spec = importlib.util.spec_from_file_location("widget", widget_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Failed to load widget: Invalid spec from {widget_path}")

        widget_module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(widget_module)
        except ImportError as e:
            raise ImportError(f"ImportError encountered while loading widget: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error during widget loading: {str(e)}")

        if not hasattr(widget_module, "main") or not hasattr(widget_module, "configure"):
            raise ValueError("Widget is missing required functions: main() and configure()")

        return widget_module
        
    def execute_enabled_widgets(self):
        style = ImGui.Selected_Style.pyimgui_style
        alpha = style.Alpha
        ui_enabled = self.__show_widget_ui
        pause_optional = self.__pause_optional_widgets
                
        if not ui_enabled:
            style.Alpha = 0.0
            style.Push()
        
        for widget_name, widget_info in self.widgets.items():
            if not widget_info.enabled:
                continue
        
            if widget_info.minimal:
                try:
                    widget_info.minimal()
                except Exception as e:
                    ConsoleLog("WidgetHandler", f"Error executing minimal of widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
                    
            if pause_optional and widget_info.optional:                        
                continue
            
            try:
                if widget_info.main:
                    widget_info.main()
                    
            except Exception as e:
                ConsoleLog("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

        if not ui_enabled:
            style.Alpha = alpha
            style.Push()
        
    def set_widget_ui_visibility(self, visible: bool):
        self.__show_widget_ui = visible
            
    def execute_configuring_widgets(self):
        for widget_name, widget_info in self.widgets.items():
            if not widget_info.configuring:
                continue
            try:
                if widget_info.configure:
                    widget_info.configure()
                    
            except Exception as e:
                ConsoleLog("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

    def get_widget_info(self, name: str) -> Widget | None:
        return self.widgets.get(name, None)

    def set_widget_configuring(self, name: str, value: bool = True):
        widget = self.widgets.get(name)
        if not widget:
            ConsoleLog("WidgetHandler", f"Widget '{name}' not found", Py4GW.Console.MessageType.Warning)
            return
        widget.configuring = value
        
    def pause_widgets(self):
        self.__pause_optional_widgets = True
        
    def resume_widgets(self):
        self.__pause_optional_widgets = False
        
    def enable_widget(self, name: str):
        self._set_widget_state(name, True)

    def disable_widget(self, name: str):
        self._set_widget_state(name, False)

    def _set_widget_state(self, name: str, state: bool):
        widget = self.widgets.get(name)
        if not widget:
            ConsoleLog("WidgetHandler", f"Widget '{name}' not found", Py4GW.Console.MessageType.Warning)
            return
        
        widget.enabled = state

        if state:
            if widget.on_enable:
                try:
                    widget.on_enable()
                except Exception as e:
                    ConsoleLog("WidgetHandler", f"Error during on_enable of widget {name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
                                
        elif not state:
            if widget.on_disable:
                try:
                    widget.on_disable()
                except Exception as e:
                    ConsoleLog("WidgetHandler", f"Error during on_disable of widget {name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
            
        widget.save_widget_state()

    def is_widget_enabled(self, name: str) -> bool:
        widget = self.widgets.get(name)
        return bool(widget and widget.enabled)

    def list_enabled_widgets(self) -> list[str]:
        return [name for name, info in self.widgets.items() if info.enabled]

initialized = False

if "_Py4GW_GLOBAL_WIDGET_HANDLER" not in sys.modules:
    mod = types.ModuleType("_Py4GW_GLOBAL_WIDGET_HANDLER")  # actual module type
    mod.handler = WidgetHandler()  # type: ignore[attr-defined]
    sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"] = mod
handler : WidgetHandler = sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"].handler
handler : WidgetHandler = sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"].handler
enable_all = ini_handler.read_bool(module_name, "enable_all", True)
old_enable_all = enable_all

window_module = ImGui.WindowModule(module_name, window_name="Widgets", window_size=(130, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

window_x = ini_handler.read_int(module_name, "x", 100)
window_y = ini_handler.read_int(module_name, "y", 100)
window_module.window_pos = (window_x, window_y)

window_module.collapse = ini_handler.read_bool(module_name, "collapsed", True)
current_window_collapsed = window_module.collapse
current_window_pos = window_module.window_pos

write_timer = Timer()
write_timer.Start()


def write_ini():
    if not write_timer.HasElapsed(1000):
        return
    global enable_all, current_window_collapsed, current_window_pos, old_enable_all
    
    if window_module.window_pos != current_window_pos:
        x, y = map(int, current_window_pos)
        current_window_pos = window_module.window_pos = (x, y)
        ini_handler.write_key(module_name, "x", str(x))
        ini_handler.write_key(module_name, "y", str(y))
            
    if window_module.collapse != current_window_collapsed:
        current_window_collapsed = window_module.collapse
        ini_handler.write_key(module_name, "collapsed", str(current_window_collapsed))
            
    if old_enable_all != enable_all:
        enable_all = old_enable_all
        ini_handler.write_key(module_name, "enable_all", str(enable_all))
            
    write_timer.Reset()

def draw_widget_ui():
    global enable_all, initialized
    style = ImGui.get_style()
    
    if ImGui.icon_button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets", 40):
        ConsoleLog(module_name, "Reloading Widgets...", Py4GW.Console.MessageType.Info)
        initialized = False
        handler.discover_widgets()
        initialized = True        
    ImGui.show_tooltip("Reload all widgets")
    PyImGui.same_line(0, 5)

    new_enable_all = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_TOGGLE_ON if enable_all else IconsFontAwesome5.ICON_TOGGLE_OFF) + "##widget_disable", enable_all, 40)
    if new_enable_all != enable_all:
        enable_all = new_enable_all
        ini_handler.write_key(module_name, "enable_all", str(enable_all))        
    ImGui.show_tooltip(f"{("Run" if not enable_all else "Pause")} all widgets")
    
    PyImGui.same_line(0, 5)
    show_widget_ui = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_EYE if handler.show_widget_ui else IconsFontAwesome5.ICON_EYE_SLASH) + "##Show Widget UIs", handler.show_widget_ui, 40)
    if show_widget_ui != handler.show_widget_ui:
        handler.set_widget_ui_visibility(show_widget_ui)
    ImGui.show_tooltip(f"{("Show" if not handler.show_widget_ui else "Hide")} all widget UIs")
    
    PyImGui.same_line(0, 5)
    pause_non_env = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_PAUSE if handler.pause_optional_widgets else IconsFontAwesome5.ICON_PLAY) + "##Pause Non-Env Widgets", not handler.pause_optional_widgets, 40)
    if pause_non_env != (not handler.pause_optional_widgets):
        if not handler.pause_optional_widgets:
            handler.pause_widgets()
        else:
            handler.resume_widgets()
            
        own_email = Player.GetAccountEmail()
        for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if acc.AccountEmail == own_email:
                continue
            
            GLOBAL_CACHE.ShMem.SendMessage(own_email, acc.AccountEmail, SharedCommandType.PauseWidgets if handler.pause_optional_widgets else SharedCommandType.ResumeWidgets)
        
    ImGui.show_tooltip(f"{("Pause" if not handler.pause_optional_widgets else "Resume")} all optional widgets")
    ImGui.separator()
    
    categorized_widgets = {}
    for name, info in handler.widgets.items():
        data = handler.widget_data_cache.get(name, {})        
        data = handler.widget_data_cache.get(name, {})        
        cat = data.get("category", "Miscellaneous")
        sub = data.get("subcategory", "")
        categorized_widgets.setdefault(cat, {}).setdefault(sub, []).append(name)

    for cat, subs in categorized_widgets.items():
        open = ImGui.collapsing_header(cat)
        
        if not open:
            continue
        
        for sub, names in subs.items():
            if not sub:
                continue
            
            if style.Theme not in ImGui.Textured_Themes:
                style.TextTreeNode.push_color((255, 200, 100, 255))
                
            open = ImGui.tree_node(sub)
            
            if style.Theme not in ImGui.Textured_Themes:
                style.TextTreeNode.pop_color()
            
            if not open:
                continue
                        
            if not ImGui.begin_table(f"Widgets {cat}{sub}", 2, PyImGui.TableFlags.Borders):
                ImGui.tree_pop()
                continue
            
            for name in names:
                widget = handler.widgets[name]
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)

                new_enabled = ImGui.checkbox(name, widget.enabled)

                if new_enabled != widget.enabled:
                    handler._set_widget_state(name, new_enabled)

                PyImGui.table_set_column_index(1)
                widget.configuring = ImGui.toggle_icon_button(IconsFontAwesome5.ICON_COG + f"##Configure{name}", widget.configuring)
                

            ImGui.end_table()
            ImGui.tree_pop()



def main():
    global initialized, enable_all, old_enable_all

    try:
        if not initialized:
            handler.discover_widgets()
            initialized = True

        old_enable_all = enable_all

        if window_module.begin():
            draw_widget_ui()
            
        window_module.process_window()
        window_module.end()

        write_ini()

        if enable_all:
            handler.execute_enabled_widgets()
            handler.execute_configuring_widgets()


    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        # Optional: Code that will run whether an exception occurred or not
        #Py4GW.Console.Log(module_name, "Execution of Main() completed", Py4GW.Console.MessageType.Info)
        # Place any cleanup tasks here
        pass

# This ensures that Main() is called when the script is executed directly.
if __name__ == "__main__":
    main()

def get_widget_handler() -> WidgetHandler:
    return sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"].handler  # type: ignore[attr-defined]

WidgetHandler.__new__ = staticmethod(lambda cls: get_widget_handler())
