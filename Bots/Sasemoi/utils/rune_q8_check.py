from Py4GWCoreLib import Item


valuable_runes = [
                {
                    'name': 'Shamans Insignia',
                    'type': 'insignia',
                    'modifiers': [
                        (9224, 2, 4),
                        (42288, 4, 8),
                        (42744, 5, 0)
                    ]
                },
                {
                    'name': 'Prodigys Insignia',
                    'type': 'insignia',
                    'modifiers': [
                        (9224, 1, 227),
                        (42288, 3, 198),
                        (42792, 5, 0)
                    ]
                },
                {
                    'name': 'Tormentors Insignia',
                    'type': 'insignia',
                    'modifiers': [
                        (9224, 1, 236),
                        (9520, 3, 216),
                        (10344, 2, 8),
                        (42288, 3, 216),
                        (41208, 10, 0)
                    ]
                },
                {
                    'name': 'Sentinels Insignia',
                    'type': 'insignia',
                    'modifiers': [
                        (9224, 1, 251),
                        (32880, 3, 246),
                        (32784, 17, 13),
                        (42288, 3, 246),
                        (41256, 0, 20)
                    ]
                },

                # Minor Runes
                {
                    'name': 'Minor Fast Casting',
                    'type': 'rune',
                    'modifiers': [
                        (9224, 0, 175),
                        (9520, 1, 95),
                        (8680, 0, 1)
                    ]
                },
                {
                    'name': 'Minor Soul Reaping',
                    'type': 'rune',
                    'modifiers': [
                        (9224, 0, 176),
                        (9520, 1, 97),
                        (8680, 6, 1)
                    ]
                },
                {
                    'name': 'Minor Inspiration',
                    'type': 'rune', 
                    'modifiers': [
                        (9224, 0, 175),
                        (9520, 1, 95),
                        (8680, 3, 1)
                    ]
                },
                {
                    'name': 'Minor Spawning',
                    'type': 'rune',
                    'modifiers': [
                        (9224, 1, 62),
                        (9520, 2, 125),
                        (8680, 36, 1)
                    ]
                },

                # Major Rune
                {
                    'name': 'Major Fast Casting',
                    'type': 'rune',
                    'modifiers': [
                        (9224, 0, 181),
                        (9520, 1, 107),
                        (8680, 0, 2),
                        (9520, 1, 107),
                        (8408, 0, 35)
                    ]
                },

                # Superior Runes
                {
                    'name': 'Superior Air',
                    'type': 'rune',
                    'modifiers': [
                        (9224, 0, 189),
                        (9520, 1, 123),
                        (8680, 8, 3),
                        (9520, 1, 123),
                        (8408, 0, 75)
                    ]
                },
                {
                    'name': 'Superior Domination',
                    'type': 'rune',
                    'modifiers': [
                        (9224, 0, 187),
                        (9520, 1, 119),
                        (8680, 2, 3),
                        (9520, 1, 119),
                        (8408, 0, 75)
                    ]
                },
                {
                    'name': 'Superior Vigor Rune',
                    'type': 'rune',
                    'modifiers': [
                        (9224, 1, 1),
                        (9520, 2, 3),
                        (10218, 2, 194)
                    ]
                }
        ]

def item_has_valuable_modifier(item):
    """
    Checks if the item contains valuable modifiers or meets type-specific modifier combinations and rarity criteria.
    Returns True if a valuable modifier or valid combination is found, otherwise False.
    """
    modifiers = Item.Customization.Modifiers.GetModifiers(item)
    
    # Check modifier groups from config
    for valuable_group in valuable_runes:
        all_matched = True
        
        for mod_tuple in valuable_group['modifiers']:
            identifier, arg1, arg2 = mod_tuple
            found = False
            
            for mod in modifiers:
                if mod.GetIdentifier() != identifier:
                    continue
                if mod.GetArg1() != arg1:
                    continue
                if mod.GetArg2() != arg2:
                    continue
                found = True
                break
            
            if not found:
                all_matched = False
                break
        
        if all_matched:
            return True  # Found complete modifier group
    
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
    if Item.Rarity.IsGold(item):
        has_requires = find_mod(10136, arg2=8)
        has_damage = find_mod(42920, arg1=15, arg2=22)
        if has_requires and has_damage:
            return True

    # Check for Shield combination: Requires 8 + Armor 16 + Gold/Purple
    if Item.Rarity.IsGold(item) or Item.Rarity.IsPurple(item):
        has_requires = find_mod(10136, arg2=8)
        has_armor = find_mod(42936, arg1=16)
        if has_requires and has_armor:
            return True

    # Check for Offhand combination: Requires 8 + Energy 12 + Gold
    if Item.Rarity.IsGold(item):
        has_requires = find_mod(10136, arg2=8)
        has_energy = find_mod(26568, arg1=12)
        if has_requires and has_energy:
            return True

    return False   