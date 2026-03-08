import os
from Py4GWCoreLib.py4gwcorelib_src.Console import Console
from Py4GWCoreLib.py4gwcorelib_src.IniHandler import IniHandler

_INI_SECTION = "EnemyBlacklist"
_INI_KEY = "model_ids"


class EnemyBlacklist:
    """
    Singleton that holds a set of enemy model IDs which should be
    completely ignored by the combat system (no targeting, no aggro detection).
    Persisted to Widgets/Config/HeroAI.ini under [EnemyBlacklist].
    """

    _instance = None
    _class_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._class_initialized:
            return
        self.__class__._class_initialized = True

        base_path = Console.get_projects_path()
        ini_path = os.path.join(base_path, "Widgets", "Config", "HeroAI.ini")
        self._ini = IniHandler(ini_path)
        self._model_ids: set[int] = set()
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self):
        raw = self._ini.read_key(_INI_SECTION, _INI_KEY, "")
        self._model_ids.clear()
        if raw.strip():
            for part in raw.split(","):
                part = part.strip()
                if part.isdigit():
                    self._model_ids.add(int(part))

    def _save(self):
        value = ",".join(str(m) for m in sorted(self._model_ids))
        self._ini.write_key(_INI_SECTION, _INI_KEY, value)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, model_id: int):
        if model_id > 0:
            self._model_ids.add(model_id)
            self._save()

    def remove(self, model_id: int):
        self._model_ids.discard(model_id)
        self._save()

    def contains(self, model_id: int) -> bool:
        return model_id in self._model_ids

    def get_all(self) -> list[int]:
        return sorted(self._model_ids)
