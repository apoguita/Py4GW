from Py4GWCoreLib import Timer, Player, ConsoleLog, Py4GW, traceback
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
    
    def _read_setting(self, section, key, default=None, *, force_account=False, force_global=False):
        parser = configparser.ConfigParser()

        paths = []
        if force_account:
            paths = [self.account_ini_path]
        elif force_global:
            paths = [self.global_ini_path]
        else:
            paths = [self.global_ini_path, self.account_ini_path]

        for path in paths:
            if not path or not os.path.exists(path):
                continue
            try:
                parser.read(path)
            except configparser.Error as e:
                ConsoleLog("WidgetHandler", f"[Warning] Corrupt INI file: {path} ({e})", Py4GW.Console.MessageType.Warning)
                continue  # Try next file

            if parser.has_section(section) and parser.has_option(section, key):
                return parser.get(section, key)
            
        return default

    def _read_setting_bool(self, section, key, default=False, *, force_account=False, force_global=False):
        val = self._read_setting(section, key, str(default), force_account=force_account, force_global=force_global)
        return val and val.lower() == "true"

    def _read_setting_int(self, section, key, default=0, *, force_account=False, force_global=False):
        val = self._read_setting(section, key, str(default), force_account=force_account, force_global=force_global)
        if val is None:
            return default
        try:
            return int(val)
        except Exception:
            return default

    def _read_setting_float(self, section, key, default=0.0, *, force_account=False, force_global=False):
        val = self._read_setting(section, key, str(default), force_account=force_account, force_global=force_global)
        if val is None:
            return default
        try:
            return float(val)
        except Exception:
            return default

    def _write_setting(self, section, key, value, *, to_account=None, force=False):
        from .config_scope import use_account_settings
        
        if to_account is None:
            to_account = use_account_settings()
            
        if not hasattr(self, "_last_global_values"):
            self._last_global_values = {}
        if not hasattr(self, "_last_account_values"):
            self._last_account_values = {}

        cache = self._last_account_values if to_account else self._last_global_values
        path = self.account_ini_path if to_account else self.global_ini_path

        if not force and cache.get((section, key)) == value:
            return

        parser = configparser.ConfigParser()
        
        if to_account and not os.path.exists(self.account_path):
            os.makedirs(self.account_path, exist_ok=True)
            self._initialize_account_config()

        if not os.path.exists(path):
            open(path, "a").close()
            
        parser.read(path)

        if not parser.has_section(section):
            parser.add_section(section)

        parser.set(section, key, str(value))

        with open(path, "w") as f:
            parser.write(f)

        cache[(section, key)] = value

    def _write_global_setting(self, section, key, value):
        self._write_setting(section, key, value, to_account=False)

    def _write_account_setting(self, section, key, value):
        self._write_setting(section, key, value, to_account=True)
    
    def _load_widget_cache(self):
        from .config_scope import use_account_settings
        
        if self.account_email == "unknown" or not use_account_settings():
            path = self.global_ini_path
        else:
            path = self.account_ini_path
            
        if not os.path.exists(path):
            return

        parser = configparser.ConfigParser()
        parser.read(path)

        for section in parser.sections():
            if section in self.widget_data_cache:
                continue
            if section in {"WidgetManager", "QuickDock", "QuickDockColor", "FloatingMenu", "Meta"}:
                continue
            get = lambda k, d: parser.get(section, k, fallback=d)
            self.widget_data_cache[section] = {
                "category": get("category", "Miscellaneous"),
                "subcategory": get("subcategory", "General"),
                "enabled": get("enabled", "True").lower() == "true",
                "icon": get("icon", "ICON_CIRCLE"),
                "quickdock": get("quickdock", "False").lower() == "true",
            }
        # Patch fallback defaults if widget got placeholder metadata
            if section in global_widget_defaults or section in account_widget_defaults:
                defaults = account_widget_defaults.get(section) or global_widget_defaults.get(section)
                current = self.widget_data_cache[section]

                needs_patch = (
                    current.get("category") == "Miscellaneous"
                )

                if needs_patch and defaults:
                    for key in ("category", "subcategory", "icon", "quickdock", "enabled"):
                        if key not in defaults:
                            continue
                        val = defaults[key]
                        if key in ("quickdock", "enabled"):
                            val = str(val).lower() == "true"
                        current[key] = val
                        self._write_setting(section, key, str(val), to_account=use_account_settings(), force=True)

                    ConsoleLog("WidgetHandler", f"Updated widget '{section}' with default category/subcategory", Py4GW.Console.MessageType.Info)

            
    def _load_all_from_dir(self):
        if not os.path.isdir(self.widgets_path):
            raise FileNotFoundError(f"Missing widget directory: {self.widgets_path}")

        py_files = [f for f in os.listdir(self.widgets_path) if f.endswith(".py")]

        for file in py_files:
            name = os.path.splitext(file)[0]
            path = os.path.join(self.widgets_path, file)
            try:
                module = self.load_widget(path)
                if not module:
                    ConsoleLog("WidgetHandler", f"Skipped widget: {name} (module load failed)", Py4GW.Console.MessageType.Warning)
                    continue
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
        if not isinstance(meta, dict):
            meta = {}
        cache = self.widget_data_cache.setdefault(name, {})

        defaults = (
            account_widget_defaults.get(name)
            or global_widget_defaults.get(name)
            or {}
        )
        
        if "enabled" not in cache or "enabled" in meta:
            cache["enabled"] = meta["enabled"] if "enabled" in meta else defaults.get("enabled", False)
        if "category" not in cache or "category" in meta:
            cache["category"] = meta["category"] if "category" in meta else defaults.get("category", "Miscellaneous")
        if "subcategory" not in cache or "subcategory" in meta:
            cache["subcategory"] = meta["subcategory"] if "subcategory" in meta else defaults.get("subcategory", "General")
        if "icon" not in cache or "icon" in meta:
            cache["icon"] = meta["icon"] if "icon" in meta else defaults.get("icon", "ICON_CIRCLE")
        if "quickdock" not in cache or "quickdock" in meta:
            cache["quickdock"] = meta["quickdock"] if "quickdock" in meta else defaults.get("quickdock", False)

        if isinstance(meta, dict) and "hidden" in meta:
            cache["hidden"] = meta["hidden"]

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

    def _set_widget_state(self, name: str, enabled_state: bool):
        from .config_scope import use_account_settings
        widget = self.widgets.get(name)
        if not widget:
            ConsoleLog("WidgetHandler", f"Unknown widget: {name}", Py4GW.Console.MessageType.Warning)
            return

        widget["enabled"] = enabled_state
        self._write_setting(name, "enabled", str(enabled_state), to_account=use_account_settings())

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
