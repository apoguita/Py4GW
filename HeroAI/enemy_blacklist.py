from Py4GWCoreLib.IniManager import IniManager

_INI_SECTION = "EnemyBlacklist"
_INI_KEY = "model_ids"


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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
