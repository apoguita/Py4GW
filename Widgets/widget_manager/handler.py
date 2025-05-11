from Py4GWCoreLib import *
from .default_settings import global_widget_defaults, account_widget_defaults, default_schema_version
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
        self.base_path = os.path.join(os.getcwd(), "widgets", "config", "account_config")
        self.global_ini_path = os.path.join(self.base_path, "global_widget_config.ini")
        
        os.makedirs(self.base_path, exist_ok=True) 
        self.account_email = Player.GetAccountEmail() or "unknown"
        self.account_path = os.path.join(self.base_path, self.account_email)
        self.account_ini_path = os.path.join(self.account_path, "widgets_meta.ini")
        self.account_initialized = False
        
        os.makedirs(self.account_path, exist_ok=True)
        self._load_widget_cache()
        self._initialize_global_config()
        self._last_global_values = {}
        self._last_account_values = {}
        self._initialized = True
        
    def _initialize_account_settings(self):
        email = Player.GetAccountEmail()
        if not email or email == "unknown":
            return
        if getattr(self, "_last_initialized_email", None) == email:
            return

        self.account_email = email
        self.account_path = os.path.join(self.base_path, email)
        self.account_ini_path = os.path.join(self.account_path, "widgets_meta.ini")

        os.makedirs(self.account_path, exist_ok=True)
        open(self.account_ini_path, "a").close()

        self._last_initialized_email = email
        self._initialize_account_config()
        self.account_initialized = True

    def _initialize_global_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.global_ini_path):
            config.read(self.global_ini_path)

        updated = False
        for section, kv in global_widget_defaults.items():
            if section not in config:
                config[section] = {}
                updated = True
            for key, value in kv.items():
                if key not in config[section]:
                    config[section][key] = value
                    updated = True

        if "Meta" not in config:
            config["Meta"] = {}
            updated = True
        if config["Meta"].get("schema_version") != default_schema_version:
            config["Meta"]["schema_version"] = default_schema_version
            updated = True

        if updated:
            os.makedirs(self.base_path, exist_ok=True)
            with open(self.global_ini_path, "w") as f:
                config.write(f)
            ConsoleLog("WidgetHandler", "Updated global config with missing defaults", Py4GW.Console.MessageType.Info)

    def _initialize_account_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.account_ini_path):
            config.read(self.account_ini_path)

        updated = False
        for section, kv in account_widget_defaults.items():
            if section not in config:
                config[section] = {}
                updated = True
            for key, value in kv.items():
                if key not in config[section]:
                    config[section][key] = value
                    updated = True

        if "Meta" not in config:
            config["Meta"] = {}
            updated = True
        if config["Meta"].get("schema_version") != default_schema_version:
            config["Meta"]["schema_version"] = default_schema_version
            updated = True

        if updated:
            os.makedirs(self.account_path, exist_ok=True)
            with open(self.account_ini_path, "w") as f:
                config.write(f)
            ConsoleLog("WidgetHandler", "Updated account config with missing defaults", Py4GW.Console.MessageType.Info)
    
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

    def _read_setting_bool(self, section, key, default=False):
        val = self._read_setting(section, key, f"{default}")
        return val and val.lower() == "true"

    def _read_setting_int(self, section, key, default=0):
        val = self._read_setting(section, key, default)
        if val is None:
            return default
        try:
            return int(val)
        except Exception:
            return default

    def _read_setting_float(self, section, key, default=0.0):
        val = self._read_setting(section, key, default)
        if val is None:
            return default
        try:
            return float(val)
        except Exception:
            return default
    
    def read_global_setting(self, section, key, default=None):
        return self._read_from_ini(self.global_ini_path, section, key, default)

    def _write_global_setting(self, section, key, value):
        if self._last_global_values.get((section, key)) == value:
            return
        self._write_to_ini(self.global_ini_path, section, key, value)
        self._last_global_values[(section, key)] = value

    def read_account_setting(self, section, key, default=None):
        return self._read_from_ini(self.account_ini_path, section, key, default)

    def _write_account_setting(self, section, key, value):
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

    def _save_widget_state(self, widget_name):
        widget = self.widgets.get(widget_name)
        if not widget:
            return

        data = self.widget_data_cache.get(widget_name, {})
        enabled = widget.get("enabled", False)
        category = data.get("category", "")
        subcategory = data.get("subcategory", "")
        icon = data.get("icon", "ICON_CIRCLE")
        quickdock = data.get("quickdock", False)

        for writer in (self._write_account_setting, self._write_global_setting):
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
        name = os.path.splitext(os.path.basename(path))[0]
        
        spec = importlib.util.spec_from_file_location("widget", path)
        if not spec or not spec.loader:
            raise ValueError(f"Invalid spec from {path}")

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            ConsoleLog("WidgetHandler", f"Failed to load widget '{name}': {e}", Py4GW.Console.MessageType.Error)
            traceback.print_exc()
            return None

        if not all(hasattr(module, attr) for attr in ("main", "configure")):
            raise ValueError("Widget missing required functions: main() and configure()")
        
        meta = getattr(module, "__widget__", None)
        if isinstance(meta, dict):
            self.widget_data_cache[name] = {
                "category": meta.get("category"),
                "subcategory": meta.get("subcategory"),
                "icon": meta.get("icon"),
                "quickdock": meta.get("quickdock"),
                "hidden": meta.get("hidden"),
            }

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
                if hasattr(info["module"], "render_ui"):
                    info["module"].render_ui()
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
        self._save_widget_state(name)

    def is_widget_enabled(self, name: str) -> bool:
        return bool(self.widgets.get(name, {}).get("enabled"))

    def list_enabled_widgets(self) -> list[str]:
        return [name for name, w in self.widgets.items() if w.get("enabled")]

# Singleton WidgetHandler setup
if "_Py4GW_GLOBAL_WIDGET_HANDLER" not in sys.modules:
    mod = types.ModuleType("_Py4GW_GLOBAL_WIDGET_HANDLER")  # actual module type
    mod.handler = WidgetHandler()  # type: ignore[attr-defined]
    sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"] = mod
handler = sys.modules["_Py4GW_GLOBAL_WIDGET_HANDLER"].handler
