from datetime import date, datetime, timedelta
import json
import math
import os
import re
import base64
from dataclasses import dataclass, field
from typing import ClassVar, Iterable, Iterator, List, Optional, SupportsIndex, overload

import Py4GW
from PyItem import ItemModifier
from Widgets.frenkey.Core.utility import get_image_name
from Widgets.frenkey.LootEx import enum
from Widgets.frenkey.LootEx.enum import Campaign, EnemyType, MaterialType, ModType, ModifierIdentifier, ModifierValueArg, ModsModels
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog
from Py4GWCoreLib.enums import Attribute, Console, DamageType, ItemType, ModelID, Profession, Rarity, ServerLanguage
from Widgets.frenkey.LootEx.texture_scraping_models import ScrapedItem

language_order = [
    ServerLanguage.German,
    ServerLanguage.English,
    ServerLanguage.Korean,
    ServerLanguage.French,
    ServerLanguage.Italian,
    ServerLanguage.Spanish,
    ServerLanguage.TraditionalChinese,
    ServerLanguage.Japanese,
    ServerLanguage.Polish,
    ServerLanguage.Russian,
    ServerLanguage.BorkBorkBork,
]

item_textures_path = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "Items")
missing_texture_path = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "missing_texture.png")

class ModsPair:
    def __init__(self, prefix: ModsModels | None, suffix: ModsModels | None):
        self.Prefix = prefix
        self.Suffix = suffix
    
    @property
    def HasPrefix(self) -> bool:
        return self.Prefix is not None
    
    @property
    def HasSuffix(self) -> bool:
        return self.Suffix is not None
            
    def get(self, mod_type: ModType) -> ModsModels | None:
        if mod_type == ModType.Prefix:
            return self.Prefix
        
        elif mod_type == ModType.Suffix:
            return self.Suffix
        
        return None
    
class IntRange:
    def __init__(self, min: int = 0, max: Optional[int] = None):
        self.min: int = min
        self.max: int = max if max is not None else min

    def __str__(self) -> str:
        return f"{self.min} - {self.max}"

    def __repr__(self) -> str:
        return f"IntRange({self.min}, {self.max})"

    def __eq__(self, other):
        if isinstance(other, IntRange):
            return self.min == other.min and self.max == other.max
        return False
    
def get_server_language() -> ServerLanguage:
    from Widgets.frenkey.LootEx import settings

    language = settings.Settings().language
    return language

@dataclass
class NickItemEntry:
    Week: date
    Item: str
    Index: int = -1
    ModelId: int = -1

    @staticmethod
    def load_from_file(path: str) -> List['NickItemEntry']:
        with open(path, 'r', encoding='utf-8') as file:
            raw_data = json.load(file)
            return [
                NickItemEntry(
                    Week=datetime.strptime(entry['Week'], "%m/%d/%y").date(),
                    Item=entry['Item'],
                    Index=entry['Index'] if 'Index' in entry else -1,
                    ModelId=entry['ModelId'] if 'ModelId' in entry else -1
                )
                for entry in raw_data
            ]

    def to_dict(self) -> dict:
        return {
            "Week": self.Week.strftime("%m/%d/%y"),
            "Item": self.Item,
            "ModelId": self.ModelId,
            "Index": self.Index
        }

    @staticmethod
    def save_to_file(path: str, entries: List['NickItemEntry']):
        with open(path, 'w', encoding='utf-8') as file:
            json.dump([entry.to_dict() for entry in entries], file, indent=4, ensure_ascii=False)

class ModifierValueRange():
    def __init__(self, modifier_value_arg : ModifierValueArg, min: int = 0, max: Optional[int] = None):
        self.modifier_value_arg: ModifierValueArg = modifier_value_arg
        self.min: int = min
        self.max: int = max if max is not None else min
    pass

class SalvageInfoCollection(dict[str, 'SalvageInfo']):
    """
    A collection of SalvageInfo objects indexed by material name.
    
    This class extends the built-in dict to provide a more specific type for
    collections of SalvageInfo objects.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def to_dict(self) -> dict:
        return {material_name: salvage_info.to_dict() for material_name, salvage_info in self.items()}
    
    @staticmethod
    def from_dict(data: dict) -> 'SalvageInfoCollection':
        """
        Create a SalvageInfoCollection from a dictionary.
        
        Args:
            data (dict): A dictionary where keys are material names and values are SalvageInfo dictionaries.
        
        Returns:
            SalvageInfoCollection: An instance of SalvageInfoCollection populated with the data.
        """
        collection = SalvageInfoCollection()
        
        for material_name, salvage_info_data in data.items():
            collection[material_name] = SalvageInfo.from_dict(salvage_info_data)
            
        return collection
    
    def get_average_value(self, is_highly_salvageable : bool = False) -> float:
        """
        Calculate the average value of all salvage materials in the collection.
        
        Returns:
            int: The total average value of all materials.
        """
        total_value = 0
        
        for salvage_info in self.values():
            total_value += salvage_info.get_average_value(is_highly_salvageable)
            
        return (total_value / len(self) if self else 0)

@dataclass
class SalvageInfo():
    amount: int = -1
    min_amount: int = -1
    max_amount: int = -1
    material_model_id: int = -1
    material_name: str = "" 
    summary: str = ""
    average_amount: float = 0
    
    def __post_init__(self):
        self.generate_summary()
        
    def get_average_amount(self, is_highly_salvageable : bool = False) -> float:
        amount = 0
        
        if self.amount != -1:
            amount = self.amount
        
        elif self.min_amount != -1 and self.max_amount != -1:
            amount = (self.min_amount + self.max_amount) / 2.0
        
        else:
            from Widgets.frenkey.LootEx.data import Data
            data = Data()
            material = data.Materials.get(self.material_model_id, None)
            
            if material is None:
                return 0
            
            if material.material_type is MaterialType.Common:
                amount = 8
            
            elif material.material_type is MaterialType.Rare:
                amount = 0.1
            
        return amount * (3 if is_highly_salvageable else 1) if amount > 0 else 0
    
    def get_average_value(self, is_highly_salvageable : bool = False) -> int:
        from Widgets.frenkey.LootEx.data import Data
        data = Data()
        material = data.Materials.get(self.material_model_id, None)
    
        if material is None:
            return 0
        
        if material.material_type is MaterialType.Common:           
            return int(self.get_average_amount(is_highly_salvageable) * material.vendor_value) if material.vendor_value > 0 else 0
        
        elif material.material_type is MaterialType.Rare:
            return int(self.get_average_amount(is_highly_salvageable) * material.vendor_value) if material.vendor_value > 0 else 0
        
        return 0
        

    def generate_summary(self):
        amount = f"{self.amount}" if self.amount != -1 else f"{self.min_amount} - {self.max_amount}" if self.min_amount != -1 and self.max_amount != -1 else None
        self.summary = f"{amount} {self.material_name}" if amount else self.material_name
        
    
    def to_dict(self) -> dict:
        return {
            "Amount": self.amount,
            "MinAmount": self.min_amount,
            "MaxAmount": self.max_amount,
            "MaterialModelID": self.material_model_id,
            "MaterialName": self.material_name
        }
        
    def __str__(self) -> str:            
        return f"SalvageInfo(Amount={self.amount}, MinAmount={self.min_amount}, MaxAmount={self.max_amount}, MaterialModelID={self.material_model_id}, MaterialName='{self.material_name}')"
    
    def __repr__(self) -> str:
        return f"SalvageInfo(amount={self.amount}, min_amount={self.min_amount}, max_amount={self.max_amount}, material_model_id={self.material_model_id}, material_name='{self.material_name}')"
    
    @staticmethod
    def from_dict(data: dict) -> 'SalvageInfo':
        info = SalvageInfo()
        info.amount = data.get("Amount", -1)
        info.min_amount = data.get("MinAmount", -1)
        info.max_amount = data.get("MaxAmount", -1)
        info.material_model_id = data.get("MaterialModelID", -1)
        info.material_name = data.get("MaterialName", "")
        info.generate_summary()
        
        return info 

class AquisitionInfo():
    def __init__(self):
        self.campaign: Campaign = Campaign.None_
        self.map: str = ""
        self.map_id: int = -1
        self.sources: List[str] = []
        
    def to_dict(self) -> dict:
        return {
            "Campaign": self.campaign.name,
            "Map": self.map,
            "MapID": self.map_id,
            "Sources": self.sources
        }
            
    @staticmethod
    def from_dict(data: dict) -> 'AquisitionInfo':
        info = AquisitionInfo()
        info.campaign = Campaign[data["Campaign"]] if "Campaign" in data else Campaign.None_
        info.map = data.get("Map", "")
        info.map_id = data.get("MapID", -1)
        info.sources = data.get("Sources", [])
        return info
                   
class ItemsByType(dict[ItemType, dict[int, 'Item']]):
    """
    A dictionary that maps ItemType to a list of Item objects.
    
    This class extends the built-in dict to provide a more specific type for
    collections of Item objects categorized by their ItemType.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.All : List['Item'] = []
    
    def add_item(self, item: 'Item'):
        """
        Add an Item to the collection under the specified ItemType.
        
        Args:
            item_type (ItemType): The type of the item to add.
            item (Item): The Item object to add.
        """
        
        if item.item_type not in self:
            self[item.item_type] = {}
        
        if len(item.names) == 0:
            return
        
        if item.model_id not in self[item.item_type]:
            self[item.item_type][item.model_id] = item
            self.All.append(item)
            
        else:
            existing_item = self[item.item_type][item.model_id]
            existing_item.update(item)
    
    def sort_items(self):
        """
        Sort all items in the collection by their model ID.
        
        This method sorts the items in each ItemType category by their model ID
        and updates the All list to reflect the sorted order.
        """
        for item_type, items in self.items():
            sorted_items = sorted(items.values(), key=lambda item: (item.name, item.model_id))
            self[item_type] = {item.model_id: item for item in sorted_items}
        
        self.All.sort(key=lambda item: item.name)
    
    def get_item_data(self, item_id: int) -> Optional['Item']:
        """
        Get an Item by its item ID.
        Args:
            item_id (int): The ID of the item to retrieve.  
        Returns:
            Item: The Item data object from the specified item ID, or None if not found.
        """
        
        if item_id <= 0:
            return None
        
        item_type = ItemType(GLOBAL_CACHE.Item.GetItemType(item_id)[0])
        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
        
        items = self.get(item_type, {})
        item = items.get(model_id, None)
                
        return item
    
    def get_item(self, item_type: ItemType, model_id : int) -> Optional['Item']:
        """
        Get an Item by its ItemType and model ID.
        
        Args:
            item_type (ItemType): The type of the item to retrieve.
            model_id (int): The model ID of the item to retrieve.
        
        Returns:
            Item: The Item object with the specified ItemType and model ID, or None if not found.
        """
        items = self.get(item_type, {})
        item = items.get(model_id, None)
            
        return item
    
    def to_json(self) -> dict:
        return {item_type.name: {item.model_id : item.to_json() for item in items.values()} for item_type, items in self.items()}
    
    def get_texture_by_name(self, name: str, language: ServerLanguage = ServerLanguage.English) -> str:
        """
        This is unsafe. This is not very precise since we get dozens of items with the same name and different models.
        
        Args:
            name (str): The name of the item to retrieve.
            language (ServerLanguage): The language of the item name.
        
        Returns:
            Item: The Item object with the specified name, or None if not found.
        """
        
        for item in self.All:
            if item.get_name(language).lower() == name.lower():
                if item.texture_file and not "missing_texture" in item.texture_file:
                    return item.texture_file
            
        return missing_texture_path
    
    @staticmethod
    def from_dict(data: dict) -> 'ItemsByType':
        """
        Create an ItemByTypes from a dictionary.
        
        Args:
            data (dict): A dictionary where keys are ItemType names and values are lists of Item JSON objects.
        
        Returns:
            ItemByTypes: An instance of ItemByTypes populated with the data.
        """
        item_by_types = ItemsByType()
        
        for item_type_name, items in data.items():
            item_type = ItemType[item_type_name]
            item_by_types[item_type] = {}
            
            for model_id, item_data in items.items():
                item = Item.from_json(item_data)
                item_by_types.add_item(item)
            
        return item_by_types

@dataclass
class Item():    
    model_id: int
    item_type: ItemType = ItemType.Unknown
    model_file_id: int = -1
    name : str = ""
    names: dict[ServerLanguage, str] = field(default_factory=dict)
    acquisition: str = ""
    description: str = ""
    attributes: list[Attribute] = field(default_factory=list)
    wiki_url: str = ""
    common_salvage: SalvageInfoCollection = field(default_factory=SalvageInfoCollection)
    rare_salvage: SalvageInfoCollection = field(default_factory=SalvageInfoCollection)
    nick_index: Optional[int] = None
    profession : Optional[Profession] = None
    contains_amount: bool = False    
    inventory_icon: Optional[str] = None
    inventory_icon_url: Optional[str] = None
    category: enum.ItemCategory = enum.ItemCategory.None_
    sub_category: enum.ItemSubCategory = enum.ItemSubCategory.None_    
    wiki_scraped: bool = False
    is_account_data : bool = False
    
    @property
    def is_nick_item(self) -> bool:
        return self.nick_index is not None
    
    def __post_init__(self):
        self.name : str = self.get_name()
        self.next_nick_week: Optional[date] = self.get_next_nick_date()
        self.weeks_until_next_nick: Optional[int] = self.get_weeks_until_next_nick()
        
        texture_file = os.path.join(item_textures_path, f"{self.inventory_icon}")
        if texture_file and os.path.exists(texture_file):
            self.texture_file = texture_file
        else:
            self.texture_file = missing_texture_path
            
    def get_weeks_until_next_nick(self) -> Optional[int]:
        if self.nick_index is None:
            return None
        
        today = datetime.now()
        monday_of_current_week = today.date() - timedelta(days=today.weekday())
        this_week = datetime.combine(monday_of_current_week, datetime.min.time())
        
        next_nick_date = self.get_next_nick_date()
        if next_nick_date is not None:
            delta = next_nick_date - this_week.date()
            
            if delta.days >= 0:
                return math.ceil(delta.days / 7)
            
        return None     
       
    def get_next_nick_date(self) -> Optional[date]:
        if self.nick_index is None:
            return None

        from Widgets.frenkey.LootEx.data import Data
        data = Data()

        start_date = datetime.combine(data.Nick_Cycle_Start_Date, datetime.min.time())
        today = datetime.now()

        # Monday 00:00 of current week
        monday_of_current_week = today.date() - timedelta(days=today.weekday())
        dt = datetime.combine(monday_of_current_week, datetime.min.time())
        
        # Iterate over possible nick cycles
        for i in range(0, 100):
            nick_date = datetime.combine(start_date + timedelta(weeks=self.nick_index + (i * data.Nick_Cycle_Count)), datetime.min.time())
            
            # If current time matches the start of this nick cycle
            if dt == nick_date:
                return nick_date.date()

            # Or if the cycle starts after current time
            if nick_date >= today:
                return nick_date.date()

    def has_missing_names(self) -> ServerLanguage | bool:
        if not self.names or not self.names.get(ServerLanguage.English, False):
            return ServerLanguage.English
        
        # for lang in ServerLanguage:
        #     if lang != ServerLanguage.Unknown:
        #         if lang not in self.names or not self.names[lang]:
        #             return lang
        
        return False
    
    def update_language(self, language: ServerLanguage):
        self.name : str = self.get_name(language)    
        
    def has_name(self, language: ServerLanguage) -> bool:        
        return language in self.names  
        
    def get_name(self, language : Optional[ServerLanguage] = None) -> str:
        if language is None:
            language = get_server_language()
        
        name = self.names.get(
            language, self.names.get(ServerLanguage.English, ""))
        
        if not name:
            # Get the first available name if the requested language is not found
            name = next(iter(self.names.values()), "") + " (No English Name)"
                
        pattern = r"^\s*\d+\s+|(\d+個)$"        
        self.contains_amount = re.search(pattern, name) is not None
        
        return name
        
    def set_name(self, name: str, language: ServerLanguage = ServerLanguage.English):
        self.names[language] = name        
        self.name = self.get_name(language)        
    
    def update(self, item: "Item"):
        if item.model_id != self.model_id:
            ConsoleLog("LootEx", f"Cannot update item with different model ID: {item.model_id} != {self.model_id}", Console.MessageType.Error)
            return
        
        self.item_type = item.item_type
        self.name = item.name
        self.model_file_id = item.model_file_id
        
        for lang, name in item.names.items():
            if lang not in self.names or not self.names[lang]:
                self.names[lang] = name
                
        if item.acquisition:            
            self.acquisition = item.acquisition
        
        self.attributes = item.attributes
        self.profession = item.profession
                    
        if item.wiki_url and not self.wiki_url:
            self.wiki_url = item.wiki_url
                
        if item.nick_index is not None:
            self.nick_index = item.nick_index
                        
        self.update_language(get_server_language())
                
    def to_json(self) -> dict:
        def get_wiki_url():
            if self.wiki_url:
                return self.wiki_url
            
            english_name = self.names.get(ServerLanguage.English, "")
            if not english_name:
                return None
            
            # Generate a wiki URL based on the English name
            base_url = "https://wiki.guildwars.com/wiki/"
            formatted_name = re.sub(r'\s+', '_', english_name.strip())
            return f"{base_url}{formatted_name}"
        
        return {
            "ModelID": self.model_id,
            "ModelFileID": self.model_file_id,
            #Names sorted by language_order
            "Names": {lang.name: name for lang, name in sorted(self.names.items(), key=lambda item: language_order.index(item[0]))},
            "ItemType": self.item_type.name,
            "Acquisition": self.acquisition,
            "Description": self.description,
            "Attributes": [attribute.name for attribute in self.attributes] if self.attributes else [],
            "CommonSalvage": (self.common_salvage or SalvageInfoCollection()).to_dict(),
            "RareSalvage": (self.rare_salvage or SalvageInfoCollection()).to_dict(),
            "WikiURL": self.wiki_url or get_wiki_url(),
            "InventoryIcon": self.inventory_icon,
            "InventoryIconURL": self.inventory_icon_url,
            "NickIndex": self.nick_index,
            "Profession": self.profession.name if self.profession and self.profession != Profession._None else None,
            "Category": self.category.name if self.category else None,
            "SubCategory": self.sub_category.name if self.sub_category else None,
            "WikiScraped": self.wiki_scraped
        }

    @staticmethod
    def from_json(json: dict) -> 'Item':
        return Item(
            model_id=json["ModelID"],
            model_file_id=json.get("ModelFileID", -1),
            names={ServerLanguage[lang]: name for lang,
                   name in json["Names"].items()},
            item_type=ItemType[json["ItemType"]],
            acquisition=json.get("Acquisition", ""),
            description=json.get("Description", ""),
            inventory_icon=json.get("InventoryIcon", None),
            inventory_icon_url=json.get("InventoryIconURL", None),
            attributes=[Attribute[attr] for attr in json["Attributes"]] if "Attributes" in json and json["Attributes"] else [],
            wiki_url=json.get("WikiURL", ""),
            common_salvage=SalvageInfoCollection.from_dict(json.get("CommonSalvage", {})),
            rare_salvage=SalvageInfoCollection.from_dict(json.get("RareSalvage", {})), 
            nick_index=json["NickIndex"] if "NickIndex" in json else None,
            profession=Profession[json["Profession"]] if "Profession" in json and json["Profession"] else None,
            category=enum.ItemCategory[json["Category"]] if "Category" in json and json["Category"] else enum.ItemCategory.None_,
            sub_category=enum.ItemSubCategory[json["SubCategory"]] if "SubCategory" in json and json["SubCategory"] else enum.ItemSubCategory.None_,
            wiki_scraped=json.get("WikiScraped", False) 
        )

    def assign_scraped_data(self, scraped_item : ScrapedItem, data):
        english_name = self.names.get(ServerLanguage.English, "")
        parts = english_name.split(" ", 1) if english_name else []
        contains_amount = len(parts) == 2 and parts[0].isdigit()
        
        if contains_amount:
            self.set_name(scraped_item.name, ServerLanguage.English)
            
        self.description = scraped_item.description or ""
        self.acquisition = scraped_item.Acquisition or ""
        self.inventory_icon = get_image_name(os.path.basename(scraped_item.inventory_icon_url)) if scraped_item.inventory_icon_url else self.inventory_icon
        self.inventory_icon_url = scraped_item.inventory_icon_url or self.inventory_icon_url
                            
        common_salvage = scraped_item.common_salvage or []
        rare_salvage = scraped_item.rare_salvage or []
                            
        for salvage_item in common_salvage:
            if salvage_item not in self.common_salvage:
                material_name = salvage_item.name
                material = next((mat for mat in data.Materials.values() if mat.name == material_name), None)
                
                if material:
                    salvage_info = SalvageInfo(
                        material_model_id=material.model_id,
                        material_name=material.name,
                        amount=salvage_item.amount,
                        min_amount=salvage_item.min_amount,
                        max_amount=salvage_item.max_amount,
                        average_amount=salvage_item.amount,
                    ) 
                    self.common_salvage[material.name] = salvage_info
                    
        for salvage_item in rare_salvage:
            if salvage_item not in self.rare_salvage:
                material_name = salvage_item.name
                material = next((mat for mat in data.Materials.values() if mat.name == material_name), None)
                
                if material:
                    salvage_info = SalvageInfo(
                        material_model_id=material.model_id,
                        material_name=material.name,
                        amount=salvage_item.amount,
                        min_amount=salvage_item.min_amount,
                        max_amount=salvage_item.max_amount,
                        average_amount=salvage_item.amount,
                    ) 
                    self.rare_salvage[material.name] = salvage_info
        self.wiki_scraped = True
        self.__post_init__()

@dataclass
class Material(Item):    
    vendor_updated: datetime = datetime.min
    vendor_value: int = 0
    material_type: MaterialType = MaterialType.Common
    material_storage_slot : int = -1
    
    def to_json(self):
        dict = super().to_json()
        dict["VendorValue"] = self.vendor_value
        dict["VendorUpdated"] = self.vendor_updated.isoformat() if self.vendor_updated else None
        dict["MaterialType"] = self.material_type.name
        dict["MaterialStorageSlot"] = self.material_storage_slot if self.material_storage_slot != -1 else None
        return dict
    
    @staticmethod
    def from_json(json: dict) -> 'Material':
        item = Item.from_json(json)
        material_type = MaterialType[json.get("MaterialType", "None_")]
        if material_type is MaterialType.None_:
            material_type=MaterialType.Common if item.model_id in enum.COMMON_MATERIALS else MaterialType.Rare
            
        
        return Material(
            model_id=item.model_id,
            model_file_id=item.model_file_id,
            names=item.names,
            item_type=item.item_type,
            acquisition=item.acquisition,
            attributes=item.attributes,
            wiki_url=item.wiki_url,
            common_salvage=item.common_salvage,
            rare_salvage=item.rare_salvage,
            nick_index=item.nick_index,
            profession=item.profession,
            vendor_value=json.get("VendorValue", 0),
            vendor_updated=datetime.fromisoformat(json["VendorUpdated"]) if "VendorUpdated" in json else datetime.min,
            material_type=material_type,
            inventory_icon=item.inventory_icon,
            inventory_icon_url=item.inventory_icon_url,
            category=item.category,
            sub_category=item.sub_category,
            wiki_scraped= item.wiki_scraped,
            material_storage_slot=json.get("MaterialStorageSlot", -1) if "MaterialStorageSlot" in json else -1
        )

@dataclass
class BaseModifierInfo:        
    identifier: int
    arg1: int
    arg2: int

    def __post_init__(self):
        self.arg = (self.arg1 << 8) | self.arg2

    @staticmethod
    def unpack_arg(arg: int) -> tuple[int, int]:
        arg1 = (arg >> 8) & 0xFF
        arg2 = arg & 0xFF
        return arg1, arg2

    @staticmethod
    def pack_arg(arg1: int, arg2: int) -> int:
        return (arg1 << 8) | arg2 
    
    def to_dict(self) -> dict:
        return {
            "Identifier": self.identifier,
            "Arg1": self.arg1,
            "Arg2": self.arg2
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'BaseModifierInfo':
        return BaseModifierInfo(
            identifier=data.get("Identifier", 0),
            arg1=data.get("Arg1", 0),
            arg2=data.get("Arg2", 0)
        )
    
@dataclass
class ModifierInfo(BaseModifierInfo):        
    modifier_value_arg: ModifierValueArg = ModifierValueArg.None_
    arg: int = 0
    min: int = 0
    max: int = 0    
    
    def to_dict(self) -> dict:
        base_dict = super().to_dict()
        base_dict.update({
            "ModifierValueArg": self.modifier_value_arg.name,
            "Min": self.min,
            "Max": self.max
        })
        return base_dict    
    
@dataclass
class ItemMod():
    identifier : str = ""
    descriptions: dict[ServerLanguage, str] = field(default_factory=dict)
    names: dict[ServerLanguage, str] = field(default_factory=dict)
    mod_type: ModType = ModType.None_    
    modifiers: list[ModifierInfo] = field(default_factory=list)
    upgrade_exists: bool = True

    def __post_init__(self):
        self.name : str = self.get_name()
        self.full_name : str = self.get_full_name()
        self.description: str  = self.get_description()
        self.applied_name : str = self.get_applied_name()
        
        # self.identifier : str = self.names.get(ServerLanguage.English, "")
        
    def get_modifier_range(self) -> IntRange:
        if not self.modifiers:
            return IntRange(0, 0)
        
        modifier_info = next((mod for mod in self.modifiers if mod.modifier_value_arg != ModifierValueArg.Fixed and mod.modifier_value_arg != ModifierValueArg.None_), None)
        
        return IntRange(modifier_info.min, modifier_info.max) if modifier_info else IntRange(0, 0)
        
    def set_name(self, name: str, language: ServerLanguage = ServerLanguage.English):
        self.names[language] = name        
        self.name = self.get_name(language)   
                
    def has_missing_names(self) -> Optional[ServerLanguage]:
        if not self.names:
            return ServerLanguage.English
        
        for lang in ServerLanguage:
            if lang != ServerLanguage.Unknown:
                if lang not in self.names or not self.names[lang]:
                    return lang
        
        return None
    
    @staticmethod
    def decode_binary_identifier(encoded: str) -> tuple[ModType, list[tuple[int, int]]]:
        """
        Decode a base64 encoded weapon mod identifier.

        Returns:
            ModType: The mod type.
            List[Tuple[int, int]]: A list of (identifier, arg) tuples for each modifier.
        """
        data = base64.urlsafe_b64decode(encoded.encode('ascii'))

        mod_type = ModType(data[0])
        modifiers = []

        i = 1
        while i + 4 < len(data):
            identifier = int.from_bytes(data[i:i+3], byteorder='big')
            arg = int.from_bytes(data[i+3:i+5], byteorder='big')
            modifiers.append((identifier, arg))
            i += 5

        return mod_type, modifiers

    def update_language(self, language: ServerLanguage):
        self.name : str = self.get_name(language)   
        self.full_name : str = self.get_full_name(language) 
        self.description: str  = self.get_description(language)
        self.applied_name : str = self.get_applied_name(language)  
    
    def get_applied_name(self, language: Optional[ServerLanguage] = None) -> str:
        name = self.get_name(language)
        return name
    
    def get_name(self, language: Optional[ServerLanguage] = None) -> str:
        if language is None:
            language = get_server_language()
                                
        name = self.names.get(
            language, self.names.get(ServerLanguage.English, ""))
            
        return name
    
    def get_full_name(self, language : Optional[ServerLanguage] = None) -> str:
        if language is None:
            language = get_server_language()
        
        name = self.names.get(
            language, self.names.get(ServerLanguage.English, ""))                
        return name
    
    def get_description(self, language : Optional[ServerLanguage] = None) -> str:
        if language is None:
            language = get_server_language()
            
        description = self.descriptions.get(
            language, self.descriptions.get(ServerLanguage.English, ""))
        
        if not description:
            return ""
        
        def get_modifier_by_id(identifier: int) -> Optional[ModifierInfo]:
            for mod in self.modifiers:
                if mod.identifier == identifier:
                    return mod
            return None

        def get_single_modifier() -> Optional[ModifierInfo]:
            return self.modifiers[0] if len(self.modifiers) == 1 else None

        def format_enum_name(name: str) -> str:
            parts = []
            for char in name:
                if char.isupper() and parts:
                    parts.append(' ')
                parts.append(char)
            name = ''.join(parts)
            return name.replace("_", " ")

        def get_formatted_value(mod: ModifierInfo, arg_type: str) -> str:
            if arg_type == "arg1":
                if mod.identifier in (9240, 10408, 8680):
                    return format_enum_name(Attribute(mod.arg1).name)
                if mod.identifier in (9400, 41240):
                    return format_enum_name(DamageType(mod.arg1).name)
                if mod.identifier in (8520, 32896):
                    return format_enum_name(EnemyType(mod.arg1).name)
            return str(getattr(mod, arg_type, f"{{{arg_type}}}"))

        def replace_indexed(match: re.Match) -> str:
            arg_type, id_str = match.group(1), match.group(2)
            mod = get_modifier_by_id(int(id_str))
            if not mod:
                return f"{{{arg_type}[{id_str}]}}"
            return get_formatted_value(mod, arg_type)

        def replace_simple(match: re.Match) -> str:
            arg_type = match.group(1)
            mod = get_single_modifier()
            if not mod:
                return f"{{{arg_type}}}"
            return get_formatted_value(mod, arg_type)

        description = re.sub(r"\{(arg1|arg2|arg|min|max)\[(\d+)\]\}", replace_indexed, description)

        if get_single_modifier():
            description = re.sub(r"\{(arg1|arg2|arg|min|max)\}", replace_simple, description)

        return description
    
    def get_custom_description(self, language: Optional[ServerLanguage] = None, *, arg1_min: Optional[int] = None, arg1_max: Optional[int] = None, arg2_min: Optional[int] = None, arg2_max: Optional[int] = None) -> str:
        if language is None:
            language = get_server_language()

        description = self.descriptions.get(
            language, self.descriptions.get(ServerLanguage.English, "")
        )

        if not description:
            return ""
                
        def get_modifier_by_id(identifier: int) -> Optional[ModifierInfo]:
            for mod in self.modifiers:
                if mod.identifier == identifier:
                    return mod
            return None

        def get_single_modifier() -> Optional[ModifierInfo]:
            return self.modifiers[0] if len(self.modifiers) == 1 else None

        def format_enum_name(name: str) -> str:
            parts = []
            for char in name:
                if char.isupper() and parts:
                    parts.append(' ')
                parts.append(char)
            name = ''.join(parts)
            return name.replace("_", " ")

        def get_formatted_value(mod: ModifierInfo, arg_type: str) -> str:
            if arg_type == "arg1":
                if mod.identifier in (9240, 10408, 8680):
                    return format_enum_name(Attribute(mod.arg1).name)
                if mod.identifier in (9400, 41240):
                    return format_enum_name(DamageType(mod.arg1).name)
                if mod.identifier in (8520, 32896):
                    return format_enum_name(EnemyType(mod.arg1).name)
                
            return str(getattr(mod, arg_type, f"{{{arg_type}}}"))

        def replace_indexed(match: re.Match) -> str:
            arg_type, id_str = match.group(1), match.group(2)
            modifier = get_modifier_by_id(int(id_str))
            
            if not modifier:
                return f"{{{arg_type}[{id_str}]}}"
            
            valid_arg1_min = min(modifier.max, max(modifier.min, arg1_min)) if arg1_min is not None else modifier.min
            valid_arg1_max = max(modifier.min, min(modifier.max, arg1_max)) if arg1_max is not None else modifier.max
            valid_arg2_min = min(modifier.max, max(modifier.min, arg2_min)) if arg2_min is not None else modifier.min
            valid_arg2_max = max(modifier.min, min(modifier.max, arg2_max)) if arg2_max is not None else modifier.max
            
            if modifier.modifier_value_arg == ModifierValueArg.Arg1 and arg_type == "arg1" and arg1_min is not None and arg1_max is not None:
                if valid_arg1_min != valid_arg1_max:
                    return f"{valid_arg1_min}...{valid_arg1_max}"
                else:
                    return str(valid_arg1_min)
            
            if modifier.modifier_value_arg == ModifierValueArg.Arg2 and arg_type == "arg2" and arg2_min is not None and arg2_max is not None:
                if valid_arg2_min != valid_arg2_max:    
                    return f"{valid_arg2_min}...{valid_arg2_max}"
                else:
                    return str(valid_arg2_min)
            
            return get_formatted_value(modifier, arg_type)

        def replace_simple(match: re.Match) -> str:
            arg_type = match.group(1)
            modifier = get_single_modifier()
            
            if not modifier:
                return f"{{{arg_type}}}"
            
            valid_arg1_min = min(modifier.max, max(modifier.min, arg1_min)) if arg1_min is not None else modifier.min
            valid_arg1_max = max(modifier.min, min(modifier.max, arg1_max)) if arg1_max is not None else modifier.max
            valid_arg2_min = min(modifier.max, max(modifier.min, arg2_min)) if arg2_min is not None else modifier.min
            valid_arg2_max = max(modifier.min, min(modifier.max, arg2_max)) if arg2_max is not None else modifier.max

            if modifier.modifier_value_arg == ModifierValueArg.Arg1 and arg_type == "arg1" and arg1_min is not None and arg1_max is not None:
                if valid_arg1_min != valid_arg1_max:
                    return f"{valid_arg1_min}...{valid_arg1_max}"
                else:
                    return str(valid_arg1_min)
            
            if modifier.modifier_value_arg == ModifierValueArg.Arg2 and arg_type == "arg2" and arg2_min is not None and arg2_max is not None:
                if valid_arg2_min != valid_arg2_max:    
                    return f"{valid_arg2_min}...{valid_arg2_max}"
                else:
                    return str(valid_arg2_min)

            return get_formatted_value(modifier, arg_type)

        
        # Replace indexed arguments: {arg1[42]}, {arg2[12]}, etc.
        # description = re.sub(r"\{(arg1|arg2|arg|min|max)\[(\d+)\]\}", replace_indexed, description)
        description = re.sub(r"\{(arg1|arg2|arg|min|max)\[(\d+)\]\}", replace_indexed, description, flags=re.DOTALL)


        # Replace simple arguments: {arg1}, {arg2}, etc.
        if get_single_modifier():
            description = re.sub(r"\{(arg1|arg2|arg|min|max)\}", replace_simple, description, flags=re.DOTALL)

        return description

@dataclass
class Rune(ItemMod):
    _rune_identifier_lookup: dict[str, str] = field(default_factory=dict)
    
    vendor_updated: datetime = datetime.min
    vendor_value: int = 0
    profession: Profession = Profession._None
    rarity: Rarity = Rarity.White
    
    
    model_id: int = -1
    model_file_id: int = -1
    texture_file: str = field(init=False)
    
    inventory_icon: Optional[str] = None
    inventory_icon_url: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.texture_file = os.path.join(item_textures_path, f"{self.inventory_icon}") if self.inventory_icon and os.path.exists(os.path.join(item_textures_path, f"{self.inventory_icon}")) else missing_texture_path
        
        
    def get_applied_name(self, language: Optional[ServerLanguage] = None) -> str:
        if language is None:
            language = get_server_language()
                                
        name = self.names.get(
            language, self.names.get(ServerLanguage.English, ""))
        
        rune_patterns : dict[ServerLanguage, str] = {
            ServerLanguage.English:             r".*Rune (?=of)",
            ServerLanguage.Spanish:            r".*(?=\()",
            ServerLanguage.Italian:            r"Runa.*(Guerriero|Mistico|Esploratore|Negromante|Ipnotizzatore|Elementalista|Assassino|Ritualista|Paragon|Derviscio)|(Runa)",
            ServerLanguage.German:             r".*Rune (?=d\.)",
            ServerLanguage.Korean:             r".*(?=\()",
            ServerLanguage.French:             r".*(?=\()",
            ServerLanguage.TraditionalChinese: r"(符文)|(\S+符文)",
            ServerLanguage.Japanese:           r".*(?=\()",
            ServerLanguage.Polish:             r".*(?=\()",
            ServerLanguage.Russian:            r".*Rune (?=of)",
            ServerLanguage.BorkBorkBork:       r".*Roone.*(?=ooff)"
        }

        insignia_patterns : dict[ServerLanguage, str] = {
            ServerLanguage.English:           r"Insignia.*]|Insignia",
            ServerLanguage.Spanish:           r"Insignia.*]|Insignia",
            ServerLanguage.Italian:           r"Insegne.*]|Insegne",
            ServerLanguage.German:            r"\[.*|Befähigung",
            ServerLanguage.Korean:            r"휘장.*|휘장",
            ServerLanguage.French:            r"Insigne.*]|Insigne",
            ServerLanguage.TraditionalChinese:r"徽記.*|徽記",
            ServerLanguage.Japanese:          r"記章.*|記章",
            ServerLanguage.Polish:            r".*Symbol|Symbol",
            ServerLanguage.Russian:           r"Insignia.*]|Insignia",
            ServerLanguage.BorkBorkBork:      r"Inseegneea.*]|Inseegneea",
        }
        
        modified_name = name
        
        if self.mod_type == ModType.Suffix:
            pattern = rune_patterns.get(language, None)
            
            if pattern:
                modified_name = re.sub(pattern, '', name)
                
        elif self.mod_type == ModType.Prefix:         
            pattern = insignia_patterns.get(language, None)
            
            if pattern:
                modified_name = re.sub(pattern, '', name).strip()

        return modified_name.strip()

    def is_in_item_modifier(self, modifiers : list["ItemModifier"]) -> bool:
        for mod in self.modifiers:
            matched = False

            for modifier in [m for m in modifiers if m.GetIdentifier() == mod.identifier]:
                if modifier:
                    arg1 = modifier.GetArg1()
                    arg2 = modifier.GetArg2()

                    if mod.modifier_value_arg == ModifierValueArg.Arg1:
                        if arg1 >= mod.min and arg1 <= mod.max and arg2 == mod.arg2:
                            matched = True
                    
                    elif mod.modifier_value_arg == ModifierValueArg.Arg2:
                        if arg2 >= mod.min and arg2 <= mod.max and arg1 == mod.arg1:
                            matched = True

                    elif mod.modifier_value_arg == ModifierValueArg.Fixed:
                        if arg1 == mod.arg1 and arg2 == mod.arg2:
                            matched = True
            
            if not matched:
                return False
        
        return True
    
    def matches_modifiers(self, modifiers : list[tuple[int, int, int]]) -> tuple[bool, bool]:
        """
        Check if the rune matches the given modifiers.
        
        Args:
            modifiers (list[tuple[int, int, int]]): A list of tuples containing identifier, arg1, and arg2.
        
        Returns:
            tuple[bool, bool]: A tuple where the first element indicates if it matches any modifier,
                               and the second element indicates if it matches the maximum value.
        """
        
        results : list[tuple[bool, bool]] = []
        
        for mod in self.modifiers:    
            matched = False
            maxed = False   
                 
            for identifier, arg1, arg2 in modifiers:
                if mod.identifier != identifier:
                    continue
                
                if mod.modifier_value_arg == ModifierValueArg.Arg1:
                    if arg1 >= mod.min and arg1 <= mod.max and arg2 == mod.arg2:
                        matched = True
                        maxed = arg1 >= mod.max
                        results.append((matched, maxed))
                
                elif mod.modifier_value_arg == ModifierValueArg.Arg2:
                    if arg2 >= mod.min and arg2 <= mod.max and arg1 == mod.arg1:
                        matched = True
                        maxed = arg2 >= mod.max
                        results.append((matched, maxed))

                elif mod.modifier_value_arg == ModifierValueArg.Fixed:
                    if arg1 == mod.arg1 and arg2 == mod.arg2:
                        matched = True
                        maxed = True
                        results.append((matched, maxed))                        
        
            if not matched:
                return False, False        
        
        if not results:
            return False, False
        
        if any(result[0] == False for result in results):
            return False, False
        
        return all(result[0] for result in results), all(result[1] for result in results)        
        
        
    def to_json(self) -> dict:
        return {
            'Identifier': self.identifier,
            'ModelId': self.model_id,
            'ModelFileId': self.model_file_id,
            'Descriptions': {lang.name: name for lang, name in self.descriptions.items()},
            'Names': {lang.name: n for lang, n in self.names.items()},
            'ModType': self.mod_type.name,
            'Profession': self.profession.name,
            'Rarity': self.rarity.name,
            'UpgradeExists': self.upgrade_exists,
            'VendorUpdated': self.vendor_updated.isoformat() if self.vendor_updated else None,
            'VendorValue': self.vendor_value,
            'InventoryIcon': self.inventory_icon,
            'InventoryIconURL': self.inventory_icon_url,
            'Modifiers': [
                {
                    'Identifier': modifier.identifier,
                    'Arg1': modifier.arg1,
                    'Arg2': modifier.arg2,
                    'Arg': modifier.arg,
                    'ModifierValueArg': modifier.modifier_value_arg.name,
                    'Min': modifier.min,
                    'Max': modifier.max
                } for modifier in self.modifiers
            ]
        }
    
    @staticmethod
    def from_json(json: dict) -> 'Rune':
        return Rune(       
            identifier=json["Identifier"],    
            model_id=json.get("ModelId", -1),
            model_file_id=json.get("ModelFileId", -1),
            descriptions={ServerLanguage[lang]: name for lang, name in json["Descriptions"].items()},
            names={ServerLanguage[lang]: name for lang, name in json["Names"].items()},
            mod_type=ModType[json["ModType"]],
            profession=Profession[json["Profession"]],
            rarity=Rarity[json["Rarity"]],
            upgrade_exists=json.get("UpgradeExists", True),
            vendor_updated=datetime.fromisoformat(json["VendorUpdated"]) if "VendorUpdated" in json else datetime.min,
            vendor_value=json.get("VendorValue", 0),
            inventory_icon=json.get("InventoryIcon", None),
            inventory_icon_url=json.get("InventoryIconURL", None),
            modifiers=[
                ModifierInfo(
                    identifier=modifier["Identifier"],
                    arg1=modifier["Arg1"],
                    arg2=modifier["Arg2"],
                    arg=modifier["Arg"] if "Arg" in modifier else 0,
                    modifier_value_arg=ModifierValueArg[modifier["ModifierValueArg"]],
                    min=modifier["Min"] if "Min" in modifier else 0,
                    max=modifier["Max"] if "Max" in modifier else 0
                ) for modifier in json["Modifiers"]
            ]
        )

@dataclass
class WeaponMod(ItemMod):
    _mod_identifier_lookup: dict[str, str] = field(default_factory=dict)    
    target_types : list[ItemType] = field(default_factory=list)
    item_mods : dict[ItemType, ModsModels] = field(default_factory=dict)
    item_type_specific : dict[ItemType, BaseModifierInfo] = field(default_factory=dict)

    ## extracted weapon mods share the same modelid, thus we need to check the item type it belongs to through ModifierIdentifier.ItemType which gives us a ModTargetType

    def __post_init__(self):
        from Widgets.frenkey.LootEx.data import Data
        data = Data()
        
        ItemMod.__post_init__(self)
        self.is_inscription : bool = self.names.get(ServerLanguage.English, "").startswith("\"") if self.names else False
        

    def is_in_item_modifier(self, modifiers : list["ItemModifier"], item_type : ItemType, tolerance : int = -1) -> bool:
        is_tolerance_set = tolerance if tolerance >= 0 else 0
                
        for mod in self.modifiers:            
            if not is_tolerance_set:
                tolerance = mod.arg1 if mod.modifier_value_arg == ModifierValueArg.Arg1 else mod.arg2 if mod.modifier_value_arg == ModifierValueArg.Arg2 else 0
                
            matched = False
            for modifier in [m for m in modifiers if m.GetIdentifier() == mod.identifier]:                
                arg1 = modifier.GetArg1()
                arg2 = modifier.GetArg2()

                if mod.modifier_value_arg == ModifierValueArg.Arg1:
                    if arg1 >= mod.min and arg1 <= mod.max and arg2 == mod.arg2:
                        matched = arg1 >= mod.max - tolerance
                
                elif mod.modifier_value_arg == ModifierValueArg.Arg2:
                    if arg2 >= mod.min and arg2 <= mod.max and arg1 == mod.arg1:
                        matched = arg2 >= mod.max - tolerance

                elif mod.modifier_value_arg == ModifierValueArg.Fixed:
                    if arg1 == mod.arg1 and arg2 == mod.arg2:
                        matched = True
                        
                elif mod.modifier_value_arg == ModifierValueArg.None_:
                    matched = True
                        
            if not matched:       
                return False
            
            
        from Widgets.frenkey.LootEx import utility
        if item_type == ItemType.Rune_Mod:
            applied_to_item_type_mod = next((modifier for modifier in modifiers if modifier.GetIdentifier() == ModifierIdentifier.TargetItemType), None)
            if not applied_to_item_type_mod:
                return False
            
            applied_to_item_type_id = applied_to_item_type_mod.GetArg1()
            applied_to_item_type = ItemType(applied_to_item_type_id)
            
            return any(utility.Util.IsMatchingItemType(applied_to_item_type, target_item_type) for target_item_type in self.target_types)
            
        else:
            return any(utility.Util.IsMatchingItemType(item_type, target_item_type) for target_item_type in self.target_types)

    def get_matching_modifiers(self, modifiers : list[tuple[int, int, int]], item_type : ItemType, model_id: int) -> list[tuple[int, int, int]]:
        """
        Check if the rune matches the given modifiers.
        
        Args:
            modifiers (list[tuple[int, int, int]]): A list of tuples containing identifier, arg1, and arg2.
        
        Returns:
            tuple[bool, bool]: A tuple where the first element indicates if it matches any modifier,
                                and the second element indicates if it matches the maximum value.
        """
        results : list[tuple[int, int, int]] = []
        
        if item_type in self.item_type_specific:
            item_type_specific = self.item_type_specific[item_type]
            
            matches = any(identifier == item_type_specific.identifier and arg1 == item_type_specific.arg1 and arg2 == item_type_specific.arg2 for identifier, arg1, arg2 in modifiers)
            if not matches:
                return []
        
        for mod in self.modifiers: #The modifiers stored in the Item Mod json   
            matched = False
                    
            for identifier, arg1, arg2 in modifiers: # The modifiers from the item in game
                if mod.identifier != identifier:
                    continue
                
                if mod.modifier_value_arg == ModifierValueArg.Arg1:
                    if arg1 >= mod.min and arg1 <= mod.max and arg2 == mod.arg2:
                        matched = True
                        results.append((identifier, arg1, arg2))
                
                elif mod.modifier_value_arg == ModifierValueArg.Arg2:
                    if arg2 >= mod.min and arg2 <= mod.max and arg1 == mod.arg1:
                        matched = True
                        results.append((identifier, arg1, arg2))

                elif mod.modifier_value_arg == ModifierValueArg.Fixed:
                    if arg1 == mod.arg1 and arg2 == mod.arg2:
                        matched = True
                        results.append((identifier, arg1, arg2))
                
                elif mod.modifier_value_arg == ModifierValueArg.None_:
                    matched = True
                    results.append((identifier, arg1, arg2))
        
            if not matched:
                return []
                    
        if not results:
            return []
        
        
        from Widgets.frenkey.LootEx import utility
        if item_type == ItemType.Rune_Mod:
            applied_to_item_type_mod = next((identifier, arg1, arg2) for identifier, arg1, arg2 in modifiers if identifier == ModifierIdentifier.TargetItemType)
            applied_to_item_type = ItemType(applied_to_item_type_mod[1])

            mod_model_id = self.item_mods.get(applied_to_item_type, None) or 0
            
            return results if mod_model_id == model_id else []

        else:
            matches_item_type = any(utility.Util.IsMatchingItemType(item_type, target_item_type) for target_item_type in self.item_mods.keys())
            return results if matches_item_type else []
    
    def has_item_type(self, item_type: ItemType) -> bool:
        if not self.target_types:
            return True

        from Widgets.frenkey.LootEx.data import Data
        data = Data()
        
        if (self.target_types):
            for target_type in self.target_types:
                if item_type == target_type or item_type in data.ItemType_MetaTypes.get(target_type, []):
                    return True
        else:
            # If no target types are specified, return True
            return True
                    
        return False       

    def to_json(self) -> dict:
        return {
            'Identifier': self.identifier,          
            'Descriptions': {lang.name: name for lang, name in self.descriptions.items()},
            #Names sorted by language_order
            'Names': {lang.name : n for lang, n in sorted(self.names.items(), key=lambda x: language_order.index(x[0]))},
            'ModType': self.mod_type.name,
            'ItemMods': {item_type.name: mod_info.name for item_type, mod_info in self.item_mods.items()} if self.item_mods else {},
            'TargetTypes': [target_type.name for target_type in self.target_types],      
            'UpgradeExists': self.upgrade_exists, 
            'ItemTypeSpecific': {item_type.name: mod_info.to_dict() for item_type, mod_info in self.item_type_specific.items()} if self.item_type_specific else {},
            'Modifiers': [
                {
                    'Identifier': modifier.identifier,
                    'Arg1': modifier.arg1,
                    'Arg2': modifier.arg2,
                    'Arg': modifier.arg,
                    'ModifierValueArg': modifier.modifier_value_arg.name,
                    'Min': modifier.min,
                    'Max': modifier.max
                } for modifier in self.modifiers
            ]
        }
    
    def update(self, item_mod: 'WeaponMod'):
        if item_mod.mod_type != self.mod_type:
            ConsoleLog("LootEx", f"Cannot update weapon mod with different mod type: {item_mod.mod_type} != {self.mod_type}", Console.MessageType.Error)
            return
                
        for lang, name in item_mod.names.items():
            if lang not in self.names or not self.names[lang] or self.names[lang] == "" or self.names[lang] != name:
                self.names[lang] = name
                
        for lang, description in item_mod.descriptions.items():
            if lang not in self.descriptions or not self.descriptions[lang] or self.descriptions[lang] == "" or self.descriptions[lang] != description:
                self.descriptions[lang] = description
    
    @staticmethod
    def from_json(json: dict) -> 'WeaponMod':
        return WeaponMod(            
            identifier=json["Identifier"],
            descriptions={ServerLanguage[lang]: name for lang, name in json["Descriptions"].items()},
            names={ServerLanguage[lang]: name for lang, name in json["Names"].items()},
            mod_type=ModType[json["ModType"]],
            item_mods={ItemType[item_type]: ModsModels[mod_info] for item_type, mod_info in json.get("ItemMods", {}).items()},
            target_types=[ItemType[target_type] for target_type in json["TargetTypes"]] if "TargetTypes" in json else [],
            upgrade_exists=json["UpgradeExists"],
            item_type_specific={ItemType[item_type]: BaseModifierInfo.from_dict(mod_info) for item_type, mod_info in json.get("ItemTypeSpecific", {}).items()},
            modifiers=[
                ModifierInfo(
                    identifier=modifier["Identifier"],
                    arg1=modifier["Arg1"],
                    arg2=modifier["Arg2"],
                    arg=modifier["Arg"],
                    modifier_value_arg=ModifierValueArg[modifier["ModifierValueArg"]],
                    min=modifier["Min"],
                    max=modifier["Max"]
                ) for modifier in json["Modifiers"]
            ]
        )    

class ModInfo:
    def __init__(self, mod : ItemMod | None = None):
        self.identifier: str = ""
        self.min: int = 0
        self.max: int = 0
        
        if mod:
            self.identifier = mod.identifier
            modifier_range = mod.get_modifier_range()
            
            self.min = modifier_range.max
            self.max = modifier_range.max
        
    def to_dict(self) -> dict:
        return {
            "identifier": self.identifier,
            "min": self.min,
            "max": self.max
        }
        
    @staticmethod
    def from_dict(data: dict) -> "ModInfo":
        mod = ModInfo()
        
        mod.identifier = data.get("identifier", "")
        mod.min = data.get("min", 0)
        mod.max = data.get("max", 0)
        
        return mod

class BaseModInfo():
    def __init__(self):
        self.Mod : ItemMod
        self.Modifiers : list[tuple[int, int, int]] = []
        self.IsMaxed : bool = False
        self.Value : int = 0
        
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseModInfo):
            return NotImplemented
        return self.Modifiers == other.Modifiers

    def __hash__(self) -> int:
        # convert list of tuples to a tuple of tuples so it’s hashable
        return hash(tuple(self.Modifiers))

    def __lt__(self, other: "BaseModInfo") -> bool:
        """Optional: allows sorting ModInfos (for example by Value or Modifier count)."""
        if not isinstance(other, BaseModInfo):
            return NotImplemented
        return (self.Value, len(self.Modifiers)) < (other.Value, len(other.Modifiers))

    
class RuneModInfo(BaseModInfo):
    @property
    def Rune(self) -> Rune:
        return self.Mod  # type: ignore
    
    @staticmethod
    def get_from_modifiers(modifiers: list[tuple[int, int, int]], item_type: ItemType = ItemType.Unknown) -> list["RuneModInfo"] | None:
        if not modifiers:
            return None
        
        from Widgets.frenkey.LootEx.data import Data
        data = Data()
        
        mod_infos : list["RuneModInfo"] = []
        for rune in data.Runes.values():
            matches, is_maxed = rune.matches_modifiers(modifiers)
            if not matches:
                continue
                    
            rune_mod_info = RuneModInfo()
            rune_mod_info.Mod = rune
            rune_mod_info.Modifiers = modifiers
            rune_mod_info.IsMaxed = is_maxed
            
            mod_infos.append(rune_mod_info) 
        
        return mod_infos   

class WeaponModInfo(BaseModInfo):       
    @property
    def WeaponMod(self) -> WeaponMod:
        return self.Mod  # type: ignore
     
    @staticmethod
    def get_from_modifiers(modifiers: list[tuple[int, int, int]], item_type: ItemType = ItemType.Unknown, model_id: int = -1) -> list["WeaponModInfo"] | None:
        if not modifiers:
            return None
    
        from Widgets.frenkey.LootEx.data import Data
        data = Data()
        
        mod_infos : list["WeaponModInfo"] = []
        
        for weapon_mod in data.Weapon_Mods.values():
            matching_modifiers = weapon_mod.get_matching_modifiers(modifiers, item_type, model_id)
            
            if not matching_modifiers:
                continue
                    
            weapon_mod_info = WeaponModInfo()
            weapon_mod_info.Mod = weapon_mod
            weapon_mod_info.Modifiers = matching_modifiers
            
            def get_variable_mod_info() -> Optional[ModifierInfo]:
                if len(weapon_mod.modifiers) == 1:
                    return weapon_mod.modifiers[0]
                    
                for mod in weapon_mod.modifiers:
                    return mod
                    
                return None
            
            mod_info = get_variable_mod_info()
            
            if mod_info:
                matching_modifier = next((m for m in matching_modifiers if m[0] == mod_info.identifier), None)
                
                if matching_modifier:
                    _, arg1, arg2 = matching_modifier if matching_modifier else (0, 0, 0)
                    
                    if mod_info.modifier_value_arg == ModifierValueArg.Arg1:
                        weapon_mod_info.Value = arg1
                        weapon_mod_info.IsMaxed = weapon_mod_info.Value >= mod_info.max                        
                    
                    elif mod_info.modifier_value_arg == ModifierValueArg.Arg2:
                        weapon_mod_info.Value = arg2
                        weapon_mod_info.IsMaxed = weapon_mod_info.Value >= mod_info.max
                    
                    elif mod_info.modifier_value_arg == ModifierValueArg.Fixed:
                        weapon_mod_info.Value = 0
                        weapon_mod_info.IsMaxed = True
                    
                    elif mod_info.modifier_value_arg == ModifierValueArg.None_:
                        weapon_mod_info.Value = 0
                        weapon_mod_info.IsMaxed = True
            
                mod_infos.append(weapon_mod_info)
            
        return mod_infos

class ItemModifiersInformation:
    def __init__(self):
        from Widgets.frenkey.LootEx.models import WeaponModInfo, RuneModInfo        
                                
        self.target_item_type: ItemType = ItemType.Unknown
        self.damage: tuple[int, int] = (0, 0)
        self.shield_armor: tuple[int, int] = (0, 0)
        self.requirements: int = 0
        self.attribute: Attribute = Attribute.None_
        self.is_highly_salvageable: bool = False
        self.has_increased_value: bool = False
        
        self.runes: list[RuneModInfo] = []
        self.max_runes: list[RuneModInfo] = []
        self.runes_to_keep: list[RuneModInfo] = []
        self.runes_to_sell: list[RuneModInfo] = []
        
        self.weapon_mods: list[WeaponModInfo] = []
        self.max_weapon_mods: list[WeaponModInfo] = []
        self.weapon_mods_to_keep: list[WeaponModInfo] = []
        
        self.mods: list[RuneModInfo | WeaponModInfo] = []
        self.has_mods: bool = False

    def populate_from_modifiers(self, modifiers: list[ItemModifier], item_type: ItemType, model_id: int, is_inscribable: bool) -> "ItemModifiersInformation":
        from Widgets.frenkey.LootEx.models import WeaponModInfo
        from Widgets.frenkey.LootEx.settings import Settings
        settings = Settings()
        
        from Widgets.frenkey.LootEx import utility
        
        modifier_values: list[tuple[int, int, int]] = [
            (modifier.GetIdentifier(), modifier.GetArg1(), modifier.GetArg2())
            for modifier in modifiers if modifier is not None
        ]

        if not modifier_values:
            return self
        
        is_weapon: bool = utility.Util.IsWeaponType(item_type)
        is_armor: bool = utility.Util.IsArmorType(item_type)
        is_upgrade: bool = item_type == ItemType.Rune_Mod
        is_rune: bool = False
                    
        for identifier, arg1, arg2 in modifier_values:
            if identifier is None or arg1 is None or arg2 is None:
                continue

            if identifier == ModifierIdentifier.TargetItemType.value:
                self.target_item_type = ItemType(
                    arg1) if arg1 is not None else ItemType.Unknown
                is_rune = arg1 == 0 and arg2 == 0 and is_upgrade

            if identifier == ModifierIdentifier.Damage.value:
                self.damage = (
                    arg2, arg1) if arg1 is not None and arg2 is not None else (0, 0)

            if identifier == ModifierIdentifier.Damage_NoReq.value:
                self.damage = (
                    arg2, arg1) if arg1 is not None and arg2 is not None else (0, 0)

            if identifier == ModifierIdentifier.ShieldArmor.value:
                self.shield_armor = (
                    arg1, arg2) if arg1 is not None and arg2 is not None else (0, 0)

            if identifier == ModifierIdentifier.Requirement.value:
                self.requirements = arg2 if arg2 is not None else 0
                self.attribute = Attribute(
                    arg1) if arg1 is not None else Attribute.None_
            
            if identifier == ModifierIdentifier.ImprovedVendorValue.value:
                self.has_increased_value = True
                
            if identifier == ModifierIdentifier.HighlySalvageable.value:
                self.is_highly_salvageable = True
                
        if is_armor or is_rune:
            runes = RuneModInfo.get_from_modifiers(modifier_values, item_type)
            self.runes = runes if runes else []
            self.max_runes = [rune for rune in self.runes if rune.IsMaxed]
            self.runes_to_keep = []
            self.runes_to_sell = []
            
            for rune in self.runes:
                setting = settings.profile.runes.get(rune.Rune.identifier, None) if settings.profile else None   
                if setting and setting.valuable:
                    self.runes_to_keep.append(rune)

                if setting and setting.should_sell:
                    self.runes_to_sell.append(rune)

        if is_weapon or (is_upgrade and not is_rune):            
            self.weapon_mods = WeaponModInfo.get_from_modifiers(modifier_values, item_type, model_id) or []
            self.max_weapon_mods = [mod for mod in self.weapon_mods if mod.IsMaxed and (mod.WeaponMod.mod_type != ModType.Inherent or (is_inscribable or is_upgrade))]
            self.weapon_mods_to_keep = [mod for mod in self.max_weapon_mods if settings.profile and settings.profile.weapon_mods.get(mod.WeaponMod.identifier, {}).get(item_type.name, False)]
                            
        
        self.mods = self.runes + self.weapon_mods
        self.has_mods = bool(self.runes or self.weapon_mods)
        
        return self

    @staticmethod
    def GetModsFromModifiers(modifiers: list[ItemModifier], item_type: ItemType, model_id: int, is_inscribable: bool) -> "ItemModifiersInformation":
        info = ItemModifiersInformation()
        info.populate_from_modifiers(modifiers, item_type, model_id, is_inscribable)
        return info