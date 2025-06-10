import PyInventory
import PyItem
import Py4GW

from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib import Bag
from typing import Dict, List
import time
from enum import Enum


#PyInventory.Bag(bag_enum.value, bag_enum.name)

class Bag_enum(Enum):
    NoBag = 0
    Backpack = 1
    Belt_Pouch = 2
    Bag_1 = 3
    Bag_2 = 4
    Equipment_Pack = 5
    Material_Storage = 6
    Unclaimed_Items = 7
    Storage_1 = 8
    Storage_2 = 9
    Storage_3 = 10
    Storage_4 = 11
    Storage_5 = 12
    Storage_6 = 13
    Storage_7 = 14
    Storage_8 = 15
    Storage_9 = 16
    Storage_10 = 17
    Storage_11 = 18
    Storage_12 = 19
    Storage_13 = 20
    Storage_14 = 21
    Equipped_Items = 22
    Max = 23

class RawItemCache:
    _instance = None

    def __new__(cls, throttle: int = 75):
        if cls._instance is None:
            cls._instance = super(RawItemCache, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, throttle: int = 75):
        if self._initialized:
            self.throttle = throttle
            return
        
        self.throttle = throttle
        self.bags: Dict[int, PyInventory.Bag] = {}
        self.transitory_items: Dict[int, PyItem.PyItem] = {}
        self.update_throttle = ThrottledTimer(throttle)
        self.map_valid = False
        self._initialized = True
        
    def reset(self):
        self.bags.clear()
        self.transitory_items.clear()
        self.update_throttle.Reset()
        self.map_valid = False
        
    def update(self):
        
        if not self.update_throttle.IsExpired():
            return

        self.update_throttle.Reset()
        self.bags.clear()

        for bag in range(Bag_enum.Backpack.value, Bag_enum.Max.value):
            try:
                bag_instance = PyInventory.Bag(bag, str(bag))
                self.bags[bag] = bag_instance
            except Exception:
                continue  # Skip invalid bags
            
        # Clean up transitory items that no longer exist
        to_remove = []
        for item_id, item in self.transitory_items.items():
            this_item = PyItem.PyItem(item_id)
            if not this_item:
                to_remove.append(item_id)
            elif item.agent_id == 0:  # Invalid agent ID
                to_remove.append(item_id)
            elif item.agent_item_id == 0:  # Invalid agent item I
                to_remove.append(item_id)   

        for item_id in to_remove:
            del self.transitory_items[item_id]
            
    def add_transitory_item(self, item_id: int):
        """
        Manually adds an item to the transitory cache if it is not already in any bag.
        """
        if self.get_item_by_id(item_id):
            return  # Already exists in cache

        item = PyItem.PyItem(item_id)
        if item.item_id != 0:
            self.transitory_items[item_id] = item
            
    def get_items(self, bag: int):
        """
        Returns a list of item IDs in the specified bag.
        """
        if bag not in self.bags:
            return []

        bag_instance = self.bags[bag]
        items = bag_instance.GetItems()
        item_ids = [item.item_id for item in items]
        
        return item_ids
                    
    def get_all_items(self):
        """
        Returns a list of all item IDs in all bags.
        """
        all_item_ids = []
        
        for bag in range(Bag_enum.Backpack.value, Bag_enum.Max.value):
            if bag not in self.bags:
                continue
            
            bag_instance = self.bags[bag]
            items = bag_instance.GetItems()
            item_ids = [item.item_id for item in items]
            all_item_ids.extend(item_ids)

        return all_item_ids
    
    def get_bag(self, bag: int):
        """
        Returns a Bag instance for the given bag enum.
        Returns None if the bag is invalid or has no items.
        """
        if bag not in self.bags:
            return None

        bag_instance = self.bags[bag]
        bag_instance.GetContext()
        return bag_instance
    
    def get_bags(self, bag_list: List[int]):
        """
        Returns a list of Bag instances for the given bag enums.
        """
        bags = []
        
        for bag in bag_list:
            if bag not in self.bags:
                continue
            
            bag_instance = self.bags[bag]
            bags.append(bag_instance)
        
        return bags
    
    def get_all_bags(self):
        """
        Returns a list of all Bag instances.
        """
        return list(self.bags.values())
    
    def get_item_by_id(self, item_id: int):
        for bag in self.bags.values():
            item = bag.FindItemById(item_id)
            if item:
                return item
        
        # Check transitory cache
        item = self.transitory_items.get(item_id)
        if item and item.item_id != 0:
            return item

        # Attempt to create and cache it
        item = PyItem.PyItem(item_id)
        if item.item_id != 0:
            self.transitory_items[item_id] = item
            return item
    
        return None  # Item not found
    
class ItemCache:
    def __init__(self, raw_item_array):
        self.raw_item_array:RawItemCache = raw_item_array
        self.name_cache: dict[int, tuple[str, float]] = {}  # agent_id -> (name, timestamp)
        self.name_requested: set[int] = set()
        self.name_timeout_ms = 1_000
        
        self.Rarity = self._Rarity(self)
        self.Properties = self._Properties(self)
        self.Type = self._Type(self)
        self.Usage = self._Usage(self)
        self.Customization = self._Customization(self)
        self.Trade = self._Trade(self)
        
    def _update_cache(self):
        now = time.time() * 1000
        for item_id in list(self.name_requested):
            item = self.raw_item_array.get_item_by_id(item_id)
            if item and item.IsItemNameReady():
                name = item.GetName()
                if name in ("Unknown", "Timeout"):
                    name = ""
                self.name_cache[item_id] = (name, now)
                self.name_requested.discard(item_id)

            
    def _reset_cache(self):
        """Resets the name cache and requested set."""
        self.name_cache.clear()
        self.name_requested.clear()
        
    def GetAgentID(self, item_id: int) -> int:
        item = self.raw_item_array.get_item_by_id(item_id)
        if item is None:
            return 0
        return item.agent_id
    
    def GetAgentItemID(self, item_id: int) -> int:
        item = self.raw_item_array.get_item_by_id(item_id)
        if item is None:
            return 0
        return item.agent_item_id
    
    def GetItemIdFromModelID(self, model_id):
        """Purpose: Retrieve the item ID from the model ID."""
        bags = self.raw_item_array.get_all_bags()

        for bag in bags:
            for item in bag.GetItems():
                # Check if the item's model ID matches the given model ID
                if item.model_id == model_id:
                    return item.item_id  # Return the item ID if a match is found

        return 0  # Return 0 if no matching item is found
    
    def GetItemByAgentID(self, agent_id: int):
        item = self.raw_item_array.get_item_by_id(agent_id)
        return item
    
    def RequestName(self, item_id: int):
        item = self.raw_item_array.get_item_by_id(item_id)
        if item is None:
            return
        item.RequestName()
        
    def IsNameReady(self, item_id: int) -> bool:
        item = self.raw_item_array.get_item_by_id(item_id)
        if item is None:
            return False
        return item.IsItemNameReady()
        
    def GetName(self, item_id: int) -> str:
        now = time.time() * 1000  # current time in ms
        item = self.raw_item_array.get_item_by_id(item_id)
        if item is None:
            return ""

        # Cached and still valid
        if item_id in self.name_cache:
            name, timestamp = self.name_cache[item_id]
            if now - timestamp < self.name_timeout_ms:
                return name
            else:
                # Expired; refresh
                if item_id not in self.name_requested:
                    item.RequestName()
                    self.name_requested.add(item_id)
                return name  # Return old while waiting

        # Not cached yet; request and return empty for now
        item.RequestName()
        self.name_requested.add(item_id)
        return ""  
        
    def GetItemType(self, item_id: int):
        item = self.raw_item_array.get_item_by_id(item_id)
        if item is None:
            return 0, ""
        return item.item_type.ToInt(), item.item_type.GetName()
        
    def GetModelID(self, item_id: int) -> int:
        item = self.raw_item_array.get_item_by_id(item_id)
        if item is None:
            return 0
        return item.model_id
     
    def GetSlot(self, item_id: int) -> int:
        item = self.raw_item_array.get_item_by_id(item_id)
        if item is None:
            return 0
        return item.slot   
    
    def GetDyeColor(self, item_id: int) -> int: 
        item = self.raw_item_array.get_item_by_id(item_id)   
        if item is None:
            return 0    
        mods = item.modifiers
        for mod in mods:
            modColor = mod.GetArg1()
            if modColor != 0:
                return modColor
        return 0
        
    class _Rarity:
        def __init__(self, parent):
            self._parent = parent
        
        def GetRarity(self, item_id: int):
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return 0, ""
            return item.rarity.value, item.rarity.name
        
        def IsWhite(self,item_id):
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            rarity_name  = item.rarity.name
            return rarity_name == "White"
        
        def IsBlue(self,item_id):
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            rarity_name  = item.rarity.name
            return rarity_name == "Blue"

        def IsPurple(self,item_id):
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            rarity_name  = item.rarity.name
            return rarity_name == "Purple"
        
        def IsGold(self,item_id):
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            rarity_name  = item.rarity.name
            return rarity_name == "Gold"
        
        def IsGreen(self,item_id):
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            rarity_name  = item.rarity.name
            return rarity_name == "Green"
        
    class _Properties:
        def __init__(self, parent):
            self._parent = parent
        
        def IsCustomized(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_customized 
        
        def GetValue(self, item_id: int) -> int:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return 0
            return item.value
        
        def GetQuantity(self, item_id: int) -> int:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return 0
            return item.quantity
        
        def IsEquipped(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return False if item.equipped == 0 else True
        
        def GetProfession(self, item_id: int) -> int:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return 0
            return item.profession
        
        def GetInteraction(self, item_id: int) -> int:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return 0
            return item.interaction
        
    class _Type:
        def __init__(self, parent):
            self._parent = parent
        
        def IsWeapon(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_weapon
        
        def IsArmor(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_armor
        
        def IsInventoryItem(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_inventory_item
        
        def IsStorageItem(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_storage_item
        
        def IsMaterial(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_material
        
        def IsRareMaterial(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_rare_material    
        
        def IsZCoin(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_zcoin
        
        def IsTome(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_tome
        
        def IsTrophy(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            _, item_type_name = self._parent.GetItemType(item_id)
            
            if item_type_name == "Trophy":
                return True
            return False
        
    class _Usage:
        def __init__(self, parent):
            self._parent = parent
        
        def IsUsable(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_usable   
        
        def GetUses(self, item_id: int) -> int:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return 0
            return item.uses
        
        def IsSalvageable(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_salvageable
        
        def IsMaterialSalvageable(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return False if item.is_material_salvageable == 0 else True
        
        def IsSalvageKit(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return False if item.is_salvage_kit == 0 else True
        
        def IsLesserKit(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_lesser_kit
        
        def IsExpertSalvageKit(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_expert_salvage_kit
        
        def IsPerfectSalvageKit(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_perfect_salvage_kit
        
        def IsIDKit(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_id_kit
        
        def IsIdentified(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_identified
        
    class _Customization:
        def __init__(self, parent):
            self._parent = parent
            self.Modifiers = self._Modifiers(parent)
        
        def IsInscription(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_inscription   
        
        def IsInscribable(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_inscribable
        
        def IsPrefixUpgradable(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_prefix_upgradable
        
        def IsSuffixUpgradable(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_suffix_upgradable
        
        class _Modifiers:
            def __init__(self, parent):
                self._parent = parent
            
            def GetModifierCount(self, item_id):
                item = self._parent.raw_item_array.get_item_by_id(item_id)
                if item is None:
                    return 0
                return len(item.modifiers)
            
            def GetModifiers(self, item_id):
                item = self._parent.raw_item_array.get_item_by_id(item_id)
                if item is None:
                    return []
                return item.modifiers
        
            def ModifierExists(self, item_id, mod_id):
                item = self._parent.raw_item_array.get_item_by_id(item_id)
                if item is None:
                    return False
                for mod in item.modifiers:
                    if mod.GetIdentifier() == mod_id:
                        return True
                return False

            def GetModifierValues(self, item_id,identifier_lookup):
                item = self._parent.raw_item_array.get_item_by_id(item_id)
                if item is None:
                    return None, None, None
                for modifier in item.modifiers:
                    if modifier.GetIdentifier() == identifier_lookup:
                        arg = modifier.GetArg()
                        arg1 = modifier.GetArg1()
                        arg2 = modifier.GetArg2()

                        return arg, arg1, arg2

                return None, None, None
        
        def GetDyeInfo(self, item_id):
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return PyItem.PyItem(item_id).dye_info
            return item.dye_info
        
        def GetItemFormula(self, item_id):
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return 0
            return item.item_formula
        
        def IsStackable(self, item_id):
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return (item.interaction & 0x80000) != 0
        
        def IsSparkly(self, item_id):
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_sparkly
        
    class _Trade:
        def __init__(self, parent):
            self._parent = parent
        
        def IsOfferedInTrade(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_offered_in_trade
        
        def IsTradable(self, item_id: int) -> bool:
            item = self._parent.raw_item_array.get_item_by_id(item_id)
            if item is None:
                return False
            return item.is_tradable
        
        
class ItemArray:
    _raw_item_cache: RawItemCache = RawItemCache()
    
    def GetItemArray(self, bags_to_check: List[Bag]):
        """
        Given a list of Bag enums, retrieve item IDs from cached bags.
        :param bags_to_check: A list of Bag enum members.
        :return: List of item IDs.
        """
        # Convert Bag enums to int for cache access
        bag_ids = [bag_enum.value for bag_enum in bags_to_check]
        bags = self._raw_item_cache.get_bags(bag_ids)

        all_item_ids = []
        for bag_enum, bag in zip(bags_to_check, bags):
            try:
                items = bag.GetItems()
                all_item_ids.extend([item.item_id for item in items])
            except Exception as e:
                Py4GW.Console.Log("GetItemArray", f"Error retrieving items from {bag_enum.name}: {str(e)}", Py4GW.Console.MessageType.Error)

        return all_item_ids
    
    def GetRawItemArray(self, bag_list: List[int]) -> List[PyItem.PyItem]:
        bags = self._raw_item_cache.get_bags(bag_list)
        items = []
        for bag in bags:
            items.extend(bag.GetItems())
        return items
    
    def GetAllBags(self):
        return self._raw_item_cache.get_all_bags()
    
    def GetBag(self, bag: int):
        return self._raw_item_cache.get_bag(bag)
   
    def CreateBagList(self, *bag_ids) -> List[Bag]:
        """
        Creates a list of Bag enum members based on the provided bag IDs.
        :param bag_ids: A variable number of bag IDs (integers).
        :return: A list of Bag enum members.
        """
        valid_bags = []
        for bag_id in bag_ids:
            try:
                valid_bags.append(Bag(bag_id))
            except ValueError:
                Py4GW.Console.Log("CreateBagList", f"Invalid bag ID: {bag_id}", Py4GW.Console.MessageType.Error)
        return valid_bags
        
        
        
        
        
        
        
        
        