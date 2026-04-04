from __future__ import annotations

from typing import ClassVar

from Py4GWCoreLib.enums_src.GameData_enums import DyeColor
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Sources.frenkeyLib.ItemHandling.GlobalConfigs.Rule import DyeRule, DyesRule, ItemTypesRule, ItemTypeRule, ModelIdRule, ModelIdsRule, RaritiesRule, RarityRule, Rule


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

    def HasMatchingRule(self, rule: Rule) -> bool:
        '''
        Checks whether an equivalent rule is already contained in the config.
        '''
        return any(existing_rule.equals(rule) for existing_rule in self)
            
    #region Helpers to add and create rules easily
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
    
    def AddModelId(self, model_id: int):
        '''
        Helper method to add a ModelIdRule to the config.
        '''
        rule = ModelIdRule(model_id)
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
        rule = RarityRule(rarity)
        self.AddRule(rule)
    
    def AddRarities(self, rarities: list[Rarity]):
        '''
        Helper method to add a RaritiesRule to the config.
        '''
        rule = RaritiesRule(rarities)
        self.AddRule(rule)
    
    def AddItemType(self, item_type: ItemType):
        '''
        Helper method to add an ItemTypeRule to the config.
        '''
        rule = ItemTypeRule(item_type)
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
        rule = DyeRule(dye_color)
        self.AddRule(rule)
    
    def AddDyeColors(self, dye_colors: list[DyeColor]):
        '''
        Helper method to add a DyeColorsRule to the config.
        '''
        rule = DyesRule(dye_colors)
        self.AddRule(rule)
    #endregion
