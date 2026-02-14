MODULE_NAME = "WidgetManagerV2"

import os
import traceback
import Py4GW
import PyImGui
from Py4GWCoreLib import ImGui, IniManager, Player
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler


class WidgetTreeNode:
    def __init__(self):
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
        return self.children[name]
    
    def is_hovered(self):
        return self.window_hovered or any(child.is_hovered() for child in self.children.values())
    
    def close(self):
        self.open = False
        for child in self.children.values():
            child.close()
    
widget_manager = get_widget_handler()
tree = WidgetTreeNode()

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
    desired_open_node: WidgetTreeNode | None = None

    window_pos = PyImGui.get_window_pos()
    window_size = PyImGui.get_window_size()

    for key, node in parent_node.children.items():
        node.pos = PyImGui.get_cursor_screen_pos()

        PyImGui.selectable(
            f"{key}##Selectable_{depth}_{key}",
            node.open,
            PyImGui.SelectableFlags.NoFlag,
            (0, 0)
        )

        node.hovered = PyImGui.is_item_hovered()

        if node.hovered:
            desired_open_node = node

    # fallback: keep previously open node if nothing hovered
    if desired_open_node is None:
        desired_open_node = next(
            (n for n in parent_node.children.values() if n.open),
            None
        )

    # enforce ONE open per depth
    for node in parent_node.children.values():
        node.open = (node is desired_open_node)

    if desired_open_node is None:
        return

    node = desired_open_node

    PyImGui.set_next_window_pos(
        (window_pos[0] + window_size[0] - 2, node.pos[1] - 2),
        PyImGui.ImGuiCond.Always
    )

    if PyImGui.begin(
        f"##Popup_{depth}_{id(node)}",
        False,
        PyImGui.WindowFlags.AlwaysAutoResize
        | PyImGui.WindowFlags.NoTitleBar
        | PyImGui.WindowFlags.NoMove
        | PyImGui.WindowFlags.NoSavedSettings
    ):

        # ---- recurse AFTER popup content ----
        draw_node(INI_KEY, node, depth + 1)
        
        # ---- widgets table ----
        if node.widgets:
            table_id = f"WidgetsTable##tree_depth_{depth}"
            PyImGui.set_next_item_width(-1)

            flags = (
                PyImGui.TableFlags.Borders
                | PyImGui.TableFlags.SizingStretchProp
                | PyImGui.TableFlags.NoSavedSettings
            )

            if ImGui.begin_table(table_id, 2, flags):
                PyImGui.table_setup_column("Widget", PyImGui.TableColumnFlags.WidthStretch, 1.0)
                PyImGui.table_setup_column("Cfg", PyImGui.TableColumnFlags.WidthFixed, 40.0)

                for widget_id in node.widgets:
                    widget = widget_manager.widgets.get(widget_id)
                    if not widget:
                        continue

                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)

                    label = f"{widget.plain_name}##{widget_id}"
                    v_enabled = widget_manager._widget_var(widget_id, "enabled")
                    section_name = f"Widget:{widget_id}"

                    val = bool(IniManager().get(INI_KEY, v_enabled, False, section=section_name))
                    new_val = ImGui.checkbox(label, val)

                    if new_val != val:
                        widget.enable() if new_val else widget.disable()
                        IniManager().set(INI_KEY, v_enabled, widget.enabled, section=section_name)
                        IniManager().save_vars(INI_KEY)

                    PyImGui.table_set_column_index(1)
                    if widget.has_configure_property:
                        ImGui.toggle_icon_button(
                            IconsFontAwesome5.ICON_COG + f"##cfg_{widget_id}",
                            widget.configuring
                        )
                    else:
                        PyImGui.text_disabled(IconsFontAwesome5.ICON_COG)

                ImGui.end_table()
                if PyImGui.is_item_hovered():
                    for node in node.children.values():
                        node.open = False

        node.window_hovered = PyImGui.is_window_hovered()

    PyImGui.end()
  
def create_tree():
    global tree, widget_manager
    
    for widget_id, widget in widget_manager.widgets.items():
        folder = widget.widget_path  # "A/B/C" or ""
        node = tree

        if folder:
            for part in folder.split("/"):
                node = node.get_child(part)

        node.widgets.append(widget_id)
    pass

def draw():    
    if not INI_KEY:
        return
            
    if INI_KEY:
        if ImGui.Begin(ini_key=INI_KEY, name="Widget Manager V2", flags=PyImGui.WindowFlags.AlwaysAutoResize):
            widgets = widget_manager.widgets
                                
            if ImGui.icon_button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets", 40):
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
                40
            )

            if new_enable_all != e_all:
                IniManager().set(key= INI_KEY, var_name="enable_all", value=new_enable_all, section="Configuration")
                IniManager().save_vars(INI_KEY)

            widget_manager.enable_all = new_enable_all


            ImGui.show_tooltip(f"{("Run" if not widget_manager.enable_all else "Pause")} all widgets")
            
            PyImGui.same_line(0, 5)
            show_widget_ui = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_EYE if widget_manager.show_widget_ui else IconsFontAwesome5.ICON_EYE_SLASH) + "##Show Widget UIs", widget_manager.show_widget_ui, 40)
            if show_widget_ui != widget_manager.show_widget_ui:
                widget_manager.set_widget_ui_visibility(show_widget_ui)
            ImGui.show_tooltip(f"{("Show" if not widget_manager.show_widget_ui else "Hide")} all widget UIs")
            
            PyImGui.same_line(0, 5)
            pause_non_env = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_PAUSE if widget_manager.pause_optional_widgets else IconsFontAwesome5.ICON_PLAY) + "##Pause Non-Env Widgets", not widget_manager.pause_optional_widgets, 40)
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
            ImGui.separator()
            draw_node(INI_KEY, tree)
            
            tree.window_hovered = PyImGui.is_window_hovered()
            
            if tree.is_hovered() == False :
                for node in tree.children.values():                    
                    node.close()
                
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
