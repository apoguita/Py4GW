
from typing import Callable
from types import ModuleType
import traceback
import Py4GW
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
import importlib.util
import os
import types
import sys
import PyImGui
from dataclasses import dataclass, field
from types import ModuleType
from typing import Callable, Optional

module_name = "Widget Manager"

#region widget
@dataclass
class Widget:
    """
    Widget data class with callback extraction in __post_init__
    """
    # Core identity (passed to __init__)
    name: str                     # "folder/script_name"
    module: ModuleType            # Loaded Python module
    
    # INI configuration (passed to __init__)
    ini_key: str = ""             # "" or valid key
    ini_path: str = ""            # "Widgets/folder"
    ini_filename: str = ""        # "script_name.ini"
    
    # Runtime state (defaults)
    enabled: bool = False
    configuring: bool = False
    optional: bool = True
    
    # Extracted callbacks (will be populated in __post_init__)
    main: Optional[Callable] = field(default=None, init=False)
    minimal: Optional[Callable] = field(default=None, init=False)
    configure: Optional[Callable] = field(default=None, init=False)
    on_enable: Optional[Callable] = field(default=None, init=False)
    on_disable: Optional[Callable] = field(default=None, init=False)
    
    def __post_init__(self):
        """Extract callbacks from module after initialization"""
        # Extract main callback
        main_func = getattr(self.module, "main", None)
        if callable(main_func):
            self.main = main_func
        
        # Extract minimal callback
        minimal_func = getattr(self.module, "minimal", None)
        if callable(minimal_func):
            self.minimal = minimal_func
        
        # Extract configure callback
        configure_func = getattr(self.module, "configure", None)
        if callable(configure_func):
            self.configure = configure_func
        
        # Extract on_enable callback
        on_enable_func = getattr(self.module, "on_enable", None)
        if callable(on_enable_func):
            self.on_enable = on_enable_func
        
        # Extract on_disable callback
        on_disable_func = getattr(self.module, "on_disable", None)
        if callable(on_disable_func):
            self.on_disable = on_disable_func
        
        # Set optional flag from module if not already set
        if hasattr(self.module, 'OPTIONAL'):
            self.optional = bool(self.module.OPTIONAL)
            
    @property
    def folder(self) -> str:
        """Extract folder path from name"""
        if '/' in self.name:
            return self.name.rsplit('/', 1)[0]
        return ""
    
    @property  
    def script_name(self) -> str:
        """Extract script name from name"""
        if '/' in self.name:
            return self.name.rsplit('/', 1)[1]
        return self.name
    
    @property
    def can_save(self) -> bool:
        """Check if widget can save (has INI key)"""
        return bool(self.ini_key)
    
    @property
    def needs_ini_key(self) -> bool:
        """Check if widget needs INI key resolved"""
        # FIXED: Your logic was inverted
        return not self.ini_key and bool(self.ini_path) and bool(self.ini_filename)
    
    @property
    def is_global(self) -> bool:
        """Check if widget is global (works without account)"""
        return bool(getattr(self.module, 'GLOBAL', False))
    
    
#region widget handler
class WidgetHandler:
    _instance = None
    _widgets_folder = "Widgets"
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, widgets_path=None):
        # Singleton guard
        if hasattr(self, "_initialized"):
            return
            
        # Path resolution
        if widgets_path:
            self.widgets_path = os.path.abspath(widgets_path)
        else:
            base_dir = Py4GW.Console.get_projects_path()
            self.widgets_path = os.path.join(base_dir, self._widgets_folder)
            
        self.MANAGER_INI_KEY = ""
        self.MANAGER_INI_PATH = "Widgets/WidgetManager"
        self.MANAGER_INI_FILENAME = "WidgetManager.ini"
        self.MANAGER_VARS_ADDED = False
        
        # Core state
        self.widgets: dict[str, Widget] = {}
        self.show_ui = True
        self.pause_optionals = False
        self.run_once = False
        self.enable_all = True
        
        self.discovered = False
        self.widget_initialized = False
        self._initialized = True
        
    # Properties
    @property
    def pause_optional_widgets(self):
        return self.pause_optionals
    
    @property
    def show_widget_ui(self):
        return self.show_ui
    
    # Public API
    def _widget_section(self, widget_id: str) -> str:
        return f"Widget:{widget_id}"

    def _widget_var(self, widget_id: str, name: str) -> str:
        return f"{widget_id}__{name}"


    def set_widget_ui_visibility(self, visible: bool):
        self.show_ui = visible
        
    def pause_widgets(self):
        self.pause_optionals = True
        
    def resume_widgets(self):
        self.pause_optionals = False
        
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
            
        IniManager().set(self.MANAGER_INI_KEY, "widget_enabled", widget.enabled, name)
        IniManager().save_vars(self.MANAGER_INI_KEY)
        
    def enable_widget(self, name: str):
        self._set_widget_state(name, True)

    def disable_widget(self, name: str):
        self._set_widget_state(name, False)
        
    def _log_success(self, message: str):
        ConsoleLog("WidgetManager", message, Py4GW.Console.MessageType.Info)
    
    def _log_error(self, message: str):
        ConsoleLog("WidgetManager", message, Py4GW.Console.MessageType.Error)
        
    def is_widget_enabled(self, name: str) -> bool:
        widget = self.widgets.get(name)
        return bool(widget and widget.enabled)
    
    def list_enabled_widgets(self) -> list[str]:
        return [name for name, info in self.widgets.items() if info.enabled]
        
    # --------------------------------------------
    # Ini management helpers
    
    def _ensure_manager_key(self) -> str:
        """Get or create GLOBAL INI key for widget manager (standard pattern)"""
        if not self.MANAGER_INI_KEY:
            # GLOBAL key - works without account
            self.MANAGER_INI_KEY = IniManager().ensure_global_key(self.MANAGER_INI_PATH, self.MANAGER_INI_FILENAME)
        return self.MANAGER_INI_KEY
        
    def _add_manager_vars(self):
        """Add widget manager INI variables (standard pattern)"""
        key = self._ensure_manager_key()
        if not key:
            return
        
        # Declare manager variables (once)
        IniManager().add_bool(key, "enable_all", "Window config", "enable_all", default=True)
        
    def _load_ini_manager_once(self):
        """Load widget manager state from INI (standard pattern - runs once)"""
        
        if not self.MANAGER_INI_KEY:
            self.MANAGER_INI_KEY = IniManager().ensure_global_key(self.MANAGER_INI_PATH, self.MANAGER_INI_FILENAME)
            if not self.MANAGER_INI_KEY:
                return
            
            # Add variables (once)
            self._add_manager_vars()
            
            # Load values (once)
            IniManager().load_once(self.MANAGER_INI_KEY)
        
        # Apply loaded values to widget manager
        self.enable_all = bool(IniManager().get(self.MANAGER_INI_KEY, "enable_all", True))
        
    def save_manager_state(self):
        """Save widget manager state to GLOBAL INI"""
        key = self._ensure_manager_key()
        if not key:
            return
        
        IniManager().set(key, "enable_all", self.enable_all)
        IniManager().save_vars(key)
        
    # --------------------------------------------
    # Widget discovery
    def discover(self):
        """Phase 1: Discover widgets without INI configuration"""
        self.widgets.clear()
        
        try:
            self._scan_widget_folders()
        except Exception as e:
            self._log_error(f"Discovery failed: {e}")
            raise
 
    def _scan_widget_folders(self):
        """Find .widget folders and load .py files"""
        if not os.path.isdir(self.widgets_path):
            raise FileNotFoundError(f"Widgets folder missing: {self.widgets_path}")
        
        for current_dir, dirs, files in os.walk(self.widgets_path):
            if ".widget" not in files:
                continue
                
            for py_file in [f for f in files if f.endswith(".py")]:
                self._load_widget_module(current_dir, py_file)
            
            dirs.clear()
            
    def _load_widget_module(self, folder: str, filename: str):
        """Load a widget module without INI configuration"""
        # Create widget ID
        rel_folder = os.path.relpath(folder, self.widgets_path)
        widget_id = f"{rel_folder}/{filename}" if rel_folder != "." else filename
        
        if widget_id in self.widgets:
            return
        
        script_path = os.path.join(folder, filename)
        
        try:
            # 1. Load Python module only
            module = self._import_widget_module(script_path, widget_id)
            
            # 2. Create Widget with EMPTY INI data
            widget = Widget(
                name=widget_id,
                module=module,
                ini_key="",           # Empty - will be set later
                ini_path="",          # Empty - will be set later  
                ini_filename="",      # Empty - will be set later
                enabled=False,        # Default disabled
                optional=bool(getattr(module, "OPTIONAL", True))
            )
            
            # 3. Register
            self.widgets[widget_id] = widget
            
            #4. Ini handling (SECTION PER WIDGET)
            key = self._ensure_manager_key()
            if not key:
                return

            section = self._widget_section(widget_id)

            IniManager().add_bool(key, self._widget_var(widget_id, "enabled"), section, "enabled", default=False)
            IniManager().add_bool(key, self._widget_var(widget_id, "optional"), section, "optional", default=widget.optional)



            
            
            self._log_success(f"Discovered: {widget_id}")
            
        except Exception as e:
            self._log_error(f"Failed to discover {widget_id}: {e}")
            
    def _import_widget_module(self, script_path: str, widget_id: str) -> ModuleType:
        """Load Python module with unique name"""
        # Generate unique module name
        unique_name = f"py4gw_widget_{widget_id.replace('/', '_').replace('.', '_')}"
        
        spec = importlib.util.spec_from_file_location(unique_name, script_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Invalid module spec: {script_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[unique_name] = module
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            del sys.modules[unique_name]
            raise
        
        # Validate required functions
        if not hasattr(module, "main") or not callable(module.main):
            raise ValueError("Widget missing main() function")
        if not hasattr(module, "configure") or not callable(module.configure):
            raise ValueError("Widget missing configure() function")
        
        return module
    
    
    def draw_widget_ui(self, INI_KEY: str):
        style = ImGui.get_style()
        
        if ImGui.icon_button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets", 40):
            ConsoleLog(module_name, "Reloading Widgets...", Py4GW.Console.MessageType.Info)
            widget_manager.widget_initialized = False
            widget_manager.discover()
            widget_manager.widget_initialized = True        
        ImGui.show_tooltip("Reload all widgets")
        PyImGui.same_line(0, 5)

        e_all = bool(IniManager().get(INI_KEY, "enable_all", False))
        new_enable_all = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_TOGGLE_ON if widget_manager.enable_all else IconsFontAwesome5.ICON_TOGGLE_OFF) + "##widget_disable", e_all, 40)

        if new_enable_all != e_all:
                IniManager().set(INI_KEY, "enable_all", new_enable_all)
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

        # ------------------------------------------------------------
        # Folder-based Widgets (TREE UI)
        # ------------------------------------------------------------

        style = ImGui.get_style()

        # Build tree from widget paths
        tree: dict = {}

        for widget_id in widget_manager.widgets:
            #if "/" not in widget_id:
            #    continue

            parts = widget_id.split("/")
            node = tree
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node.setdefault("__widgets__", []).append(widget_id)


        def draw_node(node: dict, depth: int = 0):
            for key, value in sorted(node.items()):
                # Leaf: render widgets table
                if key == "__widgets__":
                    table_id = f"WidgetsTable##tree_depth_{depth}"
                    if ImGui.begin_table(table_id, 2, PyImGui.TableFlags.Borders):
                        for widget_id in value:
                            widget = widget_manager.widgets.get(widget_id)
                            if not widget:
                                continue

                            PyImGui.table_next_row()
                            PyImGui.table_set_column_index(0)

                            display_name = widget_id.split("/")[-1]

                            label = f"{display_name}##{widget_id}"
                            
                            v_enabled = self._widget_var(widget_id, "enabled")

                            val = bool(IniManager().get(INI_KEY, v_enabled, False))
                            new_enabled = ImGui.checkbox(label, val)

                            if new_enabled != val:
                                widget.enabled = new_enabled
                                IniManager().set(INI_KEY, v_enabled, new_enabled)
                                IniManager().save_vars(INI_KEY)


                            PyImGui.table_set_column_index(1)

                            # IMPORTANT: strong unique ImGui ID for config toggle too
                            widget.configuring = ImGui.toggle_icon_button(
                                IconsFontAwesome5.ICON_COG + f"##Configure{widget_id}",
                                widget.configuring
                            )

                        ImGui.end_table()
                    continue

                # Folder nodes
                if depth == 0:
                    # IMPORTANT: also make header id stable+unique
                    open_ = ImGui.collapsing_header(f"{key}##FolderHeader_{key}")
                else:
                    if style.Theme not in ImGui.Textured_Themes:
                        style.TextTreeNode.push_color((255, 200, 100, 255))

                    open_ = ImGui.tree_node(f"{key}##Tree_{depth}_{key}")

                    if style.Theme not in ImGui.Textured_Themes:
                        style.TextTreeNode.pop_color()

                if open_:
                    draw_node(value, depth + 1)
                    if depth > 0:
                        ImGui.tree_pop()


        draw_node(tree)

    def execute_enabled_widgets(self):
        style = ImGui.Selected_Style.pyimgui_style
        alpha = style.Alpha
        ui_enabled = self.show_widget_ui
        pause_optional = self.pause_optional_widgets

        if not ui_enabled:
            style.Alpha = 0.0
            style.Push()

        for widget_name, widget_info in self.widgets.items():
            if not widget_info.enabled:
                continue
 
            if widget_info.minimal is not None:
                try:
                    widget_info.minimal()
                except Exception as e:
                    ConsoleLog("WidgetHandler", f"Error executing minimal of widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

            if pause_optional and widget_info.optional:
                continue

            if widget_info.main is not None:
                try:
                    widget_info.main()
                except Exception as e:
                    ConsoleLog("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

        if not ui_enabled:
            style.Alpha = alpha
            style.Push()
        
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
 
#region main
widget_manager: WidgetHandler = WidgetHandler()

# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------
def main():
    # Global singleton
    widget_manager = WidgetHandler()
    
    try:
        if not widget_manager.discovered:
            # One-time INI initialization (like widget template)
            widget_manager._load_ini_manager_once()
            
            widget_manager.discover()
            widget_manager.discovered = True

        # now load everything once (manager + widgets)
        IniManager().load_once(widget_manager.MANAGER_INI_KEY)
        
        # manager var
        widget_manager.enable_all = bool(IniManager().get(widget_manager.MANAGER_INI_KEY, "enable_all", True))

        # apply per-widget enabled state from per-widget section
        for wid, w in widget_manager.widgets.items():
            w.enabled = bool(IniManager().get(widget_manager.MANAGER_INI_KEY, widget_manager._widget_var(wid, "enabled"), False))

        # Draw UI using GLOBAL INI key (always works)
        key = widget_manager._ensure_manager_key()
        if key and ImGui.Begin(ini_key=key, name="Widget Manager", flags=PyImGui.WindowFlags.AlwaysAutoResize):
            widget_manager.draw_widget_ui(key)  # Pass manager to UI
        ImGui.End(key)

        if widget_manager.enable_all:
            widget_manager.execute_enabled_widgets()
            widget_manager.execute_configuring_widgets()

    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, traceback.format_exc(), Py4GW.Console.MessageType.Error)

if __name__ == "__main__":
    main()