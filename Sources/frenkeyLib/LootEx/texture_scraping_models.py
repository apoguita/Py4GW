
import os
from typing import Optional

from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Sources.frenkeyLib.LootEx.enum import ITEM_TEXTURE_FOLDER


class ScrapedSalvageResult:
    def __init__(self, name: str, min_amount: int = -1, max_amount: int = -1, amount: int = -1):
        self.name = name
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.amount = amount        
    
    def to_json(self) -> dict:
        return {
            "name": self.name,
            "min_amount": self.min_amount,
            "max_amount": self.max_amount,
            "amount": self.amount
        }
        
    @staticmethod
    def from_json(data: dict) -> 'ScrapedSalvageResult':
        return ScrapedSalvageResult(
            name=data["name"],
            min_amount=data.get("min_amount", -1),
            max_amount=data.get("max_amount", -1),
            amount=data.get("amount", -1)
        )
        
    
    def __str__(self) -> str:
        if self.amount >= 0:
            return f"{self.name} x{self.amount}"
        elif self.min_amount >= 0 and self.max_amount >= 0:
            return f"{self.name} x{self.min_amount}-{self.max_amount}"
        else:
            return self.name

class ScrapedItem:
    def __init__(self, name: str):
        self.name = name
        self.inventory_icon_url: Optional[str] = None
        self.inventory_icon_path: Optional[str] = None
        self.common_salvage: list[ScrapedSalvageResult] = []
        self.rare_salvage: list[ScrapedSalvageResult] = []
        self.item_type: Optional[str] = None
        self.acquisition_tree : Optional[list[dict]] = None
        self.description : Optional[str] = None
        self._inventory_icon_exists : Optional[bool] = None
    
    def compose_tree(self, tree, indent=0) -> str:
        if tree is None:
            return "No Acquisition Info"
        
        lines = []
        for node in tree:
            name = node.get("name", "<no name>")
            lines.append("\t" * indent + str(name))
            children = node.get("children", [])
            if children:
                lines.append(self.compose_tree(children, indent + 1))      
                   
        return "\n".join(lines)
    @property
    def Acquisition(self):           
        
        if self.acquisition_tree is None:
            return "No Acquisition Info"
        
        return self.compose_tree(self.acquisition_tree)
                
    
    @property
    def IconPath(self) -> str:
        if self.inventory_icon_path:
            return self.inventory_icon_path
        
        if self.inventory_icon_url is None:
            return ""
        
        relative_file_path_from_url = self.inventory_icon_url.lstrip("/\\").replace("/", "\\")
        file_name = os.path.basename(relative_file_path_from_url)
        path = os.path.join(ITEM_TEXTURE_FOLDER, file_name)
        
        return path
    
    @property
    def IconExists(self) -> bool:
        if self._inventory_icon_exists is None:
            if self.inventory_icon_path:
                self._inventory_icon_exists = os.path.exists(self.inventory_icon_path)
                return self._inventory_icon_exists
            
            elif self.inventory_icon_url is None:
                self._inventory_icon_exists = False
                return self._inventory_icon_exists
            
            relative_file_path_from_url = self.inventory_icon_url.lstrip("/\\").replace("/", "\\") if self.inventory_icon_url else None 
            file_name = os.path.basename(relative_file_path_from_url ) if relative_file_path_from_url else None
            
            if file_name is None:
                self._inventory_icon_exists = False
                return self._inventory_icon_exists
            
            path = os.path.join(ITEM_TEXTURE_FOLDER, file_name)
            
            self._inventory_icon_exists = os.path.exists(path) if path else False
        
        return bool(self._inventory_icon_exists)
        
    def to_json(self) -> dict:
        return {
            "name": self.name,
            "inventory_icon_url": self.inventory_icon_url,
            "common_salvage": [s.to_json() for s in self.common_salvage],
            "rare_salvage": [s.to_json() for s in self.rare_salvage],
            "item_type": self.item_type,
            "acquisition_tree": self.acquisition_tree,
            "description": self.description
        }        
    
    @staticmethod
    def from_json(data: dict) -> 'ScrapedItem':
        item = ScrapedItem(data["name"])
        item.inventory_icon_url = data.get("inventory_icon_url")
        item.common_salvage = [ScrapedSalvageResult.from_json(s) for s in data.get("common_salvage", [])]
        item.rare_salvage = [ScrapedSalvageResult.from_json(s) for s in data.get("rare_salvage", [])]
        item.item_type = data.get("item_type")
        item.acquisition_tree = data.get("acquisition_tree")
        item.description = data.get("description")
        
        return item
