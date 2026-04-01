# singleton instance which contains all the item data of our `items.json` file. This is used to avoid having to read the file multiple times and to have a central place to access item data from

from dataclasses import dataclass, field
import json
import os
import traceback
from typing import Optional

from Py4GW import Console

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.enums_src.GameData_enums import Attribute, Profession
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.native_src.internals import string_table
from Sources.frenkeyLib.ItemHandling.Items.types import MaterialType

PERSISTENT = True

@dataclass
class SalvageInfo():
    amount: int = -1
    min_amount: int = -1
    max_amount: int = -1
    model_id: int = -1
    name: str = "" 
    summary: str = ""
    average_amount: float = 0
    
    def __post_init__(self):
        self.generate_summary()

    def generate_summary(self):
        amount = f"{self.amount}" if self.amount != -1 else f"{self.min_amount} - {self.max_amount}" if self.min_amount != -1 and self.max_amount != -1 else None
        self.summary = f"{amount} {self.name}" if amount else self.name
        
    
    def to_dict(self) -> dict:
        return {
            "amount": self.amount,
            "min_amount": self.min_amount,
            "max_amount": self.max_amount,
            "model_id": self.model_id,
            "name": self.name
        }
        
    def __str__(self) -> str:            
        return f"SalvageInfo(amount={self.amount}, min_amount={self.min_amount}, max_amount={self.max_amount}, model_id={self.model_id}, name='{self.name}')"
    
    def __repr__(self) -> str:
        return f"SalvageInfo(amount={self.amount}, min_amount={self.min_amount}, max_amount={self.max_amount}, model_id={self.model_id}, name='{self.name}')"
    
    @staticmethod
    def from_dict(data: dict) -> 'SalvageInfo':
        info = SalvageInfo()
        info.amount = data.get("amount", -1)
        info.min_amount = data.get("min_amount", -1)
        info.max_amount = data.get("max_amount", -1)
        info.model_id = data.get("model_id", -1)
        info.name = data.get("name", "")
        info.generate_summary()
        
        return info 
    
    @staticmethod
    def from_dict_OLD(data: dict) -> 'SalvageInfo':
        info = SalvageInfo()
        info.amount = data.get("Amount", -1)
        info.min_amount = data.get("MinAmount", -1)
        info.max_amount = data.get("MaxAmount", -1)
        info.model_id = data.get("MaterialModelID", -1)
        info.name = data.get("MaterialName", "")
        info.generate_summary()
        
        return info 

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
    def from_dict_OLD(data: dict) -> 'SalvageInfoCollection':
        collection = SalvageInfoCollection()
        
        for material_name, salvage_info_data in data.items():
            collection[material_name] = SalvageInfo.from_dict_OLD(salvage_info_data)
            
        return collection


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

@dataclass
class ItemData:        
    model_id: int = -1
    item_type: ItemType = ItemType.Unknown
    model_file_id: int = -1
    english_name: str = ""
    name_encoded : bytes = bytes()
    attributes: list[Attribute] = field(default_factory=list)
    common_salvage: Optional[SalvageInfoCollection] = field(default_factory=SalvageInfoCollection)
    rare_salvage: Optional[SalvageInfoCollection] = field(default_factory=SalvageInfoCollection)
    nick_index: Optional[int] = None
    profession : Optional[Profession] = None
    
    # Optional fields we have to more or less manually fill/scrape
    wiki_url: str = ""
    acquisition: str = ""
    description: str = ""
    category: str = ""
    sub_category: str = ""
    
    skin: Optional[str] = None
    
    @property
    def name(self) -> str:
        if self.name_encoded:
            try:
                return string_table.decode(self.name_encoded)
            except UnicodeDecodeError:
                pass
            
        return self.english_name

    @staticmethod    
    def from_json(data: dict) -> 'ItemData':
        profession_name = data.get("profession")
        english_name = data.get("name", "")
        
        item_data = ItemData(
            english_name=english_name,
            name_encoded=bytes.fromhex(data["name_encoded"]) if "name_encoded" in data and data["name_encoded"] else bytes(),
            model_id=data.get("model_id", -1),
            item_type=ItemType[data.get("item_type", "Unknown")],
            model_file_id=data.get("model_file_id", -1),
            attributes=[Attribute[attr] for attr in data.get("attributes", [])],
            common_salvage=SalvageInfoCollection.from_dict(data.get("common_salvage", {})) if data.get("common_salvage") else None,
            rare_salvage=SalvageInfoCollection.from_dict(data.get("rare_salvage", {})) if data.get("rare_salvage") else None,
            nick_index=data.get("nick_index"),
            profession=Profession[profession_name] if profession_name else None,
            wiki_url=data.get("wiki_url", ""),
            acquisition=data.get("acquisition", ""),
            description=data.get("description", ""),
            category=data.get("category", ""),
            sub_category=data.get("sub_category", ""),
            skin=data.get("skin")
        )
        
        return item_data

    @staticmethod
    def from_jsonOLD(json: dict) -> 'ItemData':
        names = {ServerLanguage[lang]: name for lang, name in json["Names"].items()} if "Names" in json else {}
        
        return ItemData(
            model_id=json.get("ModelID", -1),
            model_file_id=json.get("ModelFileID", -1),
            name_encoded=bytes.fromhex(json["NameEncoded"]) if "NameEncoded" in json and json["NameEncoded"] else bytes(),
            english_name=names.get(ServerLanguage.English, ""),
            item_type=ItemType[json.get("ItemType", "Unknown")],
            acquisition=json.get("Acquisition", ""),
            description=json.get("Description", ""),
            skin=json.get("InventoryIcon", None),
            attributes=[Attribute[attr] for attr in json["Attributes"]] if "Attributes" in json and json["Attributes"] else [],
            wiki_url=json.get("WikiURL", ""),
            common_salvage=SalvageInfoCollection.from_dict_OLD(json.get("CommonSalvage", {})),
            rare_salvage=SalvageInfoCollection.from_dict_OLD(json.get("RareSalvage", {})), 
            nick_index=json["NickIndex"] if "NickIndex" in json else None,
            profession=Profession[json["Profession"]] if "Profession" in json and json["Profession"] else None,
            category=json["Category"] if "Category" in json else "",
            sub_category=json["SubCategory"] if "SubCategory" in json else "",
        )

    def to_json(self) -> dict:
        data = {
            "model_id": self.model_id,
            "item_type": self.item_type.name,
            "model_file_id": self.model_file_id,
            "name": self.english_name,
            "name_encoded" : self.name_encoded.hex() if self.name_encoded else "",
            "attributes": [attr.name for attr in self.attributes],
            "common_salvage": self.common_salvage.to_dict() if self.common_salvage else None,
            "rare_salvage": self.rare_salvage.to_dict() if self.rare_salvage else None,
            "nick_index": self.nick_index,
            "profession": self.profession.name if self.profession else None,
            "wiki_url": self.wiki_url,
            "acquisition": self.acquisition,
            "description": self.description,
            "category": self.category,
            "sub_category": self.sub_category,
            "skin": self.skin
        }
        
        return dict(sorted(data.items(), key=lambda item: item[0]))

project_path = Console.get_projects_path()
default_item_json_path = os.path.join(project_path, "Sources", "frenkeyLib", "ItemHandling", "Items", "items.json")
item_json_path = os.path.join(project_path, "Sources", "frenkeyLib", "ItemHandling", "Items", "items copy.json")
if not os.path.exists(item_json_path):
    item_json_path = default_item_json_path

class ItemDataContainer():
    def __init__(self):
        self.data : dict[ItemType, dict[int, ItemData]] = {}
        self.requires_save = False
        
        self.load_data()
    
    def get_item_data(self, item_id: Optional[int] = None, item_type: Optional[ItemType] = None, model_id : Optional[int] = None) -> Optional[ItemData]:     
        """
        Get item data for a given item ID or item type + model ID.
        Args:
            item_id (Optional[int]): The runtime item ID to get data for. If no item type and model ID are provided, these will be looked up using the item ID.
            item_type (Optional[ItemType]): The item type to look up. Required if item_id is not provided.
            model_id (Optional[int]): The model ID to look up. Required if item_id is not provided.
        Returns:
            Optional[ItemData]: The item data for the given item ID or item type + model ID, or None if no data is found.
        """   
        
        item_type = item_type if item_type is not None else (ItemType(GLOBAL_CACHE.Item.GetItemType(item_id)[0]) if item_id else None)
        model_id = model_id if model_id is not None else (GLOBAL_CACHE.Item.GetModelID(item_id) if item_id else None)
        
        if item_type is None or model_id is None:
            return None
        
        return self.data.get(item_type, {}).get(model_id, None)

    def get_or_create_item_data(self, item_type: ItemType, model_id: int) -> ItemData:
        if item_type not in self.data:
            self.data[item_type] = {}

        if model_id not in self.data[item_type]:
            self.data[item_type][model_id] = ItemData(model_id=model_id, item_type=item_type)

        return self.data[item_type][model_id]

    def queue_save(self):
        self.requires_save = True

    def load_data(self):
        try:
            with open(item_json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
                
                for item_type_name, items in json_data.items():
                    for item_model_id, item_data_dict in items.items():
                        try:
                            item_data = ItemData.from_json(item_data_dict)
                        except Exception as item_error:
                            Console.Log(
                                "ItemDataContainer",
                                f"Error parsing item '{item_type_name}/{item_model_id}': {type(item_error).__name__}: {item_error}",
                                Console.MessageType.Error
                            )
                            Console.Log(
                                "ItemDataContainer",
                                traceback.format_exc(),
                                Console.MessageType.Error
                            )
                            continue
                        
                        if not item_data or item_data.model_id == -1 or item_data.item_type == ItemType.Unknown:
                            continue
                        
                        if item_data.item_type not in self.data:
                            self.data[item_data.item_type] = {}
                            
                        self.data[item_data.item_type][item_data.model_id] = item_data
            
                Console.Log("ItemDataContainer", f"Loaded item data for {sum(len(items) for items in self.data.values())} items across {len(self.data)} item types.", Console.MessageType.Success)
        except Exception as e:
            Console.Log("ItemDataContainer", f"Error loading item data: {e}", Console.MessageType.Error)
        
    
    def save_data(self):
        try:
            with open(item_json_path, "w", encoding="utf-8") as f:
                json_data = {item_type.name: {str(item_data.model_id): item_data.to_json() for item_data in items.values()} for item_type, items in self.data.items()}
                json.dump(json_data, f, indent=4, ensure_ascii=False)
                Console.Log("ItemDataContainer", f"Saved item data for {sum(len(items) for items in self.data.values())} items across {len(self.data)} item types.", Console.MessageType.Success)
                self.requires_save = False
        except Exception as e:
            Console.Log("ItemDataContainer", f"Error saving item data: {e}", Console.MessageType.Error)

    def save_data_if_queued(self):
        if not self.requires_save:
            return

        self.save_data()

ITEM_DATA = ItemDataContainer()

DAMAGE_RANGES : dict[ItemType, dict[int, tuple[int, int]]] = {
    ItemType.Axe: {
        0:  (6, 12),
        1:  (6, 12),
        2:  (6, 14),
        3:  (6, 17),
        4:  (6, 19),
        5:  (6, 22),
        6:  (6, 24),
        7:  (6, 25),
        8:  (6, 27),
        9:  (6, 28),
    },
    
    ItemType.Bow: {
        0:  (9, 13),
        1:  (9, 14),
        2:  (10, 16),
        3:  (11, 18),
        4:  (12, 20),
        5:  (13, 22),
        6:  (14, 25),
        7:  (14, 25),
        8:  (14, 27),
        9:  (14, 28),
    },

    ItemType.Daggers: {
        0:  (4, 8),
        1:  (4, 8),
        2:  (5, 9),
        3:  (5, 11),
        4:  (6, 12),
        5:  (6, 13),
        6:  (7, 14),
        7:  (7, 15),
        8:  (7, 16),
        9:  (7, 17),
    },

    ItemType.Offhand: {
        0:  (6, 6),
        1:  (6, 6),
        2:  (7, 7),
        3:  (8, 8),
        4:  (9, 9),
        5:  (10, 10),
        6:  (11, 11),
        7:  (11, 11),
        8:  (12, 12),
        9:  (12, 12),
    },

    ItemType.Hammer: {
        0:  (11, 15),
        1:  (11, 16),
        2:  (12, 19),
        3:  (14, 22),
        4:  (15, 24),
        5:  (16, 28),
        6:  (17, 30),
        7:  (18, 32),
        8:  (18, 34),
        9:  (19, 35),
    },

    ItemType.Scythe: {
        0:  (8, 17),
        1:  (8, 18),
        2:  (9, 21),
        3:  (10, 24),
        4:  (10, 28),
        5:  (10, 32),
        6:  (10, 35),
        7:  (10, 36),
        8:  (9, 40),
        9:  (9, 41),
    },

    ItemType.Shield: {
        0:  (8, 8),
        1:  (9, 9),
        2:  (10, 10),
        3:  (11, 11),
        4:  (12, 12),
        5:  (13, 13),
        6:  (14, 14),
        7:  (15, 15),
        8:  (16, 16),
        9:  (16, 16),
    },

    ItemType.Spear: {
        0:  (8, 12),
        1:  (8, 13),
        2:  (10, 15),
        3:  (11, 17),
        4:  (11, 19),
        5:  (12, 21),
        6:  (13, 23),
        7:  (13, 25),
        8:  (14, 26),
        9:  (14, 27),
    },

    ItemType.Staff: {
        0:  (7, 11),
        1:  (7, 11),
        2:  (8, 13),
        3:  (9, 14),
        4:  (10, 16),
        5:  (10, 18),
        6:  (10, 19),
        7:  (11, 20),
        8:  (11, 21),
        9:  (11, 22),
    },

    ItemType.Sword: {
        0:  (8, 10),
        1:  (8, 11),
        2:  (9, 13),
        3:  (11, 14),
        4:  (12, 16),
        5:  (13, 18),
        6:  (14, 19),
        7:  (14, 20),
        8:  (15, 22),
        9:  (15, 22),
    },

    ItemType.Wand: {
        0:  (7, 11),
        1:  (7, 11),
        2:  (8, 13),
        3:  (9, 14),
        4:  (10, 16),
        5:  (10, 18),
        6:  (11, 19),
        7:  (11, 20),
        8:  (11, 21),
        9:  (11, 22),
    },
}
