from platform import node
import Py4GW
import os
import PyImGui
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.py4gwcorelib_src.IniHandler import IniHandler
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from dataclasses import dataclass, field
from typing import Any

# ------------------------------------------------------------
# Config Node
# ------------------------------------------------------------

@dataclass
class ConfigNode:
    key: str
    path: str
    filename: str
    ini_handler: IniHandler
    update_time: ThrottledTimer
    needs_update: bool = False
    is_global: bool = False

    initialized: bool = False
    x_pos: int = 0
    y_pos: int = 0
    width: int = 0
    height: int = 0
    collapsed: bool = False
    
    write_time: ThrottledTimer = field(default_factory=lambda: ThrottledTimer(500))
    pending_writes: dict[tuple[str, str], str] = field(default_factory=dict)
    cached_values: dict[tuple[str, str], str] = field(default_factory=dict)
    needs_flush: bool = False
    
    begin_called: bool = False
    begin_returned_true: bool = False

    #varfactory
    vars_defs: dict[str, tuple[str, str, Any, str]] = field(default_factory=dict)
    vars_values: dict[str, Any] = field(default_factory=dict)
    vars_dirty: set[str] = field(default_factory=set)
    vars_loaded: bool = False

@dataclass
class IniVarDef:
    var_name: str
    section: str
    key: str
    default: Any
    var_type: str  # "bool" | "int" | "float" | "str"
    
# ------------------------------------------------------------
# Config Manager (Singleton, Wrapper)
# ------------------------------------------------------------

class IniManager:
    _instance = None
    _callback_name = "_Py4GW_ConfigManager_Flush"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IniManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.defaults_path = "Defaults/"
        self.base_path = Py4GW.Console.get_projects_path() + "/Settings/"
        self._handlers: dict[str, ConfigNode] = {}
        

        self._initialized = True
        
    # --------------------------------------------------------
    # Callbacks
    # --------------------------------------------------------
    @staticmethod
    def enable():
        import PyCallback
        PyCallback.PyCallback.Register(
            IniManager._callback_name,
            PyCallback.Phase.Data,
            IniManager._flush_callback,
            priority=99
        )

    @staticmethod
    def disable():
        import PyCallback
        PyCallback.PyCallback.RemoveByName(IniManager._callback_name)

    
    # --------------------------------------------------------
    # Account / Path helpers
    # --------------------------------------------------------

    def get_account_email(self) -> str:
        return Player.GetAccountEmail()

    def get_defaults_path(self) -> str:
        return self.base_path + self.defaults_path

    def get_path(self) -> str | None:
        email = self.get_account_email()
        if email == "":
            return None
        return self.base_path + email + "/"
    
    def _is_account_ready(self) -> bool:
        email = self.get_account_email()
        self.account_ready = email != ""
        return self.account_ready

    def _make_key(self, path: str, filename: str) -> str:
        path = path.strip("/")
        filename = filename.strip("/")
        return f"{path}/{filename}" if path else filename

    # --------------------------------------------------------
    # Node creation / loading
    # --------------------------------------------------------
    def AddIniHandler(self, path: str, filename: str, is_global: bool = False) -> str:
        path = path.strip("/")
        filename = filename.strip("/")

        # account guard only for NON-global
        if not is_global and not self._is_account_ready():
            return ""

        # resolve base folder
        # - account: Settings/<email>/
        # - global : Settings/Global/
        if is_global:
            full_path = self.base_path + "Global/"
        else:
            full_path = self.get_path()
            if full_path is None:
                return ""

        key = self._make_key(path, filename)
        if not key:
            return ""

        full_filename = f"{full_path}{key}"

        existing = self._handlers.get(key)
        if existing is not None:
            return key

        try:
            file_exists = os.path.exists(full_filename)

            if not file_exists:
                template = self.get_defaults_path() + "default_template.cfg"
                template_exists = os.path.exists(template)

                if template_exists:
                    with open(template, "r", encoding="utf-8") as src:
                        content = src.read()
                else:
                    content = ""

                # Ensure directory exists
                dir_name = os.path.dirname(full_filename)
                os.makedirs(dir_name, exist_ok=True)

                with open(full_filename, "w", encoding="utf-8") as dst:
                    dst.write(content)

            # Create IniHandler
            ini = IniHandler(full_filename)

            # Load window config
            section = "Window config"
            x = ini.read_int(section, "x", 0)
            y = ini.read_int(section, "y", 0)
            w = ini.read_int(section, "width", 0)
            h = ini.read_int(section, "height", 0)
            c = ini.read_bool(section, "collapsed", False)

            node = ConfigNode(
                key=key,
                path=path.strip("/"),
                filename=filename.strip("/"),
                ini_handler=ini,
                initialized=False,
                update_time=ThrottledTimer(500),
                needs_update=False,
                x_pos=x,
                y_pos=y,
                width=w,
                height=h,
                collapsed=c,
            )

            node.is_global = bool(is_global)

            node.update_time.Start()

            self._handlers[key] = node
            return key

        except Exception as e:
            print(f"[ConfigManager.AddIniHandler] ERROR creating node for key='{key}': {e}")
            try:
                import traceback
                print(traceback.format_exc())
            except Exception:
                pass
            return ""



    # ----------------------------
    # IniHandler API — WRAPPED
    # ----------------------------
    def _get_node(self, key: str) -> ConfigNode | None:
        if not self._is_account_ready():
            return None
        if not key:
            return None
        return self._handlers.get(key, None)
    
    def _read_cached_str(self, key: str, section: str, name: str, default: str) -> str:
        node = self._get_node(key)
        if not node:
            return default

        k = (section, name)

        # pending overrides cached/disk
        if k in node.pending_writes:
            return node.pending_writes[k]

        # cached read
        if k in node.cached_values:
            return node.cached_values[k]

        # load from disk (IniHandler internally reloads if needed)
        value = node.ini_handler.read_key(section, name, default)

        # cache it as string for consistent comparisons
        node.cached_values[k] = str(value)
        return str(value)
    
    
    @staticmethod
    def _flush_callback(*args, **kwargs):
        #per frame callback to flush throttled writes
        
        cm = IniManager()

        # don’t do anything until account ready
        if not cm._is_account_ready():
            return

        # iterate all nodes and flush throttled writes
        for key, node in cm._handlers.items():
            if not getattr(node, "needs_flush", False):
                continue

            if not getattr(node, "pending_writes", None):
                node.needs_flush = False
                continue

            if not node.write_time.IsExpired():
                continue

            #print(f"[ConfigManager.FlushCallback] flushing {len(node.pending_writes)} writes key='{key}'")

            for (section, name), value in node.pending_writes.items():
                node.ini_handler.write_key(section, name, value)
                node.cached_values[(section, name)] = value

            node.pending_writes.clear()
            node.needs_flush = False

            node.write_time.Reset()
            node.write_time.Start()


    def reload(self, key: str):
        if not self._is_account_ready():
            return None
        node = self._handlers.get(key)
        return node.ini_handler.reload() if node else None


    def save(self, key: str, config):
        if not self._is_account_ready():
            return
        node = self._handlers.get(key)
        if node:
            node.ini_handler.save(config)


    def read_key(self, key: str, section: str, name: str, default=""):
        if not self._is_account_ready():
            return default
        node = self._handlers.get(key)
        return node.ini_handler.read_key(section, name, default) if node else default


    def read_int(self, key: str, section: str, name: str, default=0):
        if not self._is_account_ready():
            return default
        node = self._handlers.get(key)
        return node.ini_handler.read_int(section, name, default) if node else default


    def read_float(self, key: str, section: str, name: str, default=0.0):
        if not self._is_account_ready():
            return default
        node = self._handlers.get(key)
        return node.ini_handler.read_float(section, name, default) if node else default


    def read_bool(self, key: str, section: str, name: str, default=False):
        if not self._is_account_ready():
            return default
        node = self._handlers.get(key)
        return node.ini_handler.read_bool(section, name, default) if node else default


    def write_key(self, key: str, section: str, name: str, value):
        if not self._is_account_ready():
            return

        node = self._handlers.get(key)
        if not node:
            return

        # lazy state safety
        if not hasattr(node, "cached_values") or node.cached_values is None:
            node.cached_values = {}
        if not hasattr(node, "pending_writes") or node.pending_writes is None:
            node.pending_writes = {}
        if not hasattr(node, "needs_flush"):
            node.needs_flush = False

        k = (section, name)
        v = str(value)

        # Compare against most recent intent (pending), else cached
        prev = node.pending_writes.get(k, node.cached_values.get(k, None))
        if prev == v:
            return  # no change -> no-op

        # Stage write (callback will flush later)
        node.pending_writes[k] = v
        node.needs_flush = True


    def delete_key(self, key: str, section: str, name: str):
        if not self._is_account_ready():
            return
        node = self._handlers.get(key)
        if node:
            node.ini_handler.delete_key(section, name)


    def delete_section(self, key: str, section: str):
        if not self._is_account_ready():
            return
        node = self._handlers.get(key)
        if node:
            node.ini_handler.delete_section(section)


    def list_sections(self, key: str) -> list:
        if not self._is_account_ready():
            return []
        node = self._handlers.get(key)
        return node.ini_handler.list_sections() if node else []


    def list_keys(self, key: str, section: str) -> dict:
        if not self._is_account_ready():
            return {}
        node = self._handlers.get(key)
        return node.ini_handler.list_keys(section) if node else {}


    def has_key(self, key: str, section: str, name: str) -> bool:
        if not self._is_account_ready():
            return False
        node = self._handlers.get(key)
        return node.ini_handler.has_key(section, name) if node else False


    def clone_section(self, key: str, src: str, dst: str):
        if not self._is_account_ready():
            return
        node = self._handlers.get(key)
        if node:
            node.ini_handler.clone_section(src, dst)

    # ----------------------------
    # Window config management
    # ----------------------------
    def begin_window_config(self, key: str):
        if not key:
            return

        node = self._handlers.get(key)
        if node is None:
            return

        # mark begin frame state
        node.begin_called = True
        node.begin_returned_true = False

        if not node.initialized:
            PyImGui.set_next_window_pos(node.x_pos, node.y_pos)

            if node.width > 0 and node.height > 0:
                PyImGui.set_next_window_size(node.width, node.height)

            PyImGui.set_next_window_collapsed(node.collapsed, 0)
            node.initialized = True
            
    def mark_begin_success(self, key: str):
        node = self._handlers.get(key)
        if node is None:
            return
        node.begin_returned_true = True


            
    def track_window_collapsed(self, key: str, begin_result: bool):
        """
        Rule:
        - assume collapsed=True always
        - if Begin returned True => collapsed=False
        """
        if not key:
            return

        node = self._handlers.get(key)
        if node is None:
            return

        new_collapsed = True
        if begin_result:
            new_collapsed = False

        if new_collapsed == node.collapsed:
            return

        node.needs_update = True
        if not node.update_time.IsExpired():
            return

        node.collapsed = new_collapsed

        # use your throttled writer path (recommended)
        self.write_key(key, "Window config", "collapsed", str(node.collapsed))

        node.update_time.Reset()
        node.needs_update = False




    def end_window_config(self, key: str):
        if not key:
            return

        node = self._handlers.get(key)
        if node is None:
            return

        # If Begin() never produced an active window, DO NOT read window state
        if not getattr(node, "begin_called", False) or not getattr(node, "begin_returned_true", False):
            node.begin_called = False
            node.begin_returned_true = False
            return

        # ---- safe to read window values now ----
        end_pos = PyImGui.get_window_pos()
        end_size = PyImGui.get_window_size()
        new_collapsed = PyImGui.is_window_collapsed()

        changed_pos = (end_pos[0], end_pos[1]) != (node.x_pos, node.y_pos)
        changed_size = (end_size[0], end_size[1]) != (node.width, node.height)
        changed_collapsed = new_collapsed != node.collapsed

        if changed_pos or changed_size or changed_collapsed:
            node.needs_update = True

        if not node.needs_update:
            node.begin_called = False
            node.begin_returned_true = False
            return

        if not node.update_time.IsExpired():
            node.begin_called = False
            node.begin_returned_true = False
            return

        node.x_pos, node.y_pos = int(end_pos[0]), int(end_pos[1])
        node.ini_handler.write_key("Window config", "x", node.x_pos)
        node.ini_handler.write_key("Window config", "y", node.y_pos)

        node.width, node.height = int(end_size[0]), int(end_size[1])
        node.ini_handler.write_key("Window config", "width", node.width)
        node.ini_handler.write_key("Window config", "height", node.height)

        node.collapsed = new_collapsed
        node.ini_handler.write_key("Window config", "collapsed", node.collapsed)

        node.update_time.Reset()
        node.needs_update = False

        # clear per-frame begin status
        node.begin_called = False
        node.begin_returned_true = False

        
    # ----------------------------------------
    # Key Factory (Var Management)
    # ----------------------------------------
    def ensure_key(self, path: str, filename: str) -> str:
        return self.AddIniHandler(path, filename, is_global=False)

    def ensure_global_key(self, path: str, filename: str) -> str:
        return self.AddIniHandler(path, filename, is_global=True)


    def add_bool(self, key: str, var_name: str, section: str, name: str, default: bool = False):
        node = self._handlers.get(key)
        if not node:
            return
        node.vars_defs[var_name] = (section, name, default, "bool")

    def add_int(self, key: str, var_name: str, section: str, name: str, default: int = 0):
        node = self._handlers.get(key)
        if not node:
            return
        node.vars_defs[var_name] = (section, name, default, "int")

    def add_float(self, key: str, var_name: str, section: str, name: str, default: float = 0.0):
        node = self._handlers.get(key)
        if not node:
            return
        node.vars_defs[var_name] = (section, name, default, "float")

    def add_str(self, key: str, var_name: str, section: str, name: str, default: str = ""):
        node = self._handlers.get(key)
        if not node:
            return
        node.vars_defs[var_name] = (section, name, default, "str")

    def load_once(self, key: str):
        if not self._is_account_ready():
            return
        
        if not key:
            return

        node = self._handlers.get(key)
        if not node:
            return
        if node.vars_loaded:
            return

        for var_name, (section, name, default, t) in node.vars_defs.items():
            if t == "bool":
                v = self.read_bool(key, section, name, bool(default))
            elif t == "int":
                v = self.read_int(key, section, name, int(default))
            elif t == "float":
                v = self.read_float(key, section, name, float(default))
            else:
                v = self.read_key(key, section, name, str(default))

            node.vars_values[var_name] = v

        node.vars_loaded = True
        
    def get(self, key: str, var_name: str, default=None):
        """
        Get variable value.
        If not loaded yet, falls back to declared default or provided default.
        if loaded, returns current cached value or provided default if not found.
        """
        node = self._handlers.get(key)
        if not node:
            return default

        if var_name in node.vars_values:
            return node.vars_values[var_name]

        # if not loaded yet, fall back to declared default
        d = node.vars_defs.get(var_name)
        if d:
            return d[2]  # default

        return default

    def set(self, key: str, var_name: str, value):
        node = self._handlers.get(key)
        if not node:
            return

        old = node.vars_values.get(var_name, None)
        if old == value:
            return

        node.vars_values[var_name] = value
        node.vars_dirty.add(var_name)

    def save_vars(self, key: str):
        if not self._is_account_ready():
            return
        
        if not key:
            return

        node = self._handlers.get(key)
        if not node:
            return

        if not node.vars_dirty:
            return

        for var_name in list(node.vars_dirty):
            if var_name not in node.vars_defs:
                continue

            section, name, default, t = node.vars_defs[var_name]
            v = node.vars_values.get(var_name, default)

            # stage to throttled writer
            self.write_key(key, section, name, v)

        node.vars_dirty.clear()
        
    def remove_var(self, key: str, var_name: str):
        node = self._handlers.get(key)
        if not node:
            return

        node.vars_defs.pop(var_name, None)
        node.vars_values.pop(var_name, None)
        node.vars_dirty.discard(var_name)
        
    def remove_all_vars(self, key: str):
        node = self._handlers.get(key)
        if not node:
            return

        node.vars_defs.clear()
        node.vars_values.clear()
        node.vars_dirty.clear()
        








IniManager.enable()