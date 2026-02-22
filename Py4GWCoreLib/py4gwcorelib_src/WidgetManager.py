from typing import Callable
from types import ModuleType
import traceback
import Py4GW
import PyImGui
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
import importlib.util
import os
import sys
import PyImGui
import PyCallback
from dataclasses import dataclass, field
from types import ModuleType
from typing import Callable, Optional

_profiling_registry = None

def _get_profiling():
    global _profiling_registry
    if _profiling_registry is None:
        from Py4GWCoreLib.py4gwcorelib_src.Profiling import ProfilingRegistry
        _profiling_registry = ProfilingRegistry()
    return _profiling_registry

#region widget
@dataclass
class Widget:
    """
    Widget data class with callback extraction in __post_init__
    """
    # Core identity (passed to __init__)
    name: str                     # "folder/script_name"
    plain_name: str = ""          # script without extension
    widget_path: str = ""         # folder relative path (no script)
    script_path: str = ""         # script full path
    
    #callback data
    update_callback_id: int = 0
    draw_callback_id: int = 0   
    main_callback_id: int = 0
    
    #Extra_execution data
    has_update_property: bool = False
    has_draw_property: bool = False
    has_main_property: bool = False
    has_configure_property: bool = False
    has_tooltip_property: bool = False
    
    # INI configuration (passed to __init__)
    ini_key: str = ""             # "" or valid key
    ini_path: str = ""            # "Widgets/folder"
    ini_filename: str = ""        # "script_name.ini"
        
    # Extracted callbacks (will be populated in __post_init__)
    main: Optional[Callable] = field(default=None, init=False)
    configure: Optional[Callable] = field(default=None, init=False)
    update: Optional[Callable] = field(default=None, init=False)
    draw: Optional[Callable] = field(default=None, init=False)
    tooltip: Optional[Callable] = field(default=None, init=False)
    minimal: Optional[Callable] = field(default=None, init=False)
    
    on_enable: Optional[Callable] = field(default=None, init=False)
    on_disable: Optional[Callable] = field(default=None, init=False)
    
    module: Optional[ModuleType] = field(default=None, init=False, repr=False)
    __enabled: bool = field(default=False, init=False,)
    __configuring: bool = field(default=False, init=False)
    
    @property
    def enabled(self) -> bool:
        """Check if the widget is enabled"""
        return self.__enabled
    
    @property
    def configuring(self) -> bool:
        """Check if the widget is in configuring state"""
        return self.__configuring
    
    def load_module(self) -> bool:
        """Load the module if not already loaded"""
        if self.module is not None:
            return True  # Already loaded
        
        if not os.path.isfile(self.script_path):
            Py4GW.Console.Log("WidgetManager", f"Widget script not found: {self.script_path}", Py4GW.Console.MessageType.Error)
            return False
        
        unique_name = f"py4gw_widget_{self.name.replace('/', '_').replace('.', '_')}"
        
        spec = importlib.util.spec_from_file_location(unique_name, self.script_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Invalid module spec: {self.script_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[unique_name] = module
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            del sys.modules[unique_name]
            self.disable()
            Py4GW.Console.Log("WidgetManager", f"Failed to load widget module '{self.name}': {e}", Py4GW.Console.MessageType.Error)
            return False
        
        self.module = module
        
        if self.module:                
            # --- capability flags (what exists in the widget module) ---
            self.has_main_property      = callable(getattr(self.module, "main", None))
            self.has_configure_property = callable(getattr(self.module, "configure", None))
            self.has_update_property    = callable(getattr(self.module, "update", None))
            self.has_draw_property      = callable(getattr(self.module, "draw", None))
            self.has_tooltip_property   = callable(getattr(self.module, "tooltip", None))
            
            # Extract main callback
            self.main = getattr(self.module, "main", None) if self.has_main_property else None
            self.configure = getattr(self.module, "configure", None) if self.has_configure_property else None
            self.update = getattr(self.module, "update", None) if self.has_update_property else None
            self.draw = getattr(self.module, "draw", None) if self.has_draw_property else None
            self.tooltip = getattr(self.module, "tooltip", None) if self.has_tooltip_property else None
            self.minimal = getattr(self.module, "minimal", None) if callable(getattr(self.module, "minimal", None)) else None
            self.on_enable = getattr(self.module, "on_enable", None) if callable(getattr(self.module, "on_enable", None)) else None
            self.on_disable = getattr(self.module, "on_disable", None) if callable(getattr(self.module, "on_disable", None)) else None
            self.optional = getattr(self.module, 'OPTIONAL', True) if hasattr(self.module, 'OPTIONAL') else True
            
            self.RegisterCallbacks()
            self.PauseCallbacks()  # Start paused until explicitly enabled
            
        return True
    
    def set_configuring(self, state: bool):
        """Set configuring state"""
        self.__configuring = state
        
    def enable_configuring(self):
        """Enable configuring state"""
        self.set_configuring(True)
        
    def disable_configuring(self):  
        """Disable configuring state"""
        self.set_configuring(False)
        
    def PauseCallbacks(self):
        """Pause callbacks by id if they exist"""
        self.RegisterCallbacks()  # Ensure callbacks are registered before trying to pause
        if self.update_callback_id:
            PyCallback.PyCallback.PauseById(self.update_callback_id)
        if self.draw_callback_id:
            PyCallback.PyCallback.PauseById(self.draw_callback_id)
        if self.main_callback_id:
            PyCallback.PyCallback.PauseById(self.main_callback_id)
            
    def ResumeCallbacks(self):
        """Resume callbacks by id if they exist"""
        self.RegisterCallbacks()  # Ensure callbacks are registered before trying to resume
        if self.update_callback_id:
            PyCallback.PyCallback.ResumeById(self.update_callback_id)
        if self.draw_callback_id:
            PyCallback.PyCallback.ResumeById(self.draw_callback_id)
        if self.main_callback_id:
            PyCallback.PyCallback.ResumeById(self.main_callback_id)
            
    def RegisterCallbacks(self):
        """Register callbacks if they exist in the module"""
        def wrap_profiler(key: str, fn: Callable):
            # We return a NEW function (lambda) that the C++ Callback system 
            # will store and execute every frame.
            def callback_wrapper():
                profiling = _get_profiling()
                if profiling.enabled:
                    # Executes fn() inside the profiling scope
                    return profiling.runcall_scope("widgets", f"{self.name}:{key}", fn)
                else:
                    # Executes fn() normally
                    return fn()
            
            return callback_wrapper
       
        if self.module is None:
            return
        
        # 1. Update Callback (Logic Loop)
        if self.has_update_property and self.update is not None and self.update_callback_id == 0:
            self.update_callback_id = PyCallback.PyCallback.Register(
                self.name,
                PyCallback.Phase.Update,
                wrap_profiler("update", self.update), # Pass the wrapper
                priority=99,
                context=PyCallback.Context.Update
            )
            
        # 2. Draw Callback (Visual Loop)
        if self.has_draw_property and self.draw is not None and self.draw_callback_id == 0:
            self.draw_callback_id = PyCallback.PyCallback.Register(
                self.name,
                PyCallback.Phase.Update,
                wrap_profiler("draw", self.draw), # Pass the wrapper
                priority=99,
                context=PyCallback.Context.Draw
            )
            
        # 3. Main Callback (System Loop)
        if self.has_main_property and self.main is not None and self.main_callback_id == 0:
            self.main_callback_id = PyCallback.PyCallback.Register(
                self.name,
                PyCallback.Phase.Update,
                wrap_profiler("main", self.main), # Pass the wrapper
                priority=99,
                context=PyCallback.Context.Main
            )
        
    def disable(self):
        """Disable the widget"""
        self.PauseCallbacks()
        if self.__enabled:
            if self.module is not None:
                try:
                    if self.on_disable:
                        self.on_disable()
                    
                except Exception as e:
                    Py4GW.Console.Log("WidgetManager", f"Error during on_disable of widget {self.name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetManager", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
                
            self.__enabled = False
        
    def enable(self):
        """Enable the widget"""
        
        #ensure callback
        self.ResumeCallbacks()

        if self.enabled and self.module is not None: 
            return  # Already enabled
        
        # enable widget only if module loads successfully
        self.__enabled = self.load_module()
        
        if self.enabled:
            try:
                if self.on_enable:
                    self.on_enable()
                
            except Exception as e:
                Py4GW.Console.Log("WidgetManager", f"Error during on_enable of widget {self.name}: {str(e)}", Py4GW.Console.MessageType.Error)
                Py4GW.Console.Log("WidgetManager", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
                
    def __post_init__(self):
        """Extract callbacks from module after initialization"""      
        
        # --- capability flags (what exists in the widget module) ---
        self.has_main_property      = False
        self.has_configure_property = False
        self.has_update_property    = False
        self.has_draw_property      = False
        self.has_tooltip_property   = False
        
        # Extract main callback
        self.main : Optional[Callable] = None
        self.configure : Optional[Callable] = None
        self.update : Optional[Callable] = None
        self.draw : Optional[Callable] = None
        self.tooltip : Optional[Callable] = None
        self.minimal : Optional[Callable] = None
        self.on_enable : Optional[Callable] = None
        self.on_disable : Optional[Callable] = None
        self.optional = True  
        
        self.load_module()
        
            
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
    
    def __getitem__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")
    
    def __setitem__(self, key, value):
        if key in self.__dict__:
            self.__dict__[key] = value
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")
   
   
class WidgetConfigVars:
    def __init__(self, widget_id: str, section: str, var_name: str):
        self.widget_id = widget_id
        self.section = section
        self.var_name = var_name
            
         
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
            
        self.MANAGER_INI_KEY:str = ""
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
        self.config_vars: list[WidgetConfigVars] = []
        
        
        
    # Properties
    @property
    def pause_optional_widgets(self):
        return self.pause_optionals
    
    @property
    def show_widget_ui(self):
        return self.show_ui
    
    #region internal helpers
    def _log_error(self, message: str):
        Py4GW.Console.Log("WidgetManager", message, Py4GW.Console.MessageType.Error)
        
    def _log_success(self, message: str):
        Py4GW.Console.Log("WidgetManager", message, Py4GW.Console.MessageType.Info)
        
    def _get_config_var(self, widget_name: str, var_name: str) -> Optional[WidgetConfigVars]:
        for cv in self.config_vars:
            if cv.widget_id == widget_name and cv.var_name == var_name:
                return cv
        return None
    
    def _widget_var(self, widget_id: str, suffix: str) -> str:
        """Returns the unique variable name for IniManager lookup"""
        return f"{widget_id}__{suffix}"
    
    def _get_widget_by_plain_name(self, plain_name: str) -> Optional[Widget]:
        for widget in self.widgets.values():
            if widget.plain_name == plain_name:
                return widget
        return None
        
    def _set_widget_state(self, INI_KEY, name: str, state: bool):
        widget = self._get_widget_by_plain_name(name)
        if not widget:
            Py4GW.Console.Log("WidgetHandler", f"Widget '{name}' not found", Py4GW.Console.MessageType.Warning)
            return
        
        if state:
            widget.enable()
        else:
            widget.disable()
        
        widget_id = widget.name  # full id: "folder/file.py"
        v_enabled = self._widget_var(widget_id, "enabled")  # "folder/file.py__enabled"

        cv = self._get_config_var(widget_id, v_enabled)

        if cv:
            # Correct order: key, section, var_name, value
            IniManager().set(key=INI_KEY, section=cv.section, var_name=cv.var_name, value=state)
            IniManager().save_vars(INI_KEY)
                        

        
    # --------------------------------------------
    # region discovery
           
    def discover(self):
        if self.discovered:
            return
        
        """Phase 0: Unload currently enabled widgets"""
        for widget in self.widgets.values():
            if widget.enabled:
                widget.disable()
                                
        """Phase 1: Discover widgets without INI configuration"""
        self.widgets.clear()
        
        try:
            self._scan_widget_folders()
            self.discovered = True
        except Exception as e:
            self._log_error(f"Discovery failed: {e}")
            raise
    
    
    def _scan_widget_folders(self):
        """Find .widget folders and load .py files throughout the entire tree"""
        if not os.path.isdir(self.widgets_path):
            raise FileNotFoundError(f"Widgets folder missing: {self.widgets_path}")
        
        for current_dir, dirs, files in os.walk(self.widgets_path):
            # Check if this specific folder is marked as a widget container
            if ".widget" in files:
                for py_file in [f for f in files if f.endswith(".py")]:
                    self._load_widget_module(current_dir, py_file)

    def _load_widget_module(self, folder: str, filename: str):
        """Load a widget module without INI configuration"""
        # Create widget ID
        rel_folder = os.path.relpath(folder, self.widgets_path)
        widget_id = f"{rel_folder}/{filename}" if rel_folder != "." else filename

        plain = os.path.splitext(filename)[0]
        widget_path = "" if rel_folder == "." else rel_folder.replace("\\", "/")

                
        if widget_id in self.widgets:
            return
        
        script_path = os.path.join(folder, filename)
        
        try:
            # 1. Create Widget with EMPTY INI data
            widget = Widget(
                name=widget_id,
                plain_name=plain,
                widget_path=widget_path,
                script_path=script_path,
                ini_key="",           # Empty - will be set later
                ini_path="",          # Empty - will be set later  
                ini_filename="",      # Empty - will be set later                
            )
            
            # 3. Register
            self.widgets[widget_id] = widget
            
            #4. Ini handling (SECTION PER WIDGET)
            self.config_vars.append(WidgetConfigVars(
                widget_id=widget_id,
                section=f"Widget:{widget_id}",
                var_name=f"{widget_id}__enabled"
            ))
            self.config_vars.append(WidgetConfigVars(
                widget_id=widget_id,
                section=f"Widget:{widget_id}",
                var_name=f"{widget_id}__optional"
            ))                    

            cv = self._get_config_var(widget.name, self._widget_var(widget.name, "enabled"))
            
            enabled = bool(IniManager().get(key=self.MANAGER_INI_KEY, section=cv.section, var_name=cv.var_name, default=False)) if cv else False
            if enabled:
                widget.enable()
                
            #keep logging minimal
            #self._log_success(f"Discovered: {widget_id}")
            
        except Exception as e:
            self._log_error(f"Failed to discover {widget_id}: {e}")
                            
                
    def _apply_ini_configuration(self):
        """Apply saved enabled states and enforce System widget activation"""
        for wid, w in self.widgets.items():
            vname = self._widget_var(wid, "enabled")
            section = f"Widget:{wid}"
            
            # 1. Read the current state from IniManager (which just loaded from disk)
            enabled = bool(IniManager().get(key=self.MANAGER_INI_KEY, section=section, var_name=vname, default=False))
            
            # 2. THE FORCE: Check if this is a System widget section
            is_system = "Widget:System" in section
            
            if is_system:
                # If it's system but the disk/ini said False, we override it right now
                if not enabled:
                    # Py4GW.Console.Log("WidgetManager", f"Forcing System Widget: {wid}", Py4GW.Console.MessageType.Info)
                    enabled = True
                    # Update IniManager memory so it stays synced
                    IniManager().set(key=self.MANAGER_INI_KEY, section=section, var_name=vname, value=True)
                    # Note: No need to save_vars here unless you want to fix the file immediately; 
                    # the next global save will persist this.
                    self._log_success(f"Enforcing System Widget Enabled: {wid}")
            
            # 3. Final Activation
            if enabled:
                w.enable()
                
            
    #region UI       
    def draw_node(self, INI_KEY: str, node: dict, depth: int = 0):
        style = ImGui.get_style()
        widget_manager = self 

        for key, value in sorted(node.items()):
            # Leaf: render widgets table
            if key == "__widgets__":
                table_id = f"WidgetsTable##tree_depth_{depth}"
                PyImGui.set_next_item_width(-1)  # take full available width

                flags = (
                    PyImGui.TableFlags.Borders |
                    PyImGui.TableFlags.SizingStretchProp |
                    PyImGui.TableFlags.NoSavedSettings
                )

                if ImGui.begin_table(table_id, 2, flags):
                    PyImGui.table_setup_column("Widget", PyImGui.TableColumnFlags.WidthStretch, 1.0)
                    PyImGui.table_setup_column("Cfg", PyImGui.TableColumnFlags.WidthFixed, 40.0)
                    #PyImGui.table_headers_row()

                    for widget_id in value:
                        widget = widget_manager.widgets.get(widget_id)
                        if not widget:
                            continue

                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)

                        display_name = widget.plain_name

                        label = f"{display_name}##{widget_id}"
                        
                        v_enabled = self._widget_var(widget_id, "enabled")
                        # Define the section once to ensure consistency
                        section_name = f"Widget:{widget_id}"

                        # FIXED: Added the section parameter to the get call
                        val = bool(IniManager().get(INI_KEY, v_enabled, False, section=section_name))
                        new_enabled = ImGui.checkbox(label, val)
                        if PyImGui.is_item_hovered():
                            if widget.has_tooltip_property:
                                try:
                                    if widget.tooltip:
                                        widget.tooltip()
                                except Exception as e:
                                    Py4GW.Console.Log("WidgetHandler", f"Error during tooltip of widget {widget_id}: {str(e)}", Py4GW.Console.MessageType.Error)
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
                        
                        if widget.has_configure_property:
                            configuring = ImGui.toggle_icon_button(
                                IconsFontAwesome5.ICON_COG + f"##Configure{widget_id}",
                                widget.configuring
                            )
                            if configuring != widget.configuring:
                                widget.set_configuring(configuring)
                                
                            if PyImGui.is_item_hovered():
                                PyImGui.show_tooltip("Configure Widget")
                        else:
                            PyImGui.table_set_column_index(1)
                            PyImGui.text_disabled(IconsFontAwesome5.ICON_COG)
                            if PyImGui.is_item_hovered():
                                PyImGui.show_tooltip("No config available")

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
                self.draw_node(INI_KEY, value, depth + 1)
                if depth > 0:
                    ImGui.tree_pop()
                    
    def PauseAllWidgets(self):
        for widget in self.widgets.values():
            if widget.enabled:
                widget.disable()
                
    def ResumeAllWidgets(self):
        for widget in self.widgets.values():
            if not widget.enabled:
                widget.enable()
            
    def draw_ui(self, INI_KEY: str):
        if ImGui.icon_button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets", 40):
            Py4GW.Console.Log("Widget Manager", "Reloading Widgets...", Py4GW.Console.MessageType.Info)
            
            
            self.widget_initialized = False
            self.discovered = False
            self.discover()
            self.widget_initialized = True    
                
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
            if new_enable_all:
                self.ResumeAllWidgets()
            else:
                self.PauseAllWidgets()    
            

        self.enable_all = new_enable_all


        ImGui.show_tooltip(f"{("Run" if not self.enable_all else "Pause")} all widgets")
        
        PyImGui.same_line(0, 5)
        show_widget_ui = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_EYE if self.show_widget_ui else IconsFontAwesome5.ICON_EYE_SLASH) + "##Show Widget UIs", self.show_widget_ui, 40)
        if show_widget_ui != self.show_widget_ui:
            self.set_widget_ui_visibility(show_widget_ui)
        ImGui.show_tooltip(f"{("Show" if not self.show_widget_ui else "Hide")} all widget UIs")
        
        PyImGui.same_line(0, 5)
        pause_non_env = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_PAUSE if self.pause_optional_widgets else IconsFontAwesome5.ICON_PLAY) + "##Pause Non-Env Widgets", not self.pause_optional_widgets, 40)
        if pause_non_env != (not self.pause_optional_widgets):
            if not self.pause_optional_widgets:
                self.pause_widgets()
            else:
                self.resume_widgets()
                
            own_email = Player.GetAccountEmail()
            for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
                if acc.AccountEmail == own_email:
                    continue
                
                GLOBAL_CACHE.ShMem.SendMessage(own_email, acc.AccountEmail, SharedCommandType.PauseWidgets if self.pause_optional_widgets else SharedCommandType.ResumeWidgets)
            
        ImGui.show_tooltip(f"{("Pause" if not self.pause_optional_widgets else "Resume")} all optional widgets")
        ImGui.separator()
        
        # ------------------------------------------------------------
        # Folder-based Widgets (TREE UI)
        # ------------------------------------------------------------
        tree: dict = {}

        for widget_id, widget in self.widgets.items():
            folder = widget.widget_path  # "A/B/C" or ""
            node = tree

            if folder:
                for part in folder.split("/"):
                    node = node.setdefault(part, {})

            node.setdefault("__widgets__", []).append(widget_id)
            
        self.draw_node(INI_KEY, tree)
        
    def execute_enabled_widgets_update(self):
        profiling = _get_profiling()
        profiling_enabled = profiling.enabled
        pause_optional = self.pause_optional_widgets

        for widget_name, widget_info in self.widgets.items():
            if not widget_info.enabled:
                continue

            if pause_optional and widget_info.optional:
                continue

            if widget_info.update is not None:
                try:
                    if profiling_enabled:
                        profiling.runcall_scope("widgets", f"{widget_name}:update", widget_info.update)
                    else:
                        widget_info.update()
                except Exception as e:
                    Py4GW.Console.Log("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

    def execute_enabled_widgets_draw(self):
        profiling = _get_profiling()
        profiling_enabled = profiling.enabled
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
                    if profiling_enabled:
                        profiling.runcall_scope("widgets", f"{widget_name}:minimal", widget_info.minimal)
                    else:
                        widget_info.minimal()
                except Exception as e:
                    Py4GW.Console.Log("WidgetHandler", f"Error executing minimal of widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

            if pause_optional and widget_info.optional:
                continue

            if widget_info.draw is not None:
                try:
                    if profiling_enabled:
                        profiling.runcall_scope("widgets", f"{widget_name}:draw", widget_info.draw)
                    else:
                        widget_info.draw()
                except Exception as e:
                    Py4GW.Console.Log("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

        if not ui_enabled:
            style.Alpha = alpha
            style.Push()

    def execute_enabled_widgets_main(self):
        profiling = _get_profiling()
        profiling_enabled = profiling.enabled
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
                    if profiling_enabled:
                        profiling.runcall_scope("widgets", f"{widget_name}:minimal", widget_info.minimal)
                    else:
                        widget_info.minimal()
                except Exception as e:
                    Py4GW.Console.Log("WidgetHandler", f"Error executing minimal of widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

            if pause_optional and widget_info.optional:
                continue

            if widget_info.main is not None:
                try:
                    if profiling_enabled:
                        profiling.runcall_scope("widgets", f"{widget_name}:main", widget_info.main)
                    else:
                        widget_info.main()
                except Exception as e:
                    Py4GW.Console.Log("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

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
                Py4GW.Console.Log("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
      
      
    #region  Public API
    def set_widget_ui_visibility(self, visible: bool):
        self.show_ui = visible
        
    def pause_widgets(self):
        self.pause_optionals = True
        
    def resume_widgets(self):
        self.pause_optionals = False
    
    def is_widget_enabled(self, name: str) -> bool:
        widget = self._get_widget_by_plain_name(name)
        return bool(widget and widget.enabled)

    def list_enabled_widgets(self) -> list[str]:
        return [name for name, info in self.widgets.items() if info.enabled]
    
    def enable_widget(self, name: str):
        self._set_widget_state(self.MANAGER_INI_KEY,name, True)

    def disable_widget(self, name: str):
        self._set_widget_state(self.MANAGER_INI_KEY,name, False)
        
    def set_widget_configuring(self, name: str, value: bool = True):
        widget = self._get_widget_by_plain_name(name)
        if not widget:
            Py4GW.Console.Log("WidgetHandler", f"Widget '{name}' not found", Py4GW.Console.MessageType.Warning)
            return
        widget.set_configuring(value)
        
    def get_widget_info(self, name: str) -> Widget | None:
        # 1) direct full id lookup
        w = self.widgets.get(name, None)
        if w:
            return w

        # 2) fallback to plain_name lookup
        return self._get_widget_by_plain_name(name)

_widget_handler = WidgetHandler()

def get_widget_handler() -> WidgetHandler:
    return _widget_handler
