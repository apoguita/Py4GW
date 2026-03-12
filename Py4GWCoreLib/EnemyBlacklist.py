import PyImGui

from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib import ImGui
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.enums_src.Model_enums import ModelID

_INI_SECTION = "EnemyBlacklist"
_INI_KEY = "model_ids"
_INI_KEY_NAMES = "names"


class EnemyBlacklist:
    """
    Singleton that manages a set of enemy model IDs and names which should be
    completely ignored by the combat system (no targeting, no aggro detection).

    Persisted to Settings/Global/HeroAI/EnemyBlacklist.ini.
    The IniHandler reloads the file whenever its mtime changes, so changes
    made by any other game instance are picked up automatically on the next
    call to contains() / get_all().
    """

    _instance = None
    _class_initialized = False
    _ini_key: str = ""

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._class_initialized:
            return
        self.__class__._class_initialized = True
        self._ensure_ini_key()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_ini_key(self):
        if not self.__class__._ini_key:
            self.__class__._ini_key = IniManager().ensure_global_key("HeroAI", "EnemyBlacklist.ini")

    def _handler(self):
        self._ensure_ini_key()
        node = IniManager()._get_node(self.__class__._ini_key)
        return node.ini_handler if node else None

    def _read(self) -> set[int]:
        handler = self._handler()
        if not handler:
            return set()
        raw = handler.read_key(_INI_SECTION, _INI_KEY, "")
        ids: set[int] = set()
        if raw.strip():
            for part in raw.split(","):
                part = part.strip()
                if part.isdigit():
                    ids.add(int(part))
        return ids

    def _write(self, ids: set[int]):
        handler = self._handler()
        if not handler:
            return
        value = ",".join(str(m) for m in sorted(ids))
        handler.write_key(_INI_SECTION, _INI_KEY, value)
        handler.save(handler.config)

    def _read_names(self) -> set[str]:
        handler = self._handler()
        if not handler:
            return set()
        raw = handler.read_key(_INI_SECTION, _INI_KEY_NAMES, "")
        names: set[str] = set()
        if raw.strip():
            for part in raw.split("|"):
                stripped = part.strip().lower()
                if stripped:
                    names.add(stripped)
        return names

    def _write_names(self, names: set[str]):
        handler = self._handler()
        if not handler:
            return
        value = "|".join(sorted(names))
        handler.write_key(_INI_SECTION, _INI_KEY_NAMES, value)
        handler.save(handler.config)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_empty(self) -> bool:
        """True if neither model-ID list nor name list contains any entries."""
        return not self._read() and not self._read_names()

    def add(self, model_id: int):
        if model_id > 0:
            ids = self._read()
            ids.add(model_id)
            self._write(ids)

    def remove(self, model_id: int):
        ids = self._read()
        ids.discard(model_id)
        self._write(ids)

    def contains(self, model_id: int) -> bool:
        return model_id in self._read()

    def get_all(self) -> list[int]:
        return sorted(self._read())

    def add_name(self, name: str):
        name = name.strip().lower()
        if name:
            names = self._read_names()
            names.add(name)
            self._write_names(names)

    def remove_name(self, name: str):
        names = self._read_names()
        names.discard(name.strip().lower())
        self._write_names(names)

    def get_all_names(self) -> list[str]:
        return sorted(self._read_names())

    def is_blacklisted(self, agent_id: int) -> bool:
        """Returns True if the agent should be ignored (by model ID or by name)."""
        if Agent.GetModelID(agent_id) in self._read():
            return True
        names = self._read_names()
        if names:
            agent_name = Agent.GetNameByID(agent_id)
            if agent_name and agent_name.lower() in names:
                return True
        return False


# ------------------------------------------------------------------
# UI — shared between HeroAI configure window and CB botting panel
# ------------------------------------------------------------------

_blacklist_input: str = ""
_blacklist_name_input: str = ""


def draw_blacklist_ui():
    """Render the enemy blacklist UI (model ID and name). Usable from any widget."""
    global _blacklist_input, _blacklist_name_input

    blacklist = EnemyBlacklist()

    PyImGui.text("Blacklisted enemies are completely ignored by the combat")
    PyImGui.text("system: no targeting, no aggro detection.")
    PyImGui.spacing()

    # ----------------------------------------------------------------
    # Section: Model ID
    # ----------------------------------------------------------------
    PyImGui.text("By Model ID")
    PyImGui.set_next_item_width(120)
    _blacklist_input = PyImGui.input_text("##bl_input", _blacklist_input, 16)
    ImGui.show_tooltip("Enter a numeric model ID and press Add.")
    PyImGui.same_line(0.0, 5.0)
    if PyImGui.button("Add##bl_add"):
        val = _blacklist_input.strip()
        if val.isdigit() and int(val) > 0:
            blacklist.add(int(val))
            _blacklist_input = ""
    PyImGui.same_line(0.0, 5.0)
    if PyImGui.button(f"{IconsFontAwesome5.ICON_CROSSHAIRS} Add Target##bl_target"):
        target_id = Player.GetTargetID()
        if target_id and target_id > 0:
            model_id = Agent.GetModelID(target_id)
            if model_id > 0:
                blacklist.add(model_id)
    ImGui.show_tooltip("Add the Model ID of the currently selected target to the blacklist.")

    PyImGui.spacing()
    entries = blacklist.get_all()
    if len(entries) == 0:
        PyImGui.text("(empty)")
    else:
        table_flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.ScrollY
        if PyImGui.begin_table("##bl_table", 3, table_flags, 0, 150):
            PyImGui.table_setup_column("Model ID", PyImGui.TableColumnFlags.WidthFixed, 80)
            PyImGui.table_setup_column("Name", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("##bl_remove_col", PyImGui.TableColumnFlags.WidthFixed, 65)
            PyImGui.table_headers_row()

            to_remove = None
            for model_id in entries:
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text(str(model_id))
                PyImGui.table_set_column_index(1)
                try:
                    name = ModelID(model_id).name.replace("_", " ")
                except ValueError:
                    name = "Unknown"
                PyImGui.text(name)
                PyImGui.table_set_column_index(2)
                if PyImGui.button(f"Remove##{model_id}"):
                    to_remove = model_id
            PyImGui.end_table()

            if to_remove is not None:
                blacklist.remove(to_remove)

    PyImGui.spacing()

    # ----------------------------------------------------------------
    # Section: Name (enc string / display name)
    # ----------------------------------------------------------------
    PyImGui.text("By Name")
    PyImGui.set_next_item_width(200)
    _blacklist_name_input = PyImGui.input_text("##bl_name_input", _blacklist_name_input, 64)
    ImGui.show_tooltip("Enter the display name of an enemy (case-insensitive) and press Add.")
    PyImGui.same_line(0.0, 5.0)
    if PyImGui.button("Add##bl_name_add"):
        val = _blacklist_name_input.strip()
        if val:
            blacklist.add_name(val)
            _blacklist_name_input = ""
    PyImGui.same_line(0.0, 5.0)
    if PyImGui.button(f"{IconsFontAwesome5.ICON_CROSSHAIRS} Add Target##bl_name_target"):
        target_id = Player.GetTargetID()
        if target_id and target_id > 0:
            name = Agent.GetNameByID(target_id)
            if name:
                blacklist.add_name(name)
    ImGui.show_tooltip("Add the display name of the currently selected target to the blacklist.")

    PyImGui.spacing()
    name_entries = blacklist.get_all_names()
    if len(name_entries) == 0:
        PyImGui.text("(empty)")
    else:
        table_flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.ScrollY
        if PyImGui.begin_table("##bl_name_table", 2, table_flags, 0, 150):
            PyImGui.table_setup_column("Name", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("##bl_nremove_col", PyImGui.TableColumnFlags.WidthFixed, 65)
            PyImGui.table_headers_row()

            to_remove_name = None
            for entry_name in name_entries:
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text(entry_name)
                PyImGui.table_set_column_index(1)
                if PyImGui.button(f"Remove##n_{entry_name}"):
                    to_remove_name = entry_name
            PyImGui.end_table()

            if to_remove_name is not None:
                blacklist.remove_name(to_remove_name)
