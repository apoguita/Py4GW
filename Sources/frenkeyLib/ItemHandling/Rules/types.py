
from enum import IntEnum, auto

from Py4GWCoreLib.enums_src.Model_enums import ModelID


class ItemAction(IntEnum):
    NONE = 0
    
    Collect_Data = auto() # Basically do nothing but collect data about the item for our item database. This is for items we don't want to interact with yet but want to have data about for future rules.
    PickUp = auto() # Pick up the item and put it in the inventory.
    Drop = auto() # Drop the item to the floor the inventory.
    
    Hold = auto()
    Stash = auto()
    
    # Item processing actions:
    Identify = auto()
    Salvage_Mods = auto()
    Salvage_Rare_Materials = auto()
    Salvage_Common_Materials = auto()
    Destroy = auto()
    Deposit_Material = auto()
    
    # Merchant interactions:
    Sell_To_Merchant = auto()
    Buy_From_Merchant = auto()
    
    Sell_To_Trader = auto()
    Buy_From_Trader = auto() 
    
    Use = auto() # Use the item. The target or context should be specified in the rule's parameters.
    
    ## Some stuff we might be able to implement at some point in the future, but not a priority right now:
    TradeToPlayer = auto() # Open the trade window with a specific player and offer the item. The player name should be specified in the rule's parameters.


ACTION_LIMITS_PER_FRAME = [
    # These are actions which we have to handle yield based, 
    # we would also want to always continue with the previous item if its not finished processing
    ItemAction.Salvage_Common_Materials,
    ItemAction.Salvage_Rare_Materials,
    ItemAction.Salvage_Mods,
    ItemAction.Sell_To_Trader,
    ItemAction.Buy_From_Trader,
]

class SalvageMode(IntEnum):
    NONE = auto()
    LesserCraftingMaterials = auto()
    RareCraftingMaterials = auto()
    Prefix = auto()
    Suffix = auto()
    Inscription = auto()

MATERIAL_SLOTS : dict[int, int] = {
    ModelID.Amber_Chunk : 36,
    ModelID.Bolt_Of_Cloth : 5,
    ModelID.Bolt_Of_Damask : 14,
    ModelID.Bolt_Of_Linen : 13,
    ModelID.Bolt_Of_Silk : 15,
    ModelID.Bone : 0,
    ModelID.Chitin_Fragment : 4,
    ModelID.Deldrimor_Steel_Ingot : 18,
    ModelID.Diamond : 24,
    ModelID.Elonian_Leather_Square : 31,
    ModelID.Feather : 11,
    ModelID.Fur_Square : 12,
    ModelID.Glob_Of_Ectoplasm : 16,
    ModelID.Granite_Slab : 8,
    ModelID.Iron_Ingot : 1,
    ModelID.Jadeite_Shard : 37,
    ModelID.Leather_Square : 30,
    ModelID.Lump_Of_Charcoal : 26,
    ModelID.Monstrous_Claw : 19,
    ModelID.Monstrous_Eye : 20,
    ModelID.Monstrous_Fang : 21,
    ModelID.Obsidian_Shard : 27,
    ModelID.Onyx_Gemstone : 25,
    ModelID.Pile_Of_Glittering_Dust : 9,
    ModelID.Plant_Fiber : 10,
    ModelID.Roll_Of_Parchment : 33,
    ModelID.Roll_Of_Vellum : 34,
    ModelID.Ruby : 22,
    ModelID.Sapphire : 23,
    ModelID.Scale : 3,
    ModelID.Spiritwood_Plank : 35,
    ModelID.Steel_Ingot : 17,
    ModelID.Tanned_Hide_Square : 2,
    ModelID.Tempered_Glass_Vial : 29,
    ModelID.Vial_Of_Ink : 32,
    ModelID.Wood_Plank : 6,
}