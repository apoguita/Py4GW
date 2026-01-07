from Py4GWCoreLib import ItemArray, Item
from Py4GWCoreLib.enums import Bags
from Bots.Sasemoi.utils.rune_quality_checker import item_has_valuable_rune

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

            #TODO: There seems to be a bug where this line fails to detect gold offhands, omitting for now
            is_rarity_gold = item_instance.is_rarity_gold # Only interested in gold offhands

            return has_max_stats

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
    Check for "of specific of the profession" mods
    Check for FMN and ANA max inscriptions
    '''

    should_check_ANA = False
    desired_types = [12, 22, 26, 32] # Offhand, Wands, Staves and Daggers
    item_type_int = Item.item_instance(item_id).item_type.ToInt()

    # Sanity check for item type
    if item_type_int not in desired_types:
        return False

    modifiers = Item.Customization.Modifiers.GetModifiers(item_id)

    # Loop over modifiers
    for mod in modifiers:
        identifier = mod.GetIdentifier()
        prof_arg_id = [5, 6, 12, 35, 36] # Mesmer, Necromancer, Elementalist, Assassin, Ritualist, 

        # Early exit condition, ANA detected
        if identifier in [9522, 10248]:
            should_check_ANA = True
            continue

        # Skip uninteresting mods
        if identifier not in [10280, 10408]:
            continue

        # Forget Me Not max value identifier
        if identifier == 10280 and mod.GetArg1() == 20:
            return True
        
        # Of the profession max value identifier
        #TODO: Have to clean this up by making a dict
        if identifier == 10408 and mod.GetArg1() in prof_arg_id and mod.GetArg2() == 5:
            # Daggers can only have Necro and Assassin inscriptions
            if item_type_int == 32 and mod.GetArg1() not in [6, 35]:
                return False

            # Wands cannot have Mesmer, Elementalist or Ritualist inscriptions
            if item_type_int == 22 and mod.GetArg1() in [5, 12, 36]:
                return False
            
            if item_type_int == 26 and mod.GetArg1() == 35:
                return False
            
            return True

    # Exit condition if no extra ANA looping is needed
    if not should_check_ANA:
        return False

    # Loop over modifiers for ANA because it requires a combination of two identifiers
    aptitude_mod_collection = []
    for mod in modifiers:
        identifier = mod.GetIdentifier()
        # ANA inscription identifier
        if identifier == 9522 and mod.GetArg1() == 3 and mod.GetArg2() == 174:
            aptitude_mod_collection.append(mod)

        # ANA max value identifier
        if identifier == 10248 and mod.GetArg1() == 20 and mod.GetArg2() == 0:
            aptitude_mod_collection.append(mod)

    # If combination of both identifiers is found, ANA is present at max value
    return len(aptitude_mod_collection) == 2