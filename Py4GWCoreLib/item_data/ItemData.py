# singleton instance which contains all the item data of our `items.json` file. This is used to avoid having to read the file multiple times and to have a central place to access item data from

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
import json
import os
import traceback
from typing import Optional

from Py4GW import Console

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.GameData_enums import Attribute, Profession
from Py4GWCoreLib.enums_src.Item_enums import ItemType, NICK_CYCLE_COUNT, NICK_CYCLE_START_DATE
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.enums_src.Multiboxing_enums import ReloadType, SharedCommandType
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.native_src.internals.encoded_strings import GWStringEncoded

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
    
    def update_from(self, other: object) -> bool:
        """
        Update the current SalvageInfo with information from another SalvageInfo instance.
        Only updates fields that are missing or empty in the current instance.
        
        Args:
            other (SalvageInfo): The other SalvageInfo instance to update from.
        
        Returns:
            bool: True if any changes were made, False otherwise.
        """
        changed = False
        if not isinstance(other, SalvageInfo):
            return False
        
        if self.amount != other.amount and other.amount != -1:
            self.amount = other.amount
            changed = True
            
        if self.min_amount != other.min_amount and other.min_amount != -1:
            self.min_amount = other.min_amount
            changed = True
            
        if self.max_amount != other.max_amount and other.max_amount != -1:
            self.max_amount = other.max_amount
            changed = True
            
        if self.model_id != other.model_id and other.model_id != -1:
            self.model_id = other.model_id
            changed = True
            
        if self.name != other.name and other.name:
            self.name = other.name
            changed = True
            
        if changed:
            self.generate_summary()
            
        return changed

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

    def update_from(self, other: object) -> bool:
        """
        Update the current SalvageInfoCollection with information from another SalvageInfoCollection instance.
        Only updates fields that are missing or empty in the current instance.
        
        Args:
            other (SalvageInfoCollection): The other SalvageInfoCollection instance to update from.
        
        Returns:
            bool: True if any changes were made, False otherwise.
        """
        changed = False
        if not isinstance(other, SalvageInfoCollection):
            return False
        
        for material_name, other_info in other.items():
            if material_name in self:
                if self[material_name].update_from(other_info):
                    changed = True
            else:
                self[material_name] = other_info
                changed = True
                
        return changed

@dataclass(eq=False)
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
    
    _names: GWStringEncoded = GWStringEncoded(b"", "Unknown Item")
    
    def __post_init__(self):
        self._update_names()
        self.nick_date = self.next_nick_week
        
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        
        if name == "name_encoded" or name == "english_name":
            self._update_names()
            
    def __hash__(self) -> int:
        return hash((self.model_id, self.item_type))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ItemData):
            return NotImplemented

        return self.model_id == other.model_id and self.item_type == other.item_type

    def get_next_nick_cycle_start_date(self, start_date: Optional[datetime] = None) -> Optional[date]:
        if self.nick_index is None:
            return None

        start_date = start_date or datetime.now()
        nick_start_date = datetime.combine(NICK_CYCLE_START_DATE, datetime.min.time())

        # Monday 00:00 of the week we want to evaluate from.
        monday_of_current_week = start_date.date() - timedelta(days=start_date.weekday())
        current_week_start = datetime.combine(monday_of_current_week, datetime.min.time())

        first_matching_cycle = nick_start_date + timedelta(weeks=self.nick_index)
        if first_matching_cycle >= current_week_start:
            return first_matching_cycle.date()

        weeks_since_first_match = (current_week_start - first_matching_cycle).days // 7
        cycles_to_advance = (weeks_since_first_match + NICK_CYCLE_COUNT - 1) // NICK_CYCLE_COUNT
        next_cycle = first_matching_cycle + timedelta(weeks=cycles_to_advance * NICK_CYCLE_COUNT)
        return next_cycle.date()

    def get_weeks_until_next_nick(self, start_date: Optional[datetime] = None) -> Optional[int]:
        next_nick_week = self.get_next_nick_cycle_start_date(start_date)
        if next_nick_week is None:
            return None

        start_date = start_date or datetime.now()
        monday_of_current_week = start_date.date() - timedelta(days=start_date.weekday())
        current_week_start = datetime.combine(monday_of_current_week, datetime.min.time()).date()
        delta = next_nick_week - current_week_start
        if delta.days < 0:
            return None

        return delta.days // 7

    @property
    def next_nick_week(self) -> Optional[date]:
        return self.get_next_nick_cycle_start_date()

    @property
    def weeks_until_next_nick(self) -> Optional[int]:
        return self.get_weeks_until_next_nick()
    
    def _update_names(self):
        self._names = GWStringEncoded(self.name_encoded or bytes(), self.english_name or "Unknown Item")
    
    @property
    def names(self) -> GWStringEncoded:
        return self._names

    @property
    def name(self) -> str:
        return self._names.plain_singular
    
    @property
    def plural_name(self) -> str:
        return self._names.with_amount(2)

    @staticmethod
    def _parse_name_encoded(value: Optional[str]) -> bytes:
        if not value:
            return bytes()

        value = value.strip()
        if not value:
            return bytes()

        parts = [part.strip() for part in value.split(",") if part.strip()]
        return bytes(int(part, 16) for part in parts)

    @staticmethod
    def _format_name_encoded(value: bytes) -> str:
        if not value:
            return ""

        return ", ".join(f"0x{byte:X}" for byte in value)

    @staticmethod    
    def from_dict(data: dict) -> 'ItemData':
        profession_name = data.get("profession")
        english_name = data.get("name", "")
        
        item_data = ItemData(
            english_name=english_name,
            name_encoded=ItemData._parse_name_encoded(data.get("name_encoded")),
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

    def to_dict(self) -> dict:
        data = {
            "model_id": self.model_id,
            "item_type": self.item_type.name,
            "model_file_id": self.model_file_id,
            "name": self.english_name,
            "name_encoded" : self._format_name_encoded(self.name_encoded),
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
    
    def update_from(self, other: object) -> bool:
        """
        Update the current ItemData with information from another ItemData instance.
        Only updates fields that are missing or empty in the current instance.
        
        Args:
            other (ItemData): The other ItemData instance to update from.
        
        Returns:
            bool: True if any changes were made, False otherwise.
        """
        changed = False
        if not isinstance(other, ItemData):
            return False
        
        if self.model_id == -1 and other.model_id != -1:
            self.model_id = other.model_id
            changed = True
            
        if self.item_type == ItemType.Unknown and other.item_type != ItemType.Unknown:
            self.item_type = other.item_type
            changed = True
        
        if not self.english_name and other.english_name:
            self.english_name = other.english_name
            changed = True
            
        if not self.name_encoded and other.name_encoded:
            self.name_encoded = other.name_encoded
            changed = True

        merged_attributes = sorted(set(self.attributes).union(other.attributes), key=lambda attr: attr.name)
        if merged_attributes != self.attributes:
            self.attributes = merged_attributes
            changed = True

        if self.common_salvage is None and other.common_salvage is not None:
            self.common_salvage = other.common_salvage
            changed = True
        elif self.common_salvage is not None and other.common_salvage is not None:
            if self.common_salvage.update_from(other.common_salvage):
                changed = True
            
        if self.rare_salvage is None and other.rare_salvage is not None:
            self.rare_salvage = other.rare_salvage
            changed = True
        elif self.rare_salvage is not None and other.rare_salvage is not None:
            if self.rare_salvage.update_from(other.rare_salvage):
                changed = True
            
        if self.nick_index is None and other.nick_index is not None:
            self.nick_index = other.nick_index
            changed = True
            
        if self.profession is None and other.profession is not None:
            self.profession = other.profession
            changed = True
            
        if not self.wiki_url and other.wiki_url:
            self.wiki_url = other.wiki_url
            changed = True
            
        if not self.acquisition and other.acquisition:
            self.acquisition = other.acquisition
            changed = True
        
        if not self.description and other.description:
            self.description = other.description
            changed = True
            
        if not self.category and other.category:
            self.category = other.category
            changed = True
            
        if not self.sub_category and other.sub_category:
            self.sub_category = other.sub_category
            changed = True
            
        if self.skin is None and other.skin:
            self.skin = other.skin
            changed = True    
        
        return changed

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

MATERIAL_STORAGE_SLOTS : dict[int, int] = {
    ModelID.Bone: 0,   # Bone
    ModelID.Lump_Of_Charcoal: 26,  # Lump of Charcoal
    ModelID.Monstrous_Claw: 19,  # Monstrous Claw
    ModelID.Bolt_Of_Cloth: 5,   # Bolt of Cloth
    ModelID.Bolt_Of_Linen: 13,  # Bolt of Linen
    ModelID.Bolt_Of_Damask: 14,  # Bolt of Damask
    ModelID.Bolt_Of_Silk: 15,  # Bolt of Silk
    ModelID.Pile_Of_Glittering_Dust: 9,   # Pile of Glittering Dust
    ModelID.Glob_Of_Ectoplasm: 16,  # Glob of Ectoplasm
    ModelID.Monstrous_Eye: 20,  # Monstrous Eye
    ModelID.Monstrous_Fang: 21,  # Monstrous Fang
    ModelID.Feather: 11,  # Feather
    ModelID.Plant_Fiber: 10,  # Plant Fiber
    ModelID.Diamond: 24,  # Diamond
    ModelID.Onyx_Gemstone: 25,  # Onyx Gemstone
    ModelID.Ruby: 22,  # Ruby
    ModelID.Sapphire: 23,  # Sapphire
    ModelID.Tempered_Glass_Vial: 29,  # Tempered Glass Vial
    ModelID.Tanned_Hide_Square: 2,   # Tanned Hide Square
    ModelID.Fur_Square: 12,  # Fur Square
    ModelID.Leather_Square: 30,  # Leather Square
    ModelID.Elonian_Leather_Square: 31,  # Elonian Leather Square
    ModelID.Vial_Of_Ink: 32,  # Vial of Ink
    ModelID.Obsidian_Shard: 27,  # Obsidian Shard
    ModelID.Wood_Plank: 6,   # Wood Plank
    ModelID.Iron_Ingot: 1,   # Iron Ingot
    ModelID.Steel_Ingot: 17,  # Steel Ingot
    ModelID.Deldrimor_Steel_Ingot: 18,  # Deldrimor Steel Ingot
    ModelID.Roll_Of_Parchment: 33,  # Roll of Parchment
    ModelID.Roll_Of_Vellum: 34,  # Roll of Vellum
    ModelID.Scale: 3,   # Scale
    ModelID.Chitin_Fragment: 4,   # Chitin Fragment
    ModelID.Granite_Slab: 8,   # Granite Slab
    ModelID.Spiritwood_Plank: 35,  # Spiritwood Plank
    ModelID.Amber_Chunk: 36, # Amber Chunk
    ModelID.Jadeite_Shard: 37, # Jadeite Shard
}

RARE_MATERIALS : list[int] = [
    mat for mat, slot in MATERIAL_STORAGE_SLOTS.items() if slot > MATERIAL_STORAGE_SLOTS[ModelID.Feather]
]

COMMON_MATERIALS : list[int] = [
    mat for mat, slot in MATERIAL_STORAGE_SLOTS.items() if slot <= MATERIAL_STORAGE_SLOTS[ModelID.Feather]
]
