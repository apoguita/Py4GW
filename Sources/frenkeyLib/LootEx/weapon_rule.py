from Sources.frenkeyLib.LootEx import models, enum
from Sources.frenkeyLib.LootEx.enum import ItemAction
from Py4GWCoreLib import *

class WeaponRule:
    def __init__(self, item_type: ItemType):
        self.item_type: ItemType = item_type
        self.requirements: dict[int, models.IntRange] = {}
        self.mods: dict[str, models.ModInfo] = {}
        self.mods_type: enum.ActionModsType = enum.ActionModsType.Any
        
    def to_dict(self) -> dict:
        return {
            "item_type": self.item_type.name,
            "mods_type": self.mods_type.name,
            "requirements": {
                req: (damage_range.min, damage_range.max) for req, damage_range in self.requirements.items()
            },
            "mods": {
                mod_id: mod.to_dict() for mod_id, mod in self.mods.items()
            },
        }
        
    @staticmethod
    def from_dict(data: dict) -> "WeaponRule":
        item_type = ItemType[data["item_type"]]
        
        rule = WeaponRule(item_type)
        rule.mods_type = enum.ActionModsType[data.get("mods_type", "Any")]
        
        for req, (min_value, max_value) in data.get("requirements", {}).items():
            rule.requirements[int(req)] = models.IntRange(min_value, max_value)
            
        for mod_id, mod_data in data.get("mods", {}).items():
            rule.mods[mod_id] = models.ModInfo.from_dict(mod_data)
        
        
        return rule
    
    def add_mod(self, mod: models.ItemMod):
        if mod.identifier not in self.mods:
            self.mods[mod.identifier] = models.ModInfo(mod)
        else:
            existing_mod = self.mods[mod.identifier]
            modifier_range = mod.get_modifier_range()
            existing_mod.min = modifier_range.max
            existing_mod.max = modifier_range.max
            
    def remove_mod(self, mod: models.ItemMod):
        if mod.identifier in self.mods:
            del self.mods[mod.identifier]
            
    def matches(self, target_item) -> bool:
        from Sources.frenkeyLib.LootEx import cache
        item : cache.Cached_Item = target_item
        
        if item.item_type != self.item_type:
            return False
                
        requirement = item.requirements
        requirement_info = self.requirements.get(requirement, None) if self.requirements else None
        if not requirement_info:
            return False
                
        if (item.damage[0] < requirement_info.min or item.damage[1] < requirement_info.max):
            return False        
            
        match(self.mods_type):
            case enum.ActionModsType.Any | enum.ActionModsType.Inscribable:
                if item.is_inscribable:
                    return True

            case enum.ActionModsType.Old_School:
                if item.is_inscribable:
                    return False

        ## get the inherent mod from item.weapon_mods
        inherent_mod = next((mod for mod in item.weapon_mods if mod.WeaponMod.mod_type == enum.ModType.Inherent), None)
        
        if not inherent_mod:
            return False
                        
        if self.mods:
            for mod_id, mod_info in self.mods.items():
                if inherent_mod.WeaponMod.identifier == mod_id:                    
                    if inherent_mod.Value < mod_info.min or inherent_mod.Value > mod_info.max:
                        return False
                    
                    return True
            
        return False