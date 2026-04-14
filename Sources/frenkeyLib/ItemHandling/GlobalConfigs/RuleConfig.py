from __future__ import annotations

import json
import os
from typing import ClassVar

from Py4GWCoreLib.enums_src.GameData_enums import DyeColor
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.item_mods_src.upgrades import Upgrade
from Sources.frenkeyLib.ItemHandling.GlobalConfigs.Rule import DyesRule, ItemTypesRule, ModelIdsRule, RaritiesRule, Rule, UpgradeRule


class RuleConfig(list[Rule]):
    '''
    A config that contains rules for filtering items. This is used as a base class for the different configs, such as the loot config and the salvage config.
    It contains the basic functionality for evaluating items against the rules, as well as blacklists and whitelists.
    The specific configs can then add their own rules and functionality on top of this.
    
    All RuleConfigs are singletons, meaning that there will only be one instance of each config.
    This is because the configs are meant to be global and shared across the entire application, and having multiple instances would lead to confusion and bugs.
    The singleton pattern is implemented in a way that allows for easy subclassing, so that each specific config can have its own instance while still sharing the same base functionality.
    '''
    
    _instances: ClassVar[dict[type["RuleConfig"], "RuleConfig"]] = {}

    def __new__(cls):
        instance = cls._instances.get(cls)
        if instance is None:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[cls] = instance
        return instance
    
    def __init__(self):
        # only initialize once
        if self._initialized:
            return
        
        self._initialized = True
        
        self.blacklisted_items : list[int] = []
        self.whitelisted_items : list[int] = []
        
    def reset(self):
        '''
        Clears all blacklisted and whitelisted items from the config.
        This should be called on each map load since item ids reset on each load.
        '''
        
        self.blacklisted_items.clear()
        self.whitelisted_items.clear()
        
    
    def EvaluateItem(self, item_id: int) -> bool:
        '''
        Evaluates an item against the current rules and returns whether it matches the rules. Takes the blacklist and whitelist into account as well, with the blacklist having the highest priority, then the whitelist and then the rules. 
        This means that if an item is blacklisted, it will not match the rules even if it would normally match them, and if an item is whitelisted, it will match the rules even if it would not normally match them.
        '''
        
        # --- Hard block: blacklists ---
        if item_id in self.blacklisted_items:
            return False
        
        # --- Whitelists ---
        if item_id in self.whitelisted_items:
            return True
        
        for rule in self:
            if rule.applies(item_id):
                return True
            
        return False
    
    def EvaluateItems(self, item_ids: list[int]) -> list[int]:
        '''
        Evaluates a list of items against the current rules and returns a list of items that match the rules. Takes the blacklist and whitelist into account as well, with the blacklist having the highest priority, then the whitelist and then the rules. 
        This means that if an item is blacklisted, it will not match the rules even if it would normally match them, and if an item is whitelisted, it will match the rules even if it would not normally match them.
        '''
        
        filtered_items = []
        
        for item_id in item_ids:
            if self.EvaluateItem(item_id):
                filtered_items.append(item_id)
                
        return filtered_items

    def AddRule(self, rule: Rule):
        '''
        Adds a rule to the config if an equivalent rule is not already contained in the config. This is to prevent duplicate rules from being added, which would be redundant and adds unnecessary overhead when evaluating items against the rules.
        '''
        if not self.HasMatchingRule(rule):
            self.append(rule)
        
    def RemoveRule(self, rule: Rule):
        '''
        Removes a rule from the config if an equivalent rule is contained in the config.
        '''
        for existing_rule in self:
            if existing_rule.equals(rule):
                self.remove(existing_rule)
                break

    def HasMatchingRule(self, rule: Rule) -> bool:
        '''
        Checks whether an equivalent rule is already contained in the config.
        '''
        return any(existing_rule.equals(rule) for existing_rule in self)
            
    #region Helpers 
    """
    Helper methods to add and create rules easily without the need to create the rule objects manually.
    These methods create the rule objects and add them to the config in one step.
    This is just for convenience and readability when setting up the configs and is only a wrapper for the basic rules. More advanced rules should be created manually and added with AddRule.
    
        Example usage:
        config = RuleConfig() // LootConfig() // SalvageConfig()
        config.AddModelId(1234)
        config.AddModelIds([1234, ModelID.SomeModel])
        
        config.AddRarity(Rarity.Gold)
        config.AddRarities([Rarity.Purple, Rarity.Gold, Rarity.Green])     
           
        config.AddItemType(ItemType.Axe)
        config.AddItemTypes([ItemType.Axe, ItemType.Sword])
        
        config.AddDyeColor(DyeColor.Black)
        config.AddDyeColors([DyeColor.White, DyeColor.Black])
    """
    #region Adding helper methods for creating and adding rules in one step
    def AddModelId(self, model_id: int):
        '''
        Helper method to add a ModelIdRule to the config.
        '''
        rule = ModelIdsRule([model_id])
        self.AddRule(rule)
    
    def AddModelIds(self, model_ids: list[int|ModelID]):
        '''
        Helper method to add a ModelIdsRule to the config.
        '''
        rule = ModelIdsRule(model_ids)
        self.AddRule(rule)
        
    def AddRarity(self, rarity: Rarity):
        '''
        Helper method to add a RarityRule to the config.
        '''
        rule = RaritiesRule([rarity])
        self.AddRule(rule)
    
    def AddRarities(self, rarities: list[Rarity]):
        '''
        Helper method to add a RaritiesRule to the config.
        '''
        rule = RaritiesRule(rarities)
        self.AddRule(rule)
    
    def AddItemType(self, item_type: ItemType):
        '''
        Helper method to add an ItemTypesRule to the config.
        '''
        rule = ItemTypesRule([item_type])
        self.AddRule(rule)      
        
    def AddItemTypes(self, item_types: list[ItemType]):
        '''
        Helper method to add an ItemTypesRule to the config.
        '''
        rule = ItemTypesRule(item_types)
        self.AddRule(rule)      
        
    def AddDyeColor(self, dye_color: DyeColor):
        '''
        Helper method to add a DyeRule to the config.
        '''
        rule = DyesRule([dye_color])
        self.AddRule(rule)
    
    def AddDyeColors(self, dye_colors: list[DyeColor]):
        '''
        Helper method to add a DyeColorsRule to the config.
        '''
        rule = DyesRule(dye_colors)
        self.AddRule(rule)

    def AddUpgrade(self, upgrade: Upgrade):
        '''
        Helper method to add an UpgradeRule to the config.
        '''
        rule = UpgradeRule([upgrade])
        self.AddRule(rule)

    def AddUpgrades(self, upgrades: list[(tuple[Upgrade, list[ItemType]] | Upgrade)]):
        '''
        Helper method to add an UpgradeRule to the config.
        '''
        rule = UpgradeRule(upgrades)
        self.AddRule(rule)

    #endregion Adding helper methods for creating and adding rules in one step
    
    #region Deleting helper methods for creating and adding rules in one step
    def RemoveModelId(self, model_id: int):
        '''
        Helper method to remove a ModelIdRule from the config.
        '''
        rule = ModelIdsRule([model_id])
        self.RemoveRule(rule)
        
    def RemoveModelIds(self, model_ids: list[int|ModelID]):
        '''
        Helper method to remove a ModelIdsRule from the config.
        '''
        rule = ModelIdsRule(model_ids)
        self.RemoveRule(rule)
        
    def RemoveRarity(self, rarity: Rarity):
        '''
        Helper method to remove a RarityRule from the config.
        '''
        rule = RaritiesRule([rarity])
        self.RemoveRule(rule)
        
    def RemoveRarities(self, rarities: list[Rarity]):
        '''
        Helper method to remove a RaritiesRule from the config.
        '''
        rule = RaritiesRule(rarities)
        self.RemoveRule(rule)
        
    def RemoveItemType(self, item_type: ItemType):
        '''
        Helper method to remove an ItemTypesRule from the config.
        '''
        rule = ItemTypesRule([item_type])
        self.RemoveRule(rule)
        
    def RemoveItemTypes(self, item_types: list[ItemType]):
        '''
        Helper method to remove an ItemTypesRule from the config.
        '''
        rule = ItemTypesRule(item_types)
        self.RemoveRule(rule)
        
    def RemoveDyeColor(self, dye_color: DyeColor):
        '''
        Helper method to remove a DyesRule from the config.
        '''
        rule = DyesRule([dye_color])
        self.RemoveRule(rule)
        
    def RemoveDyeColors(self, dye_colors: list[DyeColor]):
        '''
        Helper method to remove a DyesRule from the config.
        '''
        rule = DyesRule(dye_colors)
        self.RemoveRule(rule)

    def RemoveUpgrade(self, upgrade: Upgrade):
        '''
        Helper method to remove an UpgradeRule from the config.
        '''
        rule = UpgradeRule([upgrade])
        self.RemoveRule(rule)

    def RemoveUpgrades(self, upgrades: list[(tuple[Upgrade, list[ItemType]] | Upgrade)]):
        '''
        Helper method to remove an UpgradeRule from the config.
        '''
        rule = UpgradeRule(upgrades)
        self.RemoveRule(rule)
    #endregion Deleting helper methods for creating and adding rules in one step
    
    #endregion Helpers

    #region Json Serialization
    def to_json_format(self) -> list[dict]:
        '''
        Serializes the rules to a JSON-compatible structure.
        '''
        
        return [rule.to_dict() for rule in self]
    
    @classmethod
    def from_json(cls, json_data: list[dict]) -> "RuleConfig":
        '''
        Deserializes the rules from a JSON-compatible structure into this config class' singleton instance.
        '''
        if not isinstance(json_data, list):
            raise ValueError("RuleConfig JSON payload must be a list of rule objects.")

        parsed_rules: list[Rule] = []

        for rule_data in json_data:
            if not isinstance(rule_data, dict):
                continue

            rule = Rule.from_dict(rule_data)
            if rule is None:
                continue

            if any(existing_rule.equals(rule) for existing_rule in parsed_rules):
                continue

            parsed_rules.append(rule)

        instance = cls()
        instance.clear()
        instance.extend(parsed_rules)
        
        return instance
    #endregion Json Serialization
    
    #region Loading and Saving
    def Save(self, file_path: str):
        '''
        Saves the config to a JSON file at the specified file path.
        '''
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_json_format(), f, indent=4, ensure_ascii=False)
            
    @classmethod
    def Load(cls, file_path: str) -> "RuleConfig":
        '''
        Loads the config from a JSON file at the specified file path and returns a new instance of the config with the loaded rules.
        '''
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        return cls.from_json(json_data)
    #endregion Loading and Saving
