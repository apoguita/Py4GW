# PyItem.pyi - Auto-generated .pyi file for PyItem module

from typing import Any, List, overload
from enum import Enum, IntEnum

# Enum DyeColor (SafeDyeColor)
class DyeColor:
    NoColor: int
    Blue: int
    Green: int
    Purple: int
    Red: int
    Yellow: int
    Brown: int
    Orange: int
    Silver: int
    Black: int
    Gray: int
    White: int
    Pink: int

# Enum ItemType (SafeItemType)
class ItemType:
    Salvage: int
    Axe: int
    Bag: int
    Boots: int
    Bow: int
    Bundle: int
    Chestpiece: int
    Rune_Mod: int
    Usable: int
    Dye: int
    Materials_or_Zcoins: int
    Offhand: int
    Gloves: int
    Hammer: int
    Headpiece: int
    CC_Shards: int
    Key: int
    Leggings: int
    Gold_Coin: int
    Quest_Item: int
    Wand: int
    Shield: int
    Staff: int
    Sword: int
    Kit: int
    Trophy: int
    Scroll: int
    Daggers: int
    Present: int
    Minipet: int
    Scythe: int
    Spear: int
    Storybook: int
    Costume: int
    Costume_Headpiece: int
    Unknown: int

# Enum SalvageAllType
class SalvageAllType:
    Nothing: int
    White: int
    BlueAndLower: int
    PurpleAndLower: int
    GoldAndLower: int

# Enum IdentifyAllType
class IdentifyAllType:
    Nothing: int
    All: int
    Blue: int
    Purple: int
    Gold: int

# Enum Rarity
class Rarity(IntEnum):
    White = 0
    Blue = 1
    Purple = 2
    Gold = 3
    Green = 4

# Class ItemModifier (SafeItemModifier)
class ItemModifier:
    def __init__(self, identifier: int) -> None: ...
    
    def GetIdentifier(self) -> int: ...
    def GetArg1(self) -> int: ...
    def GetArg2(self) -> int: ...
    def GetArg(self) -> int: ...
    def IsValid(self) -> bool: ...
    def GetModBits(self) -> int: ...
    def ToString(self) -> str: ...

# Class ItemTypeClass (SafeItemTypeClass)
class ItemTypeClass:
    def __init__(self, item_type: int) -> None: ...
    
    def ToInt(self) -> int: ...
    def GetName(self) -> str: ...
    
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...

# Class DyeColorClass (SafeDyeColorClass)
class DyeColorClass:
    def __init__(self, dye_color: int) -> None: ...
    def ToInt(self) -> int: ...
    def ToString(self) -> str: ...

# Class DyeInfo (SafeDyeInfoClass)
class DyeInfo:
    dye_tint: int
    dye1: DyeColorClass
    dye2: DyeColorClass
    dye3: DyeColorClass
    dye4: DyeColorClass

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, dye_info: Any) -> None: ...
    def ToString(self) -> str: ...


# Class Item (SafeItem)
class PyItem:
    item_id: int
    agent_id: int
    agent_item_id: int
    name: str
    modifiers: List[ItemModifier]
    is_customized: bool
    item_type: ItemTypeClass
    dye_info: DyeInfo
    value: int
    interaction: int
    model_id: int
    model_file_id: int
    item_formula: int
    is_material_salvageable: int
    quantity: int
    equipped: int
    profession: int
    slot: int
    is_stackable: bool
    is_inscribable: bool
    is_material: bool
    is_zcoin: bool
    rarity: Rarity
    uses: int
    is_id_kit: bool
    is_salvage_kit: bool
    is_tome: bool
    is_lesser_kit: bool
    is_expert_salvage_kit: bool
    is_perfect_salvage_kit: bool
    is_weapon: bool
    is_armor: bool
    is_salvageable: bool
    is_inventory_item: bool
    is_storage_item: bool
    is_rare_material: bool
    is_offered_in_trade: bool
    is_sparkly: bool
    is_identified: bool
    is_prefix_upgradable: bool
    is_suffix_upgradable: bool
    is_stackable: bool
    is_usable: bool
    is_tradable: bool
    is_inscription: bool
    is_rarity_blue: bool
    is_rarity_purple: bool
    is_rarity_green: bool
    is_rarity_gold: bool

    def __init__(self, item_id: int) -> None: ...
    def GetContext(self) -> None: ...
    def RequestName(self) -> None: ...
    def IsItemNameReady(self) -> bool: ...
    def GetName(self) -> str: ...
    def IsItemValid(self, item_id: int) -> bool: ...
