from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, ClassVar, Self, cast

from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Py4GWCoreLib.enums_src.Model_enums import ModelID


@dataclass(frozen=True)
class BuyConfigEntry:
    key: str
    label: str
    quantity: int
    model_id: ModelID | int | None = None
    item_type: ItemType | None = None
    description: str = ""


class BuyConfig():
    _initialized: bool = False    
    _instance : ClassVar[Self | None] = None

    def __new__(cls: type[Self]) -> Self:
        instance = cast(Self | None, cls._instance)
        if instance is None:
            instance = cast(Self, super().__new__(cls))
            instance._initialized = False
            cls._instance = instance
        return instance
            
    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.lesser_salvage_kits: int = 0
        self.expert_salvage_kits: int = 0
        self.superior_salvage_kits: int = 0
        self.superior_identification_kits: int = 0
        self.lockpicks: int = 0
        self.keys: int = 0

    @classmethod
    def Load(cls: type[Self], file_path: str) -> Self:
        '''
        Loads the config from a JSON file at the specified file path and returns a new instance of the config with the loaded rules.
        '''
        if not os.path.isfile(file_path):
            return cls()  # Return an empty config if the file does not exist
        
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        instance = cls()
        instance.load_dict(json_data or {})
        
        return instance
    
    def to_dict(self) -> dict[str, int]:
        return {
            "lesser_salvage_kits": max(0, int(self.lesser_salvage_kits)),
            "expert_salvage_kits": max(0, int(self.expert_salvage_kits)),
            "superior_salvage_kits": max(0, int(self.superior_salvage_kits)),
            "superior_identification_kits": max(0, int(self.superior_identification_kits)),
            "lockpicks": max(0, int(self.lockpicks)),
            "keys": max(0, int(self.keys)),
        }

    def load_dict(self, data: dict[str, Any]) -> None:
        self.lesser_salvage_kits = max(0, int(data.get("lesser_salvage_kits", 0) or 0))
        self.expert_salvage_kits = max(0, int(data.get("expert_salvage_kits", 0) or 0))
        self.superior_salvage_kits = max(0, int(data.get("superior_salvage_kits", 0) or 0))
        self.superior_identification_kits = max(0, int(data.get("superior_identification_kits", 0) or 0))
        self.lockpicks = max(0, int(data.get("lockpicks", 0) or 0))
        self.keys = max(0, int(data.get("keys", 0) or 0))

    def load_legacy_inventory_stock(self, entries: list[dict[str, Any]]) -> None:
        self.lesser_salvage_kits = 0
        self.expert_salvage_kits = 0
        self.superior_identification_kits = 0
        self.lockpicks = 0
        self.keys = 0

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            model_id_raw = entry.get("model_id")
            quantity = entry.get("quantity", 0)
            if not isinstance(model_id_raw, int):
                continue

            quantity_value = max(0, int(quantity or 0))

            try:
                model_id = ModelID(model_id_raw)
            except ValueError:
                model_id = model_id_raw

            if model_id == ModelID.Salvage_Kit:
                self.lesser_salvage_kits = max(self.lesser_salvage_kits, quantity_value)
            elif model_id in (ModelID.Expert_Salvage_Kit, ModelID.Superior_Salvage_Kit):
                self.expert_salvage_kits = max(self.expert_salvage_kits, quantity_value)
            elif model_id == ModelID.Superior_Identification_Kit:
                self.superior_identification_kits = max(self.superior_identification_kits, quantity_value)
            elif model_id == ModelID.Lockpick:
                self.lockpicks = max(self.lockpicks, quantity_value)
            else:
                item_type_name = entry.get("item_type")
                if item_type_name == ItemType.Key.name:
                    self.keys = max(self.keys, quantity_value)

    def get_entries(self) -> list[BuyConfigEntry]:
        return [
            BuyConfigEntry(
                key="lesser_salvage_kits",
                label="Salvage Kits",
                quantity=self.lesser_salvage_kits,
                model_id=ModelID.Salvage_Kit,
                item_type=ItemType.Kit,
                description="Keeps regular salvage kits in stock.",
            ),
            BuyConfigEntry(
                key="expert_salvage_kits",
                label="Expert Salvage Kits",
                quantity=self.expert_salvage_kits,
                model_id=ModelID.Expert_Salvage_Kit,
                item_type=ItemType.Kit,
                description="Keeps expert salvage kits in stock.",
            ),
            BuyConfigEntry(
                key="superior_salvage_kits",
                label="Superior Salvage Kits",
                quantity=self.superior_salvage_kits,
                model_id=ModelID.Superior_Salvage_Kit,
                item_type=ItemType.Kit,
                description="Keeps superior salvage kits in stock.",
            ),
            BuyConfigEntry(
                key="superior_identification_kits",
                label="(Superior) Identification Kits",
                quantity=self.superior_identification_kits,
                model_id=ModelID.Superior_Identification_Kit,
                item_type=ItemType.Kit,
                description="Keeps identification kits in stock.",
            ),
            BuyConfigEntry(
                key="lockpicks",
                label="Lockpicks",
                quantity=self.lockpicks,
                model_id=ModelID.Lockpick,
                item_type=ItemType.Key,
                description="Keeps lockpicks in stock.",
            ),
            # TODO: Need a better key handling for this.
            # BuyConfigEntry(
            #     key="keys",
            #     label="Any Keys",
            #     quantity=self.keys,
            #     item_type=ItemType.Key,
            #     description="Keeps generic chest keys in stock.",
            # ),
        ]
