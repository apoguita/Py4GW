import os
import configparser

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
            self.config.read(self.filename)
        return self.config

    def save(self, config: configparser.ConfigParser) -> None:
        """
        Save changes to the INI file.
        """
        with open(self.filename, 'w') as configfile:
            config.write(configfile)

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