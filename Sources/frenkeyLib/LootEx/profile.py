import os
import json
from Sources.frenkeyLib.LootEx import skin_rule, filter, messaging
from Sources.frenkeyLib.LootEx.filter import Filter
from Sources.frenkeyLib.LootEx.weapon_rule import WeaponRule
from Sources.frenkeyLib.LootEx.item_configuration import *
from Py4GWCoreLib import Console
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog
from Py4GWCoreLib.enums import DyeColor

class RuneConfiguration:
    def __init__(self, identifier: str = "", valuable: bool = False, should_sell: bool = False):
        self.identifier = identifier
        self.valuable = valuable
        self.should_sell = should_sell
        pass
    
    def to_dict(self) -> dict:
        return {
            "identifier": self.identifier,
            "valuable": self.valuable,
            "should_sell": self.should_sell
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'RuneConfiguration':
        rune_config = RuneConfiguration()
        rune_config.valuable = data.get("valuable", False)
        rune_config.should_sell = data.get("should_sell", False)
        rune_config.identifier = data.get("identifier", "")
        
        return rune_config

class ItemConfigurations(dict[ItemType, dict[int, ItemConfiguration]]):
    """A dictionary to hold item configurations by item type and model ID."""
    
    def __init__(self):
        super().__init__()

    def add_item(self, item: models.Item, action: ItemAction = ItemAction.Stash):
        """Add an item configuration to the dictionary."""
        if item.item_type not in self:
            self[item.item_type] = {}
        
        if item.model_id not in self[item.item_type]:
            self[item.item_type][item.model_id] = ItemConfiguration(item.model_id, item.item_type, action)
        else:
            if len(self[item.item_type][item.model_id].conditions) == 1:
                self[item.item_type][item.model_id].conditions[0].action = action
    
    def get_item_config(self, item_type : ItemType, model_id: int) -> ItemConfiguration | None:
        """Get the item configuration for a specific item."""
        if item_type in self and model_id in self[item_type]:
            return self[item_type][model_id]
        
        return None
    
    def delete_item_config(self, item_type : ItemType, model_id: int):
        """Delete an item configuration from the dictionary."""
        
        if item_type in self:            
            if model_id in self[item_type]:
                del self[item_type][model_id]
                
                if not self[item_type]:
                    del self[item_type]

class OldSchoolItemsConfigurations(dict[int, ItemConfiguration]):
    pass

class Profile:
    def __init__(self, profile_name: str):
        self.name = profile_name

        self.dyes = {dye: False for dye in DyeColor if dye != DyeColor.NoColor}
        self.identification_kits: int = 1
        self.salvage_kits: int = 2
        self.expert_salvage_kits: int = 1
        self.lockpicks: int = 10
        self.sell_threshold: int = 200
        self.nick_action: ItemAction = ItemAction.Hold
        self.nick_weeks_to_keep: int = -1
        self.nick_items_to_keep: int = 0
        self.changed : bool = False
        self.polling_interval : float = 1  # Default polling interval in seconds
        self.loot_range : int = 4800
                
        self.deposit_full_stacks: bool = False

        # Collection of Filters
        self.filters: list[filter.Filter] = []
        self.filters_by_item_type: dict[ItemType, list[filter.Filter]] = {}
                
        # Collection of Action Rules
        self.skin_rules: list[skin_rule.SkinRule] = []
        self.skin_rules_by_model: dict[ItemType, dict[int, list[skin_rule.SkinRule]]] = {}        
        
        self.weapon_rules: dict[ItemType, WeaponRule] = {
            item_type: WeaponRule(item_type)
             for item_type in [
                ItemType.Axe,
                ItemType.Bow,
                ItemType.Daggers,
                ItemType.Hammer,
                ItemType.Offhand,
                ItemType.Scythe,
                ItemType.Shield,
                ItemType.Spear,
                ItemType.Staff,
                ItemType.Sword,
                ItemType.Wand
                ]
        }

        self.rune_action: ItemAction = ItemAction.Hold
        self.runes: dict[str, RuneConfiguration] = {}
        
        self.weapon_mod_action: ItemAction = ItemAction.Hold
        self.weapon_mods: dict[str, dict[str, bool]] = {}
        self.blacklist: dict[ItemType, dict[int, bool]] = {}
        
        self.rare_weapons : dict[str, bool] = {}
        from Sources.frenkeyLib.LootEx.data import Data
        self.rare_weapons = {name: True for (name, _) in Data().Rare_Weapon_ModelIds.keys()}
        
        self.even_consets : bool = False
        self.include_storage_materials : bool = False
        self.include_material_storage_materials : bool = False
        self.recipes : dict[str, bool] = {}

    def setup_lookups(self):
        self.filters_by_item_type.clear()
        self.skin_rules_by_model.clear()
        
        for filter in self.filters:
            for item_type in filter.item_types:
                if item_type not in self.filters_by_item_type:
                    self.filters_by_item_type[item_type] = []
                    
                self.filters_by_item_type[item_type].append(filter)
        
        for rule in self.skin_rules:
            if rule.models:
                for model_info in rule.models:
                    if model_info.item_type not in self.skin_rules_by_model:
                        self.skin_rules_by_model[model_info.item_type] = {}
                        
                    if model_info.model_id not in self.skin_rules_by_model[model_info.item_type]:
                        self.skin_rules_by_model[model_info.item_type][model_info.model_id] = []
                    
                    if rule not in self.skin_rules_by_model[model_info.item_type][model_info.model_id]:
                        self.skin_rules_by_model[model_info.item_type][model_info.model_id].append(rule)
            else:
                from Sources.frenkeyLib.LootEx.data import Data
                data = Data()
                
                ## Get all items from data.Items.All which have item.inventory_icon == rule.skin
                items_with_skin = [
                    item for item in data.Items.All
                    if item.inventory_icon == rule.skin
                ]
                
                for item in items_with_skin:
                    if item.item_type not in self.skin_rules_by_model:
                        self.skin_rules_by_model[item.item_type] = {}
                        
                    if item.model_id not in self.skin_rules_by_model[item.item_type]:
                        self.skin_rules_by_model[item.item_type][item.model_id] = []
                        
                    if rule not in self.skin_rules_by_model[item.item_type][item.model_id]:
                        self.skin_rules_by_model[item.item_type][item.model_id].append(rule)
                        
        pass

    def save(self):
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        self.setup_lookups()
        
        """Save the profile as a JSON file."""
        self.changed = True
        
        profile_dict = {
            "name": self.name,            
            "polling_interval": self.polling_interval,
            "loot_range": self.loot_range,
            "deposit_full_stacks": self.deposit_full_stacks,
            "dyes": {dye.name: value for dye, value in self.dyes.items()},
            "identification_kits": self.identification_kits,
            "salvage_kits": self.salvage_kits,
            "expert_salvage_kits": self.expert_salvage_kits,
            "lockpicks": self.lockpicks,
            "sell_threshold": self.sell_threshold,
            "nick_action": self.nick_action.name,
            "nick_weeks_to_keep": self.nick_weeks_to_keep,
            "nick_items_to_keep": self.nick_items_to_keep,
            "rare_weapons": self.rare_weapons,
            "filters": [Filter.to_dict(filter) for filter in self.filters],
            "rules": [
                rule.to_dict() for rule in self.skin_rules
            ],
            "weapon_rules": {
                item_type.name: weapon_rule.to_dict()
                for item_type, weapon_rule in self.weapon_rules.items()
            },
            "rune_action": self.rune_action.name,
            "runes":  {
                rune_identifier: rune_config.to_dict()
                for rune_identifier, rune_config in self.runes.items()
            },
            "weapon_mod_action": self.weapon_mod_action.name,
            "weapon_mods": {
                mod_name: {weapon_type: is_active for weapon_type,
                           is_active in types.items()}
                for mod_name, types in self.weapon_mods.items()
            },
            "blacklist": {
                item_type.name: list(self.blacklist[item_type].keys())
                for item_type in self.blacklist
            },
            "recipes": self.recipes,  
            "even_consets": self.even_consets,
            "include_storage_materials": self.include_storage_materials,
            "include_material_storage_materials": self.include_material_storage_materials,
        }
        
        file_path = os.path.join(
            settings.profiles_path, f"{self.name}.json")

        with open(file_path, 'w') as file:
            # ConsoleLog(
            #     "LootEx", f"Saving profile {self.name}...", Console.MessageType.Debug)
            json.dump(profile_dict, file, indent=4)
        
        messaging.SendReloadProfiles()

    def load(self):
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        """Load the profile from a JSON file."""
        file_path = os.path.join(
            settings.profiles_path, f"{self.name}.json")

        try:
            with open(file_path, 'r') as file:
                profile_dict = json.load(file)
                self.name = profile_dict.get("name", self.name)
                self.polling_interval = profile_dict.get("polling_interval", self.polling_interval)
                self.loot_range = profile_dict.get("loot_range", self.loot_range)
                self.deposit_full_stacks = profile_dict.get("deposit_full_stacks", self.deposit_full_stacks)  
                self.dyes = {DyeColor[dye]: value for dye,
                value in profile_dict.get("dyes", {}).items()}              
                self.identification_kits = profile_dict.get(
                    "identification_kits", self.identification_kits)
                self.salvage_kits = profile_dict.get(
                    "salvage_kits", self.salvage_kits)
                self.expert_salvage_kits = profile_dict.get(
                    "expert_salvage_kits", self.expert_salvage_kits)
                self.lockpicks = profile_dict.get("lockpicks", self.lockpicks)
                self.sell_threshold = profile_dict.get(
                    "sell_threshold", self.sell_threshold)                                
                self.rare_weapons = profile_dict.get(
                    "rare_weapons", self.rare_weapons)
                self.nick_action = ItemAction[profile_dict.get("nick_action", self.nick_action.name)]
                self.nick_weeks_to_keep = profile_dict.get(
                    "nick_weeks_to_keep", self.nick_weeks_to_keep)
                self.nick_items_to_keep = profile_dict.get(
                    "nick_items_to_keep", self.nick_items_to_keep)
                self.filters = [Filter.from_dict(
                    filter) for filter in profile_dict.get("filters", [])]
                
                self.skin_rules = [
                    skin_rule.SkinRule.from_dict(rule) for rule in profile_dict.get("rules", [])
                ]
                
                weapon_rules = profile_dict.get("weapon_rules", False)
                if weapon_rules:
                    self.weapon_rules = {
                        ItemType[item_type]: WeaponRule.from_dict(rule)
                        for item_type, rule in weapon_rules.items()
                    }
                    
                self.rune_action = ItemAction[profile_dict.get("rune_action", self.rune_action.name)]
                self.runes =  {
                    rune_identifier: RuneConfiguration.from_dict(rune_config)
                    for rune_identifier, rune_config in profile_dict.get("runes", {}).items()
                }
                self.weapon_mod_action = ItemAction[profile_dict.get("weapon_mod_action", self.weapon_mod_action.name)]
                self.weapon_mods = {
                    mod_name: {weapon_type: is_active for weapon_type,
                               is_active in types.items()}
                    for mod_name, types in profile_dict.get("weapon_mods", {}).items()
                }
                
                self.blacklist = {
                    ItemType[item_type]: {int(model_id): True for model_id in model_ids}
                    for item_type, model_ids in profile_dict.get("blacklist", {}).items()
                }                     
                self.recipes = profile_dict.get("recipes", self.recipes)
                self.even_consets = profile_dict.get("even_consets", self.even_consets) 
                self.include_storage_materials = profile_dict.get("include_storage_materials", self.include_storage_materials)
                self.include_material_storage_materials = profile_dict.get("include_material_storage_materials", self.include_material_storage_materials)
                                
            self.setup_lookups()
            
        except FileNotFoundError:
            ConsoleLog(
                "LootEx", f"Profile file {file_path} not found. Using default settings.", Console.MessageType.Warning)

    def delete(self):
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        """Delete the profile file."""
        file_path = os.path.join(
            settings.profiles_path, f"{self.name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            ConsoleLog(
                "LootEx", f"Profile {self.name} deleted.", Console.MessageType.Info)
        else:
            ConsoleLog(
                "LootEx", f"Profile file {file_path} not found.", Console.MessageType.Warning)

    def add_filter(self, filter: Filter):
        """Add a filter to the profile."""
        if filter not in self.filters:
            self.filters.append(filter)
            self.changed = True
            
    def remove_filter(self, filter: Filter):
        """Remove a filter from the profile."""
        if filter in self.filters:
            self.filters.remove(filter)
            self.changed = True
    
    def move_filter(self, filter: Filter, new_index: int):
        """Move a filter to a new index in the profile."""
        if filter in self.filters:
            current_index = self.filters.index(filter)
            
            if current_index != new_index:
                self.filters.pop(current_index)
                self.filters.insert(new_index, filter)
                self.changed = True

    def add_rule(self, rule: skin_rule.SkinRule):
        """Add an action rule to the profile."""
        if any(existing_rule.skin == rule.skin for existing_rule in self.skin_rules):
            return
        
        self.skin_rules.append(rule)
        self.changed = True
            
    def remove_rule(self, rule: skin_rule.SkinRule):
        """Remove an action rule from the profile."""
        if rule in self.skin_rules:
            self.skin_rules.remove(rule)
            self.changed = True

    def set_rune(self, rune_identifier: str, is_valuable: bool, should_sell: bool | None = None):
        """Set the value of a rune in the profile."""
        config = self.runes.get(rune_identifier, RuneConfiguration(rune_identifier, is_valuable))
        
        if should_sell is not None and config.should_sell != should_sell:
            config.should_sell = should_sell
        
        if config.valuable != is_valuable:
            config.valuable = is_valuable
            
        self.changed = True
        
        if rune_identifier not in self.runes:
            self.runes[rune_identifier] = config
            return
                
        if not self.runes[rune_identifier].valuable and not self.runes[rune_identifier].should_sell:
            if rune_identifier in self.runes:
                del self.runes[rune_identifier]
        
    def contains_weapon_mod(self, mod_name: str) -> bool:
        """Check if the profile contains a specific weapon mod."""
        return mod_name in self.weapon_mods and any(self.weapon_mods[mod_name].values())
            
    def blacklist_item(self, item_type : ItemType, model_id: int):
        """Blacklist an item in the profile."""      
        if item_type not in self.blacklist:
            self.blacklist[item_type] = {}
            
              
        if model_id not in self.blacklist[item_type]:
            self.blacklist[item_type][model_id] = True

    def whitelist_item(self, item_type : ItemType, model_id: int):
        """Remove an item from the blacklist in the profile."""
        if item_type in self.blacklist:
            if model_id in self.blacklist[item_type]:
                del self.blacklist[item_type][model_id]
                
                if not self.blacklist[item_type]:
                    del self.blacklist[item_type]

    def is_blacklisted(self, item_type : ItemType, model_id: int) -> bool:
        """Check if an item is blacklisted in the profile."""
        return item_type in self.blacklist and model_id in self.blacklist[item_type]