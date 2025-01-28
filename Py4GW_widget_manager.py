
from Py4GWCoreLib import *
import importlib.util
import os

module_name = "Widget Manager"
ini_file_location = "Py4GW.ini"
ini_handler = IniHandler(ini_file_location)

class WidgetHandler:
    global ini_file_location, ini_handler

    def __init__(self, widgets_path="Widgets"):
        self.widgets_path = widgets_path
        self.widgets = {}  # {widget_name: {"module": module, "enabled": False, "configuring": False}}

    def discover_widgets(self):
        """Discover and load all valid widgets from the widgets directory."""
        try:
            for file in os.listdir(self.widgets_path):
                if file.endswith(".py"):
                    widget_path = os.path.join(self.widgets_path, file)
                    widget_name = os.path.splitext(file)[0]
                    try:
                        # Load the widget module
                        widget_module = self.load_widget(widget_path)

                        # Check if keys for the widget exist; if not, create them with defaults
                        if not ini_handler.has_key(widget_name, "category"):
                            ini_handler.write_key(widget_name, "category", "Miscellaneous")
                        if not ini_handler.has_key(widget_name, "subcategory"):
                            ini_handler.write_key(widget_name, "subcategory", "Others")
                        if not ini_handler.has_key(widget_name, "enabled"):
                            ini_handler.write_key(widget_name, "enabled", "True")

                        # Add the widget to the handler
                        self.widgets[widget_name] = {
                            "module": widget_module,
                            "enabled": ini_handler.read_bool(widget_name, "enabled", True),
                            "configuring": False  # Default state for configuring
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

    def save_widget_states(self):
        """Save widget states to INI file."""
        for widget_name, widget_info in self.widgets.items():
            ini_handler.write_key(widget_name, "enabled", str(widget_info["enabled"]))



initialized = False
handler = WidgetHandler("Widgets")
enable_all = ini_handler.read_bool(module_name, "enable_all", True)
window_module = ImGui.WindowModule(module_name, window_name="Widget Manager", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

window_x = ini_handler.read_int(module_name, "x", 100)
window_y = ini_handler.read_int(module_name, "y", 100)
window_collapsed = ini_handler.read_bool(module_name, "collapsed", False)

window_module.window_pos = (window_x, window_y)
window_module.collapse = window_collapsed

"""PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.153, 0.318, 0.929, 1.0))  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.6, 0.6, 0.9, 1.0))  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.6, 0.6, 0.6, 1.0))"""

def RGBToNormal(r, g, b, a):
    return r / 255.0, g / 255.0, b / 255.0, a / 255.0

def main():
    global module_name,window_module, initialized, handler, enable_all, window_collapsed, ini_handler
    try:
        if not initialized:
            handler.discover_widgets()
            initialized = True

        if window_module.first_run:
            PyImGui.set_next_window_size(window_module.window_size[0], window_module.window_size[1])     
            PyImGui.set_next_window_pos(window_module.window_pos[0], window_module.window_pos[1])
            PyImGui.set_next_window_collapsed(window_module.collapse, 0)

            window_module.first_run = False

        new_collapsed = True
        old_enable_all = enable_all

        if PyImGui.begin(window_module.window_name, window_module.window_flags):
            pos = PyImGui.get_window_pos()
            new_collapsed = PyImGui.is_window_collapsed()

            if pos[0] != window_module.window_pos[0] or pos[1] != window_module.window_pos[1]:

                ini_handler.write_key(module_name, "x", str(int(pos[0])))
                ini_handler.write_key(module_name, "y", str(int(pos[1])))

            
            enable_all = PyImGui.checkbox("Toggle All Widgets", enable_all)

            PyImGui.separator()

            if enable_all:
                categorized_widgets = {}
                
                subcategory_color = RGBToNormal(255, 200, 100, 255)  # Example color for category
                category_color = RGBToNormal(200, 255, 150, 255)  # Example color for subcategory
                    
                for widget_name, widget_info in handler.widgets.items():
                    category = ini_handler.read_key(widget_name, "category", "Miscellaneous")
                    subcategory = ini_handler.read_key(widget_name, "subcategory", "")

                    if category not in categorized_widgets:
                        categorized_widgets[category] = {}
                    if subcategory not in categorized_widgets[category]:
                        categorized_widgets[category][subcategory] = []
                    categorized_widgets[category][subcategory].append(widget_name)
                  
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
                                                handler.save_widget_states()
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

        if new_collapsed != window_collapsed:
            ini_handler.write_key(module_name, "collapsed", str(new_collapsed))

        if old_enable_all != enable_all:
            ini_handler.write_key(module_name, "enable_all", str(enable_all))

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
