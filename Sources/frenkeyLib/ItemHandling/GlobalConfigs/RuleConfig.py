from __future__ import annotations

import json
import os
from typing import ClassVar, Self, cast

from Py4GWCoreLib.enums_src.GameData_enums import DyeColor
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.item_mods_src.upgrades import Upgrade
from Sources.frenkeyLib.ItemHandling.GlobalConfigs import Rule as RuleModule


class RuleConfig(list[RuleModule.Rule]):
    allowed_rule_types: ClassVar[tuple[type[RuleModule.Rule], ...] | None] = None
    
    def __init__(self):        
        self.blacklisted_items : list[int] = []
        self.whitelisted_items : list[int] = []
        
    def reset(self):
        '''
        Clears all blacklisted and whitelisted items from the config.
        This should be called on each map load since item ids reset on each load.
        '''
        
        self.blacklisted_items.clear()
        self.whitelisted_items.clear()

    @classmethod
    def GetAllowedRuleTypes(cls) -> tuple[type[RuleModule.Rule], ...] | None:
        return cls.allowed_rule_types

    @classmethod
    def _is_allowed_rule_type(cls, rule: RuleModule.Rule) -> bool:
        allowed_rule_types = cls.GetAllowedRuleTypes()
        return allowed_rule_types is None or isinstance(rule, allowed_rule_types)

    @classmethod
    def _cast_rule(cls, rule: RuleModule.Rule) -> RuleModule.Rule:
        if not cls._is_allowed_rule_type(rule):
            raise TypeError(
                f"{type(rule).__name__} is not allowed in {cls.__name__}."
            )

        return cast(RuleModule.Rule, rule)

    def GetMatchedRule(self, item_id: int) -> RuleModule.Rule | None:
        '''
        Returns the first rule that matches the item id, or None if no rule matches.
        '''
        for rule in self:
            if rule.applies(item_id):
                return rule
            
        return None

    def EvaluateItem(self, item_id: int) -> bool:        
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

    def AddRule(self, rule: RuleModule.Rule):
        '''
        Adds a rule to the config if an equivalent rule is not already contained in the config. This is to prevent duplicate rules from being added, which would be redundant and adds unnecessary overhead when evaluating items against the rules.
        '''
        typed_rule = self._cast_rule(rule)

        if not self.HasMatchingRule(rule):
            self.append(typed_rule)
        
    def RemoveRule(self, rule: RuleModule.Rule):
        '''
        Removes a rule from the config if an equivalent rule is contained in the config.
        '''
        for existing_rule in self:
            if existing_rule.equals(rule):
                self.remove(existing_rule)
                break

    def HasMatchingRule(self, rule: RuleModule.Rule) -> bool:
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
        rule = RuleModule.ModelIdsRule([model_id])
        self.AddRule(rule)
    
    def AddModelIds(self, model_ids: list[int|ModelID]):
        '''
        Helper method to add a ModelIdsRule to the config.
        '''
        rule = RuleModule.ModelIdsRule(model_ids)
        self.AddRule(rule)
        
    def AddRarity(self, rarity: Rarity):
        '''
        Helper method to add a RarityRule to the config.
        '''
        rule = RuleModule.RaritiesRule([rarity])
        self.AddRule(rule)
    
    def AddRarities(self, rarities: list[Rarity]):
        '''
        Helper method to add a RaritiesRule to the config.
        '''
        rule = RuleModule.RaritiesRule(rarities)
        self.AddRule(rule)
    
    def AddItemType(self, item_type: ItemType):
        '''
        Helper method to add an ItemTypesRule to the config.
        '''
        rule = RuleModule.ItemTypesRule([item_type])
        self.AddRule(rule)      
        
    def AddItemTypes(self, item_types: list[ItemType]):
        '''
        Helper method to add an ItemTypesRule to the config.
        '''
        rule = RuleModule.ItemTypesRule(item_types)
        self.AddRule(rule)      
        
    def AddDyeColor(self, dye_color: DyeColor):
        '''
        Helper method to add a DyeRule to the config.
        '''
        rule = RuleModule.DyesRule([dye_color])
        self.AddRule(rule)
    
    def AddDyeColors(self, dye_colors: list[DyeColor]):
        '''
        Helper method to add a DyeColorsRule to the config.
        '''
        rule = RuleModule.DyesRule(dye_colors)
        self.AddRule(rule)

    def AddUpgrade(self, upgrade: Upgrade):
        '''
        Helper method to add an UpgradeRule to the config.
        '''
        rule = RuleModule.UpgradesRule([upgrade])
        self.AddRule(rule)

    def AddUpgrades(self, upgrades: list[(tuple[Upgrade, list[ItemType]] | Upgrade)]):
        '''
        Helper method to add an UpgradeRule to the config.
        '''
        rule = RuleModule.UpgradesRule(upgrades)
        self.AddRule(rule)

    #endregion Adding helper methods for creating and adding rules in one step
    
    #region Deleting helper methods for creating and adding rules in one step
    def RemoveModelId(self, model_id: int):
        '''
        Helper method to remove a ModelIdRule from the config.
        '''
        rule = RuleModule.ModelIdsRule([model_id])
        self.RemoveRule(rule)
        
    def RemoveModelIds(self, model_ids: list[int|ModelID]):
        '''
        Helper method to remove a ModelIdsRule from the config.
        '''
        rule = RuleModule.ModelIdsRule(model_ids)
        self.RemoveRule(rule)
        
    def RemoveRarity(self, rarity: Rarity):
        '''
        Helper method to remove a RarityRule from the config.
        '''
        rule = RuleModule.RaritiesRule([rarity])
        self.RemoveRule(rule)
        
    def RemoveRarities(self, rarities: list[Rarity]):
        '''
        Helper method to remove a RaritiesRule from the config.
        '''
        rule = RuleModule.RaritiesRule(rarities)
        self.RemoveRule(rule)
        
    def RemoveItemType(self, item_type: ItemType):
        '''
        Helper method to remove an ItemTypesRule from the config.
        '''
        rule = RuleModule.ItemTypesRule([item_type])
        self.RemoveRule(rule)
        
    def RemoveItemTypes(self, item_types: list[ItemType]):
        '''
        Helper method to remove an ItemTypesRule from the config.
        '''
        rule = RuleModule.ItemTypesRule(item_types)
        self.RemoveRule(rule)
        
    def RemoveDyeColor(self, dye_color: DyeColor):
        '''
        Helper method to remove a DyesRule from the config.
        '''
        rule = RuleModule.DyesRule([dye_color])
        self.RemoveRule(rule)
        
    def RemoveDyeColors(self, dye_colors: list[DyeColor]):
        '''
        Helper method to remove a DyesRule from the config.
        '''
        rule = RuleModule.DyesRule(dye_colors)
        self.RemoveRule(rule)

    def RemoveUpgrade(self, upgrade: Upgrade):
        '''
        Helper method to remove an UpgradeRule from the config.
        '''
        rule = RuleModule.UpgradesRule([upgrade])
        self.RemoveRule(rule)

    def RemoveUpgrades(self, upgrades: list[(tuple[Upgrade, list[ItemType]] | Upgrade)]):
        '''
        Helper method to remove an UpgradeRule from the config.
        '''
        rule = RuleModule.UpgradesRule(upgrades)
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
    def from_json(cls: type[Self], json_data: list[dict]) -> Self:
        '''
        Deserializes the rules from a JSON-compatible structure into this config class' singleton instance.
        '''
        if not isinstance(json_data, list):
            raise ValueError("RuleConfig JSON payload must be a list of rule objects.")

        parsed_rules: list[RuleModule.Rule] = []

        for rule_data in json_data:
            if not isinstance(rule_data, dict):
                continue

            rule = RuleModule.Rule.from_dict(rule_data)
            if rule is None:
                continue

            if not cls._is_allowed_rule_type(rule):
                continue

            typed_rule = cast(RuleModule.Rule, rule)

            if any(existing_rule.equals(typed_rule) for existing_rule in parsed_rules):
                continue

            parsed_rules.append(typed_rule)

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
    def Load(cls: type[Self], file_path: str) -> Self:
        '''
        Loads the config from a JSON file at the specified file path and returns a new instance of the config with the loaded rules.
        '''
        if not os.path.isfile(file_path):
            return cls()  # Return an empty config if the file does not exist
        
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            
        return cls.from_json(json_data)
    #endregion Loading and Saving
