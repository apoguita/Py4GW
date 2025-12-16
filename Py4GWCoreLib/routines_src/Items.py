import importlib

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()

#region Items
class Items: 
    @staticmethod
    def GetUnidentifiedItems(rarities: list[str], slot_blacklist: list[tuple[int,int]]) -> list[int]:
        from ..Item import Item
        from ..ItemArray import ItemArray
        from ..enums_src.Item_enums import Bags
        unidentified_items = []
        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)

            for item_id in item_array:
                item_instance = Item.item_instance(item_id)
                slot = item_instance.slot
                if (bag_id, slot) in slot_blacklist:
                    continue
                if item_instance.rarity.name not in rarities:
                    continue
                if not item_instance.is_identified:
                    unidentified_items.append(item_id)
        return unidentified_items

    @staticmethod
    def GetSalvageableItems(rarities: list[str], slot_blacklist: list[tuple[int,int]]) -> list[int]:
        from ..Item import Item
        from ..ItemArray import ItemArray
        from ..enums_src.Item_enums import Bags
        salvageable_items = []
        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)

            for item_id in item_array:
                item_instance = Item.item_instance(item_id)
                slot = item_instance.slot
                if (bag_id, slot) in slot_blacklist:
                    continue
                if item_instance.rarity.name not in rarities:
                    continue
                
                if not (item_instance.is_identified or item_instance.rarity.name == "White"):
                    continue
                
                if item_instance.is_salvageable:
                    salvageable_items.append(item_id)
        return salvageable_items
