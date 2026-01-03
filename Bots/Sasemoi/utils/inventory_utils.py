from Py4GWCoreLib import ItemArray, Item
from Py4GWCoreLib.enums import Bags
from Bots.Sasemoi.utils.rune_quality_checker import item_has_valuable_rune
# from Py4GWCoreLib import Rarity

def get_unidentified_items(rarities: list[str], slot_blacklist: list[tuple[int,int]]) -> list[int]:
    '''
    Returns a list of all unidentified item IDs in the player's inventory
    '''
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

def filter_valuable_weapon_type(item_id: int) -> bool:
    '''
    Checks for extreme rare stats on shields, swords and offhands

    q5 shields with ideal armor or q8 with max armor

    q8 swords with max damage

    q8 offhands with max energy (gold rarity only)
    '''
    desired_types = [12, 24, 27] # Offhand, Shield, Sword
    item_instance = Item.item_instance(item_id)
    item_modifiers = item_instance.modifiers
    item_req = 13 # Default high req to skip uninteresting items

    if item_instance.item_type.ToInt() not in desired_types:
        return False

    # Check Q9 max stats
    for mod in item_modifiers:
        # Dont waste time on uninteresting mods
        # [requirement, shield armor, sword damage, offhand energy]
        if mod.GetIdentifier() not in [10136, 42936, 42920, 26568]:
            continue

        # Store item requirement
        if mod.GetIdentifier() == 10136:
            item_req = mod.GetArg2() # Item requirement value

            # high req found, break early
            if item_req >= 9:
                break
        
        # Handle Shield
        # 42936 = Shield armor mod identifier
        if item_instance.item_type.ToInt() == 24 and mod.GetIdentifier() == 42936:
            has_ideal_q5_stats = mod.GetArg1() == 12 or mod.GetArg1() == 13 # Ideal shield armor for q5
            has_max_stats = mod.GetArg1() == 16 # Max armor

            return (item_req == 5 and has_ideal_q5_stats) or has_max_stats

        # Handle Sword -- Only Q8 with max stats are interesting
        # 42920 = Sword damage mod identifier
        if item_instance.item_type.ToInt() == 27 and mod.GetIdentifier() == 42920:
            has_max_stats = mod.GetArg2() == 15 and mod.GetArg1() == 22 # Max damage mod
            return has_max_stats
        

        # Handle Offhand -- Only Q8 Offhands with max stats are interesting
        # 26568 = Offhand energy mod identifier
        if item_instance.item_type.ToInt() == 12 and mod.GetIdentifier() == 26568:
            has_max_stats = mod.GetArg1() == 12 # Max Energy mod
            is_rarity_gold = item_instance.is_rarity_gold # Only interested in gold offhands
            return has_max_stats and is_rarity_gold

    return False


def filter_valuable_rune_type(item_id: int) -> bool:
    '''
    Check for valuable runes on salvage type items
    '''

    desired_types = [0] # Salvage Type
    if Item.item_instance(item_id).item_type.ToInt() not in desired_types:
        return False

    return item_has_valuable_rune(item_id)


def filter_valuable_inscription_type(item_id: int) -> bool:
    '''
    Check for FMN and ANA max inscriptions on wands, staves and offhands
    '''

    desired_types = [12, 22, 26] # Offhand, Wands and Staves
    if Item.item_instance(item_id).item_type.ToInt() not in desired_types:
        return False

    # Check for inscriptions
    modifiers = Item.Customization.Modifiers.GetModifiers(item_id)

    # Forget Me Not max value check
    for mod in modifiers:
        # Forget Me Not max value identifier
        if mod.GetIdentifier() == 10280 and mod.GetArg1() == 20:
            return True
        
        # Of the necromancer max value identifier
        elif mod.GetIdentifier() == 10408 and mod.GetArg1() == 6 and mod.GetArg2() == 5:
            return True

        
    
    # ANA max value check
    aptitude_mod_collection = []
    for mod in modifiers:
        # ANA inscription identifier
        if mod.GetIdentifier() == 9522 and mod.GetArg1() == 3 and mod.GetArg2() == 174:
            aptitude_mod_collection.append(mod)

        # ANA max value identifier
        if mod.GetIdentifier() == 10248 and mod.GetArg1() == 20 and mod.GetArg2() == 0:
            aptitude_mod_collection.append(mod)

    # If combination of both identifiers is found, ANA is present at max value
    return len(aptitude_mod_collection) == 2