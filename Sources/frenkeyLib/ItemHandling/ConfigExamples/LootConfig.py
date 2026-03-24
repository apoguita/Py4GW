
import json
import os
from typing import Optional

from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.frenkeyLib.ItemHandling.Rules.base_rule import BaseRule
from Sources.frenkeyLib.ItemHandling.Rules.profile import RuleProfile
from Sources.frenkeyLib.ItemHandling.Rules.types import ItemAction

class LootConfig:
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
        
        self.blacklisted_items : list[int] = []
        self.whitelisted_items : list[int] = []
        
        self.rules : list[BaseRule] = []
        self.load()
        
    @property
    def default_folder(self) -> str:
        # project_path = Console.get_projects_path()
        path = os.path.join("Settings", "Global", "Item & Inventory")
        return path
    
    @property
    def default_path(self) -> str:
        return os.path.join(self.default_folder, "LootConfig.json")
                
    def reset(self):
        self.blacklisted_items.clear()
        self.whitelisted_items.clear()
        
    @classmethod
    def from_dict(cls, data: dict) -> "LootConfig":
        config = cls()
        
        rules = [BaseRule.from_dict(rule_data) for rule_data in data.get("rules", [])]
        config.rules = [rule for rule in rules if rule and rule.action == ItemAction.PickUp]
        
        return config
    
    def to_dict(self) -> dict:
        return {
            "rules": [rule.to_dict() for rule in self.rules]
        }   
        
    def load(self, path: Optional[str] = None):
        ## Whatever Path
        path = path or self.default_path
        
        try:
            with open(path, "r", encoding="utf-8") as file:
                payload = json.load(file)
        
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        
        return self.from_dict(payload)
    
    def save(self, path: Optional[str] = None):
        path = path or self.default_path
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, indent=4, ensure_ascii=False)
                 
        
        # ------- Loot Filtering Logic -------
    
    def GetfilteredLootArray(self, distance: float = Range.SafeCompass.value, multibox_loot: bool = False, allow_unasigned_loot=False) -> list[int]:
        
        def IsValidItem(item_id):
            if not Agent.IsValid(item_id):
                return False    
            player_agent_id = Player.GetAgentID()
            owner_id = Agent.GetItemAgentOwnerID(item_id)
            return ((owner_id == player_agent_id) or (owner_id == 0))
        
        if not Routines.Checks.Map.MapValid():
            return []
            
        loot_array = AgentArray.GetItemArray()
        loot_array = AgentArray.Filter.ByDistance(loot_array, Player.GetXY(), distance)

        loot_array = AgentArray.Filter.ByCondition(
            loot_array,
            lambda item_id: IsValidItem(item_id)
        )
        
        pick_up_array = []

        for agent_id in loot_array[:]:  # Iterate over a copy to avoid modifying while iterating
            item_data = Agent.GetItemAgentByID(agent_id)
            if item_data is None:
                continue
            
            item_id = item_data.item_id
            
            # --- Hard block: blacklists ---
            if item_id in self.blacklisted_items:
                continue
            
            # --- Whitelists ---
            if item_id in self.whitelisted_items:
                pick_up_array.append(agent_id)
                continue
            
            for rule in self.rules:
                if rule.applies(item_id):
                    pick_up_array.append(agent_id)
                    break  # No need to check other rules if one matches
            
        pick_up_array = AgentArray.Sort.ByDistance(pick_up_array, Player.GetXY())

        return pick_up_array
