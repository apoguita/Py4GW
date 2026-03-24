
from typing import Optional

import Py4GW
import PyInventory

import Py4GWCoreLib
from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.Item import Bag, Item
from Py4GWCoreLib.enums_src.Item_enums import MAX_STACK_SIZE, ItemType, Rarity
from Sources.frenkeyLib.ItemHandling.Items.ItemCache import ITEM_CACHE
from Sources.frenkeyLib.ItemHandling.Items.item_snapshot import ItemSnapshot
from Sources.frenkeyLib.ItemHandling.Rules.profile import RuleProfile
from Sources.frenkeyLib.ItemHandling.Rules.types import ItemAction

@staticmethod
def GetZeroFilledBags(start_bag: Bag, end_bag: Bag) -> tuple[list[int], dict[Bag, int]]:
    inventory = []
    bag_sizes = {}

    bags = list(range(start_bag.value, end_bag.value + 1))
    for bag_id in bags:
        if bag_id is None:
            continue
        
        bag_enum = Py4GWCoreLib.Bag(bag_id)
        if bag_enum is None:
            continue
        
        bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
        if bag is None:
            continue
        
        bag.GetContext()
        
        bag_sizes[bag_enum] = bag.GetSize() if bag else 0     
        slots = [0] * bag_sizes[bag_enum]
        
        for item in bag.GetItems():
            if 0 <= item.slot < bag_sizes[bag_enum]:
                slots[item.slot] = item.item_id
                
                
        inventory.extend(slots)
    return inventory, bag_sizes

@staticmethod
def HasSpaceForItem(item_id: int, start_bag: Bag, end_bag: Bag, quantity: Optional[int] = None) -> tuple[bool, int]:
    item = ITEM_CACHE.get_item_snapshot(item_id)
    quantity = quantity if quantity is not None else item.quantity if item else 0
    
    if not item or not item.is_valid:
        return False, 0
    
    inventory_snapshot = ITEM_CACHE.get_inventory_snapshot(start_bag, end_bag)
    item_stacks = [i for bag in inventory_snapshot.values() for i in bag.values() if i is not None and 
                   i.is_valid and i.is_stackable and i.model_id == item.model_id and 
                   i.item_type == item.item_type and i.quantity < MAX_STACK_SIZE] if item and item.is_stackable else []
    
    # Check for existing stacks with space for (partial) item.quantity. If we can fit the item into existing stacks, we don't need to check for free slots
    if item_stacks:
        total_available_space = sum(MAX_STACK_SIZE - stack.quantity for stack in item_stacks)
        if total_available_space >= quantity:
            return True, total_available_space
    
    # If the item is not stackable or we don't have enough space in existing stacks, check for free slots
    free_slots = sum((MAX_STACK_SIZE if item.is_stackable else 1) for bag in inventory_snapshot.values() for i in bag.values() if i is None)
    return free_slots > 0, free_slots

@staticmethod
def GetDestinationSlots(item_id: int, start_bag: Bag, end_bag: Bag) -> list[tuple[Bag, int, Optional[ItemSnapshot]]]:
    item = ITEM_CACHE.get_item_snapshot(item_id)
    
    if not item or not item.is_valid:
        return []
    
    inventory_snapshot = ITEM_CACHE.get_inventory_snapshot(start_bag, end_bag)
    destination_slots : list[tuple[Bag, int, Optional[ItemSnapshot]]] = []
    
    if item.is_stackable:
        for bag_enum, bag in inventory_snapshot.items():
            for slot, stack_item in bag.items():
                if stack_item and stack_item.is_valid and stack_item.is_stackable and stack_item.model_id == item.model_id and stack_item.item_type == item.item_type and stack_item.quantity < MAX_STACK_SIZE:
                    destination_slots.append((bag_enum, slot, stack_item))
                    
                    if sum(MAX_STACK_SIZE - s.quantity for _, _, s in destination_slots if s is not None) >= item.quantity:
                        return destination_slots
    
    # If the item is not stackable or we don't have enough space in existing stacks, find free slots
    for bag_enum, bag in inventory_snapshot.items():
        for slot, stack_item in bag.items():
            if stack_item is None:
                return [(bag_enum, slot, None)]
    
    return destination_slots

@staticmethod
def GetItemLocation(item_id: int) -> Optional[tuple[Bag, int]]:
    inventory_snapshot = ITEM_CACHE.get_inventory_snapshot(Bag.Backpack, Bag.Max)
    
    for bag_enum, bag in inventory_snapshot.items():
        for slot, item in bag.items():
            if item and item.is_valid and item.id == item_id:
                return (bag_enum, slot)
    
    return None

@staticmethod
def GetItemsLocations(item_ids: list[int]) -> list[tuple[Bag, int]]:
    inventory_snapshot = ITEM_CACHE.get_inventory_snapshot(Bag.Backpack, Bag.Max)
    locations = []
    
    for bag_enum, bag in inventory_snapshot.items():
        for slot, item in bag.items():
            if item and item.is_valid and item.id in item_ids:
                locations.append((bag_enum, slot))
    
    return locations

@staticmethod
def IsWeaponType(item_type : ItemType) -> bool:
    return item_type in (
            ItemType.Axe,
            ItemType.Bow,
            ItemType.Daggers,
            ItemType.Hammer,
            ItemType.Offhand,
            ItemType.Scythe,
            ItemType.Shield,
            ItemType.Spear,
            ItemType.Staff,
            ItemType.Sword,
            ItemType.Wand
        )