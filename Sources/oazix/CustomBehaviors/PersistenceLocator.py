from Py4GWCoreLib import IniManager


class PersistenceLocator:
    _instance = None

    INI_PATH = "Widgets/CustomBehaviors"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PersistenceLocator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._skills = PersistenceLocator.SkillSettings()
        self._common = PersistenceLocator.CommonSettings()
        self._botting = PersistenceLocator.BottingSettings()

    @property
    def skills(self) -> "PersistenceLocator.SkillSettings":
        return self._skills

    @property
    def common(self) -> "PersistenceLocator.CommonSettings":
        return self._common

    @property
    def botting(self) -> "PersistenceLocator.BottingSettings":
        return self._botting

    class SkillSettings:

        def __init__(self):
            self._global_ini_filename = "skills_global.ini"
            self._account_ini_filename = "skills.ini"
            self._global_key: str = ""
            self._account_key: str = ""

        def _ensure_global_key(self) -> str:
            """Ensure the global INI key is created and return it."""
            if not self._global_key:
                self._global_key = IniManager().ensure_global_key(PersistenceLocator.INI_PATH, self._global_ini_filename)
            return self._global_key

        def _ensure_account_key(self) -> str:
            """Ensure the account INI key is created and return it."""
            if not self._account_key:
                self._account_key = IniManager().ensure_key(PersistenceLocator.INI_PATH, self._account_ini_filename)
            return self._account_key

        def read(self, skill_name: str, setting_name: str) -> str | None:
            """Read a string value for a skill setting.

            First tries to read from account-specific settings, then falls back to global.

            Args:
                skill_name: The skill name used as section (e.g., "BloodIsPower")
                setting_name: The setting key (e.g., "enabled")

            Returns:
                The value if found, None otherwise.
            """
            # Try account-specific first
            account_key = self._ensure_account_key()
            if account_key:
                result = IniManager().read_key(account_key, skill_name, setting_name, "")
                if result != "":
                    return result

            # Fall back to global
            global_key = self._ensure_global_key()
            if not global_key:
                return None
            result = IniManager().read_key(global_key, skill_name, setting_name, "")
            return result if result != "" else None

        def read_or_default(self, skill_name: str, setting_name: str, default: str) -> str:
            """Read a string value for a skill setting, returning a default if not found.

            Args:
                skill_name: The skill name used as section (e.g., "BloodIsPower")
                setting_name: The setting key (e.g., "enabled")
                default: Default value if not found

            Returns:
                The value if found, default otherwise.
            """
            result = self.read(skill_name, setting_name)
            return result if result is not None else default

        def write_global(self, skill_name: str, setting_name: str, value: str) -> None:
            """Write a string value for a skill setting to global storage.

            Args:
                skill_name: The skill name used as section (e.g., "BloodIsPower")
                setting_name: The setting key (e.g., "enabled")
                value: The value to write
            """
            key = self._ensure_global_key()
            if not key:
                return

            # Get the node and write directly to ini_handler for immediate disk write
            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.write_key(skill_name, setting_name, value)

        def write_for_account(self, skill_name: str, setting_name: str, value: str) -> None:
            """Write a string value for a skill setting to account-specific storage.

            Args:
                skill_name: The skill name used as section (e.g., "BloodIsPower")
                setting_name: The setting key (e.g., "enabled")
                value: The value to write
            """
            key = self._ensure_account_key()
            if not key:
                return

            # Get the node and write directly to ini_handler for immediate disk write
            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.write_key(skill_name, setting_name, value)

        def delete(self, skill_name: str, setting_name: str) -> None:
            """Delete a setting from both global and account-specific storage.

            Args:
                skill_name: The skill name used as section (e.g., "BloodIsPower")
                setting_name: The setting key (e.g., "enabled")
            """
            # Delete from account-specific
            account_key = self._ensure_account_key()
            if account_key:
                node = IniManager()._handlers.get(account_key)
                if node:
                    node.ini_handler.delete_key(skill_name, setting_name)

            # Delete from global
            global_key = self._ensure_global_key()
            if global_key:
                node = IniManager()._handlers.get(global_key)
                if node:
                    node.ini_handler.delete_key(skill_name, setting_name)

    class CommonSettings:
        """Nested class for common/general settings with its own INI file (common.ini)."""

        def __init__(self):
            self._ini_filename = "common.ini"
            self._section = "General"
            self._key: str = ""

        def _ensure_key(self) -> str:
            """Ensure the INI key is created and return it."""
            if not self._key:
                self._key = IniManager().ensure_global_key(PersistenceLocator.INI_PATH, self._ini_filename)
            return self._key

        def read(self, name: str) -> str | None:
            """Read a string value for a common setting.

            Returns:
                The value if found, None otherwise.
            """
            key = self._ensure_key()
            if not key:
                return None
            result = IniManager().read_key(key, self._section, name, "")
            return result if result != "" else None

        def read_or_default(self, name: str, default: str) -> str:
            """Read a string value for a common setting, returning a default if not found.

            Args:
                name: The setting key
                default: Default value if not found

            Returns:
                The value if found, default otherwise.
            """
            result = self.read(name)
            return result if result is not None else default

        def write(self, name: str, value: str) -> None:
            """Write a string value for a common setting."""
            key = self._ensure_key()
            if not key:
                return

            # Get the node and write directly to ini_handler for immediate disk write
            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.write_key(self._section, name, value)

    class BottingSettings:
        """Nested class for botting utility skills settings with its own INI file (botting.ini).

        Uses global-only storage (no per-account settings).
        """

        def __init__(self):
            self._ini_filename = "botting.ini"
            self._key: str = ""

        def _ensure_key(self) -> str:
            """Ensure the global INI key is created and return it."""
            if not self._key:
                self._key = IniManager().ensure_global_key(PersistenceLocator.INI_PATH, self._ini_filename)
            return self._key

        def read(self, section: str, setting_name: str) -> str | None:
            """Read a string value for a botting setting.

            Args:
                section: The section name (e.g., "PacifistSkills", "AggressiveSkills")
                setting_name: The setting key (e.g., skill name)

            Returns:
                The value if found, None otherwise.
            """
            key = self._ensure_key()
            if not key:
                return None
            result = IniManager().read_key(key, section, setting_name, "")
            return result if result != "" else None

        def read_or_default(self, section: str, setting_name: str, default: str) -> str:
            """Read a string value for a botting setting, returning a default if not found.

            Args:
                section: The section name
                setting_name: The setting key
                default: Default value if not found

            Returns:
                The value if found, default otherwise.
            """
            result = self.read(section, setting_name)
            return result if result is not None else default

        def write(self, section: str, setting_name: str, value: str) -> None:
            """Write a string value for a botting setting to global storage.

            Args:
                section: The section name (e.g., "PacifistSkills", "AggressiveSkills")
                setting_name: The setting key
                value: The value to write
            """
            key = self._ensure_key()
            if not key:
                return

            # Get the node and write directly to ini_handler for immediate disk write
            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.write_key(section, setting_name, value)

        def delete_section(self, section: str) -> None:
            """Delete an entire section from the botting settings.

            Args:
                section: The section name to delete
            """
            key = self._ensure_key()
            if not key:
                return

            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.delete_section(section)

        def delete(self, section: str, setting_name: str) -> None:
            """Delete a specific setting from the botting settings.

            Args:
                section: The section name
                setting_name: The setting key to delete
            """
            key = self._ensure_key()
            if not key:
                return

            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.delete_key(section, setting_name)
