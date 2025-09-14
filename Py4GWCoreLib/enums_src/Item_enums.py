from enum import Enum
from enum import IntEnum


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


# endregion