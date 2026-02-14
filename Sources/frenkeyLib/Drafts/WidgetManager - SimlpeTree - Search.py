MODULE_NAME = "WidgetManagerV2"

import os
import traceback
import Py4GW
import PyImGui
from Py4GWCoreLib import ImGui, IniManager, Player
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import Widget, get_widget_handler


class WidgetTreeNode:
    def __init__(self):
        self.name: str = ""
        
        # hierarchy
        self.children: dict[str, WidgetTreeNode] = {}
        self.widgets: list[str] = []

        # ui state
        self.window_hovered: bool = False
        self.hovered: bool = False
        self.active: bool = False
        self.open: bool = False
        self.pos = (0.0, 0.0)
        
        # optional extra state
        self.last_hover_frame: int = 0
        self.last_active_frame: int = 0

    def get_child(self, name: str) -> "WidgetTreeNode":
        if name not in self.children:
            self.children[name] = WidgetTreeNode()
            self.children[name].name = name
            
        return self.children[name]
    
    def is_hovered(self):
        return self.window_hovered or any(child.is_hovered() for child in self.children.values())
    
    def close(self):
        self.open = False
        for child in self.children.values():
            child.close()
    
widget_filter = ""
widget_manager = get_widget_handler()
tree = WidgetTreeNode()
tree.name = "Root"
filtered_widgets : list[Widget] = []

INI_KEY = ""
INI_PATH = "Widgets/WidgetManagerV2"
INI_FILENAME = "WidgetManagerV2.ini"

def on_enable():
    Py4GW.Console.Log(MODULE_NAME, f"{MODULE_NAME} loaded successfully.")

def on_disable():
    Py4GW.Console.Log(MODULE_NAME, f"{MODULE_NAME} unloaded successfully.")
    
def configure():
    Py4GW.Console.Log(MODULE_NAME, f"{MODULE_NAME} configuration opened.")

def draw_node(INI_KEY: str, parent_node: WidgetTreeNode, depth: int = 0):
        style = ImGui.get_style()

        for key, node in sorted(parent_node.children.items()):
            # Leaf: render widgets table
                    
            # Folder nodes
            if depth == 0:
                # IMPORTANT: also make header id stable+unique
                node.open = ImGui.collapsing_header(f"{node.name}##FolderHeader_{parent_node.name}_{key}")
            else:
                if style.Theme not in ImGui.Textured_Themes:
                    style.TextTreeNode.push_color((255, 200, 100, 255))

                node.open = ImGui.tree_node(f"{node.name}##Tree_{depth}_{node.name}")

                if style.Theme not in ImGui.Textured_Themes:
                    style.TextTreeNode.pop_color()

            if node.open:
                draw_node(INI_KEY, node, depth + 1)
                    
                if node.open and node.widgets:
                    table_id = f"WidgetsTable##tree_depth_{depth}"
                    PyImGui.set_next_item_width(-1)  # take full available width

                    flags = (
                        PyImGui.TableFlags.Borders |
                        PyImGui.TableFlags.SizingStretchProp |
                        PyImGui.TableFlags.NoSavedSettings
                    )

                    if ImGui.begin_table(table_id, 2, flags):
                        PyImGui.table_setup_column("Widget", PyImGui.TableColumnFlags.WidthStretch, 1.0)
                        PyImGui.table_setup_column("Cfg", PyImGui.TableColumnFlags.WidthFixed, 30.0)
                        #PyImGui.table_headers_row()

                        for widget_id in node.widgets:
                            widget = widget_manager.widgets.get(widget_id)
                            if not widget:
                                continue
                            
                            draw_widget(widget)

                        ImGui.end_table()
                        
                if depth > 0:
                    ImGui.tree_pop()    

def draw_widget(widget: Widget):
    PyImGui.table_next_row()
    PyImGui.table_set_column_index(0)

    display_name = widget.plain_name
    
    v_enabled = widget_manager._widget_var(widget.folder_script_name, "enabled")
    # Define the section once to ensure consistency
    section_name = f"Widget:{widget.folder_script_name}"
    # FIXED: Added the section parameter to the get call
    val = bool(IniManager().get(INI_KEY, v_enabled, False, section=section_name))
    new_enabled = ImGui.checkbox(f"##{widget.folder_script_name}{widget.widget_path}", val)
    PyImGui.same_line(0, 5)
    ImGui.text_wrapped(display_name)
    if PyImGui.is_item_hovered():
        if widget.has_tooltip_property:
            try:
                if widget.tooltip:
                    widget.tooltip()
            except Exception as e:
                Py4GW.Console.Log("WidgetHandler", f"Error during tooltip of widget {widget.folder_script_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
        else:
            PyImGui.show_tooltip(f"Enable/Disable {display_name} widget")

    if new_enabled != val:
        # Using consistent section name
        if new_enabled:
            widget.enable()
        else:
            widget.disable()
            
        IniManager().set(key=INI_KEY, var_name=v_enabled, value=widget.enabled, section=section_name)
        IniManager().save_vars(INI_KEY)

    PyImGui.table_set_column_index(1)

    PyImGui.begin_disabled(not widget.has_configure_property)
    configuring = ImGui.toggle_icon_button(
        IconsFontAwesome5.ICON_COG if widget.has_configure_property else IconsFontAwesome5.ICON_SLASH + f"##Configure{widget.folder_script_name}",
        widget.configuring, 30.0
    )
    if configuring != widget.configuring:
        widget.set_configuring(configuring)
        
    if PyImGui.is_item_hovered():
        PyImGui.show_tooltip("Configure Widget")
    PyImGui.end_disabled()


def create_tree():
    global tree, widget_manager
    
    for widget_id, widget in widget_manager.widgets.items():
        folder = widget.widget_path  # "A/B/C" or ""
        node = tree

        if folder:
            for part in folder.split("/"):
                node = node.get_child(part)

        node.widgets.append(widget_id)        

def filter_widgets(filter_text: str):
    global filtered_widgets, widget_manager, tree
    
    filtered_widgets.clear()
    if not filter_text:
        return
    
    filtered_widgets = [w for w in widget_manager.widgets.values() if filter_text.lower() in w.plain_name.lower() or filter_text.lower() in w.folder.lower()]
    

def draw():    
    global widget_filter
    
    if not INI_KEY:
        return
            
    if INI_KEY:
        PyImGui.set_next_window_size(300, 0)
        if ImGui.Begin(ini_key=INI_KEY, name="Widget Manager V2", flags=PyImGui.WindowFlags.AlwaysAutoResize):
            button_width = (PyImGui.get_content_region_avail()[0] - 15)/ 4
                                
            if ImGui.icon_button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets", button_width):
                Py4GW.Console.Log("Widget Manager", "Reloading Widgets...", Py4GW.Console.MessageType.Info)
                
                widget_manager.widget_initialized = False
                widget_manager.discovered = False
                widget_manager.discover()
                widget_manager.widget_initialized = True    
                    
            ImGui.show_tooltip("Reload all widgets")
            PyImGui.same_line(0, 5)
            
            e_all = bool(IniManager().get(key=INI_KEY, var_name="enable_all", default=True, section="Configuration"))
            new_enable_all = ImGui.toggle_icon_button(
                (IconsFontAwesome5.ICON_TOGGLE_ON if e_all else IconsFontAwesome5.ICON_TOGGLE_OFF) + "##widget_disable",
                e_all,
                button_width
            )

            if new_enable_all != e_all:
                IniManager().set(key= INI_KEY, var_name="enable_all", value=new_enable_all, section="Configuration")
                IniManager().save_vars(INI_KEY)

            widget_manager.enable_all = new_enable_all


            ImGui.show_tooltip(f"{("Run" if not widget_manager.enable_all else "Pause")} all widgets")
            
            PyImGui.same_line(0, 5)
            show_widget_ui = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_EYE if widget_manager.show_widget_ui else IconsFontAwesome5.ICON_EYE_SLASH) + "##Show Widget UIs", widget_manager.show_widget_ui, button_width)
            if show_widget_ui != widget_manager.show_widget_ui:
                widget_manager.set_widget_ui_visibility(show_widget_ui)
            ImGui.show_tooltip(f"{("Show" if not widget_manager.show_widget_ui else "Hide")} all widget UIs")
            
            PyImGui.same_line(0, 5)
            pause_non_env = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_PAUSE if widget_manager.pause_optional_widgets else IconsFontAwesome5.ICON_PLAY) + "##Pause Non-Env Widgets", not widget_manager.pause_optional_widgets, button_width)
            if pause_non_env != (not widget_manager.pause_optional_widgets):
                if not widget_manager.pause_optional_widgets:
                    widget_manager.pause_widgets()
                else:
                    widget_manager.resume_widgets()
                    
                own_email = Player.GetAccountEmail()
                for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
                    if acc.AccountEmail == own_email:
                        continue
                    
                    GLOBAL_CACHE.ShMem.SendMessage(own_email, acc.AccountEmail, SharedCommandType.PauseWidgets if widget_manager.pause_optional_widgets else SharedCommandType.ResumeWidgets)
                
            ImGui.show_tooltip(f"{("Pause" if not widget_manager.pause_optional_widgets else "Resume")} all optional widgets")
            
            PyImGui.push_item_width(-1)
            changed, widget_filter = ImGui.search_field("##WidgetFilter", widget_filter)
            PyImGui.pop_item_width()
            if changed:
                filter_widgets(widget_filter)
                
            ImGui.separator()
            
            style = ImGui.get_style()
            style.DisabledAlpha.push_style_var(0.4)
            if not filtered_widgets:
                draw_node(INI_KEY, tree)
            else:
                flags = (
                    PyImGui.TableFlags.Borders |
                    PyImGui.TableFlags.NoSavedSettings |
                    PyImGui.TableFlags.ScrollY
                )
                
                height = min(PyImGui.get_io().display_size_y / 3.0, len(filtered_widgets) * 34 )
                
                if ImGui.begin_table("#filtered widgets", 2, flags, width=-1, height=height):
                    PyImGui.table_setup_column("Widget", PyImGui.TableColumnFlags.WidthStretch, 1.0)
                    PyImGui.table_setup_column("Cfg", PyImGui.TableColumnFlags.WidthFixed, 30.0)
                    #PyImGui.table_headers_row()

                    for widget in filtered_widgets:
                        if not widget:
                            continue
                        
                        draw_widget(widget)

                    ImGui.end_table()
            style.TextDisabled.pop_color()
                
        ImGui.End(INI_KEY)
    
def update():
    pass

def main():
    global INI_KEY
    
    if not INI_KEY:
        if not os.path.exists(INI_PATH):
            os.makedirs(INI_PATH, exist_ok=True)

        INI_KEY = IniManager().ensure_global_key(
            INI_PATH,
            INI_FILENAME
        )
        
        if not INI_KEY: return
        
        # widget_manager.MANAGER_INI_KEY = INI_KEY
        
        # widget_manager.discover()
        # _add_config_vars()
        IniManager().load_once(INI_KEY)

        # FIX 1: Explicitly load the global manager state into the handler
        widget_manager.enable_all = bool(IniManager().get(key=INI_KEY, var_name="enable_all", default=False, section="Configuration"))
        widget_manager._apply_ini_configuration()
        
        create_tree()
            
    
    
# These functions need to be available at module level
__all__ = ['on_enable', 'on_disable', 'configure', 'draw', 'update', 'main']

if __name__ == "__main__":
    main()
