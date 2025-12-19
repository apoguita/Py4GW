

from Py4GWCoreLib import ItemArray, Item
from Py4GWCoreLib.enums import Bags

def get_unidentified_items(rarities: list[str], slot_blacklist: list[tuple[int,int]]) -> list[int]:
    ''' Returns a list of all unidentified item IDs in the player's inventory '''
    unidentified_items = []

    # Loop over all bags
    for bag_id in range(Bags.Backpack, Bags.Bag2+1):
        bag_to_check = ItemArray.CreateBagList(bag_id)
        item_array = ItemArray.GetItemArray(bag_to_check) # Get all items in the baglist

        # Loop over items
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

def filter_valuable_loot(item_id: int) -> bool:
    desired_types = [12, 24, 27] # Offhand, Shield, Sword
    item_instance = Item.item_instance(item_id)
    item_modifiers = item_instance.modifiers
    item_req = 13 # Default high req to skip uninteresting items

    # Check Q9 max stats
    for mod in item_modifiers:
        # Dont waste time on uninteresting mods
        # [requirement, shield armor, sword damage, offhand energy]
        if mod.GetIdentifier() not in [10136, 42936, 42920, 26568]:
            continue

        # Store item requirement
        if mod.GetIdentifier() == 10136:
            item_req = mod.GetArg2() # Item requirement value

            # Low req found, continue checking other mods
            if item_req <= 9:
                continue
            # High req found, skip entire item
            else:
                return False
        
        
        # Handle Shield
        # 42936 = Shield armor mod identifier
        if item_instance.item_type.ToInt() == 24 and mod.GetIdentifier() == 42936:
            has_ideal_q5_stats = mod.GetArg1() == 12 or mod.GetArg1() == 13 # Ideal shield armor for q5
            has_max_stats = mod.GetArg1() == 16 # Max armor

            # Handle Q5 Shields
            if item_req == 5 and has_ideal_q5_stats:
                return True

            # Handle uninteresting Shields
            if not has_max_stats :
                return False

        # Handle Sword -- Only Q8 and Q9 Swords with max stats are interesting
        # 42920 = Sword damage mod identifier
        if item_instance.item_type.ToInt() == 27 and mod.GetIdentifier() == 42920:
            has_max_stats = mod.GetArg2() == 15 and mod.GetArg1() == 22 # Max damage mod
            return has_max_stats
        

        # Handle Offhand -- Only Q8 and Q9 Offhands with max stats are interesting
        # 26568 = Offhand energy mod identifier
        if item_instance.item_type.ToInt() == 12 and mod.GetIdentifier() == 26568:
            has_max_stats = mod.GetArg1() == 12 # Max Energy mod
            return has_max_stats and item_req <= 9 # Only interested in Q8 or lower
        


    return False