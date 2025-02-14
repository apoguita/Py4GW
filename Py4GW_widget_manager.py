from Py4GWCoreLib import *
import importlib.util
import os

module_name = "Widget Manager"
ini_file_location = "Py4GW.ini"
ini_handler = IniHandler(ini_file_location)
sync_interval = 1000

class WidgetHandler:
    global ini_file_location, ini_handler, sync_interval

    def __init__(self, widgets_path="Widgets"):
        self.widgets_path = widgets_path
        self.widgets = {}  # {widget_name: {"module": module, "enabled": False, "configuring": False}}
        self.widget_data_cache = {}  # Caches INI data to avoid constant reads
        self.sync_interval = sync_interval
        self.last_write_time = Timer()
        self.last_write_time.Start()
        
        self._load_widget_cache()


    def _load_widget_cache(self):
        """Caches all INI settings **once** at startup to avoid repeated disk reads."""
        for section in ini_handler.list_sections():
            self.widget_data_cache[section] = {
                "category": ini_handler.read_key(section, "category", "Miscellaneous"),
                "subcategory": ini_handler.read_key(section, "subcategory", "Others"),
                "enabled": ini_handler.read_bool(section, "enabled", True)
            }

    def discover_widgets(self):
        """Discover and load all valid widgets from the widgets directory (loads INI data once)."""
        try:
            self._load_widget_cache()  # Cache INI values before discovery

            for file in os.listdir(self.widgets_path):
                if file.endswith(".py"):
                    widget_path = os.path.join(self.widgets_path, file)
                    widget_name = os.path.splitext(file)[0]

                    try:
                        # Load widget module
                        widget_module = self.load_widget(widget_path)

                        # Load settings from cache instead of real-time INI reads
                        category = self.widget_data_cache.get(widget_name, {}).get("category", "Miscellaneous")
                        subcategory = self.widget_data_cache.get(widget_name, {}).get("subcategory", "Others")
                        enabled = self.widget_data_cache.get(widget_name, {}).get("enabled", True)

                        # Store widget
                        self.widgets[widget_name] = {
                            "module": widget_module,
                            "enabled": enabled,
                            "configuring": False
                        }

                        Py4GW.Console.Log("WidgetHandler", f"Loaded widget: {widget_name}", Py4GW.Console.MessageType.Info)

                    except Exception as e:
                        Py4GW.Console.Log("WidgetHandler", f"Failed to load widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                        Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

        except Exception as e:
            Py4GW.Console.Log("WidgetHandler", f"Unexpected error during widget discovery: {str(e)}", Py4GW.Console.MessageType.Error)
            Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

    def load_widget(self, widget_path):
        """Load a widget module dynamically from the given path."""
        try:
            spec = importlib.util.spec_from_file_location("widget", widget_path)
            widget_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(widget_module)

            if not hasattr(widget_module, "main") or not hasattr(widget_module, "configure"):
                raise ValueError("Widget is missing required functions: main() and configure()")

            return widget_module
        except ImportError as e:
            raise ImportError(f"ImportError encountered while loading widget: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error during widget loading: {str(e)}")

    def execute_enabled_widgets(self):
        """Execute the main() function of all enabled widgets."""
        try:
            for widget_name, widget_info in self.widgets.items():
                if widget_info["enabled"]:
                    try:
                        widget_info["module"].main()
                    except Exception as e:
                        Py4GW.Console.Log("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                        Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
        except Exception as e:
            Py4GW.Console.Log("WidgetHandler", f"Unexpected error during widget execution: {str(e)}", Py4GW.Console.MessageType.Error)
            Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

    def execute_configuring_widgets(self):
        """Execute the main() function of all configuring widgets."""
        try:
            for widget_name, widget_info in self.widgets.items():
                if widget_info["configuring"]:
                    try:
                        widget_info["module"].configure()
                    except Exception as e:
                        Py4GW.Console.Log("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                        Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
        except Exception as e:
            Py4GW.Console.Log("WidgetHandler", f"Unexpected error during widget execution: {str(e)}", Py4GW.Console.MessageType.Error)
            Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

    def save_widget_state(self, widget_name):
        """Saves the state of a single widget instead of all at once."""
        if widget_name in self.widgets:
            ini_handler.write_key(widget_name, "enabled", str(self.widgets[widget_name]["enabled"]))




initialized = False
handler = WidgetHandler("Widgets")
enable_all = ini_handler.read_bool(module_name, "enable_all", True)
old_enable_all = enable_all

window_module = ImGui.WindowModule(module_name, window_name="Widget Manager", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

window_x = ini_handler.read_int(module_name, "x", 100)
window_y = ini_handler.read_int(module_name, "y", 100)
window_module.window_pos = (window_x, window_y)

window_module.collapse = ini_handler.read_bool(module_name, "collapsed", True)
current_window_collapsed = window_module.collapse


write_timer = Timer()
write_timer.Start()

current_window_pos = window_module.window_pos



def write_ini():
    global module_name, window_module, enable_all, ini_handler
    global write_timer, current_window_pos, current_window_collapsed, old_enable_all
    if write_timer.HasElapsed(1000):
        if current_window_pos[0] != window_module.window_pos[0] or current_window_pos[1] != window_module.window_pos[1]:
            window_module.window_pos = (int(current_window_pos[0]), int(current_window_pos[1]))
            ini_handler.write_key(module_name, "x", str(int(current_window_pos[0])))
            ini_handler.write_key(module_name, "y", str(int(current_window_pos[1])))
        
        if current_window_collapsed != window_module.collapse:
            window_module.collapse = current_window_collapsed
            ini_handler.write_key(module_name, "collapsed", str(current_window_collapsed))
            
        if old_enable_all != enable_all:
            enable_all = old_enable_all
            ini_handler.write_key(module_name, "enable_all", str(enable_all))
            
        write_timer.Reset()

def main():
    global module_name,window_module, initialized, handler, enable_all, ini_handler
    global current_window_pos, current_window_collapsed, old_enable_all
    try:
        if not initialized:
            handler.discover_widgets()
            initialized = True

        if window_module.first_run:
            PyImGui.set_next_window_size(window_module.window_size[0], window_module.window_size[1])     
            PyImGui.set_next_window_pos(window_module.window_pos[0], window_module.window_pos[1])
            PyImGui.set_next_window_collapsed(window_module.collapse, 0)
            window_module.first_run = False

        current_window_collapsed = True
        old_enable_all = enable_all

        if PyImGui.begin(window_module.window_name, window_module.window_flags):
            current_window_pos = PyImGui.get_window_pos()
            current_window_collapsed = False
            
            enable_all = PyImGui.checkbox("Toggle All Widgets", enable_all)

            PyImGui.separator()

            if enable_all:
                categorized_widgets = {}
                
                subcategory_color = Utils.RGBToNormal(255, 200, 100, 255)  # Example color for category
                category_color = Utils.RGBToNormal(200, 255, 150, 255)  # Example color for subcategory
                    
                # Use cached INI data instead of real-time INI reads
                for widget_name, widget_info in handler.widgets.items():
                    widget_data = handler.widget_data_cache.get(widget_name, {})
                    category = widget_data.get("category", "Miscellaneous")
                    subcategory = widget_data.get("subcategory", "")

                    if category not in categorized_widgets:
                        categorized_widgets[category] = {}
                    if subcategory not in categorized_widgets[category]:
                        categorized_widgets[category][subcategory] = []
                    categorized_widgets[category][subcategory].append(widget_name)
                  
                # Render the UI using cached widget data
                  
                for category, subcategories in categorized_widgets.items():
                    if PyImGui.collapsing_header(category):  # Render category
                        for subcategory, widgets in subcategories.items():
                            if subcategory:  # Render subcategory if present
                                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, subcategory_color)
                                if PyImGui.tree_node(subcategory):
                                    PyImGui.pop_style_color(1)
                                    if PyImGui.begin_table(f"Widgets {category}{subcategory}", 2,PyImGui.TableFlags.Borders):
                                        for widget_name in widgets:
                                            widget_info = handler.widgets[widget_name]
                                            
                                            color_status = widget_info["enabled"]
                                            if color_status:
                                                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, category_color)

                                            # Render widget checkbox and config button
                                            PyImGui.table_next_row()
                                            PyImGui.table_set_column_index(0)
                                            new_enabled = PyImGui.checkbox(f"{widget_name}", widget_info["enabled"])
                                            if new_enabled != widget_info["enabled"]:
                                                widget_info["enabled"] = new_enabled
                                                handler.save_widget_state(widget_name) 

                                            PyImGui.table_set_column_index(1)
                                            widget_info["configuring"] = ImGui.toggle_button(
                                                IconsFontAwesome5.ICON_COG + f"##Configure{widget_name}",
                                                widget_info["configuring"]
                                            )
                                            if color_status:
                                                PyImGui.pop_style_color(1)
                                        PyImGui.end_table()
                                    PyImGui.tree_pop()
                                else:
                                    PyImGui.pop_style_color(1)
                    
        PyImGui.end()
        
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
