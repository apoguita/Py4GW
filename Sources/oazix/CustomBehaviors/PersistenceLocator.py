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
        self._flagging = PersistenceLocator.FlaggingSettings()
        self._following = PersistenceLocator.FollowingSettings()

    @property
    def skills(self) -> "PersistenceLocator.SkillSettings":
        return self._skills

    @property
    def common(self) -> "PersistenceLocator.CommonSettings":
        return self._common

    @property
    def botting(self) -> "PersistenceLocator.BottingSettings":
        return self._botting

    @property
    def flagging(self) -> "PersistenceLocator.FlaggingSettings":
        return self._flagging

    @property
    def following(self) -> "PersistenceLocator.FollowingSettings":
        return self._following

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

    class FlaggingSettings:
        """Nested class for flagging grid settings with its own INI file (flagging.ini).

        Persists grid_index to email mappings for character positioning.
        Uses global storage (shared across all accounts).
        """

        SECTION = "GridAssignments"
        SECTION_FOLLOW_FLAG = "FollowFlag"

        def __init__(self):
            self._ini_filename = "flagging.ini"
            self._key: str = ""

        def _ensure_key(self) -> str:
            """Ensure the global INI key is created and return it."""
            if not self._key:
                self._key = IniManager().ensure_global_key(PersistenceLocator.INI_PATH, self._ini_filename)
            return self._key

        def read_assignment(self, grid_index: int) -> str | None:
            """Read the email assigned to a grid index.

            Args:
                grid_index: The grid slot index (0-35)

            Returns:
                The email if found, None otherwise.
            """
            key = self._ensure_key()
            if not key:
                return None
            result = IniManager().read_key(key, self.SECTION, str(grid_index), "")
            return result if result != "" else None

        def write_assignment(self, grid_index: int, email: str) -> None:
            """Write an email assignment to a grid index.

            Args:
                grid_index: The grid slot index (0-35)
                email: The account email to assign
            """
            key = self._ensure_key()
            if not key:
                return

            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.write_key(self.SECTION, str(grid_index), email)

        def delete_assignment(self, grid_index: int) -> None:
            """Delete an assignment from a grid index.

            Args:
                grid_index: The grid slot index to clear
            """
            key = self._ensure_key()
            if not key:
                return

            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.delete_key(self.SECTION, str(grid_index))

        def read_all_assignments(self) -> dict[int, str]:
            """Read all grid assignments.

            Returns:
                Dictionary mapping grid_index to email.
            """
            key = self._ensure_key()
            if not key:
                return {}

            node = IniManager()._handlers.get(key)
            if not node:
                return {}

            assignments: dict[int, str] = {}
            keys_dict = node.ini_handler.list_keys(self.SECTION)
            for idx_str, email in keys_dict.items():
                try:
                    grid_index = int(idx_str)
                    if email:
                        assignments[grid_index] = email
                except ValueError:
                    continue

            return assignments

        def clear_all_assignments(self) -> None:
            """Clear all grid assignments."""
            key = self._ensure_key()
            if not key:
                return

            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.delete_section(self.SECTION)

        def read_spacing_radius(self) -> float:
            """Read the spacing radius setting.

            Returns:
                The spacing radius value, or 100.0 as default.
            """
            key = self._ensure_key()
            if not key:
                return 100.0
            result = IniManager().read_key(key, "Settings", "spacing_radius", "")
            if result:
                try:
                    return float(result)
                except ValueError:
                    pass
            return 100.0

        def write_spacing_radius(self, radius: float) -> None:
            """Write the spacing radius setting.

            Args:
                radius: The spacing radius value to save.
            """
            key = self._ensure_key()
            if not key:
                return

            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.write_key("Settings", "spacing_radius", str(radius))

        def read_follow_flag_threshold(self) -> float | None:
            """Read the follow flag normal threshold setting.

            Returns:
                The threshold value, or None if not found.
            """
            key = self._ensure_key()
            if not key:
                return None
            result = IniManager().read_key(key, self.SECTION_FOLLOW_FLAG, "threshold", "")
            if result:
                try:
                    return float(result)
                except ValueError:
                    pass
            return None

        def write_follow_flag_threshold(self, threshold: float) -> None:
            """Write the follow flag normal threshold setting.

            Args:
                threshold: The threshold value to save.
            """
            key = self._ensure_key()
            if not key:
                return

            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.write_key(self.SECTION_FOLLOW_FLAG, "threshold", str(threshold))

        def read_follow_flag_required_threshold(self) -> float | None:
            """Read the follow flag required threshold setting.

            Returns:
                The threshold value, or None if not found.
            """
            key = self._ensure_key()
            if not key:
                return None
            result = IniManager().read_key(key, self.SECTION_FOLLOW_FLAG, "required_threshold", "")
            if result:
                try:
                    return float(result)
                except ValueError:
                    pass
            return None

        def write_follow_flag_required_threshold(self, threshold: float) -> None:
            """Write the follow flag required threshold setting.

            Args:
                threshold: The threshold value to save.
            """
            key = self._ensure_key()
            if not key:
                return

            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.write_key(self.SECTION_FOLLOW_FLAG, "required_threshold", str(threshold))

        def delete_follow_flag_thresholds(self) -> None:
            """Delete both follow flag threshold settings."""
            key = self._ensure_key()
            if not key:
                return

            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.delete_key(self.SECTION_FOLLOW_FLAG, "threshold")
                node.ini_handler.delete_key(self.SECTION_FOLLOW_FLAG, "required_threshold")

    class FollowingSettings:
        """Nested class for following force settings with its own INI file (following.ini).

        Persists per-account force activation settings (allies repulsion, leader attraction, enemies repulsion).
        Uses global storage (shared across all accounts).
        """

        SECTION = "ForceActivations"

        def __init__(self):
            self._ini_filename = "following.ini"
            self._key: str = ""

        def _ensure_key(self) -> str:
            """Ensure the global INI key is created and return it."""
            if not self._key:
                self._key = IniManager().ensure_global_key(PersistenceLocator.INI_PATH, self._ini_filename)
            return self._key

        def read_force_settings(self, account_email: str) -> tuple[bool, bool, bool] | None:
            """Read force activation settings for an account.

            Args:
                account_email: The account email

            Returns:
                Tuple of (allies_repulsion, leader_attraction, enemies_repulsion) if found, None otherwise.
            """
            key = self._ensure_key()
            if not key:
                return None

            node = IniManager()._handlers.get(key)
            if not node:
                return None

            # Read the three force settings
            allies_str = node.ini_handler.read_key(self.SECTION, f"{account_email}_allies_repulsion", "")
            leader_str = node.ini_handler.read_key(self.SECTION, f"{account_email}_leader_attraction", "")
            enemies_str = node.ini_handler.read_key(self.SECTION, f"{account_email}_enemies_repulsion", "")

            # If any setting is missing, return None
            if not allies_str or not leader_str or not enemies_str:
                return None

            # Convert to booleans
            try:
                allies = allies_str.lower() == "true"
                leader = leader_str.lower() == "true"
                enemies = enemies_str.lower() == "true"
                return (allies, leader, enemies)
            except:
                return None

        def write_force_settings(self, account_email: str, allies_repulsion: bool, leader_attraction: bool, enemies_repulsion: bool) -> None:
            """Write force activation settings for an account.

            Args:
                account_email: The account email
                allies_repulsion: Whether allies repulsion is active
                leader_attraction: Whether leader attraction is active
                enemies_repulsion: Whether enemies repulsion is active
            """
            key = self._ensure_key()
            if not key:
                return

            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.write_key(self.SECTION, f"{account_email}_allies_repulsion", str(allies_repulsion))
                node.ini_handler.write_key(self.SECTION, f"{account_email}_leader_attraction", str(leader_attraction))
                node.ini_handler.write_key(self.SECTION, f"{account_email}_enemies_repulsion", str(enemies_repulsion))

        def read_all_force_settings(self) -> dict[str, tuple[bool, bool, bool]]:
            """Read all force settings.

            Returns:
                Dictionary mapping account_email to (allies_repulsion, leader_attraction, enemies_repulsion).
            """
            key = self._ensure_key()
            if not key:
                return {}

            node = IniManager()._handlers.get(key)
            if not node:
                return {}

            settings: dict[str, tuple[bool, bool, bool]] = {}
            keys_dict = node.ini_handler.list_keys(self.SECTION)

            # Group keys by email
            emails_data: dict[str, dict[str, bool]] = {}
            for key_name, value in keys_dict.items():
                # Parse key format: "email_setting_type"
                if "_allies_repulsion" in key_name:
                    email = key_name.replace("_allies_repulsion", "")
                    if email not in emails_data:
                        emails_data[email] = {}
                    emails_data[email]["allies"] = value.lower() == "true"
                elif "_leader_attraction" in key_name:
                    email = key_name.replace("_leader_attraction", "")
                    if email not in emails_data:
                        emails_data[email] = {}
                    emails_data[email]["leader"] = value.lower() == "true"
                elif "_enemies_repulsion" in key_name:
                    email = key_name.replace("_enemies_repulsion", "")
                    if email not in emails_data:
                        emails_data[email] = {}
                    emails_data[email]["enemies"] = value.lower() == "true"

            # Convert to final format (only include complete entries)
            for email, data in emails_data.items():
                if "allies" in data and "leader" in data and "enemies" in data:
                    settings[email] = (data["allies"], data["leader"], data["enemies"])

            return settings

        def clear_all_force_settings(self) -> None:
            """Clear all force settings."""
            key = self._ensure_key()
            if not key:
                return

            node = IniManager()._handlers.get(key)
            if node:
                node.ini_handler.delete_section(self.SECTION)
