from Widgets.frenkey.LootEx import utility
from Widgets.frenkey.LootEx.enum import ItemAction, ItemCategory
from Py4GWCoreLib import *


class Filter:
    def __init__(self, filter_name: str):
        self.name: str = filter_name
        self.item_types: dict[ItemType, bool] = {
            item_type: False for item_type in ItemType}
        self.rarities: dict[Rarity, bool] = {
            rarity: False for rarity in Rarity}
        self.materials: dict[int, bool] = {}
        self.action: ItemAction = ItemAction.Stash
        self.salvage_item_max_vendorvalue = 1500
        self.full_stack_only: bool = False

    def handles_item(self, target_item) -> bool:
        from Widgets.frenkey.LootEx import cache
        item : cache.Cached_Item = target_item
        
        item_type_match = self.item_types.get(item.item_type, False)
        
        if not item_type_match:
            return False

        if not self.rarities.get(item.rarity, False) or self.rarities[item.rarity] is False:
            return False
        
        if item.is_rare_weapon_to_keep and self.action is not ItemAction.Loot:
            return False
    
        if self.action == ItemAction.Sell_To_Merchant:
            if item.value <= 0:
                return False

        if self.action == ItemAction.Salvage or self.action == ItemAction.Salvage or self.action == ItemAction.Salvage_Rare_Materials or self.action == ItemAction.Salvage_Common_Materials:
            if self.materials:
                if not item.data:
                    return False

                material_match = False
                
                
                common_materials = [
                    m.material_model_id for m in item.data.common_salvage.values()]
                rare_materials = [
                    m.material_model_id for m in item.data.rare_salvage.values()]
                
                for material in self.materials:
                    if material in common_materials or material in rare_materials:
                        material_match = True
                        break

                if not material_match:
                    return False

                if item.value > self.salvage_item_max_vendorvalue:
                    return False

        return True

    def get_action(self, item) -> ItemAction:                
        if self.handles_item(item):                
            if item.is_stackable and self.full_stack_only:
                if item.quantity < 250:
                    return ItemAction.Hold
                
            return self.action

        return ItemAction.NONE

    @staticmethod
    def to_dict(data: "Filter") -> dict:
        return {
            "name": data.name,
            "item_types": {item_type.name: value for item_type, value in data.item_types.items()},
            "rarities": {rarity.name: value for rarity, value in data.rarities.items()},
            "materials": {material: value for material, value in data.materials.items()},
            "salvage_item_max_vendorvalue": data.salvage_item_max_vendorvalue,
            "action": data.action.name,
            "full_stack_only": data.full_stack_only
        }

    @staticmethod
    def from_dict(data) -> "Filter":
        name = data.get("name", None)

        if not name:
            raise ValueError("Filter must have a name")

        loot_filter = Filter(name)

        action = ItemAction[data.get("action", "Stash")]
        loot_filter.action = action
        
        loot_filter.full_stack_only = data.get("full_stack_only", False)
       
        loot_filter.salvage_item_max_vendorvalue = data.get(
            "salvage_item_max_vendorvalue", 1500)

        item_types: dict[str, bool] = data.get("item_types", {})
        loot_filter.item_types = {
            ItemType[item_type]: value for item_type, value in item_types.items()}

        rarities: dict[str, bool] = data.get("rarities", {})
        loot_filter.rarities = {
            Rarity[rarity]: value for rarity, value in rarities.items()}

        materials = data.get("materials", {})
        loot_filter.materials = {
            int(material): value for material, value in materials.items()}

        return loot_filter
