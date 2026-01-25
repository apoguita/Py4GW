
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
    
    

class WidgetManager:
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
        
        # Core state
        self.widgets: dict[str, Widget] = {}
        self.show_ui = True
        self.pause_optionals = False
        self.run_once = False
        self.enable_all = True
        
        self.discovered = False
        self._initialized = True
        
    # Properties
    @property
    def pause_optional_widgets(self):
        return self.pause_optionals
    
    @property
    def show_widget_ui(self):
        return self.show_ui
    
    # Public API
    def set_widget_ui_visibility(self, visible: bool):
        self.show_ui = visible
        
    def pause_widgets(self):
        self.pause_optionals = True
        
    def resume_widgets(self):
        self.pause_optionals = False
        
    def _log_success(self, message: str):
        ConsoleLog("WidgetManager", message, Py4GW.Console.MessageType.Info)
    
    def _log_error(self, message: str):
        ConsoleLog("WidgetManager", message, Py4GW.Console.MessageType.Error)
        
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
        
        
        
#region legacy
class WidgetNode:
    def __init__(self, name: str, module: ModuleType, widget_data: dict,
                 ini_key: str, ini_path: str, ini_filename: str):
        self.name: str = name
        self.module: ModuleType = module
        self.configuring: bool = False

        # per-widget ini binding
        self.ini_key: str = ini_key
        self.ini_path: str = ini_path
        self.ini_filename: str = ini_filename

        # state (from widget INI, not Py4GW.ini)
        self.enabled: bool = bool(widget_data.get("enabled", False))
        self.optional: bool = bool(widget_data.get("optional", bool(module.__dict__.get("OPTIONAL", True))))

        self.category: str = str(widget_data.get("category", "Miscellaneous"))
        self.subcategory: str = str(widget_data.get("subcategory", "Others"))

        # IMPORTANT: defaults must be None, not lambda
        self.main: Callable | None = None
        self.minimal: Callable | None = None
        self.configure: Callable | None = None
        self.on_enable: Callable | None = None
        self.on_disable: Callable | None = None

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
        return
        ini_handler.write_key(self.name, "enabled", str(self.enabled))
        ini_handler.write_key(self.name, "optional", str(self.optional))

#region widget handler
class WidgetHandler:
    _instance = None
    _widgets_folder_path = "Widgets"

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, widgets_path=_widgets_folder_path):
        if getattr(self, "_initialized", False):
            return

        import sys
        try:
            module_file = sys.modules[__name__].__file__
        except (KeyError, AttributeError):
            module_file = None

        base_dir = os.path.dirname(os.path.abspath(module_file)) if module_file else os.getcwd()
        resolved_path = widgets_path or os.path.join(base_dir, WidgetHandler._widgets_folder_path)
        self.widgets_path = os.path.abspath(resolved_path)
        self.__show_widget_ui = True
        self.__pause_optional_widgets = False

        self.widgets : dict[str, WidgetNode] = {}
        self.widget_data_cache = {}
        from Py4GWCoreLib.py4gwcorelib_src.Timer import Timer
        self.last_write_time = Timer()
        self.last_write_time.Start()
        self._initialized = True
    
    @property
    def pause_optional_widgets(self):
        return self.__pause_optional_widgets
    
    @property
    def show_widget_ui(self):
        return self.__show_widget_ui
    
    def _get_widget_ini_spec(self, widget_id: str, script_path: str) -> tuple[str, str]:
        """
        Returns (ini_path, ini_filename) for this widget.
        We store settings under Settings/<email>/Widgets/<relative_folder>/<script_base>.ini
        """
        # script folder relative to Widgets root
        script_dir = os.path.dirname(os.path.abspath(script_path))
        rel_dir = os.path.relpath(script_dir, self.widgets_path).replace(os.sep, "/").strip("/")

        base = os.path.splitext(os.path.basename(script_path))[0]
        ini_filename = f"{base}.ini"

        # Always prefix with Widgets/ to keep your existing convention
        ini_path = "Widgets"
        if rel_dir:
            ini_path = f"{ini_path}/{rel_dir}"

        return ini_path, ini_filename

    def _ensure_widget_ini_key(self, widget_id: str, script_path: str) -> tuple[str, str, str]:
        ini_path, ini_filename = self._get_widget_ini_spec(widget_id, script_path)

        ini_key = IniManager().ensure_key(ini_path, ini_filename)
        if ini_key:
            self._ensure_widget_meta_vars(ini_key)
            IniManager().load_once(ini_key)

        return ini_key, ini_path, ini_filename


    def _read_widget_meta(self, ini_key: str, module: ModuleType) -> dict:
        """
        Reads widget state from its own ini.
        Stored under [Window config] to match your template.
        """
        section = "Window config"

        enabled = IniManager().read_bool(ini_key, section, "widget_active", False)

        # optional default comes from module if missing
        default_optional = bool(module.__dict__.get("OPTIONAL", True))
        optional = IniManager().read_bool(ini_key, section, "optional", default_optional)

        category = IniManager().read_key(ini_key, section, "category", "Miscellaneous")
        subcategory = IniManager().read_key(ini_key, section, "subcategory", "Others")

        return {
            "enabled": enabled,
            "optional": optional,
            "category": category,
            "subcategory": subcategory,
        }

    def _write_widget_meta(self, widget: "WidgetNode"):
        if not widget.ini_key:
            return

        # ensure declared
        self._ensure_widget_meta_vars(widget.ini_key)

        IniManager().set(widget.ini_key, "widget_active", bool(widget.enabled))
        IniManager().set(widget.ini_key, "optional", bool(widget.optional))

        # only if you have add_str support:
        IniManager().set(widget.ini_key, "category", str(widget.category))
        IniManager().set(widget.ini_key, "subcategory", str(widget.subcategory))

        IniManager().save_vars(widget.ini_key)



    

    def _ensure_widget_meta_vars(self, ini_key: str):
        """
        Ensure required widget meta vars exist in IniManager for this widget ini.
        Without this, save_vars() may not write anything.
        """
        if not ini_key:
            return

        # vars live under [Window config]
        IniManager().add_bool(ini_key, "widget_active", "Window config", "widget_active", default=False)
        IniManager().add_bool(ini_key, "optional", "Window config", "optional", default=True)

        # optional meta (not required but useful)
        IniManager().add_str(ini_key, "category", "Window config", "category", default="Miscellaneous")
        IniManager().add_str(ini_key, "subcategory", "Window config", "subcategory", default="Others")


    def _load_all_from_dir(self):
        if not os.path.isdir(self.widgets_path):
            raise FileNotFoundError(f"Widget directory missing: {self.widgets_path}")

        for file in os.listdir(self.widgets_path):
            if not file.endswith(".py"):
                continue

            widget_name = os.path.splitext(file)[0]
            script_path = os.path.join(self.widgets_path, file)

            try:
                module = self.load_widget(script_path, widget_name)

                ini_key, ini_path, ini_filename = self._ensure_widget_ini_key(widget_name, script_path)
                widget_data = self._read_widget_meta(ini_key, module)

                widget = self.widgets[widget_name] = WidgetNode(
                    name=widget_name,
                    module=module,
                    widget_data=widget_data,
                    ini_key=ini_key,
                    ini_path=ini_path,
                    ini_filename=ini_filename
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

    def _load_all_from_tree(self):
        root = self.widgets_path

        if not os.path.isdir(root):
            raise FileNotFoundError(f"Widget directory missing: {root}")

        for current_dir, dirs, files in os.walk(root):
            # Rule 1: only widget folders
            if ".widget" not in files:
                continue

            # Rule 2: load ALL .py in that folder
            py_files = [f for f in files if f.endswith(".py")]
            if not py_files:
                ConsoleLog("WidgetHandler", f"Widget folder has no .py scripts: {current_dir}", Py4GW.Console.MessageType.Error)
                dirs.clear()
                continue

            rel_dir = os.path.relpath(current_dir, root).replace(os.sep, "/").strip("/")

            for py_name in py_files:
                script_path = os.path.join(current_dir, py_name)
                widget_id = f"{rel_dir}/{py_name}" if rel_dir else py_name

                if widget_id in self.widgets:
                    continue

                try:
                    module = self.load_widget(script_path, widget_id)

                    ini_key, ini_path, ini_filename = self._ensure_widget_ini_key(widget_id, script_path)
                    widget_data = self._read_widget_meta(ini_key, module)

                    widget = self.widgets[widget_id] = WidgetNode(
                        name=widget_id,
                        module=module,
                        widget_data=widget_data,
                        ini_key=ini_key,
                        ini_path=ini_path,
                        ini_filename=ini_filename
                    )

                    if widget.enabled and widget.on_enable is not None:
                        try:
                            widget.on_enable()
                        except Exception as e:
                            ConsoleLog("WidgetHandler", f"Error during on_enable of widget {widget.name}: {str(e)}", Py4GW.Console.MessageType.Error)
                            ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

                    ConsoleLog("WidgetHandler", f"Loaded folder widget: {widget_id}", Py4GW.Console.MessageType.Info)

                except Exception as e:
                    ConsoleLog("WidgetHandler", f"Failed to load folder widget {widget_id}: {e}", Py4GW.Console.MessageType.Error)
                    ConsoleLog("WidgetHandler", traceback.format_exc(), Py4GW.Console.MessageType.Error)

            dirs.clear()

    
    def discover_widgets(self):
        try:
            self.widget_data_cache.clear()
            #self._load_all_from_dir()
            self._load_all_from_tree()
            
        except Exception as e:
            ConsoleLog("WidgetHandler", f"Unexpected error during widget discovery: {str(e)}", Py4GW.Console.MessageType.Error)
            ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

    def load_widget(self, widget_path: str, widget_id: str):
        # unique import name so modules never overwrite each other
        unique_mod_name = f"py4gw_widget__{widget_id.replace('/', '__').replace('.', '_')}"

        spec = importlib.util.spec_from_file_location(unique_mod_name, widget_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Failed to load widget: Invalid spec from {widget_path}")

        widget_module = importlib.util.module_from_spec(spec)

        # register into sys.modules (important for relative imports and uniqueness)
        sys.modules[unique_mod_name] = widget_module

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

    def get_widget_info(self, name: str) -> WidgetNode | None:
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
        
        ConsoleLog(
            "WidgetHandler",
            f"_set_widget_state: '{name}' state={state} ini_key='{widget.ini_key}'",
            Py4GW.Console.MessageType.Info
        )

        if state:
            if widget.on_enable:
                try:
                    widget.on_enable()
                except Exception as e:
                    ConsoleLog("WidgetHandler", f"Error during on_enable of widget {name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
        else:
            if widget.on_disable:
                try:
                    widget.on_disable()
                except Exception as e:
                    ConsoleLog("WidgetHandler", f"Error during on_disable of widget {name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    ConsoleLog("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

        # NEW: persist into the widget's own ini file
        self._write_widget_meta(widget)


    def is_widget_enabled(self, name: str) -> bool:
        widget = self.widgets.get(name)
        return bool(widget and widget.enabled)

    def list_enabled_widgets(self) -> list[str]:
        return [name for name, info in self.widgets.items() if info.enabled]

#region main
widget_manager: WidgetManager = WidgetManager()


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
    wm_key = _ensure_widget_manager_ini()

    if new_enable_all != enable_all:
        enable_all = new_enable_all

        if wm_key:
            IniManager().set(wm_key, "enable_all", bool(enable_all))
            IniManager().save_vars(wm_key)
       
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
    for name, widget in handler.widgets.items():
        cat = widget.category or "Miscellaneous"
        sub = widget.subcategory or ""
        categorized_widgets.setdefault(cat, {}).setdefault(sub, []).append(name)


    for cat, subs in categorized_widgets.items():
        open = ImGui.collapsing_header(cat)
        
        if not open:
            continue
        
        for sub, names in subs.items():
            if not sub:
                sub = "Others"
            
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
                    ConsoleLog("WidgetUI", f"TOGGLE CLICK: {name} -> {new_enabled}", Py4GW.Console.MessageType.Info)
                    handler._set_widget_state(name, new_enabled)

                PyImGui.table_set_column_index(1)
                widget.configuring = ImGui.toggle_icon_button(IconsFontAwesome5.ICON_COG + f"##Configure{name}", widget.configuring)
                

            ImGui.end_table()
            ImGui.tree_pop()
            
    # ------------------------------------------------------------
    # Folder-based Widgets (TREE UI)
    # ------------------------------------------------------------

    ImGui.text("Folder-based Widgets")
    ImGui.separator()

    style = ImGui.get_style()

    # Build tree from widget paths
    tree: dict = {}

    for widget_id in handler.widgets:
        if "/" not in widget_id:
            continue

        parts = widget_id.split("/")
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node.setdefault("__widgets__", []).append(widget_id)


    def draw_node(node: dict, depth: int = 0):
        for key, value in sorted(node.items()):
            # Leaf: render widgets table
            if key == "__widgets__":
                # IMPORTANT: table id must be stable + unique; don't use `id(value)` (can change)
                table_id = f"WidgetsTable##tree_depth_{depth}"
                if ImGui.begin_table(table_id, 2, PyImGui.TableFlags.Borders):
                    for widget_id in value:
                        widget = handler.widgets.get(widget_id)
                        if not widget:
                            continue

                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)

                        display_name = widget_id.split("/")[-1]

                        # IMPORTANT: strong unique ImGui ID for checkbox
                        label = f"{display_name}##{widget_id}"
                        new_enabled = ImGui.checkbox(label, widget.enabled)

                        if new_enabled != widget.enabled:
                            # IMPORTANT: toggle must use the strong id (widget_id), not display_name
                            handler._set_widget_state(widget_id, new_enabled)

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

# ------------------------------------------------------------
# Widget Manager config now uses IniManager
# ------------------------------------------------------------
MANAGER_INI_KEY = ""
MANAGER_INI_PATH = "Widgets/WidgetManager"
MANAGER_INI_FILENAME = "WidgetManager.ini"
MANAGER_VARS_ADDED = False


def _ensure_manager_key() -> str:
    """Get or create GLOBAL INI key for widget manager (standard pattern)"""
    global MANAGER_INI_KEY
    if not MANAGER_INI_KEY:
        # GLOBAL key - works without account
        MANAGER_INI_KEY = IniManager().ensure_global_key(MANAGER_INI_PATH, MANAGER_INI_FILENAME)
    return MANAGER_INI_KEY

def _add_manager_vars():
    """Add widget manager INI variables (standard pattern)"""
    key = _ensure_manager_key()
    if not key:
        return
    
    # Declare manager variables (once)
    IniManager().add_bool(key, "enable_all", "Window config", "enable_all", default=True)
    
def _load_manager_once(widget_manager: WidgetManager):
    """Load widget manager state from INI (standard pattern - runs once)"""
    global MANAGER_INI_KEY
    
    if not MANAGER_INI_KEY:
        MANAGER_INI_KEY = IniManager().ensure_global_key(MANAGER_INI_PATH, MANAGER_INI_FILENAME)
        if not MANAGER_INI_KEY:
            return
        
        # Add variables (once)
        _add_manager_vars()
        
        # Load values (once)
        IniManager().load_once(MANAGER_INI_KEY)
    
    # Apply loaded values to widget manager
    widget_manager.enable_all = bool(IniManager().get(MANAGER_INI_KEY, "enable_all", True))
    
def save_manager_state(widget_manager: WidgetManager):
    """Save widget manager state to GLOBAL INI"""
    key = _ensure_manager_key()
    if not key:
        return
    
    IniManager().set(key, "enable_all", widget_manager.enable_all)
    IniManager().save_vars(key)


# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------
def main():
    # Global singleton
    widget_manager = WidgetManager()
    
    try:
        if not getattr(widget_manager, '_discovered', False):
            widget_manager.discover()
            widget_manager.discovered = True

        # One-time INI initialization (like widget template)
        _load_manager_once(widget_manager)

        # Draw UI using GLOBAL INI key (always works)
        key = _ensure_manager_key()
        if key and ImGui.Begin(ini_key=key, name="Widget Manager", 
                               flags=PyImGui.WindowFlags.AlwaysAutoResize):
            draw_widget_ui(widget_manager)  # Pass manager to UI
            ImGui.End(key)

        if widget_manager.enable_all:
            pass
            return
            widget_manager.execute_enabled_widgets()
            widget_manager.execute_configuring_widgets()

    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, traceback.format_exc(), Py4GW.Console.MessageType.Error)

if __name__ == "__main__":
    main()