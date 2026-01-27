import PyItem
import PyInventory

from enum import Enum
from .enums_src.GameData_enums import Weapon as WeaponType, Weapon_Names

class Bag(Enum):
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

class Item:
        @staticmethod
        def item_instance(item_id):
            """
            Purpose: Create an instance of an item.
            Args:
                item_id (int): The ID of the item to create an instance of.
            Returns: PyItem.Item: The item instance.
            """
            return PyItem.PyItem(item_id)

        @staticmethod
        def GetAgentID(item_id):
            """Purpose: Retrieve the agent ID of an item by its ID."""
            return Item.item_instance(item_id).agent_id

        @staticmethod
        def GetAgentItemID(item_id):
            """Purpose: Retrieve the agent item ID of an item by its ID."""
            return Item.item_instance(item_id).agent_item_id

        @staticmethod
        def GetItemIdFromModelID(model_id):
            """Purpose: Retrieve the item ID from the model ID."""
            bags_to_check = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]

            for bag_enum in bags_to_check:
                bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
                for item in bag_instance.GetItems():
                    pyitem_instance = PyItem.PyItem(item.item_id)
            
                    # Check if the item's model ID matches the given model ID
                    if pyitem_instance.model_id == model_id:
                        return pyitem_instance.item_id  # Return the item ID if a match is found

            return 0  # Return 0 if no matching item is found

        @staticmethod
        def GetItemByAgentID(agent_id):
            """Purpose: Retrieve the item associated with a given agent ID."""
            # Bags to check (Backpack, Belt Pouch, Bag 1, Bag 2, etc.)
            bags_to_check = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]

            # Iterate over the bags
            for bag_enum in bags_to_check:
                bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)

                # Iterate over the items in the bag
                for item in bag_instance.GetItems():
                    pyitem_instance = PyItem.PyItem(item.item_id)

                    # Check if the item's agent ID matches the given agent ID
                    if pyitem_instance.agent_id == agent_id:
                        return pyitem_instance  # Return the item if a match is found

            return None  # Return None if no matching item is found

        @staticmethod
        def RequestName(item_id):
            """Purpose: Request the name of an item by its ID."""
            return Item.item_instance(item_id).RequestName()
        
        @staticmethod
        def IsNameReady(item_id):
            """Purpose: Check if the name of an item is ready by its ID."""
            return Item.item_instance(item_id).IsItemNameReady()
        
        @staticmethod
        def GetName(item_id):
            """Purpose: Retrieve the name of an item by its ID."""
            return Item.item_instance(item_id).GetName()
        
        @staticmethod
        def GetItemType(item_id):
            """Purpose: Retrieve the item type of an item by its ID."""
            return Item.item_instance(item_id).item_type.ToInt(), Item.item_instance(item_id).item_type.GetName()

        @staticmethod
        def GetModelID(item_id):
            """Purpose: Retrieve the model ID of an item by its ID."""
            return Item.item_instance(item_id).model_id
        
        @staticmethod
        def GetModelFileID(item_id):
            """Purpose: Retrieve the model file ID of an item by its ID."""
            return Item.item_instance(item_id).model_file_id

        @staticmethod
        def GetSlot(item_id):
            """Purpose: Retrieve the slot of an item is in a bag by its ID."""
            return Item.item_instance(item_id).slot

        @staticmethod
        def GetDyeColor(item_id: int) -> int:
            """
            Purpose: Retrieve the Vial of Dye color by its ID.
            Args:
                item_id (int): The vial of dye item id.
            Returns: int: The Py4GWCoreLib.DyeColor equivalent value or zero (None).
            """            
            mods = Item.item_instance(item_id).modifiers

            # Check if the item has any modifiers
            for mod in mods:
                modColor = mod.GetArg1()
                
                if modColor != 0:
                    return modColor
                
            # Zero is default dye color, i.e. no dye applied
            return 0
        
        class Rarity:
            @staticmethod
            def GetRarity(item_id) -> tuple[int, str]:
                """Purpose: Retrieve the rarity of an item by its ID."""
                return Item.item_instance(item_id).rarity.value, Item.item_instance(item_id).rarity.name

            @staticmethod
            def IsWhite(item_id):
                """Purpose: Check if an item is white rarity by its ID."""
                rarity_value, rarity_name  = Item.Rarity.GetRarity(item_id)
                return rarity_name == "White"

            @staticmethod
            def IsBlue(item_id):
                """Purpose: Check if an item is blue rarity by its ID."""
                rarity_value, rarity_name  = Item.Rarity.GetRarity(item_id)
                return rarity_name == "Blue"

            @staticmethod
            def IsPurple(item_id):
                """Purpose: Check if an item is purple rarity by its ID."""
                rarity_value, rarity_name  = Item.Rarity.GetRarity(item_id)
                return rarity_name == "Purple"

            @staticmethod
            def IsGold(item_id):
                """Purpose: Check if an item is gold rarity by its ID."""
                rarity_value, rarity_name  = Item.Rarity.GetRarity(item_id)
                return rarity_name == "Gold"

            @staticmethod
            def IsGreen(item_id):
                """Purpose: Check if an item is green rarity by its ID."""
                rarity_value, rarity_name  = Item.Rarity.GetRarity(item_id)
                return rarity_name == "Green"

        class Properties:
            @staticmethod
            def IsCustomized(item_id):
                """Purpose: Check if an item is customized by its ID."""
                return Item.item_instance(item_id).is_customized

            @staticmethod
            def GetValue(item_id):
                """Purpose: Retrieve the value of an item by its ID."""
                return Item.item_instance(item_id).value

            @staticmethod
            def GetQuantity(item_id):
                """Purpose: Retrieve the quantity of an item by its ID."""
                return Item.item_instance(item_id).quantity

            @staticmethod
            def IsEquipped(item_id):
                """Purpose: Check if an item is equipped by its ID."""
                return Item.item_instance(item_id).equipped

            @staticmethod
            def GetProfession(item_id):
                """
                Purpose: Retrieve the profession of an item by its ID.
                Args:
                    item_id (int): The ID of the item to retrieve.
                Returns: int: The profession of the item.
                """
                return Item.item_instance(item_id).profession

            @staticmethod
            def GetInteraction(item_id):
                """Purpose: Retrieve the interaction of an item by its ID."""
                return Item.item_instance(item_id).interaction

        class Type:
            @staticmethod
            def IsWeapon(item_id):
                """Purpose: Check if an item is a weapon by its ID."""
                return Item.item_instance(item_id).is_weapon

            @staticmethod
            def IsArmor(item_id):
                """Purpose: Check if an item is armor by its ID."""
                return Item.item_instance(item_id).is_armor

            @staticmethod
            def IsInventoryItem(item_id):
                """Purpose: Check if an item is an inventory item by its ID."""
                return Item.item_instance(item_id).is_inventory_item

            @staticmethod
            def IsStorageItem(item_id):
                """Purpose: Check if an item is a storage item by its ID."""
                return Item.item_instance(item_id).is_storage_item

            @staticmethod
            def IsMaterial(item_id):
                """Purpose: Check if an item is a material by its ID."""
                return Item.item_instance(item_id).is_material

            @staticmethod
            def IsRareMaterial(item_id):
                """Purpose: Check if an item is a rare material by its ID."""
                return Item.item_instance(item_id).is_rare_material

            @staticmethod
            def IsZCoin(item_id):
                """Purpose: Check if an item is a ZCoin by its ID."""
                return Item.item_instance(item_id).is_zcoin

            @staticmethod
            def IsTome(item_id):
                """Purpose: Check if an item is a tome by its ID."""
                return Item.item_instance(item_id).is_tome

        class Usage:
            @staticmethod
            def IsUsable(item_id):
                """Purpose: Check if an item is usable by its ID."""
                return Item.item_instance(item_id).is_usable

            @staticmethod
            def GetUses(item_id):
                """Purpose: Retrieve the uses of an item by its ID."""
                return Item.item_instance(item_id).uses

            @staticmethod
            def IsSalvageable(item_id):
                """Purpose: Check if an item is salvageable by its ID."""
                return Item.item_instance(item_id).is_salvageable

            @staticmethod
            def IsMaterialSalvageable(item_id):
                """Purpose: Check if an item is material salvageable by its ID."""
                return Item.item_instance(item_id).is_material_salvageable

            @staticmethod
            def IsSalvageKit(item_id):
                """Purpose: Check if an item is a salvage kit by its ID."""
                return Item.item_instance(item_id).is_salvage_kit

            @staticmethod
            def IsLesserKit(item_id):
                """Purpose: Check if an item is a lesser kit by its ID."""
                return Item.item_instance(item_id).is_lesser_kit

            @staticmethod
            def IsExpertSalvageKit(item_id):
                """Purpose: Check if an item is an expert salvage kit by its ID."""
                return Item.item_instance(item_id).is_expert_salvage_kit

            @staticmethod
            def IsPerfectSalvageKit(item_id):
                """Purpose: Check if an item is a perfect salvage kit by its ID."""
                return Item.item_instance(item_id).is_perfect_salvage_kit

            @staticmethod
            def IsIDKit(item_id):
                """Purpose: Check if an item is an ID Kit by its ID."""
                return Item.item_instance(item_id).is_id_kit

            @staticmethod
            def IsIdentified(item_id):
                """Purpose: Check if an item is identified by its ID."""
                return Item.item_instance(item_id).is_identified

        class Customization:
            @staticmethod
            def IsInscription(item_id):
                """Purpose: Check if an item is an inscription by its ID."""
                return Item.item_instance(item_id).is_inscription
            @staticmethod
            def IsInscribable(item_id):
                """Purpose: Check if an item is inscribable by its ID."""
                return Item.item_instance(item_id).is_inscribable

            @staticmethod
            def IsPrefixUpgradable(item_id):
                """Purpose: Check if an item is prefix upgradable by its ID."""
                return Item.item_instance(item_id).is_prefix_upgradable

            @staticmethod
            def IsSuffixUpgradable(item_id):
                """Purpose: Check if an item is suffix upgradable by its ID."""
                return Item.item_instance(item_id).is_suffix_upgradable

            class Modifiers:
                @staticmethod
                def GetModifierCount(item_id):
                    """Purpose: Retrieve the number of modifiers of an item by its ID."""
                    return len(Item.item_instance(item_id).modifiers)

                @staticmethod
                def GetModifiers(item_id):
                    """Purpose: Retrieve the modifiers of an item by its ID."""
                    return Item.item_instance(item_id).modifiers

                @staticmethod
                def ModifierExists(item_id, identifier_lookup):
                    """Purpose: Check if a modifier exists in an item by its ID and identifier."""
                    for modifier in Item.Customization.Modifiers.GetModifiers(item_id):
                        if modifier.GetIdentifier() == identifier_lookup:
                            return True
                    return False

                @staticmethod
                def GetModifierValues(item_id, identifier_lookup):
                    """Purpose: Retrieve a modifier of an item by its ID and identifier."""
                    for modifier in Item.Customization.Modifiers.GetModifiers(item_id):
                        if modifier.GetIdentifier() == identifier_lookup:
                            arg = modifier.GetArg()
                            arg1 = modifier.GetArg1()
                            arg2 = modifier.GetArg2()

                            return arg, arg1, arg2

                    return None, None, None

            @staticmethod
            def GetDyeInfo(item_id):
                """Purpose: Retrieve the dye information of an item by its ID."""
                return Item.item_instance(item_id).dye_info

            @staticmethod
            def GetItemFormula(item_id):
                """Purpose: Retrieve the item formula of an item by its ID."""
                return Item.item_instance(item_id).item_formula

            @staticmethod
            def IsStackable(item_id):
                """Purpose: Check if an item is stackable by its ID."""
                #return Item.item_instance(item_id).is_stackable
                interaction = Item.Properties.GetInteraction(item_id)
                return (interaction & 0x80000) != 0

            @staticmethod
            def IsSparkly(item_id):
                """Purpose: Check if an item is sparkly by its ID."""
                return Item.item_instance(item_id).is_sparkly

        class Trade:
            @staticmethod
            def IsOfferedInTrade(item_id):
                """Purpose: Check if an item is offered in trade by its ID."""
                return Item.item_instance(item_id).is_offered_in_trade

            @staticmethod
            def IsTradable(item_id):
                """Purpose: Check if an item is tradable by its ID."""
                return Item.item_instance(item_id).is_tradable

        class Weapon:
            """Weapon-specific data including base damage ranges.

            All lookups accept either a WeaponType enum value (from GameData_enums.Weapon)
            or a string name (e.g. "Sword"). Using the enum is preferred.
            """

            # Base damage ranges at max requirement
            # Format: WeaponType enum -> (min_damage, max_damage)
            BASE_DAMAGE = {
                WeaponType.Sword:    (15, 22),
                WeaponType.Axe:      (6, 28),
                WeaponType.Hammer:   (19, 35),
                WeaponType.Scythe:   (9, 41),
                WeaponType.Daggers:  (7, 17),   # Per hit, strikes twice
                WeaponType.Spear:    (14, 27),
                WeaponType.Bow:      (15, 28),
                WeaponType.Wand:     (11, 22),
                WeaponType.Staff:    (11, 22),
                WeaponType.Scepter:  (11, 22),
            }

            # Attack speed (seconds per attack) at base speed (no IAS)
            ATTACK_SPEED = {
                WeaponType.Sword:    1.33,
                WeaponType.Axe:      1.33,
                WeaponType.Hammer:   1.75,
                WeaponType.Scythe:   1.50,
                WeaponType.Daggers:  1.33,  # Per strike, but double-strike
                WeaponType.Spear:    1.50,
                WeaponType.Bow:      2.00,
                WeaponType.Wand:     1.75,
                WeaponType.Staff:    1.75,
                WeaponType.Scepter:  1.75,
            }

            # Weapon range in game units (aggro bubble is ~1010)
            WEAPON_RANGE = {
                WeaponType.Sword:    144,     # Melee
                WeaponType.Axe:      144,
                WeaponType.Hammer:   144,
                WeaponType.Scythe:   144,     # Hits multiple adjacent foes
                WeaponType.Daggers:  144,
                WeaponType.Spear:    1200,    # Ranged
                WeaponType.Bow:      1200,    # Varies by bow type in practice
                WeaponType.Wand:     1200,    # Spellcasting range
                WeaponType.Staff:    1200,
                WeaponType.Scepter:  1200,
            }

            @staticmethod
            def _resolve_key(weapon_type) -> WeaponType:
                """Resolve a string or enum to a WeaponType enum value."""
                if isinstance(weapon_type, WeaponType):
                    return weapon_type
                if isinstance(weapon_type, int):
                    return WeaponType(weapon_type)
                if isinstance(weapon_type, str):
                    # Look up by name from Weapon_Names (reverse lookup)
                    for enum_val, name in Weapon_Names.items():
                        if name == weapon_type:
                            return enum_val
                return WeaponType.Unknown

            @staticmethod
            def GetBaseDamageRange(weapon_type) -> tuple:
                """
                Get the base min/max damage for a weapon type.

                Args:
                    weapon_type: WeaponType enum, int, or string name

                Returns:
                    tuple: (min_damage, max_damage) or (0, 0) if unknown
                """
                key = Item.Weapon._resolve_key(weapon_type)
                return Item.Weapon.BASE_DAMAGE.get(key, (0, 0))

            @staticmethod
            def GetAttackSpeed(weapon_type) -> float:
                """
                Get the base attack speed for a weapon type (seconds per attack).

                Args:
                    weapon_type: WeaponType enum, int, or string name

                Returns:
                    float: Seconds per attack, or 1.5 if unknown
                """
                key = Item.Weapon._resolve_key(weapon_type)
                return Item.Weapon.ATTACK_SPEED.get(key, 1.5)

            @staticmethod
            def GetWeaponRange(weapon_type) -> int:
                """
                Get the attack range for a weapon type in game units.

                Args:
                    weapon_type: WeaponType enum, int, or string name

                Returns:
                    int: Range in game units (144 = melee/adjacent)
                """
                key = Item.Weapon._resolve_key(weapon_type)
                return Item.Weapon.WEAPON_RANGE.get(key, 144)

            @staticmethod
            def GetAverageDamage(weapon_type) -> float:
                """Get the average base damage for a weapon type."""
                min_dmg, max_dmg = Item.Weapon.GetBaseDamageRange(weapon_type)
                return (min_dmg + max_dmg) / 2.0

            @staticmethod
            def GetDPS(weapon_type) -> float:
                """
                Get the theoretical base DPS for a weapon type (no skills, no IAS).
                Daggers strike twice per attack cycle, so their DPS is doubled.
                """
                avg_damage = Item.Weapon.GetAverageDamage(weapon_type)
                attack_speed = Item.Weapon.GetAttackSpeed(weapon_type)

                if attack_speed <= 0:
                    return 0.0

                dps = avg_damage / attack_speed

                key = Item.Weapon._resolve_key(weapon_type)
                if key == WeaponType.Daggers:
                    dps *= 2

                return round(dps, 1)

            @staticmethod
            def IsMelee(weapon_type) -> bool:
                """Check if a weapon type is melee range."""
                return Item.Weapon.GetWeaponRange(weapon_type) <= 144

            @staticmethod
            def IsRanged(weapon_type) -> bool:
                """Check if a weapon type is ranged."""
                return Item.Weapon.GetWeaponRange(weapon_type) > 144

            @staticmethod
            def GetAllWeaponTypes() -> list:
                """Get a list of all known weapon types as WeaponType enums."""
                return list(Item.Weapon.BASE_DAMAGE.keys())

        
