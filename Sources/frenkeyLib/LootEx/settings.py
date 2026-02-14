import datetime
from typing import Optional
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib import Player, UIManager
from Py4GWCoreLib.GlobalCache.ItemCache import Bag_enum
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog, Console
from Py4GWCoreLib.enums import ServerLanguage
import json
import os


class FrameCoords:
    def __init__(self, frame_id: int):
        self.frame_id = frame_id
        self.left, self.top, self.right, self.bottom = UIManager.GetFrameCoords(
            self.frame_id)
        self.height = self.bottom - self.top
        self.width = self.right - self.left


class Settings:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # only initialize once
        if self._initialized:
            return
        
        self._initialized = True

        from Sources.frenkeyLib.LootEx.filter import Filter
        from Sources.frenkeyLib.LootEx.profile import Profile
        
        self._initialized = True
        self.profile: Profile | None = None
        self.character_profiles: dict[str, str] = {}
        self.profiles: list[Profile] = []
        self.selected_filter: Optional[Filter] = None
        self.automatic_inventory_handling: bool = False
        self.enable_loot_filters: bool = False
        self.window_size: tuple[float, float] = (800, 600)
        self.window_position: tuple[float, float] = (500, 200)
        self.window_collapsed: bool = False
        self.window_visible: bool = False
        self.scraper_window_visible: bool = False


        self.settings_file_path = os.path.join(Console.get_projects_path(), "Widgets", "Config", "LootEx", f"{Player.GetAccountEmail()}.json")
        self.profiles_path = os.path.join(Console.get_projects_path(), "Widgets", "Config", "LootEx", "Profiles")
        self.data_collection_path = os.path.join(Console.get_projects_path(), "Widgets", "Config", "DataCollection")         
        self.current_character: str = ""
        
        self.inventory_frame_exists: bool = False
        self.inventory_frame_coords: Optional[FrameCoords] = None
        self.parent_frame_id: Optional[int] = None
                
        self.language : ServerLanguage = ServerLanguage.English
        
        self.collect_items: bool = True
        self.last_xunlai_check : datetime.datetime = datetime.datetime.min
        
        self.max_xunlai_storage : Bag_enum = Bag_enum.Storage_4
        
        self.changed = False
        self.development_mode: bool = os.path.exists("C:\\frenkey_development") 
        self.conversions : dict[str, bool] = {}
        
        self.auto_crafting_enabled : bool = False
        self.auto_withdraw_materials : bool = False
        self.auto_even_consets : bool = False
        
    def set_language(self, lang = ServerLanguage.English):
        self.language = lang
        
    
    def ReloadProfiles(self):
        from Sources.frenkeyLib.LootEx.filter import Filter
        from Sources.frenkeyLib.LootEx.profile import Profile
        
        """Reloads the profiles from the profiles directory."""
        self.profiles.clear()
        
        # Load profiles
        for file_name in os.listdir(self.profiles_path):
            if file_name.endswith(".json"):
                profile = Profile(file_name[:-5])
                profile.load()
                self.profiles.append(profile)

        if not self.profiles:
            default_profile = Profile("Default")
            default_profile.save()
            default_profile.load()
            self.profiles.append(default_profile)
        
    def SetProfile(self, profile_name: str | None):
        from Sources.frenkeyLib.LootEx import loot_handling
        from Sources.frenkeyLib.LootEx import inventory_handling
        from Sources.frenkeyLib.LootEx.filter import Filter
        from Sources.frenkeyLib.LootEx.profile import Profile
        
        self.profile = Profile("Default")
        
        if profile_name is not None:            
            for profile in self.profiles:
                if profile.name == profile_name:
                    self.profile = profile
                    break
                
            if self.profile is None:
                self.profile = self.profiles[0] if self.profiles else Profile("Default")
            
            if not self.profiles:
                self.profiles.append(self.profile)
                
        inventory_handling.InventoryHandler().reset()
        
        if self.enable_loot_filters:
            loot_handling.LootHandler().Start()
        else:
            loot_handling.LootHandler().Stop()

        if self.profile:
            inventory_handling.InventoryHandler().SetPollingInterval(self.profile.polling_interval)

    def save(self):
        """Save the settings as a JSON file."""
        settings_dict = {
            "character_profiles":  self.character_profiles,
            "automatic_inventory_handling": self.automatic_inventory_handling,
            "enable_loot_filters": self.enable_loot_filters,
            "window_size": self.window_size,
            "window_position": self.window_position,
            "window_collapsed": self.window_collapsed,
            "collect_items": self.collect_items,
            "max_xunlai_storage": self.max_xunlai_storage.value,
            "last_xunlai_check": self.last_xunlai_check.isoformat(),
            "conversions": self.conversions,
            "auto_crafting_enabled": self.auto_crafting_enabled,
            "auto_withdraw_materials": self.auto_withdraw_materials,
            "auto_even_consets" : self.auto_even_consets,
        }
        # ConsoleLog(
        #     "LootEx", f"Saving settings to '{self.settings_file_path}'...", Console.MessageType.Debug)
        if self.settings_file_path == "":
            return
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(self.settings_file_path), exist_ok=True)
        
        with open(self.settings_file_path, 'w') as file:
            json.dump(settings_dict, file, indent=4)

    def load(self):
        from Sources.frenkeyLib.LootEx.filter import Filter
        from Sources.frenkeyLib.LootEx.profile import Profile
        
        """Load the settings from a JSON file."""

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(self.settings_file_path), exist_ok=True)
        os.makedirs(self.profiles_path, exist_ok=True)
        os.makedirs(self.data_collection_path, exist_ok=True)
        
        # Load profiles
        for file_name in os.listdir(self.profiles_path):
            if file_name.endswith(".json"):
                profile = Profile(file_name[:-5])
                profile.load()
                self.profiles.append(profile)

        if not self.profiles:
            default_profile = Profile("Default")
            default_profile.save()
            default_profile.load()
            self.profiles.append(default_profile)

        try:
            with open(self.settings_file_path, 'r') as file:
                settings_dict = json.load(file)
                self.character_profiles  = settings_dict.get("character_profiles", {})
                self.automatic_inventory_handling = settings_dict.get(
                    "automatic_inventory_handling", False)
                self.enable_loot_filters = settings_dict.get(
                    "enable_loot_filters", False)
                self.window_size = tuple(
                    settings_dict.get("window_size", (400, 200)))
                self.window_position = tuple(
                    settings_dict.get("window_position", (200, 200)))
                self.window_collapsed = settings_dict.get(
                    "window_collapsed", False)
                self.max_xunlai_storage = Bag_enum(
                    settings_dict.get("max_xunlai_storage", Bag_enum.Storage_4.value))
                last_xunlai_check_str = settings_dict.get("last_xunlai_check", None)
                if last_xunlai_check_str:
                    self.last_xunlai_check = datetime.datetime.fromisoformat(
                        last_xunlai_check_str)

                self.collect_items = True # settings_dict.get("collect_items", False)
                self.conversions = settings_dict.get("conversions", {})
                self.auto_crafting_enabled = settings_dict.get("auto_crafting_enabled", False)
                self.auto_withdraw_materials = settings_dict.get("auto_withdraw_materials", False)
                self.auto_even_consets = settings_dict.get("auto_even_consets", False)
        
        except FileNotFoundError:
            ConsoleLog(
                "LootEx",
                f"Settings file for {Player.GetAccountEmail()} not found. Using default settings.",
                Console.MessageType.Warning,
            )