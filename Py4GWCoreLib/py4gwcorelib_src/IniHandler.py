import os
import tempfile
import time
import configparser
from datetime import datetime

# Atomic save() retry budget for the os.replace rename step: a Windows AV or
# search indexer can transiently hold the destination file handle, so retry a
# few times (then fall back to an in-place write) instead of failing the save.
_ATOMIC_SAVE_RETRIES = 3
_ATOMIC_SAVE_RETRY_DELAY_S = 0.01

#region IniHandler
class IniHandler:
    def __init__(self, filename: str):
        """
        Initialize the handler with the given INI file.
        """
        self.filename = filename
        self.last_modified = 0
        self.config = configparser.ConfigParser()
        self.reload()  # Load the config initially

    # ----------------------------
    # Core Methods
    # ----------------------------
    
    def reload(self) -> configparser.ConfigParser:
        """Reload the INI file only if it has changed.
        
        If the file doesn't exist, create an empty file.
        """
        if not os.path.exists(self.filename):
            # Create an empty file if it doesn't exist.
            with open(self.filename, 'w') as f:
                f.write("")
            # Update last_modified since a new file was created.
            self.last_modified = os.path.getmtime(self.filename)
            return self.config

        current_mtime = os.path.getmtime(self.filename)
        if current_mtime != self.last_modified:
            self.last_modified = current_mtime
            try:
                self.config.read(self.filename, encoding="utf-8")
            except (configparser.Error, UnicodeDecodeError, OSError) as exc:
                # Recover from corrupted INI content (for example null-byte files)
                # by backing up the bad file and recreating a clean empty one.
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"{self.filename}.corrupt_{timestamp}"
                    os.replace(self.filename, backup_name)
                except OSError:
                    # Best effort: if backup fails, continue and rewrite in place.
                    pass

                with open(self.filename, "w", encoding="utf-8") as f:
                    f.write("")

                self.config = configparser.ConfigParser()
                self.last_modified = os.path.getmtime(self.filename)
                print(f"[IniHandler] Recovered corrupted INI file: {self.filename} ({exc})")
        return self.config

    def save(self, config: configparser.ConfigParser) -> None:
        """
        Save changes to the INI file atomically.

        Serialize to a temp file in the same directory, flush+fsync, then
        os.replace() it onto the target (an atomic rename on NTFS). This
        prevents torn/half-written files when multiple processes (multibox
        clients) write the same shared INI concurrently: a reader always sees
        either the complete old file or the complete new one. If the rename
        keeps failing (for example an AV/indexer holds the destination), fall
        back to an in-place write so behavior is never worse than before.
        """
        directory = os.path.dirname(self.filename) or "."
        tmp_path = None
        try:
            fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".ini.tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as configfile:
                config.write(configfile)
                configfile.flush()
                os.fsync(configfile.fileno())

            for attempt in range(_ATOMIC_SAVE_RETRIES):
                try:
                    os.replace(tmp_path, self.filename)
                    tmp_path = None  # renamed onto target; nothing to clean up
                    break
                except PermissionError:
                    if attempt == _ATOMIC_SAVE_RETRIES - 1:
                        with open(self.filename, "w", encoding="utf-8") as configfile:
                            config.write(configfile)
                    else:
                        time.sleep(_ATOMIC_SAVE_RETRY_DELAY_S)
        finally:
            if tmp_path is not None:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        self.config = config
        try:
            self.last_modified = os.path.getmtime(self.filename)
        except OSError:
            pass

    # ----------------------------
    # Read Methods
    # ----------------------------

    def read_key(self, section: str, key: str, default_value: str = "") -> str:
        """
        Read a string value from the INI file.
        """
        config = self.reload()
        try:
            return config.get(section, key)
        except (configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    def read_int(self, section: str, key: str, default_value: int = 0) -> int:
        """
        Read an integer value.
        """
        config = self.reload()
        try:
            return config.getint(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    def read_float(self, section: str, key: str, default_value: float = 0.0) -> float:
        """
        Read a float value.
        """
        config = self.reload()
        try:
            return config.getfloat(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    def read_bool(self, section: str, key: str, default_value: bool = False) -> bool:
        """
        Read a boolean value.
        """
        config = self.reload()
        try:
            return config.getboolean(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    # ----------------------------
    # Write Methods
    # ----------------------------

    def write_key(self, section: str, key: str, value) -> None:
        """
        Write or update a key-value pair.
        """
        config = self.reload()
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, key, str(value))
        self.save(config)

    # ----------------------------
    # Delete Methods
    # ----------------------------

    def delete_key(self, section: str, key: str) -> None:
        """
        Delete a specific key.
        """
        config = self.reload()
        if config.has_section(section) and config.has_option(section, key):
            config.remove_option(section, key)
            self.save(config)

    def delete_section(self, section: str) -> None:
        """
        Delete an entire section.
        """
        config = self.reload()
        if config.has_section(section):
            config.remove_section(section)
            self.save(config)

    # ----------------------------
    # Utility Methods
    # ----------------------------

    def list_sections(self) -> list:
        """
        List all sections in the INI file.
        """
        config = self.reload()
        return config.sections()

    def list_keys(self, section: str) -> dict:
        """
        List all keys and values in a section.
        """
        config = self.reload()
        if config.has_section(section):
            return dict(config.items(section))
        return {}

    def has_key(self, section: str, key: str) -> bool:
        """
        Check if a key exists in a section.
        """
        config = self.reload()
        return config.has_section(section) and config.has_option(section, key)

    def clone_section(self, source_section: str, target_section: str) -> None:
        """
        Clone all keys from one section to another.
        """
        config = self.reload()
        if config.has_section(source_section):
            if not config.has_section(target_section):
                config.add_section(target_section)
            for key, value in config.items(source_section):
                config.set(target_section, key, value)
            self.save(config)

#endregion
