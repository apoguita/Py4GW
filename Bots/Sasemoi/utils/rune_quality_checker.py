from Py4GWCoreLib import Item
from PyItem import ItemModifier

# Neutral Runes and class + neutral insignias - Defined by modifier 9224
mod_id_9224_runes = [
                #region Insignias
                {
                    'name': 'Blessed Insignia',
                    'type': 'insignia',
                    'modifiers': [
                        (9224, 1, 233),
                    ]
                },

                {
                    'name': 'Survivor Insignia',
                    'type': 'insignia',
                    'modifiers': [
                        (9224, 1, 230),
                    ]
                },

                {
                    'name': 'Rune of Vitae',
                    'type': 'rune',
                    'modifiers': [
                        (9224, 2, 18)
                    ]
                },

                {
                    'name': 'Rune of Clarity',
                    'type': 'rune',
                    'modifiers': [
                        (9224, 2, 21)
                    ]
                },

                {
                    'name': 'Minor Vigor',
                    'type': 'rune',
                    'modifiers': [
                        (9224, 0, 255)
                    ]
                },

                {
                    'name': 'Major Vigor',
                    'type': 'rune',
                    'modifiers': [
                        (9224, 1, 0),
                    ]
                },

                {
                    'name': 'Superior Vigor',
                    'type': 'rune',
                    'modifiers': [
                        (9224, 1, 1),
                    ]
                },

                {
                    'name': 'Tormentors Insignia',
                    'type': 'insignia',
                    'modifiers': [
                        (9224, 1, 236),
                    ]
                },

                {
                    'name': 'Prodigys Insignia',
                    'type': 'insignia',
                    'modifiers': [
                        (9224, 1, 227),
                    ]
                },

                {
                    'name': 'Nightstalker Insignia',
                    'type': 'insignia',
                    'modifiers': [
                        (9224, 1, 225),
                    ]
                },

                {
                    'name': 'Shamans Insignia',
                    'type': 'insignia',
                    'modifiers': [
                        (9224, 2, 4),
                    ]
                },

                {
                    'name': 'Windwalkers Insignia',
                    'type': 'insignia',
                    'modifiers': [
                        (9224, 2, 2),
                    ]
                },
]
                #endregion


# Class Runes -- Defined by modifier 8680
mod_id_8680_runes = [
                #region Minor Runes
                {
                    'name': 'Minor Strength',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 17, 1)
                    ]
                },

                {
                    'name': 'Minor Protection Prayers',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 15, 1)
                    ]
                },
                
                {
                    'name': 'Minor Divine Favor',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 16, 1)
                    ]
                },

                {
                    'name': 'Minor Healing Prayers',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 13, 1)
                    ]
                },

                {
                    'name': 'Minor Fast Casting',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 0, 1)
                    ]
                },

                {
                    'name': 'Minor Inspiration',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 3, 1)
                    ]
                },

                {
                    'name': 'Minor Domination Magic',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 2, 1)
                    ]
                },

                {
                    'name': 'Minor Energy Storage',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 12, 1)
                    ]
                },

                {
                    'name': 'Minor Soul Reaping',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 6, 1)
                    ]
                },

                {
                    'name': 'Minor Spawning',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 36, 1)
                    ]
                },

                {
                    'name': 'Minor Mysticism',
                    'type': 'rune', 
                    'modifiers': [
                        (8680, 44, 1)
                    ]
                },

                {
                    'name': 'Minor Scythe Mastery',
                    'type': 'rune', 
                    'modifiers': [
                        (8680, 41, 1)
                    ]
                },
                #endregion

                #region Major Runes
                {
                    'name': 'Major Fast Casting',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 0, 2),
                    ]
                },

                {
                    'name': 'Major Domination Magic',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 2, 2),
                    ]
                },
                #endregion

                #region Superior Runes
                {
                    'name': 'Superior Domination',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 2, 3),
                    ]
                },

                {
                    'name': 'Superior Communing',
                    'type': 'rune',
                    'modifiers': [
                        (8680, 32, 3),
                    ]
                },
]

def item_has_valuable_rune(item_id: int) -> bool:
    """
    Checks if the item contains valuable modifiers or meets type-specific modifier combinations and rarity criteria.
    Returns True if a valuable modifier or valid combination is found, otherwise False.
    """

    def check_valuable_rune_modifiers(item_mod: ItemModifier, valuables_runes = []) -> bool:    # Check if any valuable rune modifier is present
        result = False
        for rune_identifiers in valuables_runes:
            identifier, arg1, arg2 = rune_identifiers['modifiers'][0]

            if item_mod.GetArg1() == arg1 and item_mod.GetArg2() == arg2:
                result = True
                break

        return result


    modifiers = Item.Customization.Modifiers.GetModifiers(item_id)
    found_8680 = False
    found_9224 = False

    # Loop over modifiers to find runes
    for mod in modifiers:

        # Check for valuable class runes category 8680
        if mod.GetIdentifier() == 8680:
            found_8680 = check_valuable_rune_modifiers(mod, mod_id_8680_runes[:])

        # if not found yet, check for neutral runes and insignias category 9224
        if mod.GetIdentifier() == 9224:
            found_9224 = check_valuable_rune_modifiers(mod, mod_id_9224_runes[:])

    # Even if a valuable class rune is found and neutral rune was not checked
    # I'm not checking further because I will manually salvage them for now
    return found_8680 or found_9224


    
    # Helper function to find specific modifier with arguments
    def find_mod(identifier, **kwargs):
        for mod in modifiers:
            if mod.GetIdentifier() != identifier:
                continue
            match = True
            for key, value in kwargs.items():
                if getattr(mod, f"Get{key.capitalize()}")() != value:
                    match = False
                    break
            if match:
                return mod
        return None

    # Check for Sword combination: Requires 8 + Damage Range 15-22 + Gold
    if Item.Rarity.IsGold(item_id):
        has_requires = find_mod(10136, arg2=8)
        has_damage = find_mod(42920, arg1=15, arg2=22)
        if has_requires and has_damage:
            return True

    # Check for Shield combination: Requires 8 + Armor 16 + Gold/Purple
    if Item.Rarity.IsGold(item_id) or Item.Rarity.IsPurple(item_id):
        has_requires = find_mod(10136, arg2=8)
        has_armor = find_mod(42936, arg1=16)
        if has_requires and has_armor:
            return True

    # Check for Offhand combination: Requires 8 + Energy 12 + Gold
    if Item.Rarity.IsGold(item_id):
        has_requires = find_mod(10136, arg2=8)
        has_energy = find_mod(26568, arg1=12)
        if has_requires and has_energy:
            return True

    return False   