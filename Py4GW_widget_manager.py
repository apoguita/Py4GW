from PyImGui import StyleConfig
from Py4GWCoreLib import *
import importlib.util
import os
import types
import sys

module_name = "Widget Manager"
ini_file_location = "Py4GW.ini"
ini_handler = IniHandler(ini_file_location)

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
        self.show_widget_ui = True
        
        self.widgets = {}
        self.widget_data_cache = {}
        self.last_write_time = Timer()
        self.last_write_time.Start()
        self._load_widget_cache()
        self._initialized = True

    def _load_widget_cache(self):
        for section in ini_handler.list_sections():
            if section in self.widget_data_cache:
                continue
            self.widget_data_cache[section] = {
                "category": ini_handler.read_key(section, "category", "Miscellaneous"),
                "subcategory": ini_handler.read_key(section, "subcategory", "Others"),
                "enabled": ini_handler.read_bool(section, "enabled", True)
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
                enabled = self.widget_data_cache.get(widget_name, {}).get("enabled", True)
                on_enable = getattr(module, "on_enable", None)

                self.widgets[widget_name] = {
                    "module": module,
                    "enabled": enabled,
                    "configuring": False
                }
                
                if enabled and on_enable:
                    try:
                        on_enable()
                        
                    except Exception as e:
                        ConsoleLog("WidgetHandler", f"Error during on_enable of widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                        ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

                ConsoleLog("WidgetHandler", f"Loaded widget: {widget_name}", Py4GW.Console.MessageType.Info)
                
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
        
        if not self.show_widget_ui:
            style.Alpha = 0.0
            style.Push()
        
        for widget_name, widget_info in self.widgets.items():
            if not widget_info["enabled"]:
                continue
            try:
                widget_info["module"].main()
            except Exception as e:
                ConsoleLog("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

        if not self.show_widget_ui:
            style.Alpha = alpha
            style.Push()
            
    def execute_configuring_widgets(self):
        for widget_name, widget_info in self.widgets.items():
            if not widget_info["configuring"]:
                continue
            try:
                widget_info["module"].configure() 
            except Exception as e:
                ConsoleLog("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

    def save_widget_state(self, widget_name):
        widget = self.widgets.get(widget_name)
        if widget:
            state = "Enabled" if widget["enabled"] else "Disabled"
            Py4GW.Console.Log("WidgetHandler", f'"{widget_name}" is {state}', Py4GW.Console.MessageType.Info)
            ini_handler.write_key(widget_name, "enabled", str(widget["enabled"]))
            self.widget_data_cache.setdefault(widget_name, {})["enabled"] = widget["enabled"]

    def get_widget_info(self, name: str):
        return self.widgets.get(name)

    def set_widget_configuring(self, name: str, value: bool = True):
        widget = self.widgets.get(name)
        if not widget:
            ConsoleLog("WidgetHandler", f"Widget '{name}' not found", Py4GW.Console.MessageType.Warning)
            return
        widget["configuring"] = value
        
    def enable_widget(self, name: str):
        self._set_widget_state(name, True)

    def disable_widget(self, name: str):
        self._set_widget_state(name, False)

    def _set_widget_state(self, name: str, state: bool):
        widget = self.widgets.get(name)
        if not widget:
            ConsoleLog("WidgetHandler", f"Widget '{name}' not found", Py4GW.Console.MessageType.Warning)
            return
        widget["enabled"] = state

        if state:
            if hasattr(widget["module"], "on_enable"):
                try:
                    widget["module"].on_enable()
                except Exception as e:
                    ConsoleLog("WidgetHandler", f"Error during on_enable of widget {name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
                                
        elif not state:
            if hasattr(widget["module"], "on_disable"):
                try:
                    widget["module"].on_disable()
                except Exception as e:
                    ConsoleLog("WidgetHandler", f"Error during on_disable of widget {name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
            
        self.save_widget_state(name)

    def is_widget_enabled(self, name: str) -> bool:
        widget = self.widgets.get(name)
        return bool(widget and widget["enabled"])

    def list_enabled_widgets(self) -> list[str]:
        return [name for name, info in self.widgets.items() if info["enabled"]]

initialized = False

if "_Py4GW_GLOBAL_WIDGET_HANDLER" not in sys.modules:
    mod = types.ModuleType("_Py4GW_GLOBAL_WIDGET_HANDLER")  # actual module type
    mod.handler = WidgetHandler()  # type: ignore[attr-defined]
    sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"] = mod
handler = sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"].handler
enable_all = ini_handler.read_bool(module_name, "enable_all", True)
old_enable_all = enable_all

window_module = ImGui.WindowModule(module_name, window_name="Widgets", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

window_x = ini_handler.read_int(module_name, "x", 100)
window_y = ini_handler.read_int(module_name, "y", 100)
window_module.window_pos = (window_x, window_y)

window_module.collapse = ini_handler.read_bool(module_name, "collapsed", True)
current_window_collapsed = window_module.collapse


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
        ini_handler.write_key(module_name, "x", str(x))
        ini_handler.write_key(module_name, "y", str(y))
    
    # if current_window_pos[0] != window_module.window_pos[0] or current_window_pos[1] != window_module.window_pos[1]:
    #     window_module.window_pos = (int(current_window_pos[0]), int(current_window_pos[1]))
    #     ini_handler.write_key(module_name, "x", str(int(current_window_pos[0])))
    #     ini_handler.write_key(module_name, "y", str(int(current_window_pos[1])))
        
    if current_window_collapsed != window_module.collapse:
        window_module.collapse = current_window_collapsed
        ini_handler.write_key(module_name, "collapsed", str(current_window_collapsed))
            
    if old_enable_all != enable_all:
        enable_all = old_enable_all
        ini_handler.write_key(module_name, "enable_all", str(enable_all))
            
    write_timer.Reset()

def draw_widget_ui():
    global enable_all, initialized
    style = ImGui.get_style()
    
    if ImGui.icon_button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets"):
        ConsoleLog(module_name, "Reloading Widgets...", Py4GW.Console.MessageType.Info)
        initialized = False
        handler.discover_widgets()
        initialized = True        
    ImGui.show_tooltip("Reload all widgets")
    PyImGui.same_line(0, 5)

    new_enable_all = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_TOGGLE_ON if enable_all else IconsFontAwesome5.ICON_TOGGLE_OFF) + "##widget_disable", enable_all)
    if new_enable_all != enable_all:
        enable_all = new_enable_all
        ini_handler.write_key(module_name, "enable_all", str(enable_all))        
    ImGui.show_tooltip(f"{("Run" if not enable_all else "Pause")} all widgets")
    
    PyImGui.same_line(0, 5)
    handler.show_widget_ui = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_EYE if handler.show_widget_ui else IconsFontAwesome5.ICON_EYE_SLASH) + "##Show Widget UIs", handler.show_widget_ui)
    ImGui.show_tooltip(f"{("Show" if not handler.show_widget_ui else "Hide")} all widget UIs")
    ImGui.separator()
    
    categorized_widgets = {}
    for name, info in handler.widgets.items():
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
                info = handler.widgets[name]
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                                    
                new_enabled = ImGui.checkbox(name, info["enabled"])
                    
                if new_enabled != info["enabled"]:
                    handler._set_widget_state(name, new_enabled)
                    
                PyImGui.table_set_column_index(1)                    
                info["configuring"] = ImGui.toggle_icon_button(IconsFontAwesome5.ICON_COG + f"##Configure{name}", info["configuring"])
                

            ImGui.end_table()
            ImGui.tree_pop()

def main():
    global initialized, enable_all, old_enable_all, current_window_pos, current_window_collapsed

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

        if ImGui.begin(window_module.window_name, None, window_module.window_flags):
            current_window_pos = PyImGui.get_window_pos()
            current_window_collapsed = False
            draw_widget_ui()
        ImGui.end()

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