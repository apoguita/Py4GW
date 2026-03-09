from Py4GWCoreLib.IniManager import IniManager

_INI_SECTION = "EnemyBlacklist"
_INI_KEY = "model_ids"
_INI_KEY_NAMES = "names"


class EnemyBlacklist:
    """
    Singleton that manages a set of enemy model IDs which should be
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
        from Py4GWCoreLib import Agent
        if Agent.GetModelID(agent_id) in self._read():
            return True
        names = self._read_names()
        if names:
            agent_name = Agent.GetNameByID(agent_id)
            if agent_name and agent_name.lower() in names:
                return True
        return False
