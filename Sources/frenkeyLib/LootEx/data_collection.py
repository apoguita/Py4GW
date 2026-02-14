from enum import IntEnum
import json
import os
import re
from typing import Optional, Sequence

from Py4GW import Console
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.ItemCache import Bag_enum
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.enums_src.GameData_enums import Attribute, Profession
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.enums_src.UI_enums import NumberPreference
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Sources.frenkeyLib.Core.utility import string_similarity
from Sources.frenkeyLib.LootEx import messaging, ui_manager_extensions, utility
from Sources.frenkeyLib.LootEx.cache import Cached_Item
from Sources.frenkeyLib.LootEx.enum import ALL_BAGS, ITEM_TEXTURE_FOLDER, ModType
from Sources.frenkeyLib.LootEx.models import Item, ItemModifiersInformation, ItemsByType, WeaponMod

class CollectionStatus(IntEnum):
    Unknown = 0
    NameRequested = 1
    NameCollected = 2
    RequiresSave = 3
    
    BetterDataFound = 9
    DataCollected = 10

class CollectionEntry(Item):
    def __init__(self, item_id: int, modified_items: ItemsByType):                                       
        item_type_value, _ = GLOBAL_CACHE.Item.GetItemType(item_id)
        item_type : ItemType = ItemType(item_type_value) if item_type_value in ItemType._value2member_map_ else ItemType.Unknown        
        
        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
        
        super().__init__(model_id, item_type)        
        self.from_data(model_id, item_type, modified_items)
        
        self.item_id = item_id
        self.status = CollectionStatus.Unknown
        self.changed : bool = False
        
        rarity, _ = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
        self.rarity = Rarity(rarity) if rarity in Rarity._value2member_map_ else Rarity.White
        self.quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
        self.salvageable = GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id)
        
        self.raw_name = ""
        self.unformatted_name = ""    
        self.mods_info = ItemModifiersInformation.GetModsFromModifiers(GLOBAL_CACHE.Item.Customization.Modifiers.GetModifiers(self.item_id), self.item_type, self.model_id, GLOBAL_CACHE.Item.Customization.IsInscribable(self.item_id))

        
        self.get_profession()
        self.get_attributes()
        self.get_model_file_id()
            
    def get_model_file_id(self):
        model_file_id = GLOBAL_CACHE.Item.GetModelFileID(self.item_id)
        if model_file_id != self.model_file_id:
            self.model_file_id = model_file_id
            self.changed = True
    
    def get_attributes(self):    
        if utility.Util.IsWeaponType(self.item_type):
            if self.mods_info.attribute != Attribute.None_ and self.mods_info.attribute not in self.attributes:
                self.attributes = self.attributes + [self.mods_info.attribute]
                self.changed = True
        else:
            if len(self.attributes) > 0:
                self.changed = True
                
            self.attributes = []
            return
    
    def get_profession(self):  
        pv = GLOBAL_CACHE.Item.Properties.GetProfession(self.item_id)
        profession = Profession(pv) if pv in Profession._value2member_map_ else None
        if profession and profession != Profession._None:
            if profession != self.profession:
                self.profession = profession
                self.changed = True
                    
    def from_data(self, model_id: int, item_type: ItemType, modified_items: ItemsByType):
        from Sources.frenkeyLib.LootEx.data import Data
        data = Data()
        
        item_data = modified_items.get_item(item_type, model_id) or data.Items.get_item(item_type, model_id)
        self.model_id = model_id
        self.item_type = item_type
        
        if item_data is not None:                    
            self.model_id = item_data.model_id
            self.model_file_id = item_data.model_file_id
            self.item_type = item_data.item_type
            self.name = item_data.name
            self.names = item_data.names.copy()
            self.acquisition = item_data.acquisition
            self.attributes = item_data.attributes.copy()
            self.wiki_url = item_data.wiki_url
            self.common_salvage = item_data.common_salvage
            self.rare_salvage = item_data.rare_salvage
            self.nick_index = item_data.nick_index
            self.profession = item_data.profession
            self.contains_amount = item_data.contains_amount
            self.inventory_icon = item_data.inventory_icon
            self.inventory_icon_url = item_data.inventory_icon_url
            self.category = item_data.category
            self.sub_category = item_data.sub_category
            self.wiki_scraped = item_data.wiki_scraped
            self.is_account_data = item_data.is_account_data            
            
    def request_name(self):
        ConsoleLog("LootEx DataCollector", f"Requesting name for item ID: {self.item_id}...", Console.MessageType.Debug)
        GLOBAL_CACHE._ActionQueueManager.AddAction("ACTION", lambda: GLOBAL_CACHE.Item.GetName(self.item_id))
        self.status = CollectionStatus.NameRequested
        
    def set_name(self, name: str, language: ServerLanguage = ServerLanguage.English):
        self.raw_name = name
        self.unformatted_name = self.get_name_unformatted(name)
        self.get_mods_names(self.unformatted_name, language)
        
        final_name = self.get_cleaned_item_name(self.unformatted_name, language)
        
        if final_name:
            self.names[language] = final_name
            self.status = CollectionStatus.NameCollected
                        
            self.changed = True
            self.update_language(language)
            
    def reformat_string(self, item_name: str) -> str:
        # split on uppercase letters
        item_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", item_name)

        # replace underscores with spaces
        item_name = item_name.replace("_", " ")

        # replace multiple spaces with a single space
        item_name = re.sub(r"\s+", " ", item_name)

        # strip leading and trailing spaces
        item_name = item_name.strip()

        return item_name
    
    def get_name_unformatted(self, item_name) -> str:
        #Remove markups <c=..>...</c> etc.
        while True:
            new_item_name = re.sub(r"<c=[^>]+>(.*?)</c>", r"\1", item_name)
            if new_item_name == item_name:
                break
            
            item_name = new_item_name
            
        return item_name.strip()
    
    def get_cleaned_item_name(self, item_name : str, server_language: ServerLanguage) -> str:  
        from Sources.frenkeyLib.LootEx.data import Data
        data = Data()
        
        from Sources.frenkeyLib.LootEx.models import RuneModInfo, WeaponModInfo
                
        if item_name == "STRING DO NOT LOCALIZE":
            item = data.Items.get_item(self.item_type, self.model_id)
            if item is not None:
                item_name = item.names.get(ServerLanguage.English, "")

        if item_name is None or item_name == "":
            return ""

        if self.rarity == Rarity.Green:
            # If the item is a green item, we don't need to cleanup the item name
            return item_name
                
        if utility.Util.IsWeaponType(self.item_type) or utility.Util.IsArmorType(self.item_type) or self.item_type == ItemType.Rune_Mod:
            mods, runes = self.mods_info.weapon_mods, self.mods_info.runes
            is_identified = GLOBAL_CACHE.Item.Usage.IsIdentified(self.item_id)

            if not is_identified and not GLOBAL_CACHE.Item.Properties.IsCustomized(self.item_id) and (utility.Util.IsWeaponType(self.item_type) or self.item_type == ItemType.Salvage):
                return item_name.strip()

            if len(mods) > 0:
                for mod in mods:                    
                    suffix = ("Minor" if mod.Rune.rarity == Rarity.Blue else "Major" if mod.Rune.rarity == Rarity.Purple else "Superior" if mod.Rune.rarity == Rarity.Gold else "") if mod in runes and isinstance(mod, RuneModInfo) else ""
                    
                    if mod.Mod.mod_type == ModType.Inherent:
                        # If the mod is inherent, we don't need to cleanup the item name as its not affected by the mod
                        continue
                    
                    if mod.Mod.mod_type == ModType.Prefix:
                        if self.item_type == ItemType.Rune_Mod or not GLOBAL_CACHE.Item.Customization.IsPrefixUpgradable(self.item_id):
                            continue
                        
                    if mod.Mod.mod_type == ModType.Suffix:
                        if not GLOBAL_CACHE.Item.Customization.IsSuffixUpgradable(self.item_id):
                            continue

                    if server_language == ServerLanguage.Italian:
                        ## Get all gender versions of the mod name and replace them
                        for c in ("o", "a", "i", "e"):
                            ## replace the last chacter with the current character
                            mod_name = mod.Mod.applied_name[:-1] + c
                            item_name = item_name.replace(mod_name, "").strip()
                    
                    item_name = item_name.replace(mod.Mod.applied_name, "").strip()
                    
                    if item_name.startswith("-"):
                        item_name = item_name[1:].strip()
                    
                    if self.item_type == ItemType.Rune_Mod:
                        item_name += f" ({suffix})"
                        
            if self.item_type == ItemType.Rune_Mod:
                if utility.Util.is_inscription_model_item(self.model_id):
                    inscription = {
                        ServerLanguage.English: r"Inscription",
                        ServerLanguage.German: r"Inschrift",
                        ServerLanguage.French: r"Inscription",
                        ServerLanguage.Spanish: r"Inscripción",
                        ServerLanguage.Italian: r"Iscrizione",
                        ServerLanguage.TraditionalChinese: r"鑄印",
                        ServerLanguage.Korean: r"마력석",
                        ServerLanguage.Japanese: r"刻印",
                        ServerLanguage.Polish: r"Inskrypcja",
                        ServerLanguage.Russian: r"Надпись",
                        ServerLanguage.BorkBorkBork: r"Inscreepshun"
                    }

                    target_item_type = utility.Util.get_target_item_type_from_mod(self.item_id)
                    
                    # If the item is an inscription model item, we don't need to cleanup the item name
                    return f"{inscription.get(server_language, 'Inscription')}: {self.reformat_string(target_item_type.name) if target_item_type else ''}".strip()       

        if self.quantity > 1:
            item_name = item_name.replace(str(self.quantity), "250").strip()

        return item_name
    
    def get_mods_names(self, item_name, server_language: ServerLanguage):  
        from Sources.frenkeyLib.LootEx.data import Data
        data = Data()
        
        global save_weapon_mods

        def extract_mod_name(item_name : str, mod_type: ModType = ModType.None_) -> Optional[str]:
            patterns = {}

            match mod_type:
                case ModType.Prefix:
                    patterns = {}

                case ModType.Inherent:
                    patterns = {
                        ServerLanguage.English: r"Inscription: ",
                        ServerLanguage.German: r"Inschrift: ",
                        ServerLanguage.French: r"Inscription : ",
                        ServerLanguage.Spanish: r"Inscripción: ",
                        ServerLanguage.Italian: r"Iscrizione: ",
                        ServerLanguage.TraditionalChinese: r"鑄印：",
                        ServerLanguage.Korean: r"마력석:",
                        ServerLanguage.Japanese: r"刻印：",
                        ServerLanguage.Polish: r"Inskrypcja: ",
                        ServerLanguage.Russian: r"Надпись: ",
                        ServerLanguage.BorkBorkBork: r"Inscreepshun: "
                    }

                case ModType.Suffix:
                    patterns = {
                        ServerLanguage.English: r"^.*?(?= of)",
                        ServerLanguage.German: r"^.*(?= d\.)",
                        ServerLanguage.French: r"^.*?(?=\()",
                        ServerLanguage.Spanish: r"^.*?(?=\()",
                        ServerLanguage.Italian: r"^.*(?= del)",
                        ServerLanguage.TraditionalChinese: r" .*$",
                        ServerLanguage.Japanese: r"^.*?(?=\()",
                        ServerLanguage.Korean: r"^.*?(?=\()",
                        ServerLanguage.Polish: r"^.*?(?=\()",
                        ServerLanguage.Russian: r"^.*?(?= of)",
                        ServerLanguage.BorkBorkBork: r"^.*?(?= ooff)",
                    }

            pattern = patterns.get(server_language, None)

            if item_name is None or item_name == "" or pattern is None:
                return None

            if pattern:
                item_name = re.sub(pattern, '', item_name)
            return item_name.strip()

        is_identified = GLOBAL_CACHE.Item.Usage.IsIdentified(self.item_id)
        if not is_identified and self.item_type != ItemType.Rune_Mod:
            return
    
        if self.item_type == ItemType.Rune_Mod:
            mods = self.mods_info.weapon_mods

            if len(mods) > 0:
                for mod in mods:
                    if not mod.WeaponMod.identifier in data.Weapon_Mods:
                        continue

                    if not data.Weapon_Mods[mod.WeaponMod.identifier].names:
                        data.Weapon_Mods[mod.WeaponMod.identifier].names = {}
                    mod_name = extract_mod_name(item_name, mod.WeaponMod.mod_type)
                    if mod_name == "" or mod_name is None:
                        continue

                    if utility.Util.is_inscription_model_item(self.model_id) != (mod.Mod.mod_type == ModType.Inherent):
                        continue

                    item_type = utility.Util.get_target_item_type_from_mod(
                        self.item_id) if self.item_type == ItemType.Rune_Mod else self.item_type

                    if item_type == None:
                        continue

                    item_type_match = any(utility.Util.IsMatchingItemType(
                        item_type, target_type) for target_type in mod.WeaponMod.target_types) if mod.WeaponMod.target_types else True

                    if item_type_match is False:
                        continue

                    if server_language in data.Weapon_Mods[mod.WeaponMod.identifier].names and data.Weapon_Mods[mod.WeaponMod.identifier].names[server_language] is not None:
                        # ConsoleLog(
                        #     "LootEx", f"Mod name already exists for {self.server_language.name}: {data.Weapon_Mods[index].names[self.server_language]} ({item_id})", Console.MessageType.Debug)
                        continue

                    if mod.WeaponMod.mod_type == ModType.Prefix:
                        # There is no way to gurantee to get the correct prefix name without knowing the item name
                        continue

                    if mod.WeaponMod.mod_type == ModType.Inherent:
                        ConsoleLog(
                            "LootEx", f"Setting Inherent mod name for: {data.Weapon_Mods[mod.WeaponMod.identifier].applied_name} to {mod_name}", Console.MessageType.Debug)
                        data.Weapon_Mods[mod.WeaponMod.identifier].set_name(
                            mod_name, server_language)
                        DataCollector().modified_weapon_mods[mod.WeaponMod.identifier] = data.Weapon_Mods[mod.WeaponMod.identifier]
                        continue

                    if mod.WeaponMod.mod_type == ModType.Suffix:
                        ConsoleLog(
                            "LootEx", f"Setting Suffix mod name for: {data.Weapon_Mods[mod.WeaponMod.identifier].applied_name} to {mod_name}", Console.MessageType.Debug)
                        data.Weapon_Mods[mod.WeaponMod.identifier].set_name(
                            mod_name, server_language)
                        save_weapon_mods = True
                        DataCollector().modified_weapon_mods[mod.WeaponMod.identifier] = data.Weapon_Mods[mod.WeaponMod.identifier]
                        continue

class DataCollector:
    LOG_DATA_COLLECTION = True
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DataCollector, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
    
        from Sources.frenkeyLib.LootEx.settings import Settings
        
        self.settings = Settings()
        self.modified_weapon_mods: dict[str, WeaponMod] = {}
        
        self.ready = False
        self.initialize()        
        self._initialized = True
        
        self.modified_items: ItemsByType
        self.server_language = ServerLanguage.Unknown
        self.collected_items : dict[int, CollectionEntry] = {}
                
        self.throttle = ThrottledTimer(1250)
        self.throttle.Start()
        
        self.fetched_cycles = 0
        self.existing_files : dict[str, bool] = {}
        
        self.wiki_scraped_items : dict[tuple[ItemType, int], bool] = {}

    def initialize(self):
        if self.ready:
            return
        
        account_mail = Player.GetAccountEmail()
        ready = self.settings.data_collection_path != "" and account_mail != ""
        
        if not ready:
            return
        
        account_file = os.path.join(self.settings.data_collection_path, account_mail, "items.json")
        account_items = {}
        
        ConsoleLog("LootEx DataCollector", f"Loading existing collected items from {account_file}...", Console.MessageType.Info)
        if os.path.exists(account_file):
            with open(account_file, 'r', encoding='utf-8') as file:
                account_items = json.load(file)
                
        self.modified_items = ItemsByType.from_dict(account_items)
        self.ready = True
    
    def file_exists(self, inventory_icon: str) -> bool:
        if not inventory_icon or inventory_icon == "":
            return False
        
        if inventory_icon not in self.existing_files:
            self.existing_files[inventory_icon] = os.path.exists(os.path.join(ITEM_TEXTURE_FOLDER, f"{inventory_icon}"))
        
        return self.existing_files[inventory_icon]
    
    def is_missing_localization(self, item: Cached_Item) -> tuple[bool, str]:
        if item.id is None or item.id <= 0:
            return False, "Invalid item ID"
        
        if item.data is None:
            return True, "No item data available"
        
        missing_languages = "Missing languages: \n"
        missing = False
        for language in ServerLanguage:
            if language == ServerLanguage.Unknown:
                continue
            
            if language not in item.data.names or item.data.names[language] is None or item.data.names[language] == "":
                missing_languages += f"- {language.name}\n"
                missing = True
    

        return missing, missing_languages
    
    def has_uncollected_mods(self, item : Cached_Item) -> tuple[bool, str]:
        if not item.id or item.id <= 0:
            return False, "Invalid item ID"
                
        if len(item.mods) == 0 or not (utility.Util.CanHoldMod(item.item_type)):
            return False, "No mods found for item"
                
        inherent = GLOBAL_CACHE.Item.Customization.IsInscribable(item.id) and not utility.Util.is_inscription_model_item(item.model_id)
        prefixes = GLOBAL_CACHE.Item.Customization.IsPrefixUpgradable(item.id)
        suffixes = GLOBAL_CACHE.Item.Customization.IsSuffixUpgradable(item.id)
        
        if not inherent and not prefixes and not suffixes:
            return False, "Item has no upgradable mods"
        
        collected_item = self.collected_items.get(item.id, None)
        if collected_item is None:
            return True, "Item not collected yet"
        
        
        for mod in collected_item.mods_info.mods:
            if not mod.Mod.upgrade_exists:
                continue
            
            if mod.Mod.mod_type == ModType.Inherent:
                if not inherent:
                    continue
                
            if mod.Mod.mod_type == ModType.Prefix:
                if not prefixes:
                    continue
                
            if mod.Mod.mod_type == ModType.Suffix:
                if not suffixes:
                    continue

            missing_language = mod.Mod.has_missing_names()
            if missing_language:
                return True, f"Missing {missing_language.name} mod name for {mod.Mod.names.get(ServerLanguage.English, mod.Mod.name)}"
            
        return False, "All mods are collected or unnecessary to collect"
        
    def is_item_collected(self, item: Cached_Item) -> tuple[bool, str]:        
        has_item = self.hasItem(item.id)
        return has_item, "Item data is complete" if has_item else "Item data is incomplete"
            
    def hasItem(self, item_id: int) -> bool:
        if item_id <= 0:
            return True
        
        item = self.collected_items.get(item_id, None)
        
        if item is None:        
            return False
        
        if item.status not in [CollectionStatus.DataCollected, CollectionStatus.BetterDataFound]:
            return False
    
        if not utility.Util.IsArmorType(item.item_type) and not self.file_exists(item.inventory_icon or ""):
            return False
    
        if item.salvageable and (not item.common_salvage or len(item.common_salvage) == 0) and (not item.rare_salvage or len(item.rare_salvage) == 0):
            return False
    
        return True
    
    def reset(self):
        if self.collected_items:
            ConsoleLog("LootEx DataCollector", f"Resetting data collector. Cleared {len(self.collected_items)} collected items.", Console.MessageType.Info)
        
        # self.throttle.Stop()
        self.fetched_cycles = 0
        self.collected_items.clear()
        self.reset_cache()
        GLOBAL_CACHE._reset()
    
    def reset_cache(self):
        GLOBAL_CACHE.Item.name_cache.clear()
        GLOBAL_CACHE.Item.name_requested.clear()
        
        preference = UIManager.GetIntPreference(NumberPreference.TextLanguage)
        server_language = ServerLanguage(preference)
        
        items_to_remove = []
        for _, entry in self.collected_items.items():
            if entry.status is not CollectionStatus.BetterDataFound:
                if not entry.has_name(server_language):
                    items_to_remove.append(entry.item_id)
                    
        for item_id in items_to_remove:
            del self.collected_items[item_id]
            
    def auto_assign_scraped_data(self, item: Item | None):
        if item is None:
            return
        
        english_name = item.names.get(ServerLanguage.English, "")
        if not english_name or english_name == "":
            return
        
        ConsoleLog("LootEx DataCollector", f"Auto-assigning scraped data for item: {english_name}...", Console.MessageType.Info)
        
        from Sources.frenkeyLib.LootEx.data import Data
        data = Data()
        
        ## Check if the name starts with an amount like "250"
        parts = english_name.split(" ", 1) if english_name else []
        contains_amount = len(parts) == 2 and parts[0].isdigit()
                
        search_name = english_name.replace(parts[0], "").strip() if contains_amount else english_name
        required_similarity = 0.95 if contains_amount else 1.0
        
        matching_scraped_items = [scraped_item for (key, scraped_item) in data.ScrapedItems.items() if string_similarity(scraped_item.name, search_name) >= required_similarity]
        if matching_scraped_items and len(matching_scraped_items) == 1:
            item.assign_scraped_data(matching_scraped_items[0], data)
            self.modified_items.add_item(item)
            
    def save_items(self):
        from Sources.frenkeyLib.LootEx.data import Data
        data = Data()
        
        for _, entry in self.collected_items.items():
            if entry.status == CollectionStatus.RequiresSave:
                if entry.names:
                    self.modified_items.add_item(entry)
            item = data.Items.get_item(entry.item_type, entry.model_id)
            
            if item is not None:
                item.update(entry)
            else:
                data.Items.add_item(entry)
            
        if self.modified_weapon_mods:
            data.SaveWeaponMods(shared_file=False, mods=self.modified_weapon_mods)
            self.modified_weapon_mods.clear()
        
        if self.modified_items:            
            wiki_data_missing = [item for item in self.modified_items.All if not item.wiki_scraped]
            
            for item in wiki_data_missing:
                if item is not None:
                    self.queue_data_assignment(item)
                
            data.SaveItems(shared_file=False, items=self.modified_items)            
            self.modified_items.clear()
            
            for _, entry in self.collected_items.items():
                if entry.status == CollectionStatus.RequiresSave:
                    entry.status = CollectionStatus.DataCollected
                
            if Console.is_window_active():
                # ConsoleLog("LootEx DataCollector", f"Notifying other accounts about updated data...", Console.MessageType.Info)
                messaging.SendMergingMessage()
                pass
            
        pass

    def queue_data_assignment(self, item : Item):
        if item is None:
            return
        
        ConsoleLog("LootEx DataCollector", f"Queueing auto-assignment of scraped data for item: {item.names.get(ServerLanguage.English, '')}...", Console.MessageType.Info)
        
        if not self.wiki_scraped_items.get((item.item_type, item.model_id), False):
            GLOBAL_CACHE._ActionQueueManager.AddAction("ACTION", lambda: self.auto_assign_scraped_data(item))
            self.wiki_scraped_items[(item.item_type, item.model_id)] = True
    
    def collect_item(self, item_id: int, server_language: ServerLanguage):
        if item_id <= 0:
            return
        
        if not self.ready:
            self.initialize()
            return
        
        if not self.settings.collect_items:
            ConsoleLog("LootEx DataCollector", f"Data collection is disabled in settings. Skipping item ID: {item_id}.", Console.MessageType.Debug, self.LOG_DATA_COLLECTION)
            return
        
        if server_language == ServerLanguage.Unknown:
            return
    
        invalid_model_ids = [4390988]
        highest_valid_model_id = 50000 #38057
        
        if item_id not in self.collected_items:            
            entry = CollectionEntry(item_id, self.modified_items)
            
            if entry.model_id in invalid_model_ids or entry.model_id > highest_valid_model_id:
                entry.status = CollectionStatus.DataCollected
                return
            
            self.collected_items[item_id] = entry
            
            if not entry.has_name(server_language):
                entry.request_name()
                return
            
            else:
                entry.status = CollectionStatus.RequiresSave if entry.changed else CollectionStatus.DataCollected
            
        entry = self.collected_items.get(item_id)
        
        
        if entry:              
            if entry.status is CollectionStatus.DataCollected or entry.status is CollectionStatus.BetterDataFound:
                return
                        
            if entry.status == CollectionStatus.NameRequested:
                if GLOBAL_CACHE.Item.IsNameReady(item_id):
                    name = GLOBAL_CACHE.Item.GetName(item_id)
                    
                    ConsoleLog("LootEx DataCollector", f"Collected name for item ID: {item_id} | {entry.model_id} | {entry.item_type}: {name}", Console.MessageType.Debug, self.LOG_DATA_COLLECTION)
                    
                    if not name or name == "No Item" or name == "Unknown":
                        entry.request_name()
                        return
                    
                    entry.set_name(name, server_language)                           
                return                                                                                
            
            if entry.status == CollectionStatus.NameCollected or entry.changed or entry.status == CollectionStatus.RequiresSave:
                entry.status = CollectionStatus.RequiresSave
                return
    
    def Run(self):            
        if self.throttle.IsExpired():
            self.throttle.Reset()
            
            if not self.ready:
                self.initialize()
                return
                        
            if self.settings.collect_items:
                preference = UIManager.GetIntPreference(NumberPreference.TextLanguage)
                server_language = ServerLanguage(preference)
                if server_language == ServerLanguage.Unknown:
                    return
                
                if self.server_language != server_language:
                    self.server_language = server_language
                    self.reset_cache()
                    return
                
                available_items = self.get_available_items()
                
                for item_id in available_items:
                    self.collect_item(item_id, server_language)
                    
                if self.fetched_cycles >= 3:             
                    self.save_items()
                    self.fetched_cycles = 0
                    GLOBAL_CACHE.Item.name_cache.clear()
                    GLOBAL_CACHE.Item.name_requested.clear()
                
                self.fetched_cycles += 1
                                            
        pass
    
    def get_available_items(self):        
        merchant_open = ui_manager_extensions.UIManagerExtensions.IsMerchantWindowOpen()
        
        item_array : list[int] = GLOBAL_CACHE.ItemArray.GetItemArray(ALL_BAGS)
        # trader_array : list[int] = merchant_open and GLOBAL_CACHE.Trading.Trader.GetOfferedItems() or []
        # trader2_array : list[int] = merchant_open and GLOBAL_CACHE.Trading.Trader.GetOfferedItems2() or []
        # merchant_array : list[int] = merchant_open and GLOBAL_CACHE.Trading.Merchant.GetOfferedItems() or []
        # crafter_array : list[int] = ui_manager_extensions.UIManagerExtensions.IsCrafterOpen() and GLOBAL_CACHE.Trading.Crafter.GetOfferedItems() or []
        # collector_array : list[int] = ui_manager_extensions.UIManagerExtensions.IsCollectorOpen() and GLOBAL_CACHE.Trading.Collector.GetOfferedItems() or []
        
        # all_arrays = item_array + trader_array  + trader2_array + merchant_array + crafter_array + collector_array
        
        # Placeholder for actual implementation
        return item_array