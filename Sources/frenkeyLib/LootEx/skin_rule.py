from Sources.frenkeyLib.LootEx import models, enum
from Sources.frenkeyLib.LootEx.enum import ItemAction
from Py4GWCoreLib import *

class RequirementInfo:
    def __init__(self, min_value: int, max_value: int, max_damage_only: bool = True):
        self.min: int = min_value
        self.max: int = max_value
        self.max_damage_only: bool = max_damage_only

    def to_dict(self) -> dict:
        return {
            "min": self.min,
            "max": self.max,
            "max_damage_only": self.max_damage_only
        }

    @staticmethod
    def from_dict(data: dict) -> "RequirementInfo":
        return RequirementInfo(
            data["min"],
            data["max"],
            data.get("max_damage_only", True)
        )


class ItemModelInfo:
    def __init__(self, model_id: int, item_type: ItemType):
        self.model_id: int = model_id
        self.item_type: ItemType = item_type

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "item_type": self.item_type.name
        }

    @staticmethod
    def from_dict(data: dict) -> "ItemModelInfo":
        return ItemModelInfo(
            data["model_id"],
            ItemType[data["item_type"]]
        )


class SkinRule:
    def __init__(self, skin_name: str = "", action: ItemAction = ItemAction.Stash):
        self.skin: str = skin_name
        self.action: ItemAction = action
        self.full_stack_only: bool = False
        self.models: list[ItemModelInfo] = []
        self.rarities: dict[Rarity, bool] = {
            rarity: True for rarity in Rarity
        }

        self.mods_type: enum.ActionModsType = enum.ActionModsType.Any
        self.requirements: RequirementInfo = RequirementInfo(
            9,
            13
        )
        self.mods: dict[str, models.ModInfo] = {}

    def to_dict(self) -> dict:
        return {
            "skin": self.skin,
            "action": self.action.name,
            "full_stack_only": self.full_stack_only,
            "model_ids": [model_id.to_dict() for model_id in self.models],
            "rarities": {rarity.name: enabled for rarity, enabled in self.rarities.items()},
            "requirements": self.requirements.to_dict() if self.requirements else None,
            "mods": {mod_id: mod.to_dict() for mod_id, mod in self.mods.items()},
            "mods_type": self.mods_type.name if self.mods_type else "Any"
        }

    @staticmethod
    def from_dict(data: dict) -> "SkinRule":
        rule = SkinRule(
            skin_name=data["skin"],
            action=ItemAction[data["action"]]
        )

        rule.full_stack_only = data.get("full_stack_only", False)

        rule.models = [
            ItemModelInfo.from_dict(model_id) for model_id in data.get("model_ids", [])
        ]

        rule.rarities = {Rarity[rarity]: enabled for rarity,
                         enabled in data.get("rarities", {}).items()}
        rule.requirements = RequirementInfo.from_dict(
            data["requirements"]) if data.get("requirements") else RequirementInfo(9, 13)
        rule.mods_type = enum.ActionModsType[data.get("mods_type", "Any")]

        for mod_id, mod_data in data.get("mods", {}).items():
            rule.mods[mod_id] = models.ModInfo.from_dict(mod_data)

        return rule

    def get_items(self):
        from Sources.frenkeyLib.LootEx.data import Data
        data = Data()

        if not self.models:
            items = [
                item for item in data.Items.All if item.inventory_icon == self.skin]
        else:
            items = [item for model in self.models if (
                item := data.Items.get_item(model.item_type, model.model_id)) is not None]

        return items

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
        from Sources.frenkeyLib.LootEx.data import Data
        data = Data()
        
        from Sources.frenkeyLib.LootEx import cache
        item : cache.Cached_Item = target_item
                
        if item.skin != self.skin:
            return False

        model_info = next((
            model for model in self.models if model.model_id == item.model_id and model.item_type == item.item_type
        ), None)

        if self.models and not model_info:
            return False

        if item.rarity not in self.rarities or not self.rarities[item.rarity]:
            return False

        if item.is_weapon:

            if item.requirements not in range(self.requirements.min, self.requirements.max + 1):
                return False

            if self.requirements.max_damage_only:
                max_damage_range = data.DamageRanges.get(
                    item.item_type, {}).get(item.requirements, None)
                
                if not max_damage_range:
                    return False                

                if item.damage[0] < max_damage_range.min or item.damage[1] < max_damage_range.max:
                    return False

            match(self.mods_type):
                case enum.ActionModsType.Any:
                    if item.is_inscribable:
                        return True

                case enum.ActionModsType.Inscribable:
                    if not item.is_inscribable:
                        return False

                case enum.ActionModsType.Old_School:
                    if item.is_inscribable:
                        return False                    
                    
            if self.mods:
                inherent_mods = [
                    mod for mod in item.weapon_mods if mod.WeaponMod.mod_type == enum.ModType.Inherent]

                if self.mods and (not inherent_mods or not any(
                    mod.WeaponMod.identifier in self.mods for mod in inherent_mods
                )):
                    return False

        return True

    def get_action(self, target_item) -> ItemAction: 
        from Sources.frenkeyLib.LootEx import cache
        item : cache.Cached_Item = target_item
                
        if self.action is ItemAction.Stash and item.is_stackable and self.full_stack_only:
            if item.quantity < 250:
                return ItemAction.Hold
                
        return self.action
