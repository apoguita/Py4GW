from Widgets.frenkey.LootEx import models, enum
from Widgets.frenkey.LootEx.enum import ItemAction
from Py4GWCoreLib import *

class ConfigurationCondition:
    def __init__(self, name: str = "New Condition", action: ItemAction = ItemAction.Stash):
        self.name: str = name
        self.damage_range: Optional[models.IntRange] = None
        self.requirements: Optional[dict[Attribute, models.IntRange]] = None

        self.prefix_mod: Optional[str] = None
        self.suffix_mod: Optional[str] = None
        self.inherent_mod: Optional[str] = None
        self.old_school_only: bool = False
        self.threshold: Optional[int] = None
        self.keep_in_inventory: int = 0

        self.rarities: dict[Rarity, bool] = {
            rarity: False for rarity in Rarity}

        self.action: ItemAction = action


class ItemConfiguration:
    def __init__(self, model_id: int, item_type : ItemType, action: ItemAction = ItemAction.Stash):
        self.model_id: int = model_id
        self.item_type: ItemType = item_type
        self.conditions: list[ConfigurationCondition] = [ConfigurationCondition("Default", action)]

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "item_type": self.item_type.name if isinstance(self.item_type, ItemType) else self.item_type,
            "conditions": [
                {
                    "name": condition.name,
                    "keep_in_inventory": condition.keep_in_inventory,
                    "damage_range": (condition.damage_range.min, condition.damage_range.max)
                    if condition.damage_range
                    else None,
                    "prefix_mod": condition.prefix_mod,
                    "suffix_mod": condition.suffix_mod,
                    "inherent_mod": condition.inherent_mod,
                    "old_school_only": condition.old_school_only,
                    "threshold": condition.threshold,
                    "rarities": {
                        rarity.name: value for rarity, value in condition.rarities.items()
                    },
                    "action": condition.action.name,
                    "requirements": {
                        attribute.name: (requirement.min, requirement.max)
                        for attribute, requirement in condition.requirements.items()
                    }
                    if condition.requirements
                    else None,
                }
                for condition in self.conditions
            ],
        }

    @staticmethod
    def from_dict(data) -> "ItemConfiguration":
        model_id = data["model_id"]
        item_type_name = data.get("item_type", ItemType.Unknown.name)
        item_type = ItemType[item_type_name] if item_type_name in ItemType.__members__ else ItemType.Unknown

        item = ItemConfiguration(model_id, item_type)
        item.conditions = []

        for condition_data in data.get("conditions", []):
            name = condition_data.get("name", None)
            
            if not name:
                raise ValueError("Condition name is required")
                        
            condition = ConfigurationCondition(name)            
            condition.action = ItemAction[condition_data.get("action", "Stash")]
            
            condition.keep_in_inventory = condition_data.get("keep_in_inventory", 0)
            
            damage_range = condition_data.get("damage_range", None)
            damage_range = (
                models.IntRange(
                    condition_data["damage_range"][0], condition_data["damage_range"][1]
                )
                if condition_data["damage_range"]
                else None
            )            
            condition.damage_range = damage_range
            
            condition.prefix_mod = condition_data.get("prefix_mod", None)
            condition.suffix_mod = condition_data.get("suffix_mod", None)
            condition.inherent_mod = condition_data.get("inherent_mod", None)
            condition.old_school_only = condition_data.get("old_school_only", False)
            condition.threshold = condition_data.get("threshold", None)
            
            rarities = condition_data.get("rarities", {})
            rarities = {
                Rarity[rarity]: value
                for rarity, value in rarities.items()
                if rarity in Rarity.__members__
            } if rarities else {}
            condition.rarities = rarities

            requirements = condition_data.get("requirements", {})
            requirements = (
                {
                    Attribute[attribute]: models.IntRange(
                        requirement[0], requirement[1])
                    for attribute, requirement in requirements.items()
                    if attribute in Attribute.__members__
                }
                if requirements
                else None
            )
            condition.requirements = requirements
            item.conditions.append(condition)

        return item

    def get_condition(self, item) -> Optional[ConfigurationCondition]:        
        from Widgets.frenkey.LootEx.cache import Cached_Item
        
        #sort the conditions based on their assigned action value 
        sorted_conditions = sorted(self.conditions, key=lambda c: c.action.value)
        
        for condition in sorted_conditions:            
            if item.is_weapon and item.mods:                
                has_prefix = condition.prefix_mod is None or any(mod.identifier == condition.prefix_mod for mod in item.mods)
                has_suffix = condition.suffix_mod is None or any(mod.identifier == condition.suffix_mod for mod in item.mods)
                has_inherent = condition.inherent_mod is None or any(mod.identifier == condition.inherent_mod for mod in item.mods)
                
                if (not has_prefix or not has_suffix or not has_inherent):
                    continue
                
                if condition.old_school_only and item.is_inscribable:
                    continue

                ## TODO: Fix the requirement check as attribute is wrong
                if condition.requirements:
                    if not condition.requirements.get(item.attribute, None):
                        continue
                    
                    requirement = condition.requirements[item.attribute]
                    if requirement.min > item.requirements or requirement.max < item.requirements:
                        continue
                
                if item.item_type is ItemType.Shield:
                    if condition.damage_range and (condition.damage_range.min > item.shield_armor[0] or condition.damage_range.max < item.shield_armor[1]):
                        continue
                    
                elif item.item_type is ItemType.Offhand:
                    if condition.damage_range and (condition.damage_range.min > item.damage[0] or condition.damage_range.max < item.damage[1]):
                        continue
                    
                else:                
                    if condition.damage_range and (condition.damage_range.min > item.damage[0] or condition.damage_range.max < item.damage[1]):
                        continue
                
                # if item.rarity not in condition.rarities or not condition.rarities[item.rarity]:
                #     continue
                
                return condition            
            else:
                if condition.action == ItemAction.Stash:
                    if item.quantity <= condition.keep_in_inventory:                     
                        continue
                
                return condition
            
        return None
              
    def get_action(self, item) -> enum.ItemAction:
        if item.action != ItemAction.NONE:
            return item.action
                        
        condition = self.get_condition(item)
        
        if condition:
            return condition.action
        
        return ItemAction.NONE
        