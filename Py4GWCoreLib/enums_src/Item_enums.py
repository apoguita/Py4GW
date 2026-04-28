from enum import Enum, auto
from enum import IntEnum
from .Model_enums import ModelID

MAX_STACK_SIZE = 250

# region Rarity
class Rarity(IntEnum):
    White = 0
    Blue = 1
    Purple = 2
    Gold = 3
    Green = 4


# SalvageAllType
class SalvageAllType(IntEnum):
    None_ = 0
    White = 1
    BlueAndLower = 2
    PurpleAndLower = 3
    GoldAndLower = 4


# IdentifyAllType
class IdentifyAllType(IntEnum):
    None_ = 0
    All = 1
    Blue = 2
    Purple = 3
    Gold = 4


# endregion
# region bags
class Bags(IntEnum):
    NoBag = 0
    Backpack = 1
    BeltPouch = 2
    Bag1 = 3
    Bag2 = 4
    EquipmentPack = 5
    MaterialStorage = 6
    UnclaimedItems = 7
    Storage1 = 8
    Storage2 = 9
    Storage3 = 10
    Storage4 = 11
    Storage5 = 12
    Storage6 = 13
    Storage7 = 14
    Storage8 = 15
    Storage9 = 16
    Storage10 = 17
    Storage11 = 18
    Storage12 = 19
    Storage13 = 20
    Storage14 = 21
    EquippedItems = 22

INVENTORY_BAGS = [Bags.Backpack, Bags.Bag1, Bags.Bag2, Bags.EquipmentPack]
STORAGE_BAGS = [
    Bags.Storage1, Bags.Storage2, Bags.Storage3, Bags.Storage4, Bags.Storage5, Bags.Storage6,
    Bags.Storage7, Bags.Storage8, Bags.Storage9, Bags.Storage10, Bags.Storage11, Bags.Storage12,
    Bags.Storage13, Bags.Storage14
]
# endregion
# region ItemType
class ItemType(IntEnum):
    Salvage = 0
    Axe = 2
    Bag = 3
    Boots = 4
    Bow = 5
    Bundle = 6
    Chestpiece = 7
    Rune_Mod = 8
    Usable = 9
    Dye = 10
    Materials_Zcoins = 11
    Offhand = 12
    Gloves = 13
    Hammer = 15
    Headpiece = 16
    CC_Shards = 17
    Key = 18
    Leggings = 19
    Gold_Coin = 20
    Quest_Item = 21
    Wand = 22
    Shield = 24
    Staff = 26
    Sword = 27
    Kit = 29
    Trophy = 30
    Scroll = 31
    Daggers = 32
    Present = 33
    Minipet = 34
    Scythe = 35
    Spear = 36
    Weapon = 37
    MartialWeapon = 38
    OffhandOrShield = 39
    EquippableItem = 40
    SpellcastingWeapon = 41
    Storybook = 43
    Costume = 44
    Costume_Headpiece = 45
    Unknown = 255
    
    @property
    def item_types(self) -> list["ItemType"]:
        return ITEM_TYPE_META_TYPES.get(self, [self])
    
    @staticmethod
    def is_matching_item_type(item_type: "ItemType", target: "ItemType") -> bool:
        if item_type == target:
            return True
        return item_type in ITEM_TYPE_META_TYPES.get(target, [])
    
    def matches(self, target: "ItemType") -> bool:
        if self == target:
            return True
        
        return self in ITEM_TYPE_META_TYPES.get(target, [])
    
    def is_weapon_type(self) -> bool:
        return self in WEAPON_TYPES
    
    def is_armor_type(self) -> bool:
        return self in ARMOR_TYPES

WEAPON_TYPES = frozenset(
    {
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
        ItemType.Wand,
    }
)

ARMOR_TYPES = frozenset(
    {
        ItemType.Headpiece,
        ItemType.Chestpiece,
        ItemType.Gloves,
        ItemType.Leggings,
        ItemType.Boots,
        ItemType.Salvage,
    }
)

ITEM_TYPE_META_TYPES: dict[ItemType, list[ItemType]] = {
    ItemType.Weapon: [
        ItemType.Axe,
        ItemType.Bow,
        ItemType.Daggers,
        ItemType.Hammer,
        ItemType.Scythe,
        ItemType.Spear,
        ItemType.Staff,
        ItemType.Sword,
        ItemType.Wand,
    ],
    ItemType.MartialWeapon: [
        ItemType.Axe,
        ItemType.Bow,
        ItemType.Daggers,
        ItemType.Hammer,
        ItemType.Scythe,
        ItemType.Spear,
        ItemType.Sword,
    ],
    ItemType.OffhandOrShield: [
        ItemType.Offhand,
        ItemType.Shield,
    ],
    ItemType.EquippableItem: [
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
        ItemType.Wand,
    ],
    ItemType.SpellcastingWeapon: [
        ItemType.Staff,
        ItemType.Wand,
    ],
}

# endregion

class ItemAction(IntEnum):
    NONE = 0
    
    PickUp = auto() # Pick up the item and put it in the inventory.
    Drop = auto() # Drop the item to the floor the inventory.
    
    Hold = auto() # Hold the item in the inventory, no other actions will be performed on it. This can be useful to exclude certain items from being processed by other rules.
    Stash = auto() # Move the item to the xunlai stash.
    
    # Item processing actions:
    Identify = auto() # Identify the item.
    ExtractUpgrade = auto() # Extract the upgrades of the item.
    Salvage_Rare_Materials = auto() # Salvage the item for rare materials with an (Superior) Expert Salvage Kit.
    Salvage_Common_Materials = auto() # Salvage the item for common materials with a (Basic) Salvage Kit.
    Destroy = auto() # Destroy the item.
    
    # Merchant interactions:
    Sell_To_Merchant = auto() # Sell the item to a merchant.
    
    Sell_To_Trader = auto() # Sell the item to a trader.
    
    Use = auto() # Use the item. 
    
    ## Some stuff we might be able to implement at some point in the future, but not a priority right now:
    TradeToPlayer = auto() # Open the trade window with a specific player and offer the item. The player name should be specified in the rule's parameters.

class SalvageMode(IntEnum):
    NONE = auto()
    LesserCraftingMaterials = auto()
    RareCraftingMaterials = auto()
    Prefix = auto()
    Suffix = auto()
    Inscription = auto()
    
MaterialMap = {
    ModelID.Bolt_Of_Cloth: "Bolt Of Cloth",
    ModelID.Bone: "Bone",
    ModelID.Chitin_Fragment: "Chitin Fragment",
    ModelID.Feather: "Feather",
    ModelID.Granite_Slab: "Granite Slab",
    ModelID.Iron_Ingot: "Iron Ingot",
    ModelID.Pile_Of_Glittering_Dust: "Pile Of Glittering Dust",
    ModelID.Plant_Fiber: "Plant Fiber",
    ModelID.Scale: "Scale",
    ModelID.Tanned_Hide_Square: "Tanned Hide Square",
    ModelID.Wood_Plank: "Wood Plank",
    ModelID.Amber_Chunk: "Amber Chunk",
    ModelID.Bolt_Of_Damask: "Bolt Of Damask",
    ModelID.Bolt_Of_Linen: "Bolt Of Linen",
    ModelID.Bolt_Of_Silk: "Bolt Of Silk",
    ModelID.Deldrimor_Steel_Ingot: "Deldrimor Steel Ingot",
    ModelID.Diamond: "Diamond",
    ModelID.Elonian_Leather_Square: "Elonian Leather Square",
    ModelID.Fur_Square: "Fur Square",
    ModelID.Glob_Of_Ectoplasm: "Glob Of Ectoplasm",
    ModelID.Jadeite_Shard: "Jadeite Shard",
    ModelID.Leather_Square: "Leather Square",
    ModelID.Lump_Of_Charcoal: "Lump Of Charcoal",
    ModelID.Monstrous_Claw: "Monstrous Claw",
    ModelID.Monstrous_Eye: "Monstrous Eye",
    ModelID.Monstrous_Fang: "Monstrous Fang",
    ModelID.Obsidian_Shard: "Obsidian Shard",
    ModelID.Onyx_Gemstone: "Onyx Gemstone",
    ModelID.Roll_Of_Parchment: "Roll Of Parchment",
    ModelID.Roll_Of_Vellum: "Roll Of Vellum",
    ModelID.Ruby: "Ruby",
    ModelID.Sapphire: "Sapphire",
    ModelID.Spiritwood_Plank: "Spiritwood Plank",
    ModelID.Steel_Ingot: "Steel Ingot",
    ModelID.Tempered_Glass_Vial: "Tempered Glass Vial",
    ModelID.Vial_Of_Ink: "Vial Of Ink",
}

DAMAGE_RANGES : dict[ItemType, dict[int, tuple[int, int]]] = {
    ItemType.Axe: {
        0:  (6, 12),
        1:  (6, 12),
        2:  (6, 14),
        3:  (6, 17),
        4:  (6, 19),
        5:  (6, 22),
        6:  (6, 24),
        7:  (6, 25),
        8:  (6, 27),
        9:  (6, 28),
    },
    
    ItemType.Bow: {
        0:  (9, 13),
        1:  (9, 14),
        2:  (10, 16),
        3:  (11, 18),
        4:  (12, 20),
        5:  (13, 22),
        6:  (14, 25),
        7:  (14, 25),
        8:  (14, 27),
        9:  (14, 28),
    },

    ItemType.Daggers: {
        0:  (4, 8),
        1:  (4, 8),
        2:  (5, 9),
        3:  (5, 11),
        4:  (6, 12),
        5:  (6, 13),
        6:  (7, 14),
        7:  (7, 15),
        8:  (7, 16),
        9:  (7, 17),
    },

    ItemType.Offhand: {
        0:  (6, 6),
        1:  (6, 6),
        2:  (7, 7),
        3:  (8, 8),
        4:  (9, 9),
        5:  (10, 10),
        6:  (11, 11),
        7:  (11, 11),
        8:  (12, 12),
        9:  (12, 12),
    },

    ItemType.Hammer: {
        0:  (11, 15),
        1:  (11, 16),
        2:  (12, 19),
        3:  (14, 22),
        4:  (15, 24),
        5:  (16, 28),
        6:  (17, 30),
        7:  (18, 32),
        8:  (18, 34),
        9:  (19, 35),
    },

    ItemType.Scythe: {
        0:  (8, 17),
        1:  (8, 18),
        2:  (9, 21),
        3:  (10, 24),
        4:  (10, 28),
        5:  (10, 32),
        6:  (10, 35),
        7:  (10, 36),
        8:  (9, 40),
        9:  (9, 41),
    },

    ItemType.Shield: {
        0:  (8, 8),
        1:  (9, 9),
        2:  (10, 10),
        3:  (11, 11),
        4:  (12, 12),
        5:  (13, 13),
        6:  (14, 14),
        7:  (15, 15),
        8:  (16, 16),
        9:  (16, 16),
    },

    ItemType.Spear: {
        0:  (8, 12),
        1:  (8, 13),
        2:  (10, 15),
        3:  (11, 17),
        4:  (11, 19),
        5:  (12, 21),
        6:  (13, 23),
        7:  (13, 25),
        8:  (14, 26),
        9:  (14, 27),
    },

    ItemType.Staff: {
        0:  (7, 11),
        1:  (7, 11),
        2:  (8, 13),
        3:  (9, 14),
        4:  (10, 16),
        5:  (10, 18),
        6:  (10, 19),
        7:  (11, 20),
        8:  (11, 21),
        9:  (11, 22),
    },

    ItemType.Sword: {
        0:  (8, 10),
        1:  (8, 11),
        2:  (9, 13),
        3:  (11, 14),
        4:  (12, 16),
        5:  (13, 18),
        6:  (14, 19),
        7:  (14, 20),
        8:  (15, 22),
        9:  (15, 22),
    },

    ItemType.Wand: {
        0:  (7, 11),
        1:  (7, 11),
        2:  (8, 13),
        3:  (9, 14),
        4:  (10, 16),
        5:  (10, 18),
        6:  (11, 19),
        7:  (11, 20),
        8:  (11, 21),
        9:  (11, 22),
    },
}