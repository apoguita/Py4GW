from enum import Enum, IntEnum
import os

from Py4GW import Console
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.ItemCache import Bag_enum
from Py4GWCoreLib.enums import ModelID
from Py4GWCoreLib.enums_src.Item_enums import ItemType

ALL_BAGS = GLOBAL_CACHE.ItemArray.CreateBagList(*range(Bag_enum.Backpack.value, Bag_enum.Max.value))
XUNLAI_STORAGE = GLOBAL_CACHE.ItemArray.CreateBagList(*range(Bag_enum.Storage_1.value, Bag_enum.Storage_14.value + 1))
CHARACTER_INVENTORY = GLOBAL_CACHE.ItemArray.CreateBagList(*range(Bag_enum.Backpack.value, Bag_enum.Equipment_Pack.value + 1), Bag_enum.Equipped_Items.value)
ITEM_TEXTURE_FOLDER = os.path.join(Console.get_projects_path(), "Textures", "Items")

MAX_CHARACTER_GOLD = 100000
MAX_VAULT_GOLD = 1000000
MAX_STACK_SIZE = 250

INVALID_NAMES = ["", "Unknown", "No Item"]
ITEM_CONVERSIONS : dict[tuple[ModelID, ItemType], tuple[ModelID, ItemType, int, int]] = {
    (ModelID.Silver_Zaishen_Coin, ItemType.Materials_Zcoins): (ModelID.Copper_Zaishen_Coin, ItemType.Materials_Zcoins, 50, 10),
    (ModelID.Gold_Zaishen_Coin, ItemType.Materials_Zcoins): (ModelID.Silver_Zaishen_Coin, ItemType.Materials_Zcoins, 10, 50),            
}

COMMON_MATERIALS: list[int] = [
    ModelID.Bone,
    ModelID.Iron_Ingot,
    ModelID.Tanned_Hide_Square,
    ModelID.Scale,
    ModelID.Chitin_Fragment,
    ModelID.Bolt_Of_Cloth,
    ModelID.Wood_Plank,
    ModelID.Granite_Slab,
    ModelID.Pile_Of_Glittering_Dust,
    ModelID.Plant_Fiber,
    ModelID.Feather,    
]

RARE_MATERIALS: list[int] = [
    ModelID.Fur_Square,
    ModelID.Bolt_Of_Linen,
    ModelID.Bolt_Of_Damask,
    ModelID.Bolt_Of_Silk,
    ModelID.Glob_Of_Ectoplasm,
    ModelID.Steel_Ingot,
    ModelID.Deldrimor_Steel_Ingot,
    ModelID.Monstrous_Claw,
    ModelID.Monstrous_Eye,
    ModelID.Monstrous_Fang,
    ModelID.Ruby,
    ModelID.Sapphire,
    ModelID.Diamond,
    ModelID.Onyx_Gemstone,
    ModelID.Lump_Of_Charcoal,
    ModelID.Obsidian_Shard,
    ModelID.Tempered_Glass_Vial,
    ModelID.Leather_Square,
    ModelID.Elonian_Leather_Square,
    ModelID.Vial_Of_Ink,
    ModelID.Roll_Of_Parchment,
    ModelID.Roll_Of_Vellum,
    ModelID.Spiritwood_Plank,
    ModelID.Amber_Chunk,
    ModelID.Jadeite_Shard
]

class ActionState(Enum):
    Pending = 0
    Running = 1
    Completed = 2
    Timeout = 3
    Failed = 4
    
class ModsModels(IntEnum):
    AxeGrip = 905
    AxeHaft = 893
    BowGrip = 906
    BowString = 894
    DaggerHandle = 6331
    DaggerTang = 6323
    FocusCore = 15551
    HammerGrip = 907
    HammerHaft = 895
    Inscription_EquippableItem = 17059
    Inscription_MartialWeapon = 15540
    Inscription_Offhand = 19123
    Inscription_OffhandOrShield = 15541
    Inscription_SpellcastingWeapon = 19122
    Inscription_Weapon = 15542
    ScytheGrip = 15553
    ScytheSnathe = 15543
    ShieldHandle = 15554
    SpearGrip = 15555
    Spearhead = 15544
    StaffHead = 896
    StaffWrapping = 908
    SwordHilt = 897
    SwordPommel = 909
    WandWrapping = 15552        

class ItemCategory(IntEnum):
    None_ = 0
    Sweet = 1
    Party = 2
    Alcohol = 3
    DeathPenaltyRemoval = 4
    Scroll = 5
    Tome = 6
    Key = 7
    Material = 8
    Trophy = 9
    RewardTrophy = 10
    QuestItem = 11
    RareWeapon = 12
        
class ItemSubCategory(IntEnum):
    None_ = 0
    Points_1 = 1
    Points_2 = 2
    Points_3 = 3
    Points_50 = 4
    LuckyPoint = 5
    CommonXPScroll = 6
    RareXPScroll = 7
    PassageScroll = 8
    NormalTome = 9
    EliteTome = 10
    CoreKey = 11
    PropheciesKey = 12
    FactionsKey = 13
    NightfallKey = 14
    CommonMaterial = 15
    RareMaterial = 16
    
class MaterialType(IntEnum):
    None_ = 0
    Common = 1
    Rare = 2

class MerchantType(IntEnum):
    None_ = 0
    Merchant = 1
    RuneTrader = 2
    ScrollTrader = 3
    DyeTrader = 4
    MaterialTrader = 5
    RareMaterialTrader = 6
    Collector = 7
    Crafter = 8

class ItemAction(IntEnum):
    NONE = 0
    Loot = 1
    Collect_Data = 2
    Identify = 3
    Hold = 4
    Stash = 5
    Salvage_Mods = 6
    Salvage = 7
    Salvage_Rare_Materials = 8
    Salvage_Common_Materials = 9
    Sell_To_Merchant = 10
    Sell_To_Trader = 11
    Destroy = 12
    Deposit_Material = 13    
        
class ActionModsType(IntEnum):
    Any = 0
    Old_School = 1
    Inscribable = 2
    
class LootAction(IntEnum):
    NONE = 0
    Loot = 1
    IGNORE = 2
    LOOT_IF_STACKABLE = 3

class LootItemMode(IntEnum):
    MODEL_ID = 0
    ITEM_TYPE = 1
    
class Campaign(IntEnum):
    None_ = 0
    Core = 1
    Prophecies = 2
    Factions = 3
    Nightfall = 4
    EyeOfTheNorth = 5

class MessageActions(IntEnum):
    None_ = 0
    PauseDataCollection = 1
    ResumeDataCollection = 2
    StartDataCollection = 3
    ReloadData = 4
    Start = 5
    Stop = 6
    ShowLootExWindow = 7
    HideLootExWindow = 8
    OpenXunlai = 9    
    ReloadWidgets = 10
    ReloadProfiles = 11
    LootStart = 12
    LootStop = 13
    
class SalvageOption(IntEnum):
    None_ = 0
    Prefix = 1
    Suffix = 2
    Inherent = 3
    CraftingMaterials = 4
    LesserCraftingMaterials = 5
    RareCraftingMaterials = 6
    
class SalvageKitOption(IntEnum):
    None_ = 0
    Lesser = 1
    LesserOrExpert = 2
    Expert = 3
    Perfect = 4

class WeaponType(IntEnum):
    Axe = 1
    Sword = 2
    Spear = 3
    Wand = 4
    Daggers = 5
    Hammer = 6
    Scythe = 7
    Bow = 8
    Staff = 9
    Focus = 10
    Shield = 11

class ModType(IntEnum):
    None_ = 0
    Inherent = 1
    Prefix = 2
    Suffix = 3

class EnemyType(IntEnum):
    Undead = 0
    Charr = 1
    Troll = 2
    Plant = 3
    Skeleton = 4
    Giant = 5
    Dwarf = 6
    Tengu = 7
    Demon = 8
    Dragon = 9
    Ogre = 10
    
class ModifierValueArg(IntEnum):
    None_ = -1
    Arg1 = 0
    Arg2 = 1
    Fixed = 2

class ModifierIdentifier(IntEnum):
    None_ = 0
    Requirement = 10136
    Damage = 42920
    Damage_NoReq = 42120
    DamageType = 9400
    ShieldArmor = 42936
    TargetItemType = 9656
    RuneAttribute = 8680
    HealthLoss = 8408
    ImprovedVendorValue = 9720
    HighlySalvageable = 9736